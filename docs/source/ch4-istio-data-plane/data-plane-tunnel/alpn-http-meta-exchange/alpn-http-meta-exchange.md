---
typora-root-url: ../../..
---

# 基于 ALPN 的 HTTP 元信息交换(Meta Exchange)






让我们从一个例子开始：
```
[serviceA app --h2c--> serviceA istio-proxy] ----(http over mTLS)---> [serviceB istio-proxy --h2c--> serviceB app]
```

Istio Proxy 的一个基本设计原则是尽早知道新连接的下游/上游元数据。因为这样就能尽早做出一些决定。





**对于 client side(Outbound) `Istio proxy` :**

如果它事先知道 upstream cluster 的元数据：
- upstream cluster 是同一个 Istio 网格上的另一个 "Istio Proxy"？
- upstream cluster 支持哪种类型的 TLS？Istio 网格的自动 mTLS 还是手动传统 TLS？
- upstream cluster 支持哪种应用级协议：http1.1、http2 还是 http3？

client side(Outbound) Istio Proxy 也可以根据 downstream（同一 pod 上的应用程序）连接决定 upstream 的 HTTP 版本，参见 [use_downstream_protocol_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-use-downstream-protocol-config)。



client side(Outbound) Istio Proxy 可以根据 upstream 服务器支持的 HTTP 版本覆盖(overwrite) ALPN 协议列表。


**对于 server side(Inbound) `Istio proxy` :**

例如，当 `Istio Proxy` 接受来自 downstream 的新连接时，它想知道 downstream 的一些元数据：
- downstream 是同一个 Istio 网格上的另一个 Istio Proxy 吗？
- downstream 支持哪种类型的 TLS？Istio 网格的自动 mTLS 还是手动传统 TLS？
- downstream 支持哪种应用级协议：http1.1、http2 还是 http3？

作为服务器的 "Istio Proxy" 将根据上述 downstream 元数据决定 `Network Filter Chains` 和 `Http Filter Chains` 的选择。


## 术语

- h2c - `基于 TCP 的 HTTP/2` 或 `HTTP/2 明文（Cleartext）`
- h2 - `基于 TLS 的 HTTP/2`  (使用 ALPN 作协议协商)
- ALPN - [基于 TLS 的 `ALPN(Application-Layer Protocol Negotiation 应用层协议协商)`](https://en.wikipedia.org/wiki/Application-Layer_Protocol_Negotiation)



## outbound istio-proxy 与 inbound istio-proxy 的协作



上节显示，inbound 和 outbound istio-proxy 需要合作协商 HTTP 版本。下图为一个示例的协作流程：





:::{figure-md} 图: HTTP 协议元数据交换概述

<img src="/ch4-istio-data-plane/data-plane-tunnel/alpn-http-meta-exchange/alpn-http-meta-exchange-high-level.drawio.svg" alt="图 - HTTP 协议元数据交换概述">

*图: HTTP 协议元数据交换概述*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Falpn-http-meta-exchange-high-level.drawio.svg)*


- Outbound istio-proxy

基于 `istio.alpn HTTP Filter`  和 `Upstream Cluster` 元数据。



- Inbound istio-proxy

基于 `Listener->filter_chains->filter_chain_match->application_protocols` 配置和 Outbound istio-proxy 提供的 ALPN 。





ALPN HTTP Meta Exchange 的故障排除示例： {doc}`/troubleshooting/istio-troubleshooting/http_protocol_options-accidentally-disable-http2/http_protocol_options-accidentally-disable-http2`


下图深入探究了 Envoy Proxy 和 Istio Proxy 的相关源码。它展示了背后的实现原理：



:::{figure-md}

<img src="/troubleshooting/istio-troubleshooting/http_protocol_options-accidentally-disable-http2/upstream-http-protocol-selection-src.drawio.svg" alt="图 - upstream http 协议选择示例">

*图: upstream http 协议选择示例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fupstream-http-protocol-selection-src.drawio.svg)*



## 扩展阅读
- [Better Default Networking – Protocol sniffing](https://docs.google.com/document/d/1l0oVAneaLLp9KjVOQSb3bwnJJpjyxU_xthpMKFM_l7o/edit#heading=h.edsodfixs1x7)
- [Istio MTLS Smartness Explained](https://devops-insider.mygraphql.com/zh-cn/latest/service-mesh/istio/istio-mtls/istio-mtls-smartness-explained.html#alpn)


