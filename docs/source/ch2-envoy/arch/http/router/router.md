# Router

Router 流程简述:

:::{figure-md} 图：Router 流程简述
:class: full-width
<img src="/ch2-envoy/arch/http/router/router.assets/router-filter-base-flow.drawio.svg" alt="图：Router 流程简述">

*图：Router 流程简述*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Frouter-filter-base-flow.drawio.svg)*

## 扩展阅读

如果有兴趣研究 Router 的实现细节，建议看看我 Blog 的文章：
 - [逆向工程与云原生现场分析 Part4 —— eBPF 跟踪 Istio/Envoy 之 upstream/downstream 事件驱动协作下的 HTTP 反向代理流程](https://blog.mygraphql.com/zh/posts/low-tec/trace/trace-istio/trace-istio-part4/)