# Istio 指标

## Istio 自己的 Metrics

### 标准指标说明

> 参考：https://istio.io/latest/docs/reference/config/metrics/

#### Metrics

对于 HTTP、HTTP/2 和 GRPC 流量，Istio 默认生成以下指标：

- **Request Count** (`istio_requests_total`): This is a `COUNTER` incremented for every request handled by an Istio proxy.
- **Request Duration** (`istio_request_duration_milliseconds`): This is a `DISTRIBUTION` which measures the duration of requests.
- **Request Size** (`istio_request_bytes`): This is a `DISTRIBUTION` which measures HTTP request body sizes.
- **Response Size** (`istio_response_bytes`): This is a `DISTRIBUTION` which measures HTTP response body sizes.
- **gRPC Request Message Count** (`istio_request_messages_total`): This is a `COUNTER` incremented for every gRPC message sent from a client.
- **gRPC Response Message Count** (`istio_response_messages_total`): This is a `COUNTER` incremented for every gRPC message sent from a server.

对于 TCP 流量，Istio 生成以下指标：

- **Tcp Bytes Sent** (`istio_tcp_sent_bytes_total`): This is a `COUNTER` which measures the size of total bytes sent during response in case of a TCP connection.
- **Tcp Bytes Received** (`istio_tcp_received_bytes_total`): This is a `COUNTER` which measures the size of total bytes received during request in case of a TCP connection.
- **Tcp Connections Opened** (`istio_tcp_connections_opened_total`): This is a `COUNTER` incremented for every opened connection.
- **Tcp Connections Closed** (`istio_tcp_connections_closed_total`): This is a `COUNTER` incremented for every closed connection.

#### Prometheus 的 Labels

- **Reporter**: This identifies the reporter of the request. It is set to `destination` if report is from a server Istio proxy and `source` if report is from a client Istio proxy or a gateway.

- **Source Workload**: This identifies the name of source workload which controls the source, or “unknown” if the source information is missing.

- **Source Workload Namespace**: This identifies the namespace of the source workload, or “unknown” if the source information is missing.

- **Source Principal**: This identifies the peer principal of the traffic source. It is set when peer authentication is used.

- **Source App**: This identifies the source application based on `app` label of the source workload, or “unknown” if the source information is missing.

- **Source Version**: This identifies the version of the source workload, or “unknown” if the source information is missing.

- **Destination Workload**: This identifies the name of destination workload, or “unknown” if the destination information is missing.

- **Destination Workload Namespace**: This identifies the namespace of the destination workload, or “unknown” if the destination information is missing.

- **Destination Principal**: This identifies the peer principal of the traffic destination. It is set when peer authentication is used.

- **Destination App**: This identifies the destination application based on `app` label of the destination workload, or “unknown” if the destination information is missing.

- **Destination Version**: This identifies the version of the destination workload, or “unknown” if the destination information is missing.

- **Destination Service**: This identifies destination service host responsible for an incoming request. Ex: `details.default.svc.cluster.local`.

- **Destination Service Name**: This identifies the destination service name. Ex: “details”.

- **Destination Service Namespace**: This identifies the namespace of destination service.

- **Request Protocol**: This identifies the protocol of the request. It is set to request or connection protocol.

- **Response Code**: This identifies the response code of the request. This label is present only on HTTP metrics.

- **Connection Security Policy**: This identifies the service authentication policy of the request. It is set to `mutual_tls` when Istio is used to make communication secure and report is from destination. It is set to `unknown` when report is from source since security policy cannot be properly populated.

- **Response Flags**: Additional details about the response or connection from proxy. In case of Envoy, see `%RESPONSE_FLAGS%` in [Envoy Access Log](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage#config-access-log-format-response-flags) for more detail.

例如，想统计 upstream circuit breaker 相关的 失败请求数：
```
sum(istio_requests_total{response_code="503", response_flags="UO"}) by (source_workload, destination_workload, response_code)
```

- **Canonical Service**: A workload belongs to exactly one canonical service, whereas it can belong to multiple services. A canonical service has a name and a revision so it results in the following labels.

  ```yaml
  source_canonical_service
  source_canonical_revision
  destination_canonical_service
  destination_canonical_revision
  ```

  

- **Destination Cluster**: This identifies the cluster of the destination workload. This is set by: `global.multiCluster.clusterName` at cluster install time.

- **Source Cluster**: This identifies the cluster of the source workload. This is set by: `global.multiCluster.clusterName` at cluster install time.

- **gRPC Response Status**: This identifies the response status of the gRPC. This label is present only on gRPC metrics.

### 使用

#### istio-proxy 与应用的 Metrics 整合输出

:::{figure-md} 图：istio-proxy 与应用的 Metrics 整合输出
:class: full-width

<img src="/ch1-istio-arch/istio-ports-components.assets/istio-ports-components.drawio.svg" alt="Istio端口与组件">

*图：istio-proxy 与应用的 Metrics 整合输出*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-ports-components.drawio.svg)*


