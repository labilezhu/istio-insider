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

## 线程概述

![image-20240506232521005](./thread-model.assets/threading-overview.png)

*图 : Threading overview*

*Source: [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310)*



Envoy 使用几种不同类型的线程，如上图所示。下面选择主要的说明：



- main：该线程负责服务器启动和关闭、所有 xDS API 处理（包括 DNS、健康检查和通用cluster management）、runtime、stat flushing、admin 和一般进程管理（signals、热重启等）。该线程上发生的一切都是异步和 "非阻塞 "的。一般来说，main 线程负责协调所有不需要大量 CPU 来完成的关键功能。这样，大部分管理代码就可以像单线程一样编写。

- worker： 默认情况下，Envoy 会为系统中的每个硬件线程生成一个工作线程。(这可通过 --concurrency 选项控制）。每个 worker 线程运行一个 "非阻塞 "事件循环，负责监听每个 listener、接受新连接、为连接实例化一个 filter 栈，并在连接生命周期内处理所有 IO。这样，大部分连接处理代码就可以像单线程代码一样编写。









## Thread Local



由于 Envoy 将 main 线程职责与 worker 线程职责分开，因此需要在 main 线程上完成复杂处理，然后以高度并发的方式提供给每个 worker 线程。本节将从高层介绍 Envoy 的线程本地存储 Thread Local Storage (TLS) 系统。后面我将介绍如何使用该系统处理 cluster management 。





![image-20240506233017636](./thread-model.assets/thread-local-storage-system.png)

*Source: [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310)*

*Figure : Thread Local Storage (TLS) system*



![image-20240506233250458](./thread-model.assets/cluster-manager-threading.png)

*Source: [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310)*

*Figure : Cluster manager threading*



共享的数据，如果都是加锁写读访问，并发度一定会下降。于是 Envoy 作者在分析数据同步更新的实时一致性要求不高的条件下，参考了 Linux kernel 的 [read-copy-update (RCU)](https://en.wikipedia.org/wiki/Read-copy-update) 设计模式，实现了一套 Thread Local 的数据同步机制。在底层实现上，是基于 C++11 的 `thread_local` 功能，和 libevent 的 `libevent::event_active(&raw_event_, EV_TIMEOUT, 0)` 去实现。

下图在 [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310) 基础上，尝试说明 Envoy 在源码实现层面，是如何使用 Thread Local 机制实现 thread 之间共享数据的。

:::{figure-md} 图: ThreadLocal Classes

<img src="/ch2-envoy/arch/thread-model/thread-local-classes.drawio.svg" alt="图 - ThreadLocal Classes">

*图: ThreadLocal Classes*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fthread-local-classes.drawio.svg)*


## Ref

- [Envoy threading model - Matt Klein](https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310)