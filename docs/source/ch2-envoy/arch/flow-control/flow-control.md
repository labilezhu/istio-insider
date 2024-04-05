# Flow Control

和所有代理类型的软件一样，Envoy 很重视流控。因为CPU/内存资源是有限的，时间也要避免单个流过度占用资源的情况。需要注意的是，和其它以异步/线程多路复用架构实现的软件一样，流控永远不是一个简单的事情。



Envoy 有一个[Flow Conrol 文档](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)专门叙述了其中的一些细节。我在本节中，记录一下我在这基础上的一些学习研究结果。



![代理 HTTP 响应时的 Http 流控与背压](flow-control.drawio.svg)







## Ref.

> [Flow control](https://github.com/envoyproxy/envoy/blob/main/source/docs/flow_control.md)
> [Envoy buffer management & flow control](https://docs.google.com/document/d/1EB3ybx3yTndp158c4AdQ4nutksZA9lL-BQvixhPnb_4/edit?usp=sharing)