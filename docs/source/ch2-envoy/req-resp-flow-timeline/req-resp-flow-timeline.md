# Envoy 请求与响应调度 

🎤 正式开编前。想说说我(Mark) 为何去研究 Envoy 的请求与响应调度。因为一个工作需要，需要对 Istio 网格节点故障快速恢复做一些调研。我翻阅了大量的 Istio/Envoy 文档、大咖 Blog。看到很多很杂乱的信息：
 - 健康检测
 - 熔断
 - Envoy 中的各个神秘又关系千丝万缕的 timeout 配置
 - Retry
 - `TCP keepalive`、`TCP_USER_TIMEOUT` 配置

杂乱到最后，我不得不写个文章去梳理一下信息：[Istio 网格节点故障快速恢复初探](https://blog.mygraphql.com/zh/posts/low-tec/network/tcp-close/tcp-half-open/) 。 但信息是梳理了，基础原理却没理顺。可以我下决心去钻研一下 Envoy 的文档。是的，其实 Envoy 的文档已经写得比较细致。只是：
 - 信息散落在一个个网页中，无法用时序和流程的方法组织起来，构成一个有机的整体。
 - 不去了解这个整体协作关系，只是一个一个参数分开来看，是无法理性去权衡这些参数的。
 - 指标与指标，指标与参数，与是有关系的
 - 而上面的关系，都可以通过请求与响应调度流程来串联起来

基于上面原因。我从文档、参数、指标推导出以下流程。暂时未在代码中验证，请谨慎参考。


## 请求与响应调度

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

```{hint}
互动图书：
 - 建议用 Draw.io 打开。图中包含大量的链接，链接到每一个组件、配置项、指标的文档说明。
 - 双屏，一屏看图，一屏看文档，是本书的正确阅读姿势。如果你在用手机看，那么，忽略我吧 🤦
```

:::{figure-md} 图：Envoy 请求与响应调度
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline-schedule.drawio.svg" alt="图：Envoy 请求与响应调度">

*图：Envoy 请求与响应调度*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline-schedule.drawio.svg)*


上图是请求在组件间的流转图。

先说说请求组件流转部分，流程图可以视为（未原全验证，存在部分推理）：

:::{figure-md} 图：Envoy 请求调度流程图
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline-flowchart.drawio.svg" alt="图：Envoy 请求与响应时序线">

*图：Envoy 请求调度流程图*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline-flowchart.drawio.svg)*


## 请求与响应调度时序线

下图是请求与响应的时序线，以及相关的 timeout 配置与产生的指标，以及它们的关系。

:::{figure-md} 图：Envoy 请求与响应时序线
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline.drawio.svg" alt="图：Envoy 请求与响应时序线">

*图：Envoy 请求与响应时序线*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline.drawio.svg)*


## 一些有趣的扩展阅读

> - https://www.istioworkshop.io/09-traffic-management/06-circuit-breaker/
> - https://tech.olx.com/demystifying-istio-circuit-breaking-27a69cac2ce4 