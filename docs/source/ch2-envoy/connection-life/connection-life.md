# HTTP Connection Life

## Upstream/Downstream 连接解藕

> HTTP/1.1 规范有这个设计：
> HTTP Proxy 是 L7 层的代理，应该和 L3/L4 层的连接生命周期分开。

所以，像从 Downstream 来的 `Connection: Close` 、 `Connection: Keepalive` 这种 Header， Envoy 不会 Forward 到 Upstream 。 Downstream 连接的生命周期，当然会遵从 `Connection: xyz` 的指示控制。但 Upstream 的连接生命周期不会被 Downstream 的连接生命周期影响。 即，这是两个独立的连接生命周期管理。

> [Github Issue: HTTP filter before and after evaluation of Connection: Close header sent by upstream#15788](https://github.com/envoyproxy/envoy/issues/15788#issuecomment-811429722) 说明了这个问题：
> This doesn't make sense in the context of Envoy, where downstream and upstream are decoupled and can use different protocols. I'm still not completely understanding the actual problem you are trying to solve?

## 连接超时相关配置参数



### idle_timeout

(Duration) The idle timeout for connections. The idle timeout is defined as the period in which there are no active requests. When the idle timeout is reached the connection will be closed. If the connection is an HTTP/2 downstream connection a drain sequence will occur prior to closing the connection, see [drain_timeout](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/network/http_connection_manager/v3/http_connection_manager.proto#envoy-v3-api-field-extensions-filters-network-http-connection-manager-v3-httpconnectionmanager-drain-timeout). Note that request based timeouts mean that HTTP/2 PINGs will not keep the connection alive. If not specified, this defaults to **1 hour.** To disable idle timeouts explicitly set this to 0.

> Warning
>
> Disabling this timeout has a highly likelihood of yielding connection leaks due to lost TCP FIN packets, etc.

If the [overload action](https://www.envoyproxy.io/docs/envoy/latest/configuration/operations/overload_manager/overload_manager#config-overload-manager-overload-actions) “envoy.overload\_actions.reduce\_timeouts” is configured, this timeout is scaled for downstream connections according to the value for [HTTP\_DOWNSTREAM\_CONNECTION\_IDLE](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/overload/v3/overload.proto#envoy-v3-api-enum-value-config-overload-v3-scaletimersoverloadactionconfig-timertype-http-downstream-connection-idle).



### max_connection_duration

(Duration) The maximum duration of a connection. The duration is defined as a period since a connection was established. If not set, there is no max duration. When `max_connection_duration` is reached and if there are no active streams, the connection will be closed. If the connection is a downstream connection and there are any active streams, the `drain sequence` will kick-in, and the connection will be force-closed after the drain period. See [drain\_timeout](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/network/http_connection_manager/v3/http_connection_manager.proto#envoy-v3-api-field-extensions-filters-network-http-connection-manager-v3-httpconnectionmanager-drain-timeout).

> [Github Issue: http: Allow upper bounding lifetime of downstream connections #8302](https://github.com/envoyproxy/envoy/issues/8302)
>
> [Github PR: add `max_connection_duration`: http conn man: allow to upper-bound downstream connection lifetime. #8591](https://github.com/envoyproxy/envoy/pull/8591)
>
> [Github PR: upstream: support max connection duration for upstream HTTP connections #17932](https://github.com/envoyproxy/envoy/pull/17932)



> [Github Issue: Forward Connection:Close header to downstream#14910](https://github.com/envoyproxy/envoy/issues/14910#issuecomment-773434342)
> For HTTP/1, Envoy will send a `Connection: close` header after `max_connection_duration` if another request comes in. If not, after some period of time, it will just close the connection.
>
> https://github.com/envoyproxy/envoy/issues/14910#issuecomment-773434342
>
> Note that `max_requests_per_connection` isn't (yet) implemented/supported for downstream connections.
>
> For HTTP/1, Envoy will send a `Connection: close` header after `max_connection_duration` （且在 `drain_timeout` 前） if another request comes in. If not, after some period of time, it will just close the connection.
>
> I don't know what your downstream LB is going to do, but note that according to the spec, the `Connection` header is hop-by-hop for HTTP proxies.





### max_requests_per_connection

(UInt32Value) Optional maximum requests for both upstream and downstream connections. If not specified, there is no limit. Setting this parameter to 1 will effectively disable keep alive. For HTTP/2 and HTTP/3, due to concurrent stream processing, the limit is approximate.

> [Github Issue: Forward Connection:Close header to downstream#14910](https://github.com/envoyproxy/envoy/issues/14910#issuecomment-840892488)
>
> We are having this same issue when using istio ([istio/istio#32516](https://github.com/istio/istio/issues/32516)). We are migrating to use istio with envoy sidecars frontend be an AWS ELB. We see that connections from ELB -> envoy stay open even when our application is sending `Connection: Close`. `max_connection_duration` works but does not seem to be the best option. Our applications are smart enough to know when they are overloaded from a client and send `Connection: Close` to shard load.
>
> I tried writing an envoy filter to get around this but the filter gets applied before the stripping. Did anyone discover a way to forward the connection close header?



### drain_timeout - for downstream only

(Duration) The time that Envoy will wait between sending an HTTP/2 “shutdown notification” (GOAWAY frame with max stream ID) and a final GOAWAY frame. This is used so that Envoy provides a grace period for new streams that race with the final GOAWAY frame. During this grace period, Envoy will continue to accept new streams. 

After the grace period, a final GOAWAY frame is sent and Envoy will start refusing new streams. Draining occurs both when:

* a connection hits the `idle timeout` 

  即系连接到达 `idle_timeout` 或 `max_connection_duration`后，都会开始 `draining` 的状态和`drain_timeout`计时器。对于 HTTP/1.1，在 `draining` 状态下。如果 downstream 过来请求，Envoy 都在响应中加入 `Connection: close`  header。

* or during general server draining. 

The default grace period is 5000 milliseconds (5 seconds) if this option is not specified.



###  delayed_close_timeout - for downstream only

(Duration) The delayed close timeout is for downstream connections managed by the HTTP connection manager. It is defined as a grace period after connection close processing has been locally initiated during which Envoy will wait for the peer to close (i.e., a TCP FIN/RST is received by Envoy from the downstream connection) prior to Envoy closing the socket associated with that connection。

即系在一些场景下，Envoy 会在未完全读取完 HTTP Request 前，就回写 HTTP Response 且希望关闭连接。这叫 `服务端过早关闭连接(Server Prematurely/Early Closes Connection)`。这时有几种可能情况：

- downstream 还在发送 HTTP Reqest 当中(socket write)。
- 或者是 Envoy 的 kernel 中，还有 `socket recv buffer` 未被 Envoy user-space 进取。通常是 HTTP Conent-Lentgh 大小的 BODY 还在内核的 `socket recv buffer` 中，未完整加载到 Envoy user-space

这两种情况下， 如果 Envoy 调用 `close(fd)` 去关闭连接， downstream 均可能会收到来自 Envoy kernel 的 `RST` 。最终 downstream 可能不会 read socket 中的 HTTP Response 就直接认为连接异常，向上层报告异常：`Peer connection rest`。

详见：{doc}`connection-life-race` 。

为缓解这种情况，Envoy 提供了延后关闭连接的配置。希望等待 downstream 完成 socket write 的过程。让  `kernel socket recv buffer`  数据都加载到 `user space` 中。再去调用 `close(fd)`。



NOTE: This timeout is enforced even when the socket associated with the downstream connection is pending a flush of the write buffer. However, any progress made writing data to the socket will restart the timer associated with this timeout. This means that the total grace period for a socket in this state will be <total_time_waiting_for_write_buffer_flushes>+<delayed_close_timeout>.

即系，每次 write socket 成功，这个 timer 均会被 rest.

Delaying Envoy’s connection close and giving the peer the opportunity to initiate the close sequence mitigates(缓解) a race condition that exists when **downstream clients do not drain/process data in a connection’s receive buffer** after a remote close has been detected via a socket write().  即系，可以缓解 downsteam 在 write socket 失败后，就不去 read socket 取 Response 的情况。

This race leads to such clients failing to process the response code sent by Envoy, which could result in erroneous downstream processing.

If the timeout triggers, Envoy will close the connection’s socket.

The default timeout is 1000 ms if this option is not specified.

> Note:
>
> To be useful in avoiding the race condition described above, this timeout must be set to at least <max round trip time expected between clients and Envoy>+<100ms to account for a reasonable “worst” case processing time for a full iteration of Envoy’s event loop>.



> Warning:
>
> A value of 0 will completely disable delayed close processing. When disabled, the downstream connection’s socket will be closed immediately after the write flush is completed or will never close if the write flush does not complete.



## Envoy Connection Time Life Race condition

```{toctree}
connection-life-race.md
```