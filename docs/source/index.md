---
sd_hide_title: true
---

![Book Cover](./book-cover-mockup.jpg)

# 《Istio & Envoy 内幕》 前言


   ```{warning}
   这是一本编写中的书，现在只是草稿阶段。书名为《Istio & Envoy 内幕》，英文名《Istio Insider》。
   ```

## 《Istio & Envoy 内幕》 概述


### 本书是什么

书里说的，只是在我研究与使用了 Istio 一段时间后，的思考与记录。我不是专家，更不是 Istio Committer。只是排查过一些问题，浏览和 Debug 过一些 Istio/Envoy 的代码。

在研究 Istio 过程中。发现网上是有很多非常有价值的资讯。但是，要么主要是从使用者出发，没说实现机理；要么就是说了机理，也说得很好，但内容少了系统化和连贯性。

本书中，我尝试用设计与实现角度，尽量系统地去思考：
- Istio 为什么是现在的样子
- 那些魔术配置背后的真相： Linux + Envoy 
- Istio 将来可能是什么样子


### 本书不是什么

写本书的出发点，不是教如何使用 Istio。那些网上已经有太多非常优秀的书、文章、文档了。

### 书的访问地址
- [https://istio-insider.mygraphql.com](https://istio-insider.mygraphql.com)
- [https://istio-insider.readthedocs.io](https://istio-insider.readthedocs.io)
- [https://istio-insider.rtfd.io](https://istio-insider.rtfd.io)


### 关于作者
我叫 Mark Zhu，一个中年且头发少的程序员。

Blog: [https://blog.mygraphql.com/](https://blog.mygraphql.com/)


## 目录

The following topic areas will help you understand and use the theme.

```{toctree}
:hidden:
ch1-mesh-base/index
ch2-envoy/index
ch3-control-panel/index
```