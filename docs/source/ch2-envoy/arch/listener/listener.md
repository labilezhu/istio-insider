---
typora-root-url: ../../..
---

# Listener

`Listener` 顾名思义，就是被动监听和接受连接的的组件。那么是不是每个 Listener 都会 listen socket ? 我们带着问题往下看。

开始学习 Listener 前，先回顾一下前面章节的 {doc}`/ch2-envoy/envoy@istio-conf-eg` 中的例子。

```{note}
这里下载 Envoy 的配置 yaml {download}`envoy@istio-conf-eg-inbound.envoy_conf.yaml </ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.envoy_conf.yaml>` .
```

:::{figure-md}
:class: full-width

<img src="/ch1-istio-arch/istio-ports-components.assets/istio-ports-components.drawio.svg" alt="Istio端口与组件">

*图：Istio 端口与组件*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-ports-components.drawio.svg)*

:::{figure-md}
:class: full-width
<img src="/ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-inbound.drawio.svg)*

:::{figure-md}
:class: full-width
<img src="/ch2-envoy/envoy@istio-conf-eg.assets/envoy@istio-conf-eg-outbound.drawio.svg" alt="图：Istio里的 Envoy Outbound 配置举例">

*图：Istio里的 Envoy Outbound 配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-outbound.drawio.svg)*

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
- Bind socket 的 Listener
  - 端口：15001
    - 名字：virtualOutbound
    - 职责：主要的 Outbound Listener。转发 iptable 劫持的流量到下面的 Listener
- 不 Bind socket 的 Listener
  - 名字：0.0.0.0_8080
  - 职责：所有监听 8080 端口的 upstream cluster 流量，都会经由这个 Listener 出去。
  - 配置
    - bind_to_port: false

可见，Istio 给 Listener 的名字，取得有点不太好理解。实际监听 TCP 端口的，叫 `virtualInbound`/`virtualOutbound`，不监听 TCP 端口的，反而没有 `virtual` 这个前缀。


## Listener 内部组件

:::{figure-md} 图：Listener 内部组件

<img src="/ch2-envoy/arch/listener/listener.assets/listener.drawio.svg" alt="图：Listener 内部组件">

*图：Listener 内部组件*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Flistener.drawio.svg)*


Listener 由 `Listener filters` 、`Network Filter Chains` 组成。

`Listener Filter` 和 `Network Filter` 两个概念比较容易混淆。简单说一下：

- `Listener Filter` ： 在连接建立之初，收集连接上的首几个信息，为选择 `Network Filter Chain` 做数据准备。
  - 可以是收集 TCP 基本数据， 如 src IP/port，dst IP/port, 也可以收集 iptables 转发前的原 dst IP/port 。
  - 可以是 TLS 握手数据，SNI / APLN。
- `Network Filter` ： 
  - TCP/TLS 握手后，进行更上层协议的处理，如 TCP Proxy / HTTP Proxy



### Listener filters

如，上面的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，可以看到几个 Listener filters:
 - envoy.filters.listener.original_dst
 - envoy.filters.listener.tls_inspector
 - envoy.filters.listener.http_inspector


图中已经陈述了相关的功能。

### Network Filter Chains
如，上面的 {ref}`图：Istio里的 Envoy Inbound 配置举例` 中，可以看到几个 Network Filter Chains，它们的名字是可以重复的。而其中每个都有自己的 `filter_chain_match`  ，Envoy 使用这个匹配条件，将连接匹配到不同的 `Network Filter Chain`。  

每个 `Network Filter Chain` 由顺序化的 `Network Filter` 组成。 `Network Filter` 将在后面的章节介绍。


## 代码 OOP 抽象设计

写到这里，是时候看看代码了。不过，不是直接看，先看看 C++ 类图吧。


:::{figure-md} 图：Listener 内部组件类图

<img src="/ch2-envoy/arch/listener/listener.assets/network-filter-code-oop.drawio.svg" alt="图：Listener 内部组件类图">

*图：Listener 内部组件类图*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fnetwork-filter-code-oop.drawio.svg)*


## Listener 相关的组件和启动顺序

:::{figure-md} 图：Listener 核心对象与启动顺序

<img src="/ch2-envoy/arch/listener/listener.assets/listener-core-classes-startup-process.drawio.svg" alt="图：Listener 核心对象与启动顺序">

*图：Listener 核心对象与启动顺序*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Flistener-core-classes-startup-process.drawio.svg)*


