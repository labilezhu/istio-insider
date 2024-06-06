# Listener 连接建立细节


事件驱动和连接的建立的过程和关系：
![envoy-event-model-accept](/ch2-envoy/arch/event-driven/event-driven.assets/envoy-event-model-accept.drawio.svg)


1. Envoy worker 线程挂起在 `epoll_wait()` 方法中。线程被移出 kernel 的 runnable queue。线程睡眠。
2. client 建立连接，server 内核完成3次握手，触发 listen socket 事件。
   - 操作系统把 Envoy worker 线程被移入 kernel 的 runnable queue。Envoy worker 线程被唤醒，变成 runnable。操作系统发现可用 cpu 资源，把 runnable 的 envoy worker 线程调度上 cpu。（注意，runnable 和 调度上 cpu 不是一次完成的）
3. Envoy 分析事件列表，按事件列表的 fd 调度到不同的 FileEventImpl 类的回调函数（实现见：`FileEventImpl::assignEvents`）
4. FileEventImpl 类的回调函数调用实际的业务回调函数，进行 syscall `accept`，完成 socket 连接。得到新 socket 的 FD: `$new_socket_fd`。
5. 业务回调函数把 调用 `epoll_ctl` 把 `$new_socket_fd ` 加到 epoll 监听中。
6. 回到步骤 1 。

## TCP 连接建立步骤

先看看代码，了解大概的连接建立过程和相关的实现：

:::{figure-md}
:class: full-width

<img src="/ch2-envoy/arch/listener/listener-connection.assets/envoy-classes-accept-flow.drawio.svg" alt="图：Listener TCP 连接建立流程">

*图：Listener TCP 连接建立流程*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-classes-accept-flow.drawio.svg)*




步骤是：
1. epoll 收到连接请求，完成3次握手。最好回调到 TcpListenerImpl::onSocketEvent()。
2. 最终 syscall `accept()` 获得新 socket 的 FD。
3. 调用 ActiveTcpListener::onAccept()
4. 创建新连接专用的 `ListenerFilterChain` 
5. 创建新连接专用的 `ActiveTcpSocket`，发起 `ListenerFilterChain`  流程
6. 执行 `ListenerFilterChain`  流程：
   1. 如：TlsInspector::Filter 注册监听新 socket 的事件，以便在后续新 socket 发生事件时，读 socket，抽取出 TLS SNI/ALPN。
   2. 当 `ListenerFilterChain` 中所有的 `ListenerFilter` 在新的事件和事件周期中完成其所有的数据交换和抽取的任务，本 fd 的控制权交到一环节。
7. 调用 核心函数 `ActiveTcpListener::newConnection()`
8. 调用 findFilterChain() 基于之前 `ListenerFilter` 抽取到的数据，和各 `network filter chain 配置` 的 match 条件，找到最匹配的 `network filter chain 配置` 。
9. 创建 `ServerConnection`(ConnectionImpl的子类) 对象
   1.  注册 socket 事件回调到 `Network::ConnectionImpl::onFileEvent(uint32_t events)` 中。即以后的 socket 事件将由这个`ServerConnection`处理。
10. 用之前找到的 `network filter chain 配置` 对象，创建 `transportSocket`。
11. 用之前找到的 `network filter chain 配置` 对象，创建运行期的 `NetworkFilterChain`。


## 求证过程

如果有兴趣研究实现细节，建议看看我 Blog 的文章：

 - [逆向工程与云原生现场分析 Part3 —— eBPF 跟踪 Istio/Envoy 事件驱动模型、连接建立、TLS 握手与 filter_chain 选择](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part3/)