# Istio 与 Envoy 指标

指标监控，可能是 DevOps 监控最重要的一环。但同时也可能是最难的一环。你可以从网上找到各种系统和中间件的 Grafana 监控仪表盘，它们大都设计得很漂亮得体，让人感觉监控已经完美无缺。  

但是，不知道你是否与我有同样的经历：在系统遇到问题时，手头有一大堆指标和监控仪表盘。
- 却不知道哪个指标才是问题相关的。
- 或者是，问题已经有个方向定位，却发现这个方向上，根本没有记录指标。

事情终究是要人来解决，再多的数据，如果：
- 不去理解这些数据背后的意义
- 不去主动分析自己的应用场景和部署环境需要什么数据，只是系统默认给什么就用什么

那么指标越多，越让人迷失在茫茫指标的海洋中。

作为一个混后端江湖多年的老程（老程序员），总有很多东西不懂，却难以启齿的。其中一个就是一些具体指标的意义。举个两个例子：
1. 我之前定位一个 Linux 下的网络问题，用了一个叫 `nstat` 的工具，它输出了非常多的指标，但很多会发现，有些指标是死活找不到说明文档的。这也是开源软件一直以来的问题，变化快，文档跟不上，甚至错误或过时未更新。
2. 我之前定位一个 Linux 下的 TCP 连接问题，用了一个叫 `ss` 的工具，它输出的神指标，也是搜索引擎也无能为力去解释。最后不得不看原码。还好，我把调查结果记录到 Blog 中：[《可能是最完整的 TCP 连接健康指标工具 ss 的说明》](https://blog.mygraphql.com/zh/notes/low-tec/network/tcp-inspect/)，希望对后来人有一些参考作用吧。


故事说完了，回到本书的主角 Istio 与 Envoy 上。它们的指标说明文档比上面的老爷车开源软件好一些。起码基本每个指标都有一行文字说明，虽然文字一样非常短且模糊。

## Istio 与 Envoy 指标概述

Istio 的 istio-proxy 的数据面指标是 基于 Envoy 的指标构架实现的。所以，后面我将先说 Envoy 的指标架构。


```{hint}
如果你和我一样，是个急性子。那么下图就是 Istio & Envoy 的指标地图了。它说明了指标产生在什么地方。后面内容会一步步推导出这个地图。
```

:::{figure-md} 图：Envoy@Istio的指标

<img src="/ch2-envoy/envoy@istio-metrics/index.assets/envoy@istio-metrics.drawio.svg" alt="Inbound与Outbound概念">

*图：Envoy@Istio的指标*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-metrics.drawio.svg)*


```{toctree}
:maxdepth: 1
envoy-stat.md
istio-stat.md
```
