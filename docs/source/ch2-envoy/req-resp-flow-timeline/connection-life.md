# HTTP Connection Life

## Upstream/Downstream 连接解藕

> HTTP/1.1 规范有这个设计：
> HTTP Proxy 是 L7 层的代理，应该和 L3/L4 层的连接生命周期分开。

所以，像从 Downstream 来的 `Connection: Close` 、 `Connection: Keepalive` 这种 Header， Envoy 不会 Forward 到 Upstream 。 Downstream 连接的生命周期，当然会遵从 `Connection: xyz` 的指示控制。但 Upstream 的连接生命周期不会被 Downstream 的连接生命周期影响。 即，是两个独立的连接生命周期管理。

> [Github Issue: HTTP filter before and after evaluation of Connection: Close header sent by upstream#15788](https://github.com/envoyproxy/envoy/issues/15788#issuecomment-811429722) 说明了这个问题：
> This doesn't make sense in the context of Envoy, where downstream and upstream are decoupled and can use different protocols. I'm still not completely understanding the actual problem you are trying to solve?

## Envoy 与 Downstream/Upstream 连接状态不同步

以下大部分情况，算是个发生可能性低的 race condition。但，在大流量下，再少的可能性也是有遇到的时候。`Design For  Failure` 是程序员的天职。

### Downstream 向 Envoy 关闭中的连接发送请求

> [Github Issue: 502 on our ALB when traffic rate drops#13388](https://github.com/envoyproxy/envoy/issues/13388#issuecomment-703716766)
> Fundamentally, the problem is that ALB is reusing connections that Envoy is closing. This is an inherent(固有) race condition with HTTP/1.1. 
> You need to configure the `ALB max connection` / `idle timeout` to be < `any envoy timeout`.
> 
> To have no race conditions, the ALB needs to support `max_connection_duration` and have that be less than Envoy's max connection duration. There is no way to fix this with Envoy.



从 HTTP 层面来看，有两种场景可能出现这个问题：

* 服务端过早关闭连接(Server Prematurely/Early Closes Connection)

  Downsteam 在 write HTTP  Header 后，再 write HTTP Body。然而，Envoy 在未读完 HTTP Body 前，就已经 Write Response 且 `close(fd) `了 socket。这叫 `服务端过早关闭连接(Server Prematurely/Early Closes Connection)`。别以为 Envoy 不会出现未完全读完 Request 就 write Response and close socket 的情况。因为有时候，只需要 Header 就可以判断一个请求是非法的。所以大部分是返回 4xx/5xx 的 status code。

  而这时， Downstream 的 socket 状态可能是 `CLOSE_WAIT`。是还可以 write 的状态。但这个 HTTP Body 如果被 Envoy 的 Kernel 收到，由于 socket 已经执行过 `close(fd) `， socket 的文件 fd 已经关闭，所以 Kernel 直接丢弃 HTTP Body 且返回 `RST` 给对端（因为 socket 的文件 fd 已经关闭，已经没进程可能读取到数据了）。这时，可怜的 Downstream 就会说：`Connection rest` 之类的错误。

  * 减少这种 race condition 的可行方法是：delay close socket。 Envoy 已经有相关的配置：[delayed_close_timeout](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/network/http_connection_manager/v3/http_connection_manager.proto#:~:text=is%20not%20specified.-,delayed_close_timeout,-(Duration)%20The)

* Downstream 未感知到 HTTP Keepalive 的 Envoy 连接已经关闭

  上面提到的 Keepalive 连接复用的时候。Envoy 已经调用内核的 `close(fd) `  把 socket 变为 `FIN_WAIT_1/FIN_WAIT_2` 的 状态，且已经发出 `FIN`。但 Downstream 未收到，或已经收到但应用未感知到，且同时 reuse 了这个 http keepalive 连接来发送 HTTP Request。在 TCP 协议层面看来，这是个 `half-close` 连接，未 close 的一端的确是可以发数据到对端的。但已经调用过 `close(fd)` 的 kernel (Envoy端) 在收到数据包时，直接丢弃且返回 `RST` 给对端（因为 socket 的文件 fd 已经关闭，已经没进程可能读取到数据了）。这时，可怜的 Downstream 就会说：`Connection rest` 之类的错误。

  * 减少这种 race condition 的可行方法是：让 Upstream 对端配置比 Envoy 更小的 timeout 时间。让 Upsteam 主动关闭连接。





### Envoy 向已被 Upstream 关闭的 Upstream 连接发送请求

> [Github Issue: Envoy (re)uses connection after receiving FIN from upstream #6815](https://github.com/envoyproxy/envoy/issues/6815)
> With Envoy serving as HTTP/1.1 proxy, sometimes Envoy tries to reuse a connection even after receiving FIN from upstream. In production I saw this issue even with couple of seconds from FIN to next request, and Envoy never returned FIN ACK (just FIN from upstream to envoy, then PUSH with new HTTP request from Envoy to upstream). Then Envoy returns 503 UC even though upstream is up and operational.

本质上是 kernel 中的 socket 状态已经被对端发过来的 `FIN` 更新为 `CLOSE_WAIT` 状态，但 Envoy 程序中未更新，socket 与 HTTP Request 的早前的绑定还在。Envoy 在 write socket 时一定会失败。

Envoy 已经在这个问题上做了优化，对，只能减少可能，不可能完全避免：
> [Github Issue: HTTP1 conneciton pool attach pending request to half-closed connection #2715](https://github.com/envoyproxy/envoy/issues/2715)
> The HTTP1 connection pool attach pending request when a response is complete. Though the upstream server may already closed the connection, this will result the pending request attached to it end up with 503.
>
> 应对之法：
>
> HTTP/1.1 has this inherent timing issue. As I already explained, this is solved in practice by 
>
> a) setting Connection: Closed when closing a connection immediately and 
>
> b) having a reasonable idle timeout. 
>
> The feature @ramaraochavali is adding will allow setting the idle timeout to less than upstream idle timeout to help with this case. Beyond that, you should be using `router level retries`.

