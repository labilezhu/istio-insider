# Istio 指标(草稿)

## Istio 自己的 Metrics

### 默认的标准指标说明

> https://istio.io/latest/docs/reference/config/metrics/

#### Metrics

For HTTP, HTTP/2, and GRPC traffic, Istio generates the following metrics:

- **Request Count** (`istio_requests_total`): This is a `COUNTER` incremented for every request handled by an Istio proxy.
- **Request Duration** (`istio_request_duration_milliseconds`): This is a `DISTRIBUTION` which measures the duration of requests.
- **Request Size** (`istio_request_bytes`): This is a `DISTRIBUTION` which measures HTTP request body sizes.
- **Response Size** (`istio_response_bytes`): This is a `DISTRIBUTION` which measures HTTP response body sizes.
- **gRPC Request Message Count** (`istio_request_messages_total`): This is a `COUNTER` incremented for every gRPC message sent from a client.
- **gRPC Response Message Count** (`istio_response_messages_total`): This is a `COUNTER` incremented for every gRPC message sent from a server.

For TCP traffic, Istio generates the following metrics:

- **Tcp Bytes Sent** (`istio_tcp_sent_bytes_total`): This is a `COUNTER` which measures the size of total bytes sent during response in case of a TCP connection.
- **Tcp Bytes Received** (`istio_tcp_received_bytes_total`): This is a `COUNTER` which measures the size of total bytes received during request in case of a TCP connection.
- **Tcp Connections Opened** (`istio_tcp_connections_opened_total`): This is a `COUNTER` incremented for every opened connection.
- **Tcp Connections Closed** (`istio_tcp_connections_closed_total`): This is a `COUNTER` incremented for every closed connection.

#### Labels

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

#### 与应用的 Metrics 整合到同一 endpoint 输出

:::{figure-md} 图：Istio端口与组件
:class: full-width

<img src="/ch1-istio-arch/istio-ports-components.assets/istio-ports-components.drawio.svg" alt="Istio端口与组件">

*图：Istio 端口与组件*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-ports-components.drawio.svg)*


> https://istio.io/v1.14/docs/ops/integrations/prometheus/#option-1-metrics-merging



To simplify configuration, Istio has the ability to control scraping entirely by `prometheus.io` annotations. This allows Istio scraping to work out of the box with standard configurations such as the ones provided by the [Helm `stable/prometheus`](https://github.com/helm/charts/tree/master/stable/prometheus) charts.



While `prometheus.io` annotations are not a core part of Prometheus, they have become the de facto standard to configure scraping.

This option is enabled by default but can be disabled by passing `--set meshConfig.enablePrometheusMerge=false` during [installation](https://istio.io/v1.14/docs/setup/install/istioctl/). When enabled, appropriate `prometheus.io` annotations will be added to all data plane pods to set up scraping. If these annotations already exist, they will be overwritten. With this option, the Envoy sidecar will merge Istio’s metrics with the application metrics. The merged metrics will be scraped from `/stats/prometheus:15020`.

This option exposes all the metrics in plain text.

This feature may not suit your needs in the following situations:

- You need to scrape metrics using TLS.
- Your application exposes metrics with the same names as Istio metrics. For example, your application metrics expose an `istio_requests_total` metric. This might happen if the application is itself running Envoy.
- Your Prometheus deployment is not configured to scrape based on standard `prometheus.io` annotations.

If required, this feature can be disabled per workload by adding a `prometheus.istio.io/merge-metrics: "false"` annotation on a pod.

#### 定制：为 Metrics 增加维度

> https://istio.io/latest/docs/tasks/observability/metrics/customize-metrics/#custom-statistics-configuration

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

2. Apply the following annotation to all injected pods with the list of the dimensions to extract into a Prometheus [time series](https://en.wikipedia.org/wiki/Time_series) using the following command:



This step is needed only if your dimensions are not already in [DefaultStatTags list](https://github.com/istio/istio/blob/release-1.14/pkg/bootstrap/config.go)

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template: # pod template
    metadata:
      annotations:
        sidecar.istio.io/extraStatTags: destination_port,request_host
```



To enable extra tags mesh wide, you can add `extraStatTags` to your mesh config:

```yaml
meshConfig:
  defaultConfig:
    extraStatTags:
     - destination_port
     - request_host
```

Ref:

- https://istio.io/latest/docs/reference/config/proxy_extensions/stats/#MetricConfig

#### 定制：加入 request / response 元信息维度

> https://istio.io/latest/docs/tasks/observability/metrics/classify-metrics/





### 工作原理

#### istio stat filter 使用

```yaml
labile@labile-T30 ➜ labile $ k -n istio-system get envoyfilters.networking.istio.io stats-filter-1.14 -o yaml
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


### 好参考

https://blog.christianposta.com/understanding-istio-telemetry-v2/





## Envoy 内置的 Metrics

Istio 默认用 istio-agent 去整合 Envoy 的 metrics。
而 Istio 默认打开的 Envoy 内置 Metrics 很少：

> https://istio.io/latest/docs/ops/configuration/telemetry/envoy-stats/

```
cluster_manager
listener_manager
server
cluster.xds-grpc
```

### 定制 Envoy 内置的 Metrics

> https://istio.io/latest/docs/ops/configuration/telemetry/envoy-stats/

To configure Istio proxy to record additional statistics, you can add [`ProxyConfig.ProxyStatsMatcher`](https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/#ProxyStatsMatcher) to your mesh config. For example, to enable stats for circuit breaker, retry, and upstream connections globally, you can specify stats matcher as follows:

Proxy needs to restart to pick up the stats matcher configuration.

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

You can also override the global stats matching configuration per proxy by using the `proxy.istio.io/config` annotation. For example, to configure the same stats generation inclusion as above, you can add the annotation to a gateway proxy or a workload as follows:

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

Note: If you are using `sidecar.istio.io/statsInclusionPrefixes`, `sidecar.istio.io/statsInclusionRegexps`, and `sidecar.istio.io/statsInclusionSuffixes`, consider switching to the `ProxyConfig`-based configuration as it provides a global default and a uniform way to override at the gateway and sidecar proxy.

### 原理

Envoy 配置：

```bash
istioctl proxy-config bootstrap fortio-server | yq eval -P  > /nfs/shareset/home/blog/content/zh/notes/cloud/istio/metrics/istio-metrics/envoy-config-bootstrap-default.yaml
```

> https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statsconfig

```yaml
bootstrap:
...
  statsConfig:
    statsTags:
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
        patterns:
          - prefix: reporter=
          - prefix: cluster_manager
          - prefix: listener_manager
          - prefix: server
          - prefix: cluster.xds-grpc ## only xDS cluster. No other biz cluster!!!!
          - prefix: wasm
          - suffix: rbac.allowed
          - suffix: rbac.denied
          - suffix: shadow_allowed
          - suffix: shadow_denied
          - prefix: component
```

定制后产生的配置：

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
...

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



