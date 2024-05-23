# Istio 整体架构

Istio 整体架构不是本书的重点。相信有兴趣看本书的读者也了解过了。
本节主要目的是回顾一下整体架构。我相信读者都是 Istio 用户，甚至是资深的 Istio 用户。但有时人就是这样，太深度介入一样事物时，就很容易忘记事物的全貌。  

这里也顺道说明本书后面内容的重点。毕竟精力和兴趣有限，我只会专注一部分。


:::{figure-md} Istio整体架构

<img src="index.assets/istio-arch.svg" alt="Istio 整体架构">

图：Istio 整体架构图  
来自：https://istio.io/latest/docs/ops/deployment/architecture/  
:::


- Proxy 
  这个应该不用多介绍。数据面最重要的组件。也是本书的重点。因为，相较控制面，我对数据面更有兴趣。需要注意的是，这里的 Proxy 是指 `istio-proxy` 这个 container。正如你知道的，它里面最少有两个组件：
  - 属于控制面的 `pilot-agent`。外号：本地管理员。
  - 属于数据面的 `Envoy Proxy`。外号：本地执行者。这是本书的第一个重点。
- istiod  
  外号：控制面大脑、战略级的指挥中心、权威认证授权机构。


好，大饼图先到这里。后面，我们开始拆解这些组件，和分析它们的交互。Let's go!
