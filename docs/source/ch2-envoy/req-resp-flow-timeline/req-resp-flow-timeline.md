---
typora-root-url: ../..
---

# Envoy 请求与响应调度 

🎤 正式开编前。想说说写本节的一些故事缘由。为何去研究 Envoy 的请求与响应调度？  

缘起于一个客户需求，需要对 Istio 网格节点故障快速恢复做一些调研。为此，我翻阅了大量的 Istio/Envoy 文档、大咖 Blog。看了很多很杂乱的信息：
 - 健康检测
 - 熔断
 - Envoy 中的各个神秘又关系千丝万缕的 timeout 配置
 - 请求 Retry
 - `TCP keepalive`、`TCP_USER_TIMEOUT` 配置

杂乱到最后，我不得不写个文章去梳理一下信息：[Istio 网格节点故障快速恢复初探](https://blog.mygraphql.com/zh/posts/low-tec/network/tcp-close/tcp-half-open/) 。 但信息是梳理了，基础原理却没理顺。于是，我下决心去钻研一下 Envoy 的文档。是的，其实 Envoy 的文档已经写得比较细致。只是：
 - 信息散落在一个个网页中，无法用时序和流程的方法组织起来，构成一个有机的整体。
 - 不去了解这个整体协作关系，只是一个一个参数分开来看，是无法理性去权衡这些参数的。
 - 指标与指标，指标与参数，关系复杂
 - 而上面的关系，都可以通过请求与响应调度流程串联起来

基于上面原因。我从文档、参数、指标推导出以下流程。<mark>注意：暂时未在代码中验证，请谨慎参考。</mark>

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
3. 弹性服务 (resilient micro-services)
   1. 负载均衡
   2. 突发流量的削峰平谷 ➡️ 请求排队： pending request
   3. 应对异常 upstream、熔断器、保护服务不雪崩 ➡️ 各种 timeout 配置、 Health checking 、 Outlier detection 、 Circuit breaking
   4. 弹性重试 ➡️ retry
4. 可观察性 ➡️ 无处不在的性能指标
5. 动态编程配置接口 ➡️ xDS: EDS/LDS/...

要实现这些特性，请求与响应的流程自然不可能简单。  

```{hint}
看到这里，读者可能有疑问，本节的标题叫 “请求与响应调度” ？ 难度 Envoy 需要类似 Linux Kernel 调度线程一样，去调度处理 Request 吗？   

对的，你说到点上了。
```

Envoy 应用了 `事件驱动` 设计模式。`事件驱动` 的程序，相对于 `非事件驱动` 的程序，可以用更少的线程，更灵活地控制在什么时候做什么任务，即更灵活的调度逻辑。且更绝的是：由于线程间共享的数据不多，线程的数据并发控制同时被大大简化。

在本节中，事件类型最少有：

 - 外部的网络可读、可写、连接关闭事件
 - 各类定时器
   - 重试定时
   - 各种超时配置定时

由于使用了无限的请求分配到有限的线程的模式，加上请求可能需要重试，所以线程一定要有一系列的逻辑，来 “排序” 什么请求应该先处理。什么请求由于 `超时` 或资源使用 `超过配置上限` 而应立即返回失败。

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
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline-schedule.drawio.svg)*

### 相关组件

上图是尝试说明 `Envoy 请求与响应调度 ` 过程，以及串联相关的组件。其中可以看到一些组件：

- Listener - 应答 downstream 连接请求
- HTTP Connection Manager(HCM) - HTTP 的核心组件，推动 http 流的读取、解释、路由(Router)
- HCM-router - HTTP 路由核心组件，职责是:
  - 判定 HTTP 下一跳的目标 cluster，即 upsteam cluster
  - 重试
- Load balancing - upstream cluster 内的负载均衡
- pending request queue - `等待连接池可用连接的请求队列`
- requests bind to connection - 已经分配到连接的请求
- connection pool - worker 线程与 upstream host 专用的连接池
- health checker/Outlier detection - upsteam host 健康监视，发现异常 host 并隔离。

和一些  `Circuit breaking(熔断开关) `上限条件：

- `max_retries` - 最大重试并发上限
- `max_pending_requests` -  `pending request queue` 的队列上限
- `max_request` - 最大并发请求数上限
- `max_connections` - upstream cluster 的最大连接上限

需要注意的是，上面的参数是对于整个 upstream cluster 的，即是所有 worker thread、upstream host 汇总的上限。

### 相关的监控指标

