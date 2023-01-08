# HTTP Timeout 配置(草稿)

## MAX Timeout

### max_requests_per_connection

> [Github Issue: Forward Connection:Close header to downstream#14910](https://github.com/envoyproxy/envoy/issues/14910#issuecomment-773434342)
> For HTTP/1, Envoy will send a `Connection: close` header after `max_connection_duration` if another request comes in. If not, after some period of time, it will just close the connection.

#### max_requests_per_connection and Load Balance

> [Github Issue: Forward Connection:Close header to downstream#14910](https://github.com/envoyproxy/envoy/issues/14910#issuecomment-840892488)
>
> We are having this same issue when using istio ([istio/istio#32516](https://github.com/istio/istio/issues/32516)). We are migrating to use istio with envoy sidecars frontend be an AWS ELB. We see that connections from ELB -> envoy stay open even when our application is sending `Connection: Close`. `max_connection_duration` works but does not seem to be the best option. Our applications are smart enough to know when they are overloaded from a client and send `Connection: Close` to shard load.
>
> I tried writing an envoy filter to get around this but the filter gets applied before the stripping. Did anyone discover a way to forward the connection close header?

## Idle Timeout