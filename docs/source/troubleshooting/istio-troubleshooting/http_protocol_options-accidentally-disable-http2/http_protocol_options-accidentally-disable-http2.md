---
typora-root-url: ../../..
---

# Preserving HTTP/1 header case across Envoy accidentally disabled HTTP/2 on a Istio mesh mixing HTTP1 and HTTP2

## Motivation

In a word: we want to support HTTP/2 in an Istio environment running HTTP/1.1 for a long time. So we want a HTTP/1.1 and HTTP2 hybrid mesh.

We want to support HTTP/2 in below flow of APIs between services:

```
[serviceA app --h2c--> serviceA istio-proxy] ----(http2 over mTLS)---> [serviceB istio-proxy --h2c--> serviceB app]
```


Environment:

```
service A: 
  Pod A: 
    ip addr: 192.168.88.94

service B: 10.110.152.25
  Pod B: serviceB-ver-6b54d8c7bc-6vclp
    ip addr: 192.168.33.5
```


## Symptom


So we try below curl on Pod A:

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

It seems the app running on Pod A use HTTP/2. 



Let us check if Pod B use HTTP/2 :

```bash
kubectl logs --tail=1 -f serviceB-ver-6b54d8c7bc-6vclp -c istio-proxy
```



```log
[2024-05-07T07:18:41.470Z] "GET /resource1?p1=v1 HTTP/1.1" 200 - via_upstream - "-" 0 48 16 14 "-" "curl/8.0.1" "6add007-7242-4983-9862-63cd10b8e5" "serviceB:8080" "[priv8]192.168.88.94[/priv8]:8080" outbound|8080|ver|serviceB.ns.svc.cluster.local [priv8]192.168.33.5[/priv8]:48344 [priv8]10.110.152.25[/priv8]:8080 [priv8]192.168.33.5[/priv8]:36650 - -
```

We can see the istio-proxy of serviceB use HTTP/1.1 protocol.



## Glossary

