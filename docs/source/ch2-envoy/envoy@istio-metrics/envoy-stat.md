# Envoy 指标

## Envoy 指标概述

```{note}
本节参考了： https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/observability/statistics
```

Envoy 的主要目标之一是使网络易于理解。 Envoy 会根据其配置方式产生大量统计信息。一般来说，统计数据(指标)分为三类：

- **Downstream**：Downstream 指标与外来的连接/请求有关。它们由 `listener`、`HTTP connection manager(HCM)`、`TCP proxy filter` 等产生。
- **Upstream**：Upstream 指标与外向的连接/请求有关。它们由 `connection pool`、`router filter`、`tcp proxy filter`等产生。
- **Server**：`Server` 指标信息描述 Envoy 服务器实例的运作情况。服务器正常运行时间或分配的内存量等统计信息。

在最简单场景下，单个 Envoy Proxy 通常涉及 `Downstream` 和 `Upstream` 统计数据。这两种指标反映了取该 `网络节点` 的运行情况。来自整个网格的统计数据提供了每个` 网络节点` 和整体网络健康状况的非常详细的汇总信息。Envoy 的文档对这些指标有一些简单的说明。

<!-- 从 `Envoy v2 API` 开始，Envoy 能够支持自定义、可插拔的 `指标适配插件(Stats Sink)`。 这是 [Envoy 自带的 Stats Sink 列表](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statssink)：

- envoy.stat_sinks.dog_statsd
- envoy.stat_sinks.graphite_statsd
- envoy.stat_sinks.hystrix
- envoy.stat_sinks.metrics_service
- envoy.stat_sinks.statsd
- envoy.stat_sinks.wasm -->


### Tag

Envoy 的指标还有两个子概念，支持在指标中使用： `标签(tags)`/`维度(dimensions)` 。这里的 `tags` 对等于 Prometheus 指标的 label。意义上，可以理解为：分类维度。


Envoy 的 `指标` 由规范的字符串来标识。这些字符串的动态部分（子字符串）被提取成为 `标签(tag)`。可以通过指定 [tag 提取规则(Tag Specifier configuration.)](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier) 来定制 tag 。

举个例子：
```bash
### 1. 原始的 Envoy 指标 ###

$ kubectl exec fortio-server -c istio-proxy -- curl 'localhost:15000/stats'

# 返回：
cluster.outbound|8080||fortio-server-l2.mark.svc.cluster.local.external.upstream_rq_2xx: 300

# 其中：
# - `outbound|8080||fortio-server-l2.mark.svc.cluster.local` 部分是 upstream cluster 的名字。可以正则提取作为 tag。
# - `2xx` 部分是 HTTP Status Code 的分类。可以正则提取作为 tag。 下文将有这个提取规则的配置说明。

### 2. 给 Prometheus 的指标 ###
$ kubectl exec fortio-server -c istio-proxy -- curl 'localhost:15000/stats?format=prometheus' | grep 'outbound|8080||fortio-server-l2' | grep 'external.upstream_rq'

# 返回：
envoy_cluster_external_upstream_rq{response_code_class="2xx",cluster_name="outbound|8080||fortio-server-l2.mark.svc.cluster.local"} 300

```

### 指标数据类型

Envoy 发出三种类型的值作为统计信息：

- **计数器(Counters)**：无符号整数，只会增加而不会减少。例如，总请求。
- **仪表(Gauges)**：增加和减少的无符号整数。例如，当前活动的请求。
- **直方图(Histograms)**：作为指标流的一部分的无符号整数，然后由收集器聚合以最终产生汇总的百分位值(percentile，即平常说的 P99/P50/Pxx)。例如，`Upsteam` 响应时间。

在 Envoy 的内部实现中，Counters 和 Gauges 被分批并定期刷新以提高性能。Histograms 在接收时写入。



## 指标释义

从指标的产出地点来划分，可以分为：
- cluster manager : 面向 `upstream`  的 L3/L4/L7 层指标
- http connection manager(HCM) ： 面向 `upstream` & `downstream` 的 L7 层指标
- listeners : 面向 `downstream` 的 L3/L4 层指标
- server(全局)

### cluster manager

[Envoy 文档:cluster manager stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats)

上面文档已经说得比较详细了。我只补充一些在性能调优时需要关注的方面。




### http connection manager(HCM)

[Envoy 文档:http connection manager(HCM) stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/stats)

