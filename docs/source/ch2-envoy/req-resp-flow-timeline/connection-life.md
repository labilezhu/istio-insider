# HTTP Connection Life

## Upstream/Downstream 连接解藕

> HTTP/1.1 规范有这个设计：
> HTTP Proxy 是 L7 层的代理，应该和 L3/L4 层的连接生命周期分开。

所以，像从 Downstream 来的 `Connection: Close` 、 `Connection: Keepalive` 这种 Header， Envoy 不会 Forward 到 Upstream 。 Downstream 连接的生命周期，当然会遵从 `Connection: xyz` 的指示控制。但 Upstream 的连接生命周期不会被 Downstream 的连接生命周期影响。 即，是两个独立的连接生命周期管理。

> [Github Issue: HTTP filter before and after evaluation of Connection: Close header sent by upstream#15788](https://github.com/envoyproxy/envoy/issues/15788#issuecomment-811429722) 说明了这个问题：
> This doesn't make sense in the context of Envoy, where downstream and upstream are decoupled and can use different protocols. I'm still not completely understanding the actual problem you are trying to solve?


## Downstream/Upstream 对端主动 FIN 时，Envoy 未同步状态

### Downstream 对端向 Envoy 关闭中的连接发送请求

> [Github Issue: 502 on our ALB when traffic rate drops#13388](https://github.com/envoyproxy/envoy/issues/13388#issuecomment-703716766)
> Fundamentally, the problem is that ALB is reusing connections that Envoy is closing. This is an inherent(固有) race condition with HTTP/1.1. 
> You need to configure the `ALB max connection` / `idle timeout` to be < `any envoy timeout`.
> 
> To have no race conditions, the ALB needs to support `max_connection_duration` and have that be less than Envoy's max connection duration. There is no way to fix this with Envoy.

重点是，让 Upstream 对端配置比 Envoy 更小的 timeout 时间。让 Upsteam 主动关闭连接。

### Envoy 向已被 Upstream 关闭的 Upstream 连接发送请求

> [Github Issue: Envoy (re)uses connection after receiving FIN from upstream #6815](https://github.com/envoyproxy/envoy/issues/6815)
> With Envoy serving as HTTP/1.1 proxy, sometimes Envoy tries to reuse a connection even after receiving FIN from upstream. In production I saw this issue even with couple of seconds from FIN to next request, and Envoy never returned FIN ACK (just FIN from upstream to envoy, then PUSH with new HTTP request from Envoy to upstream). Then Envoy returns 503 UC even though upstream is up and operational.

大部分情况下，这是个 race condition.

Envoy 已经在这个问题上做了优化：
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

