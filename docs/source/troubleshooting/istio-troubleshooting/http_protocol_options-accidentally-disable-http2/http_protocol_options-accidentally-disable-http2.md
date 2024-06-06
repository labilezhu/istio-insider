---
typora-root-url: ../../..
---

# 因配置 Envoy 保留 HTTP/1 header 大小写，在混合 HTTP1 和 HTTP2 的 Istio 网格上意外禁用了 HTTP/2

## 动机

简单说：我们希望在长期运行 HTTP/1.1 的 Istio 环境中支持 HTTP/2。所以我们需要一个 HTTP/1.1 和 HTTP2 混合网格。

我们希望在服务之间的以下 API 流中支持 HTTP/2：

```
[serviceA app --h2c--> serviceA istio-proxy] ----(http2 over mTLS)---> [serviceB istio-proxy --h2c--> serviceB app]
```


环境:

```
service A: 
  Pod A: 
    ip addr: 192.168.88.94

service B: 10.110.152.25
  Pod B: serviceB-ver-6b54d8c7bc-6vclp
    ip addr: 192.168.33.5
```


## 症状


所以我们在 Pod A 上尝试下面的 curl ：

```bash
curl -iv http://serviceB:8080/resource1?p1=v1 \
 -H "Content-Type:application/json" --http2-prior-knowledge
 
*   Trying 10.110.152.25:8080...
* Connected to serviceB (10.110.152.25) port 8080 (#0)
* h2h3 [:method: GET]
* h2h3 [:path: /resource1?p1=v1]
* h2h3 [:scheme: http]
* h2h3 [:authority: serviceB:8080]
* h2h3 [user-agent: curl/8.0.1]
* h2h3 [accept: */*]
* h2h3 [content-type: application/json]
* Using Stream ID: 1 (easy handle 0x557514133e80)
> GET /resource1?p1=v1 HTTP/2
> Host: serviceB:8080
> user-agent: curl/8.0.1
> accept: */*
> content-type:application/json
> 
< HTTP/2 200 
HTTP/2 200 
< content-type: application/json
content-type: application/json
< date: Tue, 07 May 2024 08:44:33 GMT
date: Tue, 07 May 2024 08:44:33 GMT
< x-envoy-upstream-service-time: 19
x-envoy-upstream-service-time: 19
< server: envoy
server: envoy
```

Pod A 上运行的应用程序似乎使用 HTTP/2。



让我们检查 Pod B 是否使用 HTTP/2 ：

```bash
kubectl logs --tail=1 -f serviceB-ver-6b54d8c7bc-6vclp -c istio-proxy
```



```
[2024-05-07T07:18:41.470Z] "GET /resource1?p1=v1 HTTP/1.1" 200 - via_upstream - "-" 0 48 16 14 "-" "curl/8.0.1" "6add007-7242-4983-9862-63cd108e5" "serviceB:8080" "[p8]192.168.88.94[/p8]:8080" outbound|8080|ver|serviceB.ns.svc.cluster.local [p8]192.168.33.5[/p8]:48344 [p8]10.110.152.25[/p8]:8080 [p8]192.168.33.5[/p8]:36650 - -
```

我们可以看到 serviceB 的 istio-proxy 使用 HTTP/1.1 协议。


## 术语

- h2c - `基于 TCP 的 HTTP/2` 或 `HTTP/2 明文（Cleartext）`
- h2 - `基于 TLS 的 HTTP/2`  (使用 ALPN 作协议协商)
- ALPN - [基于 TLS 的 `ALPN(Application-Layer Protocol Negotiation 应用层协议协商)`](https://en.wikipedia.org/wiki/Application-Layer_Protocol_Negotiation)


## 背景知识

在调查之前，假设您有以下基础知识 : {doc}`/ch4-istio-data-plane/data-plane-tunnel/alpn-http-meta-exchange/alpn-http-meta-exchange` .

:::{figure-md} 图: HTTP 协议元数据交换概述 2

<img src="/ch4-istio-data-plane/data-plane-tunnel/alpn-http-meta-exchange/alpn-http-meta-exchange-high-level.drawio.svg" alt="图 - HTTP 协议元数据交换概述">

*图: HTTP 协议元数据交换概述 2*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Falpn-http-meta-exchange-high-level.drawio.svg)*

