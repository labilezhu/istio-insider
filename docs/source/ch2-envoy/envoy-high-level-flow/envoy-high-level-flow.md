# Envoy 抽象主流程与概念

## 再说 upstream/upstream

让我们回到 {doc}`/ch2-envoy/envoy@istio-conf-eg` 的例子：


:::{figure-md}

<img src="/ch1-istio-arch/istio-data-panel-arch.assets/istio-data-panel-arch.drawio.svg" alt="Inbound与Outbound概念">

*图:Istio 里的 Envoy 配置 - 部署*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-data-panel-arch.drawio.svg)*


这里，我们只分析 `fortio-server(pod)` 内的事情。从 POD 的流量角度来讲，它可以再分为两部分：
 - inbound : 入站
 - outbound : 出站

但单单从 Envoy 实现角度看，其实没有 `inbound` 或 `outbound` `这个概念的。inbound`/`outbound` 是 Istio 里的概念。详见： {doc}`/ch1-istio-arch/service-mesh-base-concept`
 一节。 Envoy 只有 `upstream` 与 `downstream` 的概念。  

对于 `fortio-server(pod)` 的 inbound:
  - downstream: client pod
  - upstream: app:8080

对于 `fortio-server(pod)` 的 outbound:
 - downstream: app
 - upstream: `fortio-server-l2(pod)`:8080

当初，我学习 Istio 时，最难理解的就是上面的概念了。这个弯太难转了。希望读者们可以比我强。




:::{figure-md} 从 Envoy 概念看的 upstream 与 downstream 抽象流程

<img src="/ch2-envoy/envoy-high-level-flow/envoy-high-level-flow.assets/envoy-high-level-flow-abstract.drawio.svg" alt="从 Envoy 概念看的 upstream 与 downstream 抽象流程">

*从 Envoy 概念看的 upstream 与 downstream 抽象流程*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy-high-level-flow-abstract.drawio.svg)*





