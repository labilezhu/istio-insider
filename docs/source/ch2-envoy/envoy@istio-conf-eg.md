# Istio 里的 Envoy 配置(草稿)

要理解 Istio 数据面基理，首先要看懂 sidecar proxy - Envoy 的配置。本节用一个例子，看看 istiod 写了什么 “代码” 去控制这个 “可编程代理” —— Envoy 。

## 实验环境

本节的实验环境说明见于： {ref}`appendix-lab-env/appendix-lab-env-base:简单分层实验环境`。  


架构图：
:::{figure-md} 图:Istio 里的 Envoy 配置 - 部署

<img src="/ch1-istio-arch/istio-data-panel-arch.assets/istio-data-panel-arch.drawio.svg" alt="Inbound与Outbound概念">

*图:Istio 里的 Envoy 配置 - 部署*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-data-panel-arch.drawio.svg)*



首先看看 Envoy 的配置：

```bash
kubectl exec fortio-server -c istio-proxy  -- \
curl 'localhost:15000/config_dump?include_eds' | \
yq eval -P > envoy@istio-conf-eg-inbound.envoy_conf.yaml
```

```{note}
这里下载 {download}`envoy@istio-conf-eg-inbound.envoy_conf.yaml <envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.envoy_conf.yaml>` .
```

下面先不展开说明配置文件，直接看分析过程，最后，会回归到这个配置中。

## 数据流 “推断”

分析上面获取到的 Envoy 配置，可以 “推断” 到下面 Inbound 数据流图：

:::{figure-md} 图：Istio里的 Envoy Inbound 配置举例
:class: full-width
<img src="envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-inbound.drawio.svg)*


喜欢较真的程序员，对 “推断” 的事情有天然的不安感。那么，我们想法子 debug 一下，验证上图的可靠性。


### 核实 “推断”数据流


1. 开始前，先看看环境细节：

```bash
labile@labile-T30 ➜ labile $ k get pod netshoot -owide
NAME       READY   STATUS    RESTARTS   AGE   IP               NODE        NOMINATED NODE   READINESS GATES
netshoot   2/2     Running   11         8d    172.21.206.228   worknode5   <none>           <none>


labile@labile-T30 ➜ labile $ k get pod fortio-server -owide
NAME            READY   STATUS    RESTARTS   AGE   IP               NODE        NOMINATED NODE   READINESS GATES
fortio-server   2/2     Running   11         8d    172.21.206.230   worknode5   <none>           <none>


labile@labile-T30 ➜ labile $ k get svc fortio-server      
NAME            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                                        AGE
fortio-server   NodePort   10.96.215.136   <none>        8080:32463/TCP,8070:32265/TCP,8079:30167/TCP   8d


labile@labile-T30 ➜ labile $ k get endpoints fortio-server 
NAME            ENDPOINTS                                                     AGE
fortio-server   172.21.206.230:8079,172.21.206.230:8070,172.21.206.230:8080   8d

```



2. 开一个专用 `监控日志终端窗口`，：
```bash
k logs -f fortio-server -c istio-proxy
```

3. 看看客户端(netshoot) 到 fortio-server 的连接情况。发现未有连接，即到 fortio-server 的连接池未初始化。

```
$ k exec -it netshoot -- ss -tr

State Recv-Q Send-Q Local Address:Port                           Peer Address:Port Process
ESTAB 0      0          localhost:52012                             localhost:15020       
ESTAB 0      0          localhost:51978                             localhost:15020       
ESTAB 0      0           netshoot:53522 istiod.istio-system.svc.cluster.local:15012       
ESTAB 0      0           netshoot:42974 istiod.istio-system.svc.cluster.local:15012       
ESTAB 0      0          localhost:15020                             localhost:52012       
ESTAB 0      0          localhost:15020                             localhost:51978       
```

解释一下上面的命令。`-t` 是只看 tcp 连接。`-r` 是尝试对 ip 地址反向解释回域名。

````{tip}
如果你的环境中发现已经有连接，那么，强制断开它。因为后面要分析一下建立新连接的日志。这里有个 强制断开连接的 ss 命令的秘技：
```bash
k exec -it netshoot -- ss -K 'dst 172-21-206-230.fortio-server.mark.svc.cluster.local'
```
其中 `dst 172-21-206-230.fortio-server.mark.svc.cluster.local` 是个过滤器条件，用于指定执行断开的连接。命令的意思是断开`对端目标地址`为 `172-21-206-230.fortio-server.mark.svc.cluster.local` 的连接。`172-21-206-230.fortio-server.mark.svc.cluster.local`就是 k8s 自动给这个 fortio-server POD 的域名了。
````


3. 修改日志级别：
```bash

k exec fortio-server -c istio-proxy -- curl -XPOST http://localhost:15000/logging
k exec fortio-server -c istio-proxy -- curl -XPOST curl -XPOST 'http://localhost:15000/logging?level=debug'
```



4. 在 k8s cluster 内发起请求：
```bash
sleep 5 && k exec -it netshoot -- curl -v http://fortio-server:8080/
```

5. 查看连接
```bash
$ k exec -it netshoot -- ss -trn | grep fortio

State  Recv-Q  Send-Q     Local Address:Port                                             Peer Address:Port   Process  
...
ESTAB  0       0               netshoot:52352     172-21-206-230.fortio-server.mark.svc.cluster.local:8080            
...
```

6. 查看日志
这时，在之前打开的 `监控日志终端窗口` 中，应该可以看到日志：

:::{figure-md} 图：Istio里的 Envoy Inbound 组件与日志
:class: full-width
<img src="envoy@istio-conf-eg.assets/log-envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound 组件与日志*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Flog-envoy@istio-conf-eg-inbound.drawio.svg)*