## 调查

我们知道流量的路径：

```
[serviceA app --h2c--> serviceA istio-proxy] ----(http2 over mTLS)---> [serviceB istio-proxy --h2c--> serviceB app]
```

我们知道 `serviceA istio-proxy` 使用 ALPN 来与 `serviceB istio-proxy` 协商使用哪个版本的 HTTP。请参阅 [Better Default Networking – Protocol sniffing](https://docs.google.com/document/d/1l0oVAneaLLp9KjVOQSb3bwnJJpjyxU_xthpMKFM_l7o/edit#heading=h.edsodfixs1x7) 。


因此，我们在 “serviceA istio-proxy” 上运行 tcpdump 来探视两个 istio-proxy 之间的 ALPN：

```
ss -K 'dst 192.168.88.94'

tcpdump -i eth0@if3623 'host 192.168.88.94' -c 1000 -s 65535 -w /tmp/tcpdump.pcap

tshark -r /tmp/tcpdump.pcap -d tcp.port==8080,ssl -2R "ssl" -V | less
```



```
...
Transport Layer Security
    TLSv1.3 Record Layer: Handshake Protocol: Client Hello
        Content Type: Handshake (22)
        Version: TLS 1.0 (0x0301)
        Length: 2723
        Handshake Protocol: Client Hello
            Handshake Type: Client Hello (1)
            Extension: application_layer_protocol_negotiation (len=32)
                Type: application_layer_protocol_negotiation (16)
                Length: 32
                ALPN Extension Length: 30
                ALPN Protocol
                    ALPN string length: 14
                    ALPN Next Protocol: istio-http/1.1
                    ALPN string length: 5
                    ALPN Next Protocol: istio
                    ALPN string length: 8
                    ALPN Next Protocol: http/1.1      
...                    
```

未找到预期的 “istio-h2” 或 “h2” 。



### outbound istio-proxy 的 debug log

打开 outbound istio-proxy 的调试日志：

```bash
curl -XPOST http://localhost:15000/logging\?filter\=trace
```

可以看到日志输出:

```
{"level":"debug","time":"2024-05-07T07:18:41.471107Z","scope":"envoy filter","msg":"override with 3 ALPNs"}
```

### Evnoy Listener

因此，我们 dump `serviceA istio-proxy` 的 Envoy 配置：
`serviceA istio-proxy` 上的 Envoy Listener：

```yaml
configs:
  dynamic_listeners:
        - name: 0.0.0.0_8080
        active_state:
          version_info: 2024-04-16T09:30:41Z/90
          listener:
            '@type': type.googleapis.com/envoy.config.listener.v3.Listener
            name: 0.0.0.0_8080
            address:
              socket_address:
                address: 0.0.0.0
                port_value: 8080
            filter_chains:
              - filter_chain_match:
                  transport_protocol: raw_buffer
                  application_protocols:
                    - http/1.1
                    - h2c
                filters:
                  - name: envoy.filters.network.http_connection_manager
                    typed_config:
                      '@type': type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                      stat_prefix: outbound_0.0.0.0_8080
                      rds:
...
                      http_filters:
                        - name: envoy.filters.http.grpc_stats
...
                        - name: istio.alpn
                          typed_config:
                            '@type': type.googleapis.com/istio.envoy.config.filter.http.alpn.v2alpha1.FilterConfig
                            alpn_override:
                              - alpn_override:
                                  - istio-http/1.0
                                  - istio
                                  - http/1.0
                              - upstream_protocol: HTTP11
                                alpn_override:
                                  - istio-http/1.1
                                  - istio
                                  - http/1.1
                              - upstream_protocol: HTTP2
                                alpn_override:
                                  - istio-h2
                                  - istio
                                  - h2
...
                        - name: envoy.filters.http.router
                          typed_config:
                            '@type': type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
                      http_protocol_options:
                        header_key_format:
                          stateful_formatter:
                            name: preserve_case
                            typed_config:
                              '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig
```

如果您在搜索引擎中找 “istio alpn filter”，您可能找不到任何有意义的东西。仅部分文章：

-  [Better Default Networking – Protocol sniffing](https://docs.google.com/document/d/1l0oVAneaLLp9KjVOQSb3bwnJJpjyxU_xthpMKFM_l7o/edit#heading=h.edsodfixs1x7)
- [Istio MTLS Smartness Explained](https://devops-insider.mygraphql.com/zh-cn/latest/service-mesh/istio/istio-mtls/istio-mtls-smartness-explained.html#alpn)



所以现在我们知道：

- 当 upstream cluster 支持 `HTTP11` 时，TLS 流量中的 ALPN 将提供以下 HTTP 协议：

```
                                alpn_override:
                                  - istio-http/1.1
                                  - istio
                                  - http/1.1
```



- 当 upstream cluster 支持 `HTTP2` 时，TLS 流量中的 ALPN 将提供以下 HTTP 协议：

```
                              - upstream_protocol: HTTP2
                                alpn_override:
                                  - istio-h2
                                  - istio
                                  - h2
```



回顾上面的 tcpdump 输出，我们知道，“serviceA istio-proxy” 认为 upstream cluster 只支持 “HTTP/1.1”。为什么？



### Envoy upstream cluster 的 meta-data



在 “serviceA istio-proxy” 上的关于 upstream cluster “service B” 的元数据：

```yaml
    dynamic_active_clusters:
        cluster:
          '@type': type.googleapis.com/envoy.config.cluster.v3.Cluster
          name: outbound|8080|version|serviceB.ns.svc.cluster.local
          type: EDS
          eds_cluster_config:
            eds_config:
              ads: {}
              initial_fetch_timeout: 0s
              resource_api_version: V3
            service_name: outbound|8080|version|serviceB.ns.svc.cluster.local


          typed_extension_protocol_options:
            envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
              '@type': type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
              explicit_http_config:
                http_protocol_options:
                  header_key_format:
                    stateful_formatter:
                      name: preserve_case
                      typed_config:
                        '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig
```





Envoy 的 Upstream HTTP 协议选择有 3 种方法：

- [explicit_http_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-explicit-http-config) : To explicitly configure either HTTP/1 or HTTP/2 **(but not both!)** use `explicit_http_config`
- [use_downstream_protocol_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-use-downstream-protocol-config) : This allows switching on protocol based on what protocol the downstream connection used.
- [auto_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-auto-config) : This allows switching on protocol based on ALPN. If this is used, the cluster can use either HTTP/1 or HTTP/2, and will use whichever protocol is negotiated by ALPN with the upstream. Clusters configured with `AutoHttpConfig` will use the highest available protocol; HTTP/2 if supported, otherwise HTTP/1. If the upstream does not support ALPN, `AutoHttpConfig` will fail over to HTTP/1.



## 问题根源

现在我们知道直接原因是 “serviceA istio-proxy” 假设 upstream cluster 只支持 “HTTP/1.1”，这是由上面的“explicit_http_config” 及其子项 “http_protocol_options” 引起的。 但为何 upstream cluster 元数据中存在“explicit_http_config” ？ 它是由原生 Istio 生成的？


我们看一下 Istio 的 EnvoyFilter：

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  labels:
    app.kubernetes.io/managed-by: Helm
  name: mycom-myprd-mesh-preserve-header-case
  namespace: ns
spec:
  configPatches:
  - applyTo: CLUSTER
    patch:
      operation: MERGE
      value:
        typed_extension_protocol_options:
          envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
            '@type': type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
            explicit_http_config:
              http_protocol_options:
                header_key_format:
                  stateful_formatter:
                    name: preserve_case
                    typed_config:
                      '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig

  - applyTo: NETWORK_FILTER
    match:
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
    patch:
      operation: MERGE
      value:
        typed_config:
          '@type': type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          http_protocol_options:
            header_key_format:
              stateful_formatter:
                name: preserve_case
                typed_config:
                  '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig
```



看来上面的配置是从 [HTTP1.1 Header Casing - Envoy 官方文档](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/header_casing#stateful-formatters) 复制的。但 Envoy 的开发者可能没有想到 “explicit_http_config” 和 “http_protocol_options” 应用于 Istio 时的影响。



Istio 上有很多关于保留 HTTP/1.1 header 大小写的 github issue，下面按时间顺序列出了这些问题：


- [Issue: Enable preserve HTTP Header casing #32008](https://github.com/istio/istio/issues/32008#issuecomment-988865470)

- [PR: add support for preserving header key case #33030 - Fixes #32008](https://github.com/istio/istio/pull/33030)

- [Istio Technical Oversight Committee Meeting Notes - 2021/06/7](https://docs.google.com/document/d/13lxJqtlaQhmV2EwsNnS6h-_O4pobZQZuMjrzOeMgVI0/edit?usp=sharing)

  > - [howardjohn][10 min] Guidance on breaking change - header casing (https://github.com/istio/istio/pull/33030/)
  >
  > - - tl;dr - preserve HTTP key header casing (ie FooBar -> FooBar instead of FooBar -> foobar)
  >
  >   - My 2c:
  >
  >   - - For new users, it seems better in all cases to preserve the case. I don't see a need to allow an API to lowercase it
  >     - For existing users, they might have come to rely on the lowercasing. It seems a bit odd, as most apps probably assume title casing if anything, so hopefully when they adopt Istio they fix to being case insensitive instead of assuming lowercase, but I am sure in practice it may break users

- [PR: Revert "add support for preserving header key case" #33122 - Reverts #33030](https://github.com/istio/istio/pull/33122)

- [PR: support HTTP/1.1 case preserve #2817](https://github.com/istio/api/pull/2817)



讨论的结论是 Istio 不会正式支持保留 HTTP/1.1 header 大小写：

> [Issue: Enable preserve HTTP Header casing #32008](https://github.com/istio/istio/issues/32008#issuecomment-988865470)
>
> We do not intend to ever merge this feature into Istio, as we have medium term plans to use HTTP2 ~everywhere and any http2 hop destroys casing. You can apply EnvoyFilter at your own risk, with the knowledge that it *will* break sooner or later



因此，我们必须支持通过 “Istio Envoy Filter” 保留 header 大小写。但对于 HTTP/1.1 和 HTTP2 混合网格，如果您遵循 [HTTP/1.1 Header Casing - Envoy 官方文档](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/ header_casing#stateful-formatters) ，并使用 `explicit_http_config`，您可能最终会意外禁用 HTTP/2。所以一般来说 `use_downstream_protocol_config` 是一个更具兼容性和更安全的选择。


所以我们现在可以修复它：

```yaml
kubectl apply -f - <<"EOF"
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: mycom-myprd-mesh-preserve-header-case
  namespace: ns
spec:
  configPatches:
  - applyTo: CLUSTER
    patch:
      operation: MERGE
      value:
        typed_extension_protocol_options:
          envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
            '@type': type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
            use_downstream_protocol_config:
              http_protocol_options:
                header_key_format:
                  stateful_formatter:
                    name: preserve_case
                    typed_config:
                      '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig
              http2_protocol_options:
                max_concurrent_streams: 2147483647

  - applyTo: NETWORK_FILTER
    match:
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
    patch:
      operation: MERGE
      value:
        typed_config:
          '@type': type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          http_protocol_options:
            header_key_format:
              stateful_formatter:
                name: preserve_case
                typed_config:
                  '@type': type.googleapis.com/envoy.extensions.http.header_formatters.preserve_case.v3.PreserveCaseFormatterConfig
```



我们在这里使用 “use_downstream_protocol_config” ，因为我们希望 upstream 协议遵循 downstream 协议。



下图深入探究了 Envoy Proxy 和 Istio Proxy 的相关源码。尝试展示背后的原因：



:::{figure-md} 图: upstream http protocol selection troubleshooting

<img src="/troubleshooting/istio-troubleshooting/http_protocol_options-accidentally-disable-http2/upstream-http-protocol-selection-src.drawio.svg" alt="图 - upstream http protocol selection troubleshooting">

*图: upstream http protocol selection troubleshooting*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fupstream-http-protocol-selection-src.drawio.svg)*







## 结语



阅读 Istio Envoy Filter 官方文档：

> [Envoy Filter](https://istio.io/latest/docs/reference/config/networking/envoy-filter/)
>
> `EnvoyFilter` provides a mechanism to customize the Envoy configuration generated by Istio Pilot. Use EnvoyFilter to modify values for certain fields, add specific filters, or even add entirely new listeners, clusters, etc. This feature must be used with care, as incorrect configurations could potentially destabilize the entire mesh. 



也许我们应该在将其应用到 Istio 之前，通过 Envoy 的文档来检查 Istio Envoy Filters 的所有配置项。

