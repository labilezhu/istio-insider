# Istio 下 Envoy 配置举例

大部书籍和文档，都是按架构分层，自上而下(Top down) ，从概念、高层设计、基本原理、抽象流程去说明一个软件架构的。这个套路很学院派，也是非常稳重踏实的选择。但本节不采用这种方式。本节先举例分析一个具体场景下的现场分析。从具体和整体上，先让读者对设计有个感性的理解。再去分析为何要这样 “配置”，背后的抽象概念和基本原理。这样，可以让学习的人保持兴趣，也比较合符人类自然的，从具体中提炼出抽象的学习习惯。毕竟，笔者是个念过师范专业的人，虽然连个 "教师资格证" 也没拿到。

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


### 用日志检查数据流


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

```
envoy filter	original_dst: new connection accepted
envoy filter	tls inspector: new connection accepted
envoy filter	tls:onServerName(), requestedServerName: outbound_.8080_._.fortio-server.mark.svc.cluster.local
envoy conn_handler	[C12990] new connection from 172.21.206.228:52352

envoy http	[C12990] new stream
envoy http	[C12990][S11192089021443921902] request headers complete (end_stream=true):
':authority', 'fortio-server:8080'
':path', '/'
':method', 'GET'
'user-agent', 'curl/7.83.1'
'accept', '*/*'
'x-forwarded-proto', 'http'
'x-request-id', '437a5a3e-f057-4079-a959-dad3d7dcf6a6'
'x-envoy-decorator-operation', 'fortio-server.mark.svc.cluster.local:8080/*'
'x-envoy-peer-metadata', 'ChwKDkFQUF9DT05UQUlORVJTEgoaCG5ldHNob290ChoKCkNMVVNURVJfSUQSDBoKS3ViZXJuZXRlcwogCgxJTlNUQU5DRV9JUFMSEBoOMTcyLjIxLjIwNi4yMjgKGQoNSVNUSU9fVkVSU0lPThIIGgYxLjE0LjMKlAEKBkxBQkVMUxKJASqGAQokChlzZWN1cml0eS5pc3Rpby5pby90bHNNb2RlEgcaBWlzdGlvCi0KH3NlcnZpY2UuaXN0aW8uaW8vY2Fub25pY2FsLW5hbWUSChoIbmV0c2hvb3QKLwojc2VydmljZS5pc3Rpby5pby9jYW5vbmljYWwtcmV2aXNpb24SCBoGbGF0ZXN0ChoKB01FU0hfSUQSDxoNY2x1c3Rlci5sb2NhbAoSCgROQU1FEgoaCG5ldHNob290ChMKCU5BTUVTUEFDRRIGGgRtYXJrCj0KBU9XTkVSEjQaMmt1YmVybmV0ZXM6Ly9hcGlzL3YxL25hbWVzcGFjZXMvbWFyay9wb2RzL25ldHNob290ChcKEVBMQVRGT1JNX01FVEFEQVRBEgIqAAobCg1XT1JLTE9BRF9OQU1FEgoaCG5ldHNob290'
'x-envoy-peer-metadata-id', 'sidecar~172.21.206.228~netshoot.mark~mark.svc.cluster.local'

'x-envoy-attempt-count', '1'
'x-b3-traceid', '03824b6065cd13e0559df95ebf18def7'
'x-b3-spanid', '559df95ebf18def7'
'x-b3-sampled', '0'


envoy http	[C12990][S11192089021443921902] request end stream
envoy connection	[C12990] current connecting state: false
envoy router	[C12990][S11192089021443921902] cluster 'inbound|8080||' match for URL '/'
envoy upstream	transport socket match, socket default selected for host with address 172.21.206.230:8080
envoy upstream	Created host 172.21.206.230:8080.
envoy upstream	addHost() adding 172.21.206.230:8080
envoy upstream	membership update for TLS cluster inbound|8080|| added 1 removed 0
envoy upstream	re-creating local LB for TLS cluster inbound|8080||
envoy upstream	membership update for TLS cluster inbound|8080|| added 1 removed 0
envoy upstream	re-creating local LB for TLS cluster inbound|8080||
envoy router	[C12990][S11192089021443921902] router decoding headers:
':authority', 'fortio-server:8080'
':path', '/'
':method', 'GET'
':scheme', 'http'
'user-agent', 'curl/7.83.1'
'accept', '*/*'
'x-forwarded-proto', 'http'
'x-request-id', '437a5a3e-f057-4079-a959-dad3d7dcf6a6'

'x-envoy-attempt-count', '1'
'x-b3-traceid', '03824b6065cd13e0559df95ebf18def7'
'x-b3-spanid', '559df95ebf18def7'
'x-b3-sampled', '0'
'x-forwarded-client-cert', 'By=spiffe://cluster.local/ns/mark/sa/default;Hash=a3c273eef68529003f564ff48b906ea61630a25217edbc18b57495701d089904;Subject="";URI=spiffe://cluster.local/ns/mark/sa/default'

envoy pool	queueing stream due to no available connections
envoy pool	trying to create new connection
envoy pool	creating a new connection
envoy connection	[C12991] current connecting state: true
envoy client	[C12991] connecting
envoy connection	[C12991] connecting to 172.21.206.230:8080
envoy connection	[C12991] connection in progress
envoy upstream	membership update for TLS cluster inbound|8080|| added 1 removed 0
envoy upstream	re-creating local LB for TLS cluster inbound|8080||
envoy connection	[C12991] connected
envoy client	[C12991] connected
envoy pool	[C12991] attaching to next stream
envoy pool	[C12991] creating stream
envoy router	[C12990][S11192089021443921902] pool ready
envoy client	[C12991] response complete
envoy router	[C12990][S11192089021443921902] upstream headers complete: end_stream=true
envoy http	[C12990][S11192089021443921902] encoding headers via codec (end_stream=true):
':status', '200'
'date', 'Sun, 28 Aug 2022 13:46:17 GMT'
'content-length', '0'
'x-envoy-upstream-service-time', '2'
'x-envoy-peer-metadata', 'ChwKDkFQUF9DT05UQUlORVJTEgoaCG1haW4tYXBwChoKCkNMVVNURVJfSUQSDBoKS3ViZXJuZXRlcwogCgxJTlNUQU5DRV9JUFMSEBoOMTcyLjIxLjIwNi4yMzAKGQoNSVNUSU9fVkVSU0lPThIIGgYxLjE0LjMK3AEKBkxBQkVMUxLRASrOAQoWCgNhcHASDxoNZm9ydGlvLXNlcnZlcgopChZhcHAua3ViZXJuZXRlcy5pby9uYW1lEg8aDWZvcnRpby1zZXJ2ZXIKJAoZc2VjdXJpdHkuaXN0aW8uaW8vdGxzTW9kZRIHGgVpc3RpbwoyCh9zZXJ2aWNlLmlzdGlvLmlvL2Nhbm9uaWNhbC1uYW1lEg8aDWZvcnRpby1zZXJ2ZXIKLwojc2VydmljZS5pc3Rpby5pby9jYW5vbmljYWwtcmV2aXNpb24SCBoGbGF0ZXN0ChoKB01FU0hfSUQSDxoNY2x1c3Rlci5sb2NhbAoXCgROQU1FEg8aDWZvcnRpby1zZXJ2ZXIKEwoJTkFNRVNQQUNFEgYaBG1hcmsKQgoFT1dORVISORo3a3ViZXJuZXRlczovL2FwaXMvdjEvbmFtZXNwYWNlcy9tYXJrL3BvZHMvZm9ydGlvLXNlcnZlcgoXChFQTEFURk9STV9NRVRBREFUQRICKgAKIAoNV09SS0xPQURfTkFNRRIPGg1mb3J0aW8tc2VydmVy'
'x-envoy-peer-metadata-id', 'sidecar~172.21.206.230~fortio-server.mark~mark.svc.cluster.local'
'server', 'istio-envoy'

envoy wasm	wasm log stats_inbound stats_inbound: [extensions/stats/plugin.cc:645]::report() metricKey cache hit , stat=12
envoy wasm	wasm log stats_inbound stats_inbound: [extensions/stats/plugin.cc:645]::report() metricKey cache hit , stat=6
envoy wasm	wasm log stats_inbound stats_inbound: [extensions/stats/plugin.cc:645]::report() metricKey cache hit , stat=10
envoy wasm	wasm log stats_inbound stats_inbound: [extensions/stats/plugin.cc:645]::report() metricKey cache hit , stat=14
envoy pool	[C12991] response complete
envoy pool	[C12991] destroying stream: 0 remaining
```

下图说明日志相关的组件与源码链接：

:::{figure-md} 图：Istio里的 Envoy Inbound 组件与日志
:class: full-width
<img src="envoy@istio-conf-eg.assets/log-envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound 组件与日志*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Flog-envoy@istio-conf-eg-inbound.drawio.svg)*



### 用 bpftrace 检查数据流

见我的 Blog: [逆向工程与云原生现场分析 Part3 —— eBPF 跟踪 Istio/Envoy 事件驱动模型、连接建立、TLS 握手与 filter_chain 选择](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part3/)
