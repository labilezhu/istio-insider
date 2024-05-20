# 连接池

`Connection Pool` 使用连接重用和预连接等机制，提高了到同一 `upstream cluster` 下的同一 `upstream endpoint` 的连接建立效率。

## TCP Proxy 连接池
为让读者更容易理解连接池，以下先以相对比较简单的 `TCP Proxy 连接池` 来说明连接池的设计。


### TCP Proxy 连接池概述

首先看看概述一下 `Cluster Manager` / `Load Balancer` / `Connection Pool`  / `Network Filter` 的模块协作：

:::{figure-md} 图：Envoy TCP Proxy connection pool at high level
:class: full-width

<img src="/ch2-envoy/upstream/connection-pooling/connection-pooling-high-level.drawio.svg" alt="图：Envoy TCP Proxy connection pool at high level">

*图：Envoy TCP Proxy connection pool at high level*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fconnection-pooling-high-level.drawio.svg)*




### TCP Proxy 连接池详述

再在 Class 层，看看 `Cluster Manager` / `Load Balancer` / `Connection Pool`  / `Network Filter` 的模块协作：


:::{figure-md} 图：Envoy TCP Proxy connection pool at class level
:class: full-width

<img src="/ch2-envoy/upstream/connection-pooling/connection-pooling.drawio.svg" alt="图：Envoy TCP Proxy connection pool at class level">

*图：Envoy TCP Proxy connection pool at class level*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fconnection-pooling.drawio.svg)*


## HTTP 连接池

//TODO