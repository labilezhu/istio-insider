# Envoy Proxy (草稿)

要深入了解 Istio ，那么先得了解流量的核心 Envoy Proxy。这里有三个认知层次：
1. 了解原生的 可编程代理 `Envoy Proxy` 架构
2. 了解 Istio 的`Istio 定制版 Envoy Proxy`: [github.com/istio/proxy](https://github.com/istio/proxy) 做了什么扩展
3. 了解 istiod 如何编程控制 `Istio 定制版 Envoy Proxy` 以实现服务网格功能

## Envoy Filter

## Http Filter
