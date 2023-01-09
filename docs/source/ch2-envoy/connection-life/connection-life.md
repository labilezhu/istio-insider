# HTTP Connection Life

## Upstream/Downstream 连接解藕

> HTTP/1.1 规范有这个设计：
> HTTP Proxy 是 L7 层的代理，应该和 L3/L4 层的连接生命周期分开。

所以，像从 Downstream 来的 `Connection: Close` 、 `Connection: Keepalive` 这种 Header， Envoy 不会 Forward 到 Upstream 。 Downstream 连接的生命周期，当然会遵从 `Connection: xyz` 的指示控制。但 Upstream 的连接生命周期不会被 Downstream 的连接生命周期影响。 即，这是两个独立的连接生命周期管理。

> [Github Issue: HTTP filter before and after evaluation of Connection: Close header sent by upstream#15788](https://github.com/envoyproxy/envoy/issues/15788#issuecomment-811429722) 说明了这个问题：
> This doesn't make sense in the context of Envoy, where downstream and upstream are decoupled and can use different protocols. I'm still not completely understanding the actual problem you are trying to solve?

## Envoy Connection Time Life Race condition

```{toctree}
connection-life-race.md
```