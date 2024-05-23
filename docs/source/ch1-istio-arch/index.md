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




```{toctree}
:hidden:
istio-arch-overview
service-mesh-base-concept
istio-ports-components
istio-data-panel-arch
```