我们用类似著名的 [Utilization Saturation and Errors (USE)](https://www.brendangregg.com/usemethod.html) 方法学来分类指标。

资源过载型的指标：

- [downstream_cx_overflow](https://www.envoyproxy.io/docs/envoy/v1.15.2/configuration/listeners/stats#listener:~:text=downstream_cx_overflow)
- upstream_rq_retry_overflow
- upstream_rq_pending_overflow
- upstream_cx_overflow

资源饱和度指标：

- upstream_rq_pending_active
- upstream_rq_pending_total
- upstream_rq_active

错误型的指标：

- upstream_rq_retry
- ejections_acive
- ejections_*
- ssl.connection_error

信息型的指标：

- upstream_cx_total
- upstream_cx_active
- upstream_cx_http*_total

由于图中已经说明了指标、组件、配置项的关系，这里就不再文字叙述了。图中也提供了到指标文档和相关配置的链接。

### Envoy 请求调度流程

先说说请求组件流转部分，流程图可以从相关的文档推理为（未完全验证，存在部分推理）：

:::{figure-md} 图：Envoy 请求调度流程图
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline-flowchart.drawio.svg" alt="图：Envoy 请求与响应时序线">

*图：Envoy 请求调度流程图*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline-flowchart.drawio.svg)*

## 请求与响应调度时序线

本节开头说了，写本节的直接缘由是: 需要对 Istio 网格节点故障快速恢复做一些调研。`快速恢复` 的前提是：

- 对已经发送到 `故障 upstream host` 或绑定到 `故障 upstream host` 的请求，快速响应失败
- 用 `Outlier detection / health checker`  识别出   `故障 upstream host` ，并把它移出负载均衡列表

所有问题都依赖于一个问题：如何定义和发现 `upstream host` 出了故障？

- 网络分区或对端崩溃或负载过高
  - 大多数情况下，分布式系统只能通过超时来发现这种问题。所以，要快速发现 `故障 upstream host` 或 `故障 request` ，需要配置合理的 timeout
- 对端有响应，L7 层的失败（如 HTTP 500），或 L3 层的失败（如 TCP REST/No router to destination/ICMP error）
  - 这是可以快速发现的失败

对于 `网络分区或对端崩溃或负载过高`，需要 timeout 发现的情况，Envoy 提供了丰富的 timeout 配置。丰富到有时让人不知道应该用哪个才是合理的。甚至配置一不小心，就配置出一些逻辑上长短与实现设计矛盾的值。所以，我尝试用理清楚 `请求与响应调度时序线` ，然后看相关 timeout 配置关联到这个时间线的哪个点，那么整个逻辑就清楚了。配置也更容易合理化了。

下图是请求与响应的时序线，以及相关的 timeout 配置与产生的指标，以及它们的联系。

:::{figure-md} 图：Envoy 请求与响应时序线
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline.drawio.svg" alt="图：Envoy 请求与响应时序线">

*图：Envoy 请求与响应时序线*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline.drawio.svg)*



简单说明一下时间线：

1. 如果 downstream 复用了之前的连接，可以跳过 2 & 3
2. downstream发起 新连接(TCP 握手)
3. TLS 握手
4. Envoy 接收 downstream request header & body
5. Envoy 执行路由(Router)规则，判定下一跳的 upstream cluster
6. Envoy 执行 Load Balancing 算法 ，判定下一跳的 upstream cluster 的 upstream host
7. 如果 Envoy 已经有空闲连接到 upstream host，则跳过 8 & 9
8. Envoy 向 upstream host 发起新连接(TCP 握手)
9. Envoy 向 upstream host 发起TLS 握手
10. Envoy 向 upstream host 转发送 requst header & body
11. Envoy 接收 upstream host 响应的 response header & body
12. upstream host 连接开始 idle
13. Envoy 向 downstream 转发送 response header & body
14. downstream host 连接开始 idle

相应地，图中也标注了相关超时配置与时间线步骤的关系，从开始计时顺序排列如下

- max_connection_duration
- transport_socket_connect_timeout
  - 指标 `listener.downstream_cx_transport_socket_connect_timeout`

- request_headers_timeout

- requst_timeout

- Envoy 的 route.timeout 即 Istio 的 [`Istio request timeout(outbound)`](https://istio.io/latest/docs/tasks/traffic-management/request-timeouts/)

  注意，这个超时值是把 请求处理时实际的 retry 的总时间也算上的。

  - 指标 `cluster.upstream_rq_timeout`
  - 指标 `vhost.vcluster.upstream_rq_timeout`

- max_connection_duration

- connection_timeout
  - 指标 `upstream_cx_connect_timeout`

- transport_socket_connect_timeout

- httpprotocoloptions.idle_timeout

## 总结

想要 Envoy 在压力与异常情况下，有个比较符合预期的表现，需要给 Envoy 一些合理于具体应用环境与场景的配置。而要配置好这堆参数的前提，是对相关处理流程与逻辑的洞察。 上面把 `请求与响应调度` 与 `请求与响应调度时序线`  都过了一遍。希望对了解这些方面有一定的帮助。

不只是 Envoy ，其实所有做代理的中间件，可能最核心的东西都在这一块了。所以，不要期望一下把知识完全吃透。这里，也只是希望让读者在这些流程上，有一个线索，然后通过线索去学习，方可不迷失方向。

## 一些有趣的扩展阅读

> - [https://www.istioworkshop.io/09-traffic-management/06-circuit-breaker/](https://www.istioworkshop.io/09-traffic-management/06-circuit-breaker/)
> - [https://tech.olx.com/demystifying-istio-circuit-breaking-27a69cac2ce4](https://tech.olx.com/demystifying-istio-circuit-breaking-27a69cac2ce4)