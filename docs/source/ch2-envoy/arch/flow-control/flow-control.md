---
typora-root-url: ../../..
---

# 流控 - Flow Control

和所有代理类型的软件一样，Envoy 很重视流控。因为CPU/内存资源是有限的，同时也要避免单个流过度占用资源的情况。需要注意的是，和其它以异步/线程多路复用架构实现的软件一样，流控永远不是一个简单的事情。



Envoy 有一个[Envoy Flow Conrol 文档](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)专门叙述了其中的一些细节。我在本节中，记录一下我在这基础上的一些学习研究结果。我使用了翻译软件，但也加上了很多我的修正。



Envoy 中的流量控制是通过对每个 Buffer 进行限制 和 `watermark callbacks`来完成的。 当 Buffer 包含的数据超过配置的限制时，将触发`high watermark callback`，触发一系列事件，最终 **通知数据源停止发送数据**。 这种抑制可能是即时的（如停止从套接字读取）或渐进的（如停止 HTTP/2 窗口更新），因此 Envoy 中的所有 Buffer 限制都被视为`软限制`。 

当 Buffer 最终处理完毕(`drains`)时（通常是高水位线的一半，以避免来回抖动），低水位线回调将触发，通知发送者可以恢复发送数据。



下面先以 简单的 TCP 实现细节 流控过程，再说明更复杂的 HTTP2 流控过程。



## 一些流控相关的术语