> 参考：https://istio.io/v1.14/docs/ops/integrations/prometheus/#option-1-metrics-merging


Istio 能够完全通过 `prometheus.io`  annotations 来控制抓取。虽然 `prometheus.io`  annotations 不是 Prometheus 的核心部分，但它们已成为配置抓取的事实标准。

此选项默认启用，但可以通过在 [安装](https://istio.io/v1.14/docs/setup/install/istioctl/) 期间传递 `--set meshConfig.enablePrometheusMerge=false` 来禁用。启用后，将向所有数据平面 pod 添加适当的 `prometheus.io`  annotations 以设置抓取。如果这些注释已经存在，它们将被覆盖。使用此选项，Envoy sidecar 会将 Istio 的指标与应用程序指标合并。合并后的指标将从 `/stats/prometheus:15020` 中抓取。

此选项以明文形式公开所有指标。


#### 定制：为 Metrics 增加维度

> 参考： https://istio.io/latest/docs/tasks/observability/metrics/customize-metrics/#custom-statistics-configuration

如，增加端口、与 HTTP HOST 头 维度。

1.

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    telemetry:
      v2:
        prometheus:
          configOverride:
            inboundSidecar:
              metrics:
                - name: requests_total
                  dimensions:
                    destination_port: string(destination.port)
                    request_host: request.host
            outboundSidecar:
              metrics:
                - name: requests_total
                  dimensions:
                    destination_port: string(destination.port)
                    request_host: request.host
            gateway:
              metrics:
                - name: requests_total
                  dimensions:
                    destination_port: string(destination.port)
                    request_host: request.host

```

2. 使用以下命令将以下 annotation 应用到所有注入的 pod，其中包含要提取到 Prometheus [时间序列](https://en.wikipedia.org/wiki/Time_series) 的维度列表：

仅当您的维度不在 [DefaultStatTags 列表] 中时才需要此步骤（https://github.com/istio/istio/blob/release-1.14/pkg/bootstrap/config.go）

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template: # pod template
    metadata:
      annotations:
        sidecar.istio.io/extraStatTags: destination_port,request_host
```

要在网格范围内启用额外 `Tag` ，您可以将 `extraStatTags` 添加到网格配置中：

```yaml
meshConfig:
  defaultConfig:
    extraStatTags:
     - destination_port
     - request_host
```

> 参考 : https://istio.io/latest/docs/reference/config/proxy_extensions/stats/#MetricConfig

#### 定制：加入 request / response 元信息维度

可以把 request 或 repsonse 里一些基础信息 加入到 指标的维度。如，URL Path，这在需要为相同服务分隔统计不同 REST API 的指标时，相当有用。

> 参考 : https://istio.io/latest/docs/tasks/observability/metrics/classify-metrics/


### 工作原理

#### istio stat filter 使用

Istio 在自己的定制版本 Envoy 中，加入了 stats-filter 插件，用于计算 Istio 自己想要的指标：

```yaml
$ k -n istio-system get envoyfilters.networking.istio.io stats-filter-1.14 -o yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  annotations:
  labels:
    install.operator.istio.io/owning-resource-namespace: istio-system
    istio.io/rev: default
    operator.istio.io/component: Pilot
    operator.istio.io/version: 1.14.3
  name: stats-filter-1.14
  namespace: istio-system
spec:
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_OUTBOUND
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
            subFilter:
              name: envoy.filters.http.router
      proxy:
        proxyVersion: ^1\.14.*
    patch:
      operation: INSERT_BEFORE
      value:
        name: istio.stats
        typed_config:
          '@type': type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.wasm.v3.Wasm
          value:
            config:
              configuration:
                '@type': type.googleapis.com/google.protobuf.StringValue
                value: |
                  {
                    "debug": "false",
                    "stat_prefix": "istio"
                  }
              root_id: stats_outbound
              vm_config:
                code:
                  local:
                    inline_string: envoy.wasm.stats
                runtime: envoy.wasm.runtime.null
                vm_id: stats_outbound
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
            subFilter:
              name: envoy.filters.http.router
      proxy:
        proxyVersion: ^1\.14.*
    patch:
      operation: INSERT_BEFORE
      value:
        name: istio.stats
        typed_config:
          '@type': type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.wasm.v3.Wasm
          value:
            config:
              configuration:
                '@type': type.googleapis.com/google.protobuf.StringValue
                value: |
                  {
                    "debug": "false",
                    "stat_prefix": "istio",
                    "disable_host_header_fallback": true,
                    "metrics": [
                      {
                        "dimensions": {
                          "destination_cluster": "node.metadata['CLUSTER_ID']",
                          "source_cluster": "downstream_peer.cluster_id"
                        }
                      }
                    ]
                  }
              root_id: stats_inbound
              vm_config:
                code:
                  local:
                    inline_string: envoy.wasm.stats
                runtime: envoy.wasm.runtime.null
                vm_id: stats_inbound
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
            subFilter:
              name: envoy.filters.http.router
      proxy:
        proxyVersion: ^1\.14.*
    patch:
      operation: INSERT_BEFORE
      value:
        name: istio.stats
        typed_config:
          '@type': type.googleapis.com/udpa.type.v1.TypedStruct
          type_url: type.googleapis.com/envoy.extensions.filters.http.wasm.v3.Wasm
          value:
            config:
              configuration:
                '@type': type.googleapis.com/google.protobuf.StringValue
                value: |
                  {
                    "debug": "false",
                    "stat_prefix": "istio",
                    "disable_host_header_fallback": true
                  }
              root_id: stats_outbound
              vm_config:
                code:
                  local:
                    inline_string: envoy.wasm.stats
                runtime: envoy.wasm.runtime.null
                vm_id: stats_outbound
  priority: -1
```


#### istio stat Plugin 实现

https://github.com/istio/proxy/blob/release-1.14/extensions/stats/plugin.cc

内置的 Metric:

```c++
const std::vector<MetricFactory>& PluginRootContext::defaultMetrics() {
  static const std::vector<MetricFactory> default_metrics = {
      // HTTP, HTTP/2, and GRPC metrics
      MetricFactory{"requests_total", MetricType::Counter,
                    [](::Wasm::Common::RequestInfo&) -> uint64_t { return 1; },
                    static_cast<uint32_t>(Protocol::HTTP) |
                        static_cast<uint32_t>(Protocol::GRPC),
                    count_standard_labels, /* recurrent */ false},
      MetricFactory{"request_duration_milliseconds", MetricType::Histogram,
                    [](::Wasm::Common::RequestInfo& request_info) -> uint64_t {
                      return request_info.duration /* in nanoseconds */ /
                             1000000;
                    },
                    static_cast<uint32_t>(Protocol::HTTP) |
                        static_cast<uint32_t>(Protocol::GRPC),
                    count_standard_labels, /* recurrent */ false},
      MetricFactory{"request_bytes", MetricType::Histogram,
                    [](::Wasm::Common::RequestInfo& request_info) -> uint64_t {
                      return request_info.request_size;
                    },
                    static_cast<uint32_t>(Protocol::HTTP) |
                        static_cast<uint32_t>(Protocol::GRPC),
                    count_standard_labels, /* recurrent */ false},
      MetricFactory{"response_bytes", MetricType::Histogram,
                    [](::Wasm::Common::RequestInfo& request_info) -> uint64_t {
                      return request_info.response_size;
                    },
                    static_cast<uint32_t>(Protocol::HTTP) |
                        static_cast<uint32_t>(Protocol::GRPC),
                    count_standard_labels, /* recurrent */ false},
...
```


https://github.com/istio/proxy/blob/release-1.14/extensions/stats/plugin.cc#L591

```c++
void PluginRootContext::report(::Wasm::Common::RequestInfo& request_info,
                               bool end_stream) {

...
  map(istio_dimensions_, outbound_, peer_node_info.get(), request_info);

  for (size_t i = 0; i < expressions_.size(); i++) {
    if (!evaluateExpression(expressions_[i].token,
                            &istio_dimensions_.at(count_standard_labels + i))) {
      LOG_TRACE(absl::StrCat("Failed to evaluate expression: <",
                             expressions_[i].expression, ">"));
      istio_dimensions_[count_standard_labels + i] = "unknown";
    }
  }

  auto stats_it = metrics_.find(istio_dimensions_);
  if (stats_it != metrics_.end()) {
    for (auto& stat : stats_it->second) {
      if (end_stream || stat.recurrent_) {
        stat.record(request_info);
      }
      LOG_DEBUG(
          absl::StrCat("metricKey cache hit ", ", stat=", stat.metric_id_));
    }
    cache_hits_accumulator_++;
    if (cache_hits_accumulator_ == 100) {
      incrementMetric(cache_hits_, cache_hits_accumulator_);
      cache_hits_accumulator_ = 0;
    }
    return;
  }
...
}                                  
```


> 关于 Istio 的指标原理，这是一个很好的参考文章：https://blog.christianposta.com/understanding-istio-telemetry-v2/


## Envoy 内置的 Metrics

Istio 默认用 istio-agent 去整合 Envoy 的 metrics。
而 Istio 默认打开的 Envoy 内置 Metrics 很少：

> 见：https://istio.io/latest/docs/ops/configuration/telemetry/envoy-stats/

```
cluster_manager
listener_manager
server
cluster.xds-grpc
```

### 定制 Envoy 内置的 Metrics

> 参考：https://istio.io/latest/docs/ops/configuration/telemetry/envoy-stats/

如果要配置 Istio Proxy 以记录 其它 Envoy 原生的指标，您可以将 [`ProxyConfig.ProxyStatsMatcher`](https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/#ProxyStatsMatcher) 添加到网格配置中。 例如，要全局启用断路器、重试和上游连接的统计信息，您可以指定 stats matcher，如下所示：

代理需要重新启动以获取统计匹配器配置。

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    defaultConfig:
      proxyStatsMatcher:
        inclusionRegexps:
          - ".*circuit_breakers.*"
        inclusionPrefixes:
          - "upstream_rq_retry"
          - "upstream_cx"
```

您还可以使用 `proxy.istio.io/config` annotation 为个别代码指定配置。 例如，要配置与上面相同的统计信息，您可以将 annotation 添加到 gateway proxy 或 workload，如下所示：

```yaml
metadata:
  annotations:
    proxy.istio.io/config: |-
      proxyStatsMatcher:
        inclusionRegexps:
        - ".*circuit_breakers.*"
        inclusionPrefixes:
        - "upstream_rq_retry"
        - "upstream_cx"
```


### 原理

下面，看看 Istio 默认配置下，如何配置 Envoy。

```bash
istioctl proxy-config bootstrap fortio-server | yq eval -P  > envoy-config-bootstrap-default.yaml
```
输出：

```yaml
bootstrap:
...
  statsConfig:
    statsTags: # 从指标名中抓取 Tag(prometheus label)
      - tagName: cluster_name
        regex: ^cluster\.((.+?(\..+?\.svc\.cluster\.local)?)\.)
      - tagName: tcp_prefix
        regex: ^tcp\.((.*?)\.)\w+?$
      - tagName: response_code
        regex: (response_code=\.=(.+?);\.;)|_rq(_(\.d{3}))$
      - tagName: response_code_class
        regex: _rq(_(\dxx))$
      - tagName: http_conn_manager_listener_prefix
        regex: ^listener(?=\.).*?\.http\.(((?:[_.[:digit:]]*|[_\[\]aAbBcCdDeEfF[:digit:]]*))\.)
...
    useAllDefaultTags: false
    statsMatcher:
      inclusionList:
        patterns: # 选择要记录的指标
          - prefix: reporter=
          - prefix: cluster_manager
          - prefix: listener_manager
          - prefix: server
          - prefix: cluster.xds-grpc ## 只记录 xDS cluster. 即不记录用户自己服务的 cluster !!!
          - prefix: wasm
          - suffix: rbac.allowed
          - suffix: rbac.denied
          - suffix: shadow_allowed
          - suffix: shadow_denied
          - prefix: component
```

这时，如果修改 pod 的定义为：

```yaml
    annotations:
      proxy.istio.io/config: |-
        proxyStatsMatcher:
          inclusionRegexps:
          - "cluster\\..*fortio.*" #proxy upstream(outbound)
          - "cluster\\..*inbound.*" #proxy upstream(inbound，这里一般就是指到同一 pod 中运行的应用了)
          - "http\\..*"
          - "listener\\..*"
```

产生新的 Envoy 配置：

```json
 "stats_matcher": {
   "inclusion_list": {
     "patterns": [
       {
         "prefix": "reporter="
       },
       {
         "prefix": "cluster_manager"
       },
       {
         "prefix": "listener_manager"
       },
       {
         "prefix": "server"
       },
       {
         "prefix": "cluster.xds-grpc"
       },
 

       {
         "safe_regex": {
           "google_re2": {},
           "regex": "cluster\\..*fortio.*"
         }
       },
       {
         "safe_regex": {
           "google_re2": {},
           "regex": "cluster\\..*inbound.*"
         }
       },
       {
         "safe_regex": {
           "google_re2": {},
           "regex": "http\\..*"
         }
       },
       {
         "safe_regex": {
           "google_re2": {},
           "regex": "listener\\..*"
         }
       },
```

## 总结：Istio-Proxy 指标地图

要做好监控，首先要深入了解指标原理。而要了解指标原理，当然要知道指标是产生流程中的什么位置，什么组件。看完上面关于 Envoy 与 Istio 的指标说明后。可以大概得到以下结论：

:::{figure-md} 图：Istio-Proxy 指标地图
:class: full-width

<img src="/ch2-envoy/envoy@istio-metrics/index.assets/envoy@istio-metrics.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio-Proxy 指标地图*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-metrics.drawio.svg)*

```{note}
本节的实验环境说明见于： {ref}`appendix-lab-env/appendix-lab-env-base:简单分层实验环境`
```