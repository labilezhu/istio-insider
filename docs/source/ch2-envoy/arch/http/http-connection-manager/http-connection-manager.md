# http connection manager(草稿)

为了扩展性，Envoy 的 http connection manager 也设计成经典的 filter chain 实现。这个和 Listener Filter Chain 有一点类似：

:::{figure-md} 图：http connection manager 设计模型
:class: full-width 
<img src="/ch2-envoy/arch/http/http-connection-manager/http-connection-manager.assets/http-connection-manager.drawio.svg" alt="图：http connection manager 设计模型">

*图：http connection manager 设计模型*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fhttp-connection-manager.drawio.svg)*

http filter 抽象对象定义：

:::{figure-md} 图：http filter 抽象对象
:class: full-width
<img src="/ch2-envoy/arch/http/http-connection-manager/http-connection-manager.assets/http-filter-abstract.drawio.svg" alt="图：http filter 抽象对象">

*图：http filter 抽象对象*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fhttp-filter-abstract.drawio.svg)*


代码上的 http filter C++类关系：

:::{figure-md} 图：http filter C++类关系
:class: full-width
<img src="/ch2-envoy/arch/http/http-connection-manager/http-connection-manager.assets/http-filter-code-oop.drawio.svg" alt="图：http filter C++类关系">

*图：http filter C++类关系*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fhttp-filter-code-oop.drawio.svg)*


