# Upstream

```{toctree}
:hidden:
connection-pooling/connection-pooling.md
```

Envoy 的 Upstream 功能，由  `Cluster Manager` / `Load Balancer` / `Connection Pool`  三大模块去实现。这几个模块与 `Network Filter` 之间协作，完成了面向 Upstream 的流量调整与转发功能。

1. 首先，每个 worker thread 有自己专用的 `Cluster Manager` / `Load Balancer` / `Connection Pool`  实例。 当 Envoy accept 一个 downstream connection 时，会选择一个 worker thread 作为 `owner thread`。
2. 并在这个`owner thread` 内创建专用的 `Network Filter` 实例。
3. 之后所有这个 downstream connection 的相关的操作，包括所有的相关的 upstream 操作，都在这个 `owner thread` 上执行。
   
本书把这些关联的 downstream / upstream 以及相关的 `Network Filter` 实例，称为 `Downstream-Upstream-Bundle` 。
而这个 `owner thread` 的 `Cluster Manager` / `Load Balancer` / `Connection Pool` 实例是在同一 `owner thread` 上的所有 `Downstream-Upstream-Bundle` 所共享的。

