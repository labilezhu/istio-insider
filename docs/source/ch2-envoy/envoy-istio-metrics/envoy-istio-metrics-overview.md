# Istio 与 Envoy 指标概述

Istio 的 istio-proxy 的数据面指标是 基于 Envoy 的指标构架实现的。所以，后面我将先说 Envoy 的指标架构。


```{hint}
如果你和我一样，是个急性子。那么下图就是 Istio & Envoy 的指标地图了。它说明了指标产生在什么地方。后面内容会一步步推导出这个地图。
```

:::{figure-md} 图：Envoy@Istio的指标

<img src="/ch2-envoy/envoy-istio-metrics/index.assets/envoy@istio-metrics.drawio.svg" alt="Inbound与Outbound概念">

*图：Envoy@Istio的指标*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-metrics.drawio.svg)*



:::{figure-md}
:class: full-width

<img src="/ch2-envoy/req-resp-flow-timeline/req-resp-flow-timeline.assets/req-resp-flow-timeline.drawio.svg" alt="图：Envoy 请求与响应时序线上的指标">

*图：Envoy 请求与响应时序线上的指标*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Freq-resp-flow-timeline.drawio.svg)*


