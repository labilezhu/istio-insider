# Envoy 请求与响应时序线

本质上说，Envoy 就是一个代理。说起代理，第一反应应该是有以下流程的软件/硬件：
1. 接收来自 `downstream` 的 `Request`
2. 做一些逻辑，必要时修改 `Request` ，并判定`upstream`目的地
3. 转发（修改后）的 `Request` 到`upstream`
4. 如果协议是一个 `Request` & `Reponse` 式的协议（如 HTTP）
   1. 代理通常会接收`upstream`的`Response`
   2. 做一些逻辑，必要时修改 `Response` 
   3. 转发 `Response` 给 `downstream`

的确，这也是 Envoy 代理 HTTP 协议的概要流程。但 Envoy 还要实现很多特性：
1. 高效的 `downstream` / `upstream` 传输 ➡️ 需要`连接复用`与`连接池`
2. 灵活配置的转发目标服务策略 ➡️ 需要 `Router`配置策略与实现逻辑
3. 弹性服务 (resilient microservices)
   1. 负载均衡
   2. 突发流量的削峰平谷 ➡️ 请求排队： pending request
   3. 应对异常 upstream、熔断器、保护服务不雪崩 ➡️ 各种 timeout 配置、 Health checking 、 Outlier detection 、 Circuit breaking
   4. 弹性重试 ➡️ retry
4. 可观察性 ➡️ 无处不在的性能指标
5. 动态编程配置 ➡️ xDS: EDS/LDS/...

要实现这些特性，请求与响应的流程自然不可能简单。
按本书的习惯，先上图。后面，对这个图一步步展开和说明。


:::{figure-md} 图：Envoy 请求与响应时序线
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline.drawio.svg" alt="图：Envoy 请求与响应时序线">

*图：Envoy 请求与响应时序线*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline.drawio.svg)*


## 一些有趣的扩展阅读

> - https://www.istioworkshop.io/09-traffic-management/06-circuit-breaker/
> - https://tech.olx.com/demystifying-istio-circuit-breaking-27a69cac2ce4 