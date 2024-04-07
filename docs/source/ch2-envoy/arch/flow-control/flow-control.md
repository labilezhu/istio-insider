# Flow Control

和所有代理类型的软件一样，Envoy 很重视流控。因为CPU/内存资源是有限的，同时也要避免单个流过度占用资源的情况。需要注意的是，和其它以异步/线程多路复用架构实现的软件一样，流控永远不是一个简单的事情。



Envoy 有一个[Envoy Flow Conrol 文档](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)专门叙述了其中的一些细节。我在本节中，记录一下我在这基础上的一些学习研究结果。我使用了翻译软件，但也加上了很多我的修正。



Envoy 中的流量控制是通过对每个 Buffer 进行限制 和 `watermark callbacks`来完成的。 当 Buffer 包含的数据超过配置的限制时，将触发`high watermark callback`，触发一系列事件，最终 **通知数据源停止发送数据**。 这种抑制可能是即时的（如停止从套接字读取）或渐进的（如停止 HTTP/2 窗口更新），因此 Envoy 中的所有 Buffer 限制都被视为`软限制`。 

当 Buffer 最终处理完毕(`drains`)时（通常是高水位线的一半，以避免来回抖动），低水位线回调将触发，通知发送者可以恢复发送数据。



下面先以 简单的 TCP 实现细节 流控过程，再说明更复杂的 HTTP2 流控过程。



## TCP 实现细节

TCP 和 `TLS 终点` 的流量控制是通过“`Network::ConnectionImpl`” 写入 Buffer 和 “`Network::TcpProxy ` Filter” 之间的协调来处理的。



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



子系统和 Callback 机制可见前文的： {ref}`ch2-envoy/arch/oop/oop:Callback回调设计模式`  一节。



## HTTP2 实现细节

由于 HTTP/2 技术堆栈中的各种 Buffer 相当繁杂，因此从 Buffer 超出 `Watermark`限制到暂停来自数据源的数据的每段路径都有单独的 Envoy 文档说明。



![flow-control-1-upstream-backs-up-simple.drawio.svg](./flow-control-1-upstream-backs-up-simple.drawio.svg)



上图的 `Unbounded buffer` 不是说 Buffer 完成没有 limit，而是说 limit 是软性的。



> For HTTP/2, when filters, streams, or connections back up, the end result is `readDisable(true)` being called on the source stream. This results in the stream ceasing to consume window, and so not sending further flow control window updates to the peer. This will result in the peer eventually stopping sending data when the available window is consumed (or nghttp2 closing the connection if the peer violates the flow control limit) and so limiting the amount of data Envoy will buffer for each stream. 

对于 HTTP/2，当`Filter`、`streams`、 `connection` 过载(Above high watermark)时，最终结果都会调用到数据源头`Source stream`上的 `readDisable(true)`。 这会导致`Source stream`停止消耗`HTTP2 Window`，因此不会向对方发送更多的流量控制`HTTP2 Window`更新 ; 最终导致对方在可用窗口耗尽时停止发送数据（或者如果对方违反流量控制限制，nghttp2 将关闭连接），这样 Envoy 就可以对每个`steam` 限制 Buffer 的大小。 

> When `readDisable(false)` is called, any outstanding unconsumed data is immediately consumed, which results in resuming window updates to the peer and the resumption of data.

当 `Source steam` 上的  `readDisable(FALSE)` 被调用时，任何 Buffer 中未被处理的数据都会立即被处理，最终，会恢复向对端发送窗口更新并最终恢复数据流动。见：

```c++
void ConnectionImpl::StreamImpl::readDisable(bool disable) {
  ENVOY_CONN_LOG(debug, "Stream {} {}, unconsumed_bytes {} read_disable_count {}",
                 parent_.connection_, stream_id_, (disable ? "disabled" : "enabled"),
                 unconsumed_bytes_, read_disable_count_);
  if (disable) {
    ++read_disable_count_;
  } else {
    ASSERT(read_disable_count_ > 0);
    --read_disable_count_;
    if (!buffersOverrun()) {
      scheduleProcessingOfBufferedData(false);
      if (shouldAllowPeerAdditionalStreamWindow()) {
        grantPeerAdditionalStreamWindow();
      }
    }
  }
}
```

> Note that `readDisable(true)` on a stream may be called by multiple entities. It is called when any filter buffers too much, when the stream backs up and has too much data buffered, or the connection has too much data buffered. Because of this, `readDisable()` maintains a count of the number of times it has been called to both enable and disable the stream, resuming reads when each caller has called the equivalent low watermark callback. 

请注意，同一个 `stream`的 `readDisable(true)` 可能会被多个使用者重复调用。 当任何 `Filter`、`stream` 、`connection` 缓冲过多数据(Above high watermark)时，均会调用 `stream`的 `readDisable(true)`  。 因此，`stream` 的 `readDisable()` 会记住`readDisable(true)`的次数，并在每个调用者调用等次数的低水位线回调时恢复读取。 

> For example, if the TCP window upstream fills up and results in the network buffer backing up, all the streams associated with that connection will `readDisable(true)` their downstream data sources. 
>
> When the HTTP/2 flow control window fills up an individual stream may use all of the window available and call a second `readDisable(true)` on its downstream data source. 
>
> When the upstream TCP socket drains, the connection will go below its low watermark and each stream will call `readDisable(false)` to resume the flow of data. The stream which had both a network level block and a H2 flow control block will still not be fully enabled. 
>
> Once the upstream peer sends window updates, the stream buffer will drain and the second `readDisable(false)` will be called on the downstream data source, which will finally result in data flowing from downstream again.

例如：

1. 如果 upstream TCP Write Buffer 窗口填满并导致网络缓冲区满，则与该`connection`关联的所有`stream`都将 `readDisable(true)` 其 Downsteam 数据源。
2. 同时，如 HTTP/2 流控制窗口填满时，单个流可能会使用所有可用窗口并在其 Downstream 数据源上调用第二个` readDisable(true)`。 
3. 然后，随着 Upstream TCP Write Buffer 的不断发送和排空(drains)，`connection` 将低于其低水位线，每个流将调用 `readDisable(false)` 来恢复数据流。 但同时具有网络级挂起和 H2 流控制级挂起的 `stream` 仍然不会完全启用。 
4. 一旦 Upstream 对端发送 HTTP2 窗口更新，`stream` 缓冲区将排空，并且 Downstream 数据源将调用第二个 `readDisable(false)`，这最终将导致数据再次从 Downstream 流出。



## Ref.

> - [Flow control](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)
> - [Envoy buffer management & flow control](https://docs.google.com/document/d/1EB3ybx3yTndp158c4AdQ4nutksZA9lL-BQvixhPnb_4/edit?usp=sharing)