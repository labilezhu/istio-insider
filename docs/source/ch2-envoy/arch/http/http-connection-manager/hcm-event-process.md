# HCM upstream/downstream 事件驱动协作下的 HTTP 反向代理流程

## HTTP 反向代理的总流程

整体看，Socket 事件驱动的 HTTP 反向代理总流程如下：
![图：Socket 事件驱动的 HTTP 反向代理总流程](/ch2-envoy/arch/event-driven/event-driven.assets/envoy-event-model-proxy.drawio.svg)

图中看出，有4种事件驱动了整个流程。后面几节会逐个分析。

为免一下子进入各个步骤细节而让人迷途，建议回顾一下之前举例的所有步骤的总流程： 
{doc}`/ch2-envoy/envoy@istio-conf-eg`



### Downstream Read Request 模块协作

:::{figure-md} 图：Downstream Read-Ready 模块协作

<img src="/ch2-envoy/arch/http/http-connection-manager/hcm-event-process.assets/envoy-hcm-read-down-req.drawio.svg" alt="图：Downstream Read-Ready 模块协作">

*图：Downstream Read-Ready 模块协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-hcm-read-down-req.drawio.svg)*


大概说明一下流程：
1. downstream socket 可读回调
2. Http::ConnectionManagerImpl 读取 socket，增量放入 Http1::ConnectionImpl
3. Http1::ConnectionImpl 调用 nghttp2 增量解释 HTTP 请求
4. 如果 nghttp2 认为已经  完整读取了 HTTP Request 请求，则调用 `Http::ServerConnection::onMessageCompleteBase()`
5. `Http::ServerConnection::onMessageCompleteBase()` 首先 **停止 downstream ReadReady 监听**
6. `Http::ServerConnection::onMessageCompleteBase()` 调用 `Http::FilterManager` ，发起 `http filter chain` 的 decodeHeaders 迭代流程
7. 一般，`http filter chain` 的最后一个 http filter 是 `Router::Filter` ，`Router::Filter::decodeHeaders()`  被调用
8. `Router::Filter::decodeHeaders()` 的逻辑就见下图了。

#### Downstream Request Router 模块协作

:::{figure-md} 图：Downstream Request Router 模块协作

<img src="/ch2-envoy/arch/http/http-connection-manager/hcm-event-process.assets/envoy-hcm-router-on-down-req-complete.drawio.svg" alt="图：Downstream Request Router 模块协作">

*图：Downstream Request Router 模块协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-hcm-router-on-down-req-complete.drawio.svg)*

大概说明一下流程：
1. `Router::Filter` ，`Router::Filter::decodeHeaders()`  被调用
2. 根据配置的 Router 规则，匹配到 Cluster
3. 如 Cluster 连接池对象不存在，则新建
4. 新建 `Envoy::Router::UpstreamRequest` 对象。
5. 调用 `Envoy::Router::UpstreamRequest::encodeHeaders(bool end_stream)` ， encode HTTP header
6. 经过一系列的负载均衡算法，匹配到 upstream 的 host(endpoint)
7. 发现到选定的 upstream host 的连接不足，则：
   1. 打开一新的 socket fd(未连接)
   2. **注册 upstream socket FD 的 WriteReady / Connected 事件**。 准备在事件回调时写 upstream request
   3. **用 socket fd 发起到 upstream host 的异步连接请求**
8. 关联 downstream 与 upstream fd


### Upstream Write Request 模块协作

:::{figure-md} 图：upstream connect & write 模块协作

<img src="/ch2-envoy/arch/http/http-connection-manager/hcm-event-process.assets/envoy-hcm-upstream-flow-connected-write.drawio.svg" alt="图：upstream connect & write 模块协作">

*图：upstream connect & write 模块协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-hcm-upstream-flow-connected-write.drawio.svg)*



大概说明一下流程：
1. upstream socket write ready 回调
2. 发现是连接成功回调，关联 upstream socket 到 `ConnectionPool::ActiveClient`
3. upstream socket write ready 回调
4. 发现是连接可写，写入 upstream HTTP request


### Upstream Read Response 模块协作

:::{figure-md} 图：Upstream Read-Response 模块协作

<img src="/ch2-envoy/arch/http/http-connection-manager/hcm-event-process.assets/envoy-hcm-upstream-flow-read-resp.drawio.svg" alt="图：Upstream Read-Response 模块协作">

*图：Upstream Read-Response 模块协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-hcm-upstream-flow-read-resp.drawio.svg)*


### Downstream Write Response 模块协作


:::{figure-md} 图：Downstream Write Response 模块协作

<img src="/ch2-envoy/arch/http/http-connection-manager/hcm-event-process.assets/envoy-hcm-write-down-resp.drawio.svg" alt="图：Downstream Write Response 模块协作">

*图：Downstream Write Response 模块协作*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-hcm-write-down-resp.drawio.svg)*

## 求证过程

- [逆向工程与云原生现场分析 Part4 —— eBPF 跟踪 Istio/Envoy 之 upstream/downstream 事件驱动协作下的 HTTP 反向代理流程](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part4/)