可以认为，这是 downstream 的 HTTP(L7) 层的指标。

### listeners

[Envoy 文档:listener stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/listeners/stat)

可以认为，这是 downstream 的 L3/L4 层的指标。




### server

> https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/statistics


## 配置说明

```{hint}
如果你认真看过本书的前言中的 {ref}`index:本书不是什么` ，说好的不是“使用手册”，为何又讲起配置来了？好吧，我只能说，从了解使用方法入手，再学实现，比直接一来就源码的方法更好让人类入门。

本节参考：
[Envoy 文档](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto)
```


### config.bootstrap.v3.Bootstrap

[Envoy 文档:config.bootstrap.v3.Bootstrap proto](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/config/bootstrap/v3/bootstrap.proto#L44)

```json
{
  "node": {...},
  "static_resources": {...},
  "dynamic_resources": {...},
  "cluster_manager": {...},
  "stats_sinks": [],
  "stats_config": {...},
  "stats_flush_interval": {...},
  "stats_flush_on_admin": ...,
...
}
```

```{hint}
什么是 `stats sink` 本书不作说明。Istio 默认没定制相关配置。以下只说关注的部分配置。
```


- stats\_config
([config.metrics.v3.StatsConfig](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statsconfig)) 用于内部处理统计信息的配置。

- stats\_flush\_interval
([Duration](https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#duration)) 刷新 `stats sink` 的时间间隔。。出于性能原因，Envoy 不会实时刷新 counter ，仅定期刷新 counter 和 gauge 。 如果未指定，则默认值为 5000 毫秒。 `stats_flush_interval` 或 `stats_flush_on_admin` 只能设置之一。 Duration 必须至少为 1 毫秒，最多为 5 分钟。


- stats\_flush\_on\_admin
([bool](https://developers.google.com/protocol-buffers/docs/proto#scalar)) 仅当在 `管理界面(admin interface)` 上查询时才将统计信息刷新到 `sink`。 如果设置，则不会创建刷新计时器。 只能设置 `stats_flush_on_admin` 或 `stats_flush_interval` 之一。

##### config.metrics.v3.StatsConfig

[Envoy 文档:config-metrics-v3-statsconfig](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#config-metrics-v3-statsconfig)

```json
{
  "stats_tags": [],
  "use_all_default_tags": {...},
  "stats_matcher": {...},
  "histogram_bucket_settings": []
}
```

- stats_tags - 维度提取规则(对应 Prometheus 的 label 提取)
  (**多个** [config.metrics.v3.TagSpecifier](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier) ) 每个 `指标名称字符串` 都通过这些标签规则独立处理。 当一个标签匹配时，第一个捕获组不会立即从名称中删除，所以后面的 [TagSpecifiers](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier) 也可以重复匹配同一部分。在完成所有标签匹配后，再剪裁 `指标名称字符串` 的匹配部分，并作为 `stats sink` 的指标名，例如 Prometheus的指标名。

- use_all_default_tags
  (BoolValue) 使用 Envoy 中指定的所有默认标签正则表达式。 这些可以与 stats_tags 中指定的自定义标签结合使用。 它们将在自定义标签之前进行处理。Istio 默认为 false.

- stats_matcher
  ([config.metrics.v3.StatsMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statsmatcher)) 指定 Envoy 要产出哪些指标。支持 `包含`/`排除` 规则指定。 如果未提供，则所有指标都将产出。 阻止某些指标集的统计可以提高一点 Envoy 运行性能。


##### config.metrics.v3.StatsMatcher

[Envoy 文档:config-metrics-v3-statsmatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#config-metrics-v3-statsmatcher)

用于禁用/开启统计指标计算与产出的配置。

```json
{
  "reject_all": ...,
  "exclusion_list": {...},
  "inclusion_list": {...}
}
```

- reject_all
  ([bool](https://developers.google.com/protocol-buffers/docs/proto#scalar)) 如果 `reject_all` 为 true ，则禁用所有统计信息。 如果 `reject_all` 为 false，则启用所有统计信息。

- exclusion_list
  ([type.matcher.v3.ListStringMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-msg-type-matcher-v3-liststringmatcher)) 排除列表

- inclusion_list
  ([type.matcher.v3.ListStringMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-msg-type-matcher-v3-liststringmatcher)) 包含列表

[[type.matcher.v3.ListStringMatcher proto\]](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/type/matcher/v3/string.proto#L72)


