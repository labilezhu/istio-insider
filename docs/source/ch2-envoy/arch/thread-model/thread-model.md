# 线程模型

如果给你一个开源中间件，要你分析其实现，那么，你会从什么地方入手？回答可能是：
- 源码模块
- 抽象概念与设计模式
- 线程

对于现代开源中间件，我觉得线程/进程模型几乎是最重要的。因为现代中间件基本都使用了多进程或多线程以充分利用硬件资源。无论封装抽象得再好，设计模式应用得再优雅，程序终究要以线程的方式在 cpu 上面跑。而多线程是如何按职能划分的，线程之间如何同步通讯，这些东西才是难点和重点。

简单来说，Envoy 使用了 non-blocking + Event Driven + Multi-Worker-Thread 的线程设计模式。在软件设计史上，类似的设计模式的名称有很多，如：
- [staged event-driven architecture (SEDA)](https://en.wikipedia.org/wiki/Staged_event-driven_architecture)
- [Reactor pattern](https://en.wikipedia.org/wiki/Reactor_pattern)
- [Event-driven architecture (EDA)](https://en.wikipedia.org/wiki/Event-driven_architecture)

> 本节内容假设读者已经了解过 Envoy 的事件驱动模型。如果未有，可以阅读本书的 {doc}`/ch2-envoy/arch/event-driven/event-driven`。
> 本节内容参考了：[Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310) 

与 Node.JS 的单线程不同，Envoy 为了充分利用多 Core CPU 的优势，支持多个 Worker Thread 各自跑自己独立的 event loop。而这样的设计是有代价的，因为多个 worker thread / main thread 之间其实不是完全独立的，他们需要共享一些数据，如：

- Upstream Cluster 的 endpoints 、健康状态……
- 各种监控统计指标



## Thread Local

共享的数据，如果都是加锁写读访问，并发度一定会下降。于是 Envoy 作者在分析数据同步更新的实时一致性要求不高的条件下，参考了 Linux kernel 的 [read-copy-update (RCU)](https://en.wikipedia.org/wiki/Read-copy-update) 设计模式，实现了一套 Thread Local 的数据同步机制。在底层实现上，是基于 C++11 的 `thread_local` 功能，和 libevent 的 `libevent::event_active(&raw_event_, EV_TIMEOUT, 0)` 去实现。

下图在 [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310) 基础上，尝试说明 Envoy 在源码实现层面，是如何使用 Thread Local 机制实现 thread 之间共享数据的。

:::{figure-md} 图: ThreadLocal Classes

<img src="/ch2-envoy/arch/thread-model/thread-local-classes.drawio.svg" alt="图 - ThreadLocal Classes">

*图: ThreadLocal Classes*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fthread-local-classes.drawio.svg)*


## Ref

- [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310)