- `back up` - 因流量到达目标的速度慢或不畅顺，而发生数据拥塞在一个或多个中间环节的 Buffer 当中，导致 Buffer 空间耗尽的情况。以下一般翻译为中文：`拥塞`
- `buffers fill up` - 缓存空间到达限制上限
- `backpressure` - 流背压是一种反馈机制，允许系统在超过处理能力时，还能响应请求而不是在负载下崩溃。当传入数据的速率超过处理或输出数据的速率时，就会发生这种情况，从而导致拥塞和潜在的数据丢失。详见：[Backpressure explained — the resisted flow of data through software](https://medium.com/@jayphelps/backpressure-explained-the-flow-of-data-through-software-2350b3e77ce7)
- `drained` - Buffer 的排空。一般指 Buffer 由高于 low watermark，经消费下降后低于 low watermark  甚至清空的处理与排空操作。
- `HTTP/2 window` - HTTP/2 标准的流控实现方法，通过`WINDOW_UPDATE` 帧指示除了现有的流量控制窗口之外，发送方还可以传输的八位字节数。详见 “[Hypertext Transfer Protocol Version 2 (HTTP/2) - 5.2. Flow Control](https://httpwg.org/specs/rfc7540.html#FlowControl)”
- `http stream`  - HTTP/2 标准的流。详见 “[Hypertext Transfer Protocol Version 2 (HTTP/2) - 5. Streams and Multiplexing](https://httpwg.org/specs/rfc7540.html#StreamsLayer)”
- High/Low Watermark - 为控制内存或 Buffer 的消耗量，但又不想频繁高频抖动触发控制操作而使用的高水位线和低水位线设计模式，详见：[What are high and low water marks in bit streaming](https://stackoverflow.com/questions/45489405/what-are-high-and-low-water-marks-in-bit-streaming)。



## TCP 流控实现

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



## HTTP2 流控实现

由于 HTTP/2 技术堆栈中的各种 Buffer 相当繁杂，因此从 Buffer 超出 `Watermark`限制到暂停来自数据源的数据的每段路径都有单独的 Envoy 文档说明。



### HTTP2 流控总体流程



#### 最简单的 Upsteam connection 拥塞场景


> For HTTP/2, when filters, streams, or connections back up, the end result is `readDisable(true)` being called on the source stream. This results in the stream ceasing to consume window, and so not sending further flow control window updates to the peer. This will result in the peer eventually stopping sending data when the available window is consumed (or nghttp2 closing the connection if the peer violates the flow control limit) and so limiting the amount of data Envoy will buffer for each stream. 

对于 HTTP/2，当`Filter`、`streams`、 `connection` 拥塞(Above high watermark)时，最终结果都会调用到数据源头`Source stream`上的 `readDisable(true)`。 这会导致`Source stream`停止消耗`HTTP2 Window`，因此不会向对方发送更多的流量控制`HTTP2 Window Update` ; 最终导致对方在可用窗口耗尽时停止发送数据（或者如果对方违反流量控制限制，nghttp2 将关闭连接），这样 Envoy 就可以对每个`steam` 限制 Buffer 的大小。 

:::{figure-md} Upsteam connection 拥塞与背压

<img src="/ch2-envoy/arch/flow-control/flow-control-1-upstream-backs-up-simple.drawio.svg" alt="Upsteam connection 拥塞与背压">

*Upsteam connection 拥塞与背压*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fflow-control-1-upstream-backs-up-simple.drawio.svg)*


上图的 `Unbounded buffer` 不是说 Buffer 没有 limit，而是说 limit 是`软限制`。

#### Upsteam connection 与 Upstream http stream 同时拥塞场景



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

:::{figure-md} Upsteam connection 与 Upstream http stream 同时拥塞

<img src="/ch2-envoy/arch/flow-control/flow-control-2-upstream-backs-up-counter.drawio.svg" alt="Upsteam connection 与 Upstream http stream 同时拥塞">

*Upsteam connection 与 Upstream http stream 同时拥塞*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fflow-control-2-upstream-backs-up-counter.drawio.svg)*

#### Upstream 拥塞时 Router::Filter 的协作



> The two main parties involved in flow control are the router filter (`Envoy::Router::Filter`) and the connection manager (`Envoy::Http::ConnectionManagerImpl`). The router is responsible for intercepting watermark events for its own buffers, the individual upstream streams (if codec buffers fill up) and the upstream connection (if the network buffer fills up). It passes any events to the connection manager, which has the ability to call `readDisable()` to enable and disable further data from downstream. 

流量控制主要的两个相关组件是`router filter`（Envoy::Router::Filter）和`connection manager `（Envoy::Http::ConnectionManagerImpl）。 `router filter`负责拦截各种 watermark 事件：其自己的 Buffer 已满、各个upstream http streams（如果codec buffers 已满）、 upstream connection（如果网络 buffer 已满）。并将这些事件传递给ConnectionManagerImpl。然后 ConnectionManagerImpl 能够通过调用 downstream 的 stream 的 `readDisable(true/false)` 来开启或关闭来自 downstream 的数据流。



:::{figure-md}  Upstream 拥塞时 Router::Filter 的协作

<img src="/ch2-envoy/arch/flow-control/flow-control-3-upstream-backs-up-router.drawio.svg" alt="Upstream 拥塞时 Router::Filter 的协作">

*Upstream 拥塞时 Router::Filter 的协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fflow-control-3-upstream-backs-up-router.drawio.svg)*

#### Downstream 拥塞时 Http::ConnectionManagerImpl 的协作



> On the reverse path, when the downstream connection backs up, the connection manager collects events for the downstream streams and the downstream connection. It passes events to the router filter via `Envoy::Http::DownstreamWatermarkCallbacks` and the router can then call `readDisable()` on the upstream stream. Filters opt into subscribing to `DownstreamWatermarkCallbacks` as a performance optimization to avoid each watermark event on a downstream HTTP/2 connection resulting in "number of streams * number of filters" callbacks. Instead, only the router filter is notified and only the "number of streams" multiplier applies. Because the router filter only subscribes to notifications when it has an upstream connection, the connection manager tracks how many outstanding high watermark events have occurred and passes any on to the router filter when it subscribes.



在反向路径上，当 downstream connection 拥塞时，connection manager 收集 downstream 的 stream 层 和 connection 层的事件。 它通过 `Envoy::Http::DownstreamWatermarkCallbacks` 将事件传递到`router filter`，然后`router filter`可以调用 Upstream stream 上的 `readDisable(true)` 。 

设计上，`HTTP Filter` 选择性地订阅 “`DownstreamWatermarkCallbacks`”以优化性能，以避免 downstream HTTP/2 连接上的每个 watermark 事件导致 “downstream http stream 数 * filter 数” 次回调。 相反，仅通知`router filter` 并且仅调用 “downstream http stream 数”的倍数次。 

由于`router filter` 仅在拥有 upstream connection 时才订阅事件，即有空档期。因此 connection manager 会记录已发生但未处理的 high watermark 事件的数量，并在 `router filter` 订阅时将记录的事件传递给`router filter`。



:::{figure-md} Downstream 拥塞时 Http::ConnectionManagerImpl 的协作

<img src="/ch2-envoy/arch/flow-control/flow-control-4-downstream-conn-backs-up.drawio.svg" alt="Downstream 拥塞时 Http::ConnectionManagerImpl 的协作">

*Downstream 拥塞时 Http::ConnectionManagerImpl 的协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fflow-control-4-downstream-conn-backs-up.drawio.svg)*



