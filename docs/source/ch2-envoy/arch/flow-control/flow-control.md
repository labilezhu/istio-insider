# Flow Control

和所有代理类型的软件一样，Envoy 很重视流控。因为CPU/内存资源是有限的，时间也要避免单个流过度占用资源的情况。需要注意的是，和其它以异步/线程多路复用架构实现的软件一样，流控永远不是一个简单的事情。



Envoy 有一个[Envoy Flow Conrol 文档](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)专门叙述了其中的一些细节。我在本节中，记录一下我在这基础上的一些学习研究结果。我使用了翻译软件，但也加上了很多我的修正。



Envoy 中的流量控制是通过对每个 Buffer 进行限制 和 `watermark callbacks`来完成的。 当 Buffer 包含的数据超过配置的限制时，将触发`high watermark callback`，触发一系列事件，最终通知数据源停止发送数据。 这种抑制可能是即时的（如停止从套接字读取）或渐进的（如停止 HTTP/2 窗口更新），因此 Envoy 中的所有 Buffer 限制都被视为`软限制`。 

当 Buffer 最终处理完毕(`drains`)时（通常是高水位线的一半，以避免来回抖动），低水位线回调将触发，通知发送者可以恢复发送数据。



## TCP 实现细节

TCP 和 `TLS 终点` 的流量控制是通过“`Network::ConnectionImpl`”写入Buffer和“`Network::TcpProxy`”过滤器之间的协调来处理的。



`Downstream`的流量控制如下。

- Downstream `Network::ConnectionImpl::write_buffer_` 缓冲了太多数据。 它调用“`Network::ConnectionCallbacks::onAboveWriteBufferHighWatermark()`”。
- `Network::TcpProxy::DownstreamCallbacks` 接收 `onAboveWriteBufferHighWatermark()` 并在Upstream连接上调用 `readDisable(true)`。
- 当Downstream处理完毕(`drained`)时，它会调用 `Network::ConnectionCallbacks::onBelowWriteBufferLowWatermark()`
- `Network::TcpProxy::DownstreamCallbacks` 接收 `onBelowWriteBufferLowWatermark()` 并在Upstream连接上调用 `readDisable(false)`。

`Upstream`的流量控制大致相同。

- Upstream `Network::ConnectionImpl::write_buffer_` 缓冲了太多数据。 它调用“`Network::ConnectionCallbacks::onAboveWriteBufferHighWatermark()`”。
- `Network::TcpProxy::UpstreamCallbacks` 接收 `onAboveWriteBufferHighWatermark()` 并在Downstream连接上调用 `readDisable(true)`。
- 当Upstream处理完毕(`drained`)时，它会调用 `Network::ConnectionCallbacks::onBelowWriteBufferLowWatermark()`
- `Network::TcpProxy::UpstreamCallbacks` 接收 `onBelowWriteBufferLowWatermark()` 并在Downstream连接上调用 `readDisable(false)`。



子系统和 Callback 机制可见前文的： {ref}`/ch2-envoy/arch/oop/oop#Callback回调设计模式`  一节。



## HTTP2 实现细节

由于 HTTP/2 堆栈中的各种 Buffer 相当复杂，因此从 Buffer 超出 `Watermark`限制到禁用来自数据源的数据的每段路径都会单独文档说明。



![代理 HTTP 响应时的 Http 流控与背压](flow-control.drawio.svg)







## Ref.

> [Flow control](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)
> [Envoy buffer management & flow control](https://docs.google.com/document/d/1EB3ybx3yTndp158c4AdQ4nutksZA9lL-BQvixhPnb_4/edit?usp=sharing)