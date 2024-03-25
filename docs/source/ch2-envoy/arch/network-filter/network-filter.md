---
typora-root-url: ../../..
---

# Network Filter

## Network Filter Chains
在前面章節的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，可以看出，一个 Listener 可以包含多个 `Network Filter Chain`。而其中每个 Chain 都有自己的 `filter_chain_match`  ，用于配置新建立的 `Inbound Connection` 选定 `Network Filter Chain` 的策略。

每个 `Network Filter Chain` 都有自己的名字。需要注意的是，`Network Filter Chain` 的名字是允许重复的。

每个 `Network Filter Chain` 又由顺序化的 `Network Filter` 组成。 

## Network Filter

Envoy 对为保证扩展性，采用多层插件化的设计模式。其中，`Network Filter` 就是 L2 / L3 (IP/TCP) 层的组件。如，上面的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，顺序地有：
1. istio.metadata_exchange
2. envoy.filters.network.http_connection_manager

两个 Network Filter。其中，主要逻辑当然在 `http_connection_manager` 了。

### Network Filter 框架设计概念

我在学习 Envoy 的  Network Filter 框架设计时，发现它和我想像中的 Filter 设计非常不同。甚至有点违反我的直觉。见下图：

:::{figure-md} 图：Model of Network Filter Framework

<img src="/ch2-envoy/arch/network-filter/network-filter-framework-concept.drawio.svg" alt="图：Model of Network Filter Framework">

*图：Model of Network Filter Framework*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-framework-concept.drawio.svg)*

以下仅以 ReadFilter 说说：

`我直觉中的模型(My intuition Ideal model)` 是：
 1. Filter 框架层有 `Upstream` 这个概念
 2. 一个 Filter 的输出数据和事件，会是下一个 Filter 的输入数据和事件。因为这叫 Chain，应该和 Linux 的 `cat myfile | grep abc | grep def` 类似。
 3. Filter 之间逻辑上的 Buffer 应该是隔离的。


而 `现实的模型(Realistic model)` 中
1. 框架层面，没有 `Upstream` 这个概念。Filter 实现自行实现/不实现 Upstream，包括连接建立和数据读写，事件通知。所以，框架层面，更没有 Cluster / Connection Pool 等等概念了。
2. 见下面一项
3. Filter 之间共享了 Buffer，前面的 Filter 对 Buffer 的读操作，如果沒进行 `drained(排干)` ，后面的 Filter 将会重复读取数据。前面的 Filter 也可以在 Buffer 中插入新数据。 而这个有状态的 Buffer，会传递到后面的 Filter 。

### Network Filter 对象关系

写到这里，是时候看看代码了。不过，不是直接看，先看看 C++ 类图吧。


:::{figure-md} 图：Network Filter 对象关系

<img src="/ch2-envoy/arch/network-filter/network-filter-hierarchy.drawio.svg" alt="图：Network Filter 对象关系">

*图：Network Filter 对象关系*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-hierarchy.drawio.svg)*


可见，大家日常生活中，WriteFilter 并不常用 :) 。


### Network Filter 框架设计细说
在代码实现层， Network Filter 框架下，抽象对象间的协作关系如下：

:::{figure-md} 图：网络过滤器框架抽象协作

<img src="/ch2-envoy/arch/network-filter/network-filter-framework.drawio.svg" alt="图：网络过滤器框架抽象协作">

*图：网络过滤器框架抽象协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-framework.drawio.svg)*


下面，以经典的 TCP Proxy Fitler 为例，说明一下。


:::{figure-md} 图：Network Filter Framework - TCP 代理过滤器示例

<img src="/ch2-envoy/arch/network-filter/network-filter-tcpproxy.drawio.svg" alt="图：Network Filter Framework - TCP 代理过滤器示例">

*图：Network Filter Framework - TCP 代理过滤器示例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-tcpproxy.drawio.svg)*


#### Network Filter - ReadFilter 协作

:::{figure-md} 图：Network Filter - ReadFilter 协作

<img src="/ch2-envoy/arch/network-filter/network-filter-readfilter.drawio.svg" alt="图：Network Filter - ReadFilter 协作">

*图：Network Filter - ReadFilter 协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-readfilter.drawio.svg)*

ReadFilter 协作比较复杂，也是 Network Filter Framework 的核心逻辑。所以要细说。
如前所言， Framework 本身没的直接提供 Upstream / Upstream Connection Pool / Cluster / Route 这些抽象对象和相关事件。而这里，我们暂且把这些称为：`外部对象与事件`。Filter 实现需要自己去创建或获取这些 `外部对象`，也需要自己去监听这些 `外部事件` 。`外部事件` 可能包括：

- Upstream 域名解释完成
- Upstream Connection Pool 连接可用
- Upstream socket read ready
- Upstream write buffer full
- ...




#### Network Filter - WriteFilter 协作

:::{figure-md} 图：NNetwork Filter - WriteFilter 协作

<img src="/ch2-envoy/arch/network-filter/network-filter-writefilter.drawio.svg" alt="图：Network Filter - WriteFilter 协作">

*图：Network Filter - WriteFilter 协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-writefilter.drawio.svg)*

由于 `WriteFilter` 在 Envoy 中使用场景有限，只有 MySQLFilter / PostgresFilter / KafkaBrokerFilter 和 Istio 的 MetadataExchangeFilter 。所以这里就不展开说明了。

## 扩展阅读

如果有兴趣研究 Listener 的实现细节，建议看看我 Blog 的文章：
 - [逆向工程与云原生现场分析 Part2 —— eBPF 跟踪 Istio/Envoy 之启动、监听与线程负载均衡](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part2/)
 - [逆向工程与云原生现场分析 Part3 —— eBPF 跟踪 Istio/Envoy 事件驱动模型、连接建立、TLS 握手与 filter_chain 选择](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part3/)
 - [Taming a Network Filter](https://blog.envoyproxy.io/taming-a-network-filter-44adcf91517)