- h2c - HTTP/2 over TCP or HTTP/2 Cleartext
- h2 - HTTP/2 over TLS (protocol negotiation via ALPN)
- ALPN - [`ALPN(Application-Layer Protocol Negotiation)` on TLS](https://en.wikipedia.org/wiki/Application-Layer_Protocol_Negotiation)


## Background knowledge

Before the investigation, assuming you have base knowledge of {doc}`/ch4-istio-data-plane/data-plane-tunnel/alpn-http-meta-exchange/alpn-http-meta-exchange` .

:::{figure-md} Figure: HTTP protocol meta-data exchange at high level

<img src="/ch4-istio-data-plane/data-plane-tunnel/alpn-http-meta-exchange/alpn-http-meta-exchange-high-level.drawio.svg" alt="Figure - HTTP protocol meta-data exchange at high level">

*Figure: HTTP protocol meta-data exchange at high level*
:::
*[Open with Draw.io](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Falpn-http-meta-exchange-high-level.drawio.svg)*

## Investigate

We know the path of traffic:

```
[serviceA app --h2c--> serviceA istio-proxy] ----(http2 over mTLS)---> [serviceB istio-proxy --h2c--> serviceB app]
```

We know `serviceA istio-proxy` use `ALPN` to negotiate which version of HTTP used between `serviceB istio-proxy`.  See [Better Default Networking – Protocol sniffing](https://docs.google.com/document/d/1l0oVAneaLLp9KjVOQSb3bwnJJpjyxU_xthpMKFM_l7o/edit#heading=h.edsodfixs1x7)



So we run tcpdump on `serviceA istio-proxy` to inspect ALPN between 2 istio-proxy(s) :

```
ss -K 'dst 192.168.88.94'

tcpdump -i eth0@if3623 'host 192.168.88.94' -c 1000 -s 65535 -w /tmp/tcpdump.pcap

tshark -r /tmp/tcpdump.pcap -d tcp.port==8080,ssl -2R "ssl" -V | less
```



```log
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

No expected `istio-h2` or `h2` found.



### Debug log of outbound istio-proxy

Enable debug log of outbound istio-proxy: 

```bash
curl -XPOST http://localhost:15000/logging\?filter\=trace
```



Get the log:

```log
{"level":"debug","time":"2024-05-07T07:18:41.471107Z","scope":"envoy filter","msg":"override with 3 ALPNs"}
```





### Evnoy Listener



So we dump the Envoy configuration of `serviceA istio-proxy` :

Evnoy Listener on `serviceA istio-proxy`:

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

If you search `istio alpn filter` on Google, you may not found any thing meaningful. Only some articles:

-  [Better Default Networking – Protocol sniffing](https://docs.google.com/document/d/1l0oVAneaLLp9KjVOQSb3bwnJJpjyxU_xthpMKFM_l7o/edit#heading=h.edsodfixs1x7)
- [Istio MTLS Smartness Explained](https://devops-insider.mygraphql.com/zh-cn/latest/service-mesh/istio/istio-mtls/istio-mtls-smartness-explained.html#alpn)



So now we know that:

- When upstream cluster supported `HTTP11` , below HTTP protocol will be provided in ALPN:

```
                                alpn_override:
                                  - istio-http/1.1
                                  - istio
                                  - http/1.1
```



- When upstream cluster supported `HTTP2` , below HTTP protocol will be provided in ALPN:

```
                              - upstream_protocol: HTTP2
                                alpn_override:
                                  - istio-h2
                                  - istio
                                  - h2
```



Look back to above tcpdump output, we know that , `serviceA istio-proxy`  assume upstream cluster supported `HTTP/1.1`.  Why?



### Envoy upstream cluster meta-data declare



Envoy upstream cluster meta-data declare of  `serviceB` on `serviceA istio-proxy`:

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





There are 3 methods of Upstream HTTP protocol selection of Envoy:

- [explicit_http_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-explicit-http-config) : To explicitly configure either HTTP/1 or HTTP/2 **(but not both!)** use `explicit_http_config`
- [use_downstream_protocol_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-use-downstream-protocol-config) : This allows switching on protocol based on what protocol the downstream connection used.
- [auto_config](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/upstreams/http/v3/http_protocol_options.proto#envoy-v3-api-field-extensions-upstreams-http-v3-httpprotocoloptions-auto-config) : This allows switching on protocol based on ALPN. If this is used, the cluster can use either HTTP/1 or HTTP/2, and will use whichever protocol is negotiated by ALPN with the upstream. Clusters configured with `AutoHttpConfig` will use the highest available protocol; HTTP/2 if supported, otherwise HTTP/1. If the upstream does not support ALPN, `AutoHttpConfig` will fail over to HTTP/1.



## Root cause

So now we know the direct cause is `serviceA istio-proxy`  assume upstream cluster supported `HTTP/1.1`, and it is cause by above `explicit_http_config` and  it's sub item `http_protocol_options`. But way `explicit_http_config` existed in the upstream cluster meta-data ? It is generated by native Istio ?



Let's have a look at the `EnvoyFilter` of Istio:

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



It seems above configuration is copy from [HTTP/1.1 Header Casing - from official documentation of Envoy](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/header_casing#stateful-formatters).  But developers of Envoy may not think the impaction of `explicit_http_config` and `http_protocol_options` when applied on Istio. 



There are many github issues about preserve HTTP/1.1 header case :

- [Issue: Enable preserve HTTP Header casing #32008](https://github.com/istio/istio/issues/32008#issuecomment-988865470)

  >We do not intend to ever merge this feature into Istio, as we have medium term plans to use HTTP2 ~everywhere and any http2 hop destroys casing. You can apply EnvoyFilter at your own risk, with the knowledge that it *will* break sooner or later

- [Istio Technical Oversight Committee Meeting Notes - 2021/06/7](https://docs.google.com/document/d/13lxJqtlaQhmV2EwsNnS6h-_O4pobZQZuMjrzOeMgVI0/edit?usp=sharing)

  > - [howardjohn][10 min] Guidance on breaking change - header casing (https://github.com/istio/istio/pull/33030/)
  >
  > - - tl;dr - preserve HTTP key header casing (ie FooBar -> FooBar instead of FooBar -> foobar)
  >
  >   - My 2c:
  >
  >   - - For new users, it seems better in all cases to preserve the case. I don't see a need to allow an API to lowercase it
  >     - For existing users, they might have come to rely on the lowercasing. It seems a bit odd, as most apps probably assume title casing if anything, so hopefully when they adopt Istio they fix to being case insensitive instead of assuming lowercase, but I am sure in practice it may break users

- [PR: support HTTP/1.1 case preserve #2817](https://github.com/istio/api/pull/2817)

  

So we can fix it now:

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



We use `use_downstream_protocol_config` here because we want the upstream protocol follow the downstream protocol.



Below figure deep dive into the related source code of Envoy Proxy and Istio Proxy. It show you why under the hood.





:::{figure-md} Figure: upstream http protocol selection troubleshooting

<img src="/troubleshooting/istio-troubleshooting/http_protocol_options-accidentally-disable-http2/upstream-http-protocol-selection-src.drawio.svg" alt="Figure - upstream http protocol selection troubleshooting">

*Figure: upstream http protocol selection troubleshooting*
:::
*[Open with Draw.io](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fupstream-http-protocol-selection-src.drawio.svg)*







## Summary



Read the official Istio Envoy Filter documentation:  

> [Envoy Filter](https://istio.io/latest/docs/reference/config/networking/envoy-filter/)
>
> `EnvoyFilter` provides a mechanism to customize the Envoy configuration generated by Istio Pilot. Use EnvoyFilter to modify values for certain fields, add specific filters, or even add entirely new listeners, clusters, etc. This feature must be used with care, as incorrect configurations could potentially destabilize the entire mesh. 



May be we should check all configuration items of Istio Envoy Filters by the documentation  of Envoy before we apply it to Istio.