不好意思，直接由上面的 High Level 说明，一下拉回地面，讲源码了。不过我尽量不贴源码出来吓唬人，而是先从类功能、结构、职责说说。
Envoy 只有两种类型的 Listener 实现。TCP 和 UDP 的。这里我只看 TCP 了。 图中信息量不少，不用怕，我慢慢道来。

首先介绍一下核心类：
- `TcpListenerImpl` - Listener 的核心主类。负责 listen socket 和 listen socket 事件处理。
  - 每个 Worker Thread 会为配置中的每个 Listener 创建自己的专属 `TcpListenerImpl` 实例。
    - 如：我们配置了两个 Listener, L1 和 L2。有两个 work thread: W0 和 W1 。那么会有 4 个 `TcpListenerImpl` 实例。 
  - `TcpListenerImpl` 类中有 `bool bind_to_port` 属性，可以推测真有不 bind/listen socket 的 `TcpListenerImpl` 了。
- `TcpListenSocket` - 负责 Listner 的实际 socket 操作，包括 `bind` 和 `listen`
- WorkerImpl - Worker 线程的主入口类
- DispatcherImpl - 主事件循环和队列类
- ListenerManagerImpl
  - 创建 和 bind `TcpListenSocket` 。
  - 按配置参数创建 `WorkerImpl`
  - 触发创建 `TcpListenerImpl`

或者你和我一样，刚看 Envoy 的代码时，总会混淆名字相近的类。如： `TcpListenerImpl` 、 `TcpListenSocket` 。

细心的同学如果看了图例，就知道图中黑、红连线代表不同类型的线程的。说说图中主流程：
1. 进程 main 间接调用 ListenerManagerImpl
2. bind socket 绑定到 ip 和 port
3. 启动新的 worker 线程
4. 加入异步 task：`add Listener task`(每个 Worker + Listener 执行一次) 到 worker 的任务队列中。
5. worker 线程取出任务队列，执行 `add Listener task`
6. worker 线程 异步 listen socket，和注册事件处理器

细心的同学会发现问题：
- 为何要在主线程中 bind socket ？
  - 可以在进程启动早期就发现 socket 监听端口冲突等常见问题。详细解释在 Envoy 的源码文档中 https://github.com/envoyproxy/envoy/blob/main/source/docs/listener.md 。
- 两个 worker 线程可以 listen 同一个 socket?
  - 在旧版本默认不使用 `reuse_port` socket opts 情况下，是使用 duplicate socket/file descriptor 的方法为每个 work thread 复制一个文件描述符。
  - 新版本默认使用 `reuse_port` socket opts ，就可以每个线程独立 bind 相同 port 了。 好处见我的文章：[记一次 Istio 调优 Part 2 —— 饥饿的线程与 SO_REUSEPORT](https://blog.mygraphql.com/zh/posts/cloud/istio/istio-tunning/istio-thread-balance/)

### 代码级的启动顺序

:::{figure-md} 图：Listener TCP 连接建立流程

<img src="/ch2-envoy/arch/listener/listener.assets/envoy-classes-listen-flow.drawio.svg" alt="图：Listener TCP 连接建立流程">

*图：Listener TCP 连接建立流程*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-classes-listen-flow.drawio.svg)*


Listener 相关的组件和启动顺序 - 核心流程图说明以下几步（ `reuse_port=false` 情况下）：

1. 进程 main 间接调用 ListenerManagerImpl，间接建立 socket，假设文件描述符为 fd-root
2. bind socket 绑定到 ip 和 port
3. 启动新的 worker 线程
4. 加入异步 task：`add Listener task`(每个 Worker + Listener 执行一次) 到 worker 的任务队列中。
5. worker 线程取出任务队列，执行 `add Listener task`
6. worker 线程 duplicate 文件描述符 fd-root 为 fd-envoy
7. worker 线程 异步 listen socket，和注册事件处理器


## 求证过程

如果有兴趣研究 Listener 的实现细节，建议看看我 Blog 的文章：
 - [逆向工程与云原生现场分析 Part2 —— eBPF 跟踪 Istio/Envoy 之启动、监听与线程负载均衡](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part2/)
 - [逆向工程与云原生现场分析 Part3 —— eBPF 跟踪 Istio/Envoy 事件驱动模型、连接建立、TLS 握手与 filter_chain 选择](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part3/)


```{toctree}
listener-connection.md
```