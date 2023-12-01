# Network Filter

## Network Filter Chains
在前面章節的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，可以看出，一个 Listener 可以包含多个 `Network Filter Chain`。而其中每个 Chain 都有自己的 `filter_chain_match`  ，用于说明新建立的 `Inbound Connection` 选用哪个 `Network Filter Chain`。

每个 `Network Filter Chain` 都有自己的名字。需要注意的是，`Network Filter Chain` 的名字是允许重复的。

每个 `Network Filter Chain` 又由顺序化的 `Network Filter` 组成。 

## Network Filter

Envoy 对为保证扩展性，采用多层插件化的设计模式。其中，`Network Filter` 就是 L2 / L3 (IP/TCP) 层的组件。如，上面的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，顺序地有：
1. istio.metadata_exchange
2. envoy.filters.network.http_connection_manager

两个 Network Filter。其中，主要逻辑当然在 `http_connection_manager` 了。

### request 向与 response 向的 Network Filter 关系

Envoy 的官方文档，说明了 read downstream request 向与 write downstream response 向的 filter 关系：

read downstream request：
![](/ch2-envoy/arch/listener/listener.assets/lor-network-read.svg)
write downstream response：
![](/ch2-envoy/arch/listener/listener.assets/lor-network-write.svg)


*图源：[Network filter chain processing](https://www.envoyproxy.io/docs/envoy/latest/intro/life_of_a_request#network-filter-chain-processing)*


## 代码抽象

写到这里，是时候看看代码了。不过，不是直接看，先看看 C++ 类图吧。


:::{figure-md} 图：network-filter 类抽象层级

<img src="/ch2-envoy/arch/network-filter/network-filter-hierarchy.drawio.svg" alt="图：network-filter 类抽象层级">

*图：network-filter 类抽象层级*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-hierarchy.drawio.svg)*


## 扩展阅读

如果有兴趣研究 Listener 的实现细节，建议看看我 Blog 的文章：
 - [逆向工程与云原生现场分析 Part2 —— eBPF 跟踪 Istio/Envoy 之启动、监听与线程负载均衡](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part2/)
 - [逆向工程与云原生现场分析 Part3 —— eBPF 跟踪 Istio/Envoy 事件驱动模型、连接建立、TLS 握手与 filter_chain 选择](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part3/)
 - [Taming a Network Filter](https://blog.envoyproxy.io/taming-a-network-filter-44adcf91517)