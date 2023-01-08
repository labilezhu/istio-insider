# HTTP/1.1 Stream(草稿)

HTTP/2 才有 Stream 的概念。但为了在实现程序逻辑上的统一，Envoy 在实现上也对 HTTP/1.1 封装了 Steam 的概念。只是一个 HTTP/1.1 的 Request & Response 的过程，就对应一个 Stream。

> 见： https://www.envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts#stream-timeouts
> Stream timeouts apply to individual streams carried by an HTTP connection. Note that a stream is an HTTP/2 and HTTP/3 concept, however <mark>internally Envoy maps HTTP/1 requests to streams</mark> so in this context request/stream is interchangeable.

