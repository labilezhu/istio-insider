# Istio 组件架构

还记得，小时候什么电器都喜欢拆拆合合的，收音机、CD机、电脑。但总有一种神奇的能力把拆散的东西整合回来，然后，就了解它的结构了。话说到这里，再看看我家娃这代，好像完全没这个兴趣和机会了，想想，哪个小孩会去拆 pad。就算拆了，也因元件太小和精密，看不出什么机理来。很难找到自驱型学习的人了。

技术学习和学习收音机的机理一样，有两个方向：

- 从大到小（或叫自顶向下）

  从整体上看功能、架构组件、组件关系、对外接口、数据流。如一个 HTTP 请求在 Istio 体系中的旅行。

- 从小到大（或叫自下向上，或叫从底层到高层）

  举几个栗子：

  - iptable / netfilter / conntrack 之于 Istio sidecar 流量拦截
  - Envoy HTTP Filter / Route 之于 Istio Destination Rule 与 Istio Virtual Service

但更多时候，是以上两个方法的综合使用。




## Istio 整体架构

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


```{toctree}
:hidden:
service-mesh-base-concept
istio-ports-components
istio-data-panel-arch
```

