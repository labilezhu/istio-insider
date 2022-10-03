---
typora-root-url: ../../..
---

# Listener

开始讲 Listener 前，让我们回到 {doc}`/ch2-envoy/envoy@istio-conf-eg` 的例子。

```{note}
这里下载 Envoy 的配置 yaml {download}`envoy@istio-conf-eg-inbound.envoy_conf.yaml </ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.envoy_conf.yaml>` .
```

:::{figure-md}
:class: full-width

<img src="/ch1-istio-arch/istio-ports-components.assets/istio-ports-components.drawio.svg" alt="Istio端口与组件">

*图：Istio 端口与组件*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-ports-components.drawio.svg)*

:::{figure-md}
:class: full-width
<img src="/ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-inbound.drawio.svg)*

:::{figure-md}
:class: full-width
<img src="/ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-outbound.drawio.svg" alt="图：Istio里的 Envoy Outbound 配置举例">

*图：Istio里的 Envoy Outbound 配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-outbound.drawio.svg)*

## Listener 举例
上面的例子中，读者可以看到很多 Istio 配置的 Listener 的身影：

Inbound:
-  端口：15006
   -  名字：virtualInbound
   -  职责：主要的 Inbound Listener
-  端口：15090
-  端口：15000
-  ...

Outbound:
- Bind soket 的 Listener
  - 端口：15001
    - 名字：virtualOutbound
    - 职责：主要的 Outbound Listener。转发 iptable 劫持的流量到下面的 Listener
- 不 Bind soket 的 Listener
  - 名字：0.0.0.0_8080
  - 职责：所有监听 8080 端口的 upstream cluster 流量，都会经由这个 Listener 出去。
  - 配置
    - bind_to_port: false

可见，Istio 给 Listener 的名字，取得有点不太好理解。实际监听 TCP 端口的，叫 virtualInbound/virtualOutbound，真监听 TCP 端口的，反而没有 `virtual` 这个前缀。


## Listener 内部组件

:::{figure-md} 图：Listener 内部组件

<img src="/ch2-envoy/arch/listener/listener.assets/listener.drawio.svg" alt="图：Listener 内部组件">

*图：Listener 内部组件*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Flistener.drawio.svg)*


Listener 由 Listener filters 、Network Filter Chains 组成。

### Listener filters

如，上面的 [图：Istio里的 Envoy Inbound配置举例] 中，可以看到几个 Listener filters:
 - envoy.filters.listener.original_dst
 - envoy.filters.listener.tls_inspector
 - envoy.filters.listener.http_inspector
图中已经陈述了相关的功能。

### Network Filter Chains
如，上面的 [图：Istio里的 Envoy Inbound配置举例] 中，可以看到几个 Network Filter Chains，它们的名字是可以重复的。而其中每个都有有自己的`filter_chain_match`  ，用于指定连接到底要匹配到哪个 `Network Filter Chain`。  

每个 `Network Filter Chain` 由顺序化的 `Network Filter` 组成。 

### Network Filter

Envoy 对为保证扩展性，处理组件采用多层插件化的设计。其中，Network Filter 就是 L2 / L3 (IP/TCP) 层的组件了。如，上面的 [图：Istio里的 Envoy Inbound配置举例] 中，顺序地有：
1. istio.metadata_exchange
2. envoy.filters.network.http_connection_manager
两个 Network Filter。其中，主要逻辑当然在 `http_connection_manager` 了。

#### request 向与 response 向的 Network Filter 关系

Envoy 的官方文档，说明了 request 向与 response 向的 filter 关系：

请求：
![](./listener.assets/lor-network-read.svg)
响应：
![](./listener.assets/lor-network-write.svg)


*图源：[Network filter chain processing](https://www.envoyproxy.io/docs/envoy/latest/intro/life_of_a_request#network-filter-chain-processing)*


## 代码抽象

写到这里，是时候看看代码了。不过，不是直接看，先看看 C++ 类图吧。


:::{figure-md} 图：Listener 内部组件类图

<img src="/ch2-envoy/arch/listener/listener.assets/network-filter-code-oop.drawio.svg" alt="图：Listener 内部组件类图">

*图：Listener 内部组件类图*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-code-oop.drawio.svg)*
