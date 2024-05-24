# Envoy 指标

## Envoy 指标概述


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
- **直方图(Histograms)**：作为指标流的一部分的无符号整数，然后由收集器聚合以最终产生汇总的百分位值(percentile，即平常说的 P99/P50/Pxx)。例如，`Upstream` 响应时间。

在 Envoy 的内部实现中，Counters 和 Gauges 被分批并定期刷新以提高性能。Histograms 在接收时写入。


## 指标释义

从指标的产出地点来划分，可以分为：
- cluster manager : 面向 `upstream`  的 L3/L4/L7 层指标
- http connection manager(HCM) ： 面向 `upstream` & `downstream` 的 L7 层指标
- listeners : 面向 `downstream` 的 L3/L4 层指标
- server(全局)
- watch dog

下面我只选择了部分关键的性能指标来简单说明。

### cluster manager

[Envoy 文档:cluster manager stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats)

上面文档已经说得比较详细了。我只补充一些在性能调优时需要关注的方面。那么，一般需要关注什么指标？

我们从著名的 [Utilization Saturation and Errors (USE)](https://www.brendangregg.com/usemethod.html) 方法学来分析。

利用率(Utilization):
 - `upstream_cx_total` (Counter): 连接数
 - `upstream_rq_active`

饱和度(Saturation):
 - `upstream_rq_time` (Histogram): 响应时间
 - `upstream_cx_connect_ms` (Histogram)
 - `upstream_cx_rx_bytes_buffered`
 - `upstream_cx_tx_bytes_buffered`
 - `upstream_rq_pending_total` (Counter)
 - `upstream_rq_pending_active` (Gauge)
 - `circuit_breakers.*cx_open`
 - `circuit_breakers.*cx_pool_open`
 - `circuit_breakers.*rq_pending_open`
 - `circuit_breakers.*rq_open`
 - `circuit_breakers.*rq_retry_open`
 
错误(Error):
 - `upstream_cx_connect_fail` (Counter): 连接失败数
 - `upstream_cx_connect_timeout` (Counter): 连接超时数
 - `upstream_cx_overflow` (Counter): 集群连接断路器溢出的总次数
 - `upstream_cx_pool_overflow`
 - `upstream_cx_destroy_local_with_active_rq`
 - `upstream_cx_destroy_remote_with_active_rq`
 - `upstream_rq_timeout`
 - `upstream_rq_retry`
 - `upstream_rq_rx_reset`
 - `upstream_rq_tx_reset`
 - `upstream_rq_pending_overflow` (Counter) : 溢出连接池或请求（主要针对 HTTP/2 及更高版本）熔断并失败的请求总数

其它：
 - `upstream_rq_total` (Counter): TPS (吞吐)
 - `upstream_cx_destroy_local` (Counter): Envoy 主动断开的连接计数
 - `upstream_cx_destroy_remote` (Counter): Envoy 被动断开的连接计数
 - `upstream_cx_length_ms` (Histogram)




### http connection manager(HCM)

[Envoy 文档:http connection manager(HCM) stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/stats)

可以认为，这是面向 `downstream` & 部分 `upstream` 的 L7 层指标

利用率(Utilization):
 - `downstream_cx_total` 
 - `downstream_cx_active`
 - `downstream_cx_http1_active`
 - `downstream_rq_total`
 - `downstream_rq_http1_total`
 - `downstream_rq_active`


饱和度(Saturation):
 - `downstream_cx_rx_bytes_buffered` 
 - `downstream_cx_tx_bytes_buffered`
 - `downstream_flow_control_paused_reading_total`
 - `downstream_flow_control_resumed_reading_total`


错误(Error):
 - `downstream_cx_destroy_local_active_rq`
 - `downstream_cx_destroy_remote_active_rq`
 - `downstream_rq_rx_reset`
 - `downstream_rq_tx_reset`
 - `downstream_rq_too_large`
 - `downstream_rq_max_duration_reached`
 - `downstream_rq_timeout`
 - `downstream_rq_overload_close`
 - `rs_too_large`

其它：
 - `downstream_cx_destroy_remote` 
 - `downstream_cx_destroy_local`
 - `downstream_cx_length_ms`

### listeners

[Envoy 文档:listener stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/listeners/stats)

可以认为，这是 downstream 的 L3/L4 层的指标。

利用率(Utilization):
 - `downstream_cx_total` 
 - `downstream_cx_active`


饱和度(Saturation):
 - `downstream_pre_cx_active`


错误(Error):
 - `downstream_cx_transport_socket_connect_timeout`
 - `downstream_cx_overflow` 
 - `no_filter_chain_match`
 - `downstream_listener_filter_error`
 - `no_certificate`

其它：
 - `downstream_cx_length_ms` 


### server

Envoy 基础信息指标

[Envoy 文档:server stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/statistics)

利用率(Utilization):
 - `concurrency` 


错误(Error):
 - `days_until_first_cert_expiring`


### watch dog

[Envoy 文档: Watchdog](https://www.envoyproxy.io/docs/envoy/latest/operations/performance)

Envoy 还包括一个可配置的看门狗系统，它可以在 Envoy 没有响应时增加统计数据并选择性地终止服务器。 系统有两个独立的看门狗配置，一个用于主线程，一个用于工作线程； 因为不同的线程有不同的工作负载。 这些统计数据有助于从高层次上理解 Envoy 的事件循环是否因为它正在做太多工作、阻塞或没有被操作系统调度而没有响应。

饱和度(Saturation):
 - `watchdog_mega_miss`(Counter): mega 未命中数
 - `watchdog_miss`(Counter): 未命中数

如果你对 watchdog 机制的兴趣，可以参考：
> https://github.com/envoyproxy/envoy/issues/11391
> https://github.com/envoyproxy/envoy/issues/11388

### Event loop 
[Envoy 文档: Event loop](https://www.envoyproxy.io/docs/envoy/latest/operations/performance)

Envoy 架构旨在通过在少量线程上运行事件循环来优化可扩展性和资源利用率。 `“main”` 线程负责控制面处理，每个 `“worker”` 线程分担数据面的一部分任务。 Envoy 公开了两个统计信息来监控所有这些线程事件循环的性能。

跑一轮循环的耗时：事件循环的每次迭代都会执行一些任务。任务数量会随着负载的变化而变化。但是，如果一个或多个线程具有异常长尾循环执行耗时，则可能存在性能问题。例如，负责可能在工作线程之间分配不均，或者插件中可能存在长时间阻塞操作阻碍了任务进度。

轮询延迟：在事件循环的每次迭代中，事件调度程序都会轮询 I/O 事件，并在某些 `I/O 事件就绪` 或 发生 `超时` 时 “唤醒” 线程，以先发生者为准。在 `超时` 的情况下，我们可以测量轮询后预期唤醒时间与实际唤醒时间的差值；这种差异称为 “`轮询延迟`”。看到一些小的 `轮询延迟` 是正常的，通常等于内核调度程序的 “时间片(time slice”)” 或 “量子(quantum)” ——这取决于运行 Envoy 的操作系统 —— 但如果这个数字大大高于其正常观察到的基线，它表示内核调度程序可能发生延迟。

可以通过将 [enable_dispatcher_stats](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/bootstrap/v3/bootstrap.proto#envoy-v3-api-field-config-bootstrap-v3-bootstrap-enable-dispatcher-stats) 设置为 `true` 来启用这些统计信息。

- `main` 线程的事件调度器有一个以 `server.dispatcher.` 为根的统计树。 
- 每个 `worker` 线程的事件调度器都有一个以 `listener_manager.worker_<id>.dispatcher.` 为根的统计树。

每棵树都有以下统计信息：

| Name             | Type      | Description                          |
| ---------------- | --------- | ------------------------------------ |
| loop_duration_us | Histogram | 以微秒为单位的事件循环持续时间 |
| poll_delay_us    | Histogram | 以微秒为单位的轮询延迟       |

请注意，此处不包括任何辅助(非 main 与 worker)线程。

```{hint}
Watch Dog 和 Event loop 都是解决与监控事件处理延迟与时效的工具，这里有很多细节和故事，甚至可以说到 Linux Kernel。希望本书后面有时间，可以和大家一起学习和分析这些有趣的细节。
```

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
什么是 `stats sink`？ 本书不作说明。Istio 默认没定制相关配置。以下只说关注的部分配置。
```


- stats\_config
([config.metrics.v3.StatsConfig](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statsconfig)) 用于内部处理统计信息的配置。

- stats\_flush\_interval
([Duration](https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#duration)) 刷新 `stats sink` 的时间间隔。。出于性能原因，Envoy 不会实时刷新 counter ，仅定期刷新 counter 和 gauge 。 如果未指定，则默认值为 5000 毫秒。 `stats_flush_interval` 或 `stats_flush_on_admin` 只能设置之一。 Duration 必须至少为 1 毫秒，最多为 5 分钟。


- stats\_flush\_on\_admin
([bool](https://developers.google.com/protocol-buffers/docs/proto#scalar)) 仅当在 `管理界面(admin interface)` 上查询时才将统计信息刷新到 `sink`。 如果设置，则不会创建刷新计时器。 只能设置 `stats_flush_on_admin` 或 `stats_flush_interval` 之一。

### config.metrics.v3.StatsConfig

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


### config.metrics.v3.StatsMatcher

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



```{note}
本节参考了： https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/observability/statistics

下一节，将以 Istio 如何使用上面的配置为例，举例说明。
```