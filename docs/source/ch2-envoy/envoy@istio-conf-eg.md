# Istio 里的 Envoy 配置(草稿)

要理解 Istio 数据面基理，首先要看懂 sidecar proxy - Envoy 的配置。本节用一个例子，看看 istiod 写了什么 “代码” 去控制这个 “可编程代理” —— Envoy 。

```{note}
本节的实验环境说明见于： {ref}`appendix-lab-env/appendix-lab-env-base:简单分层实验环境`
```

首先看看 Envoy 的配置：

```bash
kubectl exec fortio-server -c istio-proxy  -- \
curl 'localhost:15000/config_dump?include_eds' | \
yq eval -P > envoy@istio-conf-eg-inbound.envoy_conf.yaml
```

```{note}
这里下载 {download}`envoy@istio-conf-eg-inbound.envoy_conf.yaml <envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.envoy_conf.yaml>` .
```

## 数据流 “推断”

分析上面获取到的 Envoy 配置，可以 “推断” 到下面 Inbound 数据流图：

:::{figure-md} 图：Istio里的 Envoy Inbound 配置举例

<img src="envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-inbound.drawio.svg)*


喜欢较真的程序员，对 “推断” 的事情有天然的不安感。那么，我们想法子 debug 一下，验证上图的可靠性。


### 核实 “推断”数据流

在 k8s cluster 内发起请求：

开一个专用终端窗口，监控日志：
```bash
k logs -f fortio-server -c istio-proxy
```

修改日志级别：
```bash

k exec fortio-server -c istio-proxy -- curl -XPOST http://localhost:15000/logging
k exec fortio-server -c istio-proxy -- curl -XPOST curl -XPOST 'http://localhost:15000/logging?level=debug'
```

发起请求：
```bash
k exec -it netshoot -- curl -v http://fortio-server:8080/
```