### HTTP decode/encode filter 的流控

> Each HTTP and HTTP/2 filter has an opportunity to call `decoderBufferLimit()` or `encoderBufferLimit()` on creation. No filter should buffer more than the configured bytes without calling the appropriate watermark callbacks or sending an error response.
>
> Filters may override the default limit with calls to `setDecoderBufferLimit()` and `setEncoderBufferLimit()`. These limits are applied as filters are created so filters later in the chain can override the limits set by prior filters. It is recommended that filters calling these functions should generally only perform increases to the buffer limit, to avoid potentially conflicting with the buffer requirements of other filters in the chain.
>
> Most filters do not buffer internally, but instead push back on data by returning a FilterDataStatus on `encodeData()`/`decodeData()` calls. If a buffer is a streaming buffer, i.e. the buffered data will resolve over time, it should return `FilterDataStatus::StopIterationAndWatermark` to pause further data processing, which will cause the `ConnectionManagerImpl` to trigger watermark callbacks on behalf of the filter. If a filter can not make forward progress without the complete body, it should return `FilterDataStatus::StopIterationAndBuffer`. In this case if the `ConnectionManagerImpl` buffers more than the allowed data it will return an error downstream: a 413 on the request path, 500 or `resetStream()` on the response path.



每个 HTTP 和 HTTP/2 Filter 都可以在创建时调用 `decoderBufferLimit()` 或 `encoderBufferLimit()` 以获取限制。 任何 Filter 在 buffer 超过配置的字节数时，必须调用适当的 high watermark callback 或返回错误 http 响应。

Filter 可以通过调用 `setDecoderBufferLimit() `和 `setEncoderBufferLimit() `来覆盖默认限制。 这些限制在创建 Filter 时应用，因此 Filter Chain 中后面的 Filter 可以覆盖先前 Filter 设置的限制。 建议调用这些函数的 Filter 通常应仅加大缓冲区的最大限制值，而非减少 limit，以避免与 filter chain 中其他 Filter 的缓冲区要求发生潜在冲突。

大多数 Filter 不会在内部 buffer 数据，而是通过在调用 “`encodeData()`”/“`decodeData()`” 时返回 `FilterDataStatus` 来推回数据。 

- 如果 buffer 是 `stream buffer` ，即当前缓冲区内的数据需要一些时间或外部事件才能解析，则它应该返回 `FilterDataStatus::StopIterationAndWatermark` 来暂停进一步(下一个 Filter)的数据处理，这将导致 `ConnectionManagerImpl` 因 Filter 而触发 watermark callback。 
- 如果 Filter 一定要收集到完整的 HTTP Body 才能继续，则应返回“`FilterDataStatus::StopIterationAndBuffer`”。 在这种情况下，如果“`ConnectionManagerImpl`”缓冲的数据量超过限制，它将向 downstream 返回错误：
  - 如问题发生在请求处理时，则返回 `413`; 
  - 如果问题发生在响应处理时，则返回 `500` 或“`resetStream()`”。



## Ref.

> - [Flow control](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)
> - [Envoy buffer management & flow control](https://docs.google.com/document/d/1EB3ybx3yTndp158c4AdQ4nutksZA9lL-BQvixhPnb_4/edit?usp=sharing)