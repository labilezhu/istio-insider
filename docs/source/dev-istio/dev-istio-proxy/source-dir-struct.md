# Istio Proxy 源码目录结构

## istio proxy 在 Evnoy 上增加的源码

### /src
这里放 与 Envoy 一起构建的 Native C++ 代码。

```
.
└── istio
    ├── authn
    │   ├── BUILD
    │   └── context.proto
    └── utils
        ├── attribute_names.cc
        ├── attribute_names.h
        └── BUILD
```

### /source/extensions
这是 Istio 1.6 之后才有的目录，大部分源码是重构于旧 /extensions 下的基于 WASM 的插件：
> [stats: rewrite as native extension #4079](https://github.com/istio/proxy/pull/4079)
> This is a quick prototype of Istio stats extension written as a native extension. The advantages are numerous:
> 
> - Unblocks ability to implement metric expiry, memory accounting for multi tenancy, and opens paths for Envoy improvements in that area;
> - Removes requirement to rely on regex parsing to strip tags. Tags are produced directly.
> - Removes dependency on Wasm.
> - Removes dependency on flatbuffers.
> - CPU improvements. It is well known that Istio proxy is not frugal with CPU. This PR removes a lot of abstraction overhead (via Wasm, flatbuffers, regexes), and can be made extremely efficient with regards to memory / CPU cycles (Envoy uses highly efficient packed strings which are sub-pointer size).

```
    ├── common
    │   ├── authn.cc
    │   ├── authn.h
    │   ├── authn_test.cc
    │   ├── BUILD
    │   ├── filter_names.cc
    │   ├── filter_names.h
    │   ├── ...
    └── filters
        ├── http
        │   ├── alpn
        │   │   ├── alpn_filter.cc
        │   │   ├── alpn_filter.h
        │   │   ├── alpn_test.cc
        │   │   ├── BUILD
        │   │   ├── ...
        │   ├── authn
        │   │   ├── authenticator_base.cc
        │   │   ├── authenticator_base.h
        │   │   ├── authenticator_base_test.cc
        │   │   ├── authn_utils.cc
        │   │   ├── authn_utils.h
        │   │   ├── authn_utils_test.cc
        │   │   ├── BUILD
        │   │   ├── filter_context.cc
        │   │   ├── filter_context.h
        │   │   ├── filter_context_test.cc
        │   │   ├── http_filter.cc
        │   │   ├── http_filter_factory.cc
        │   │   ├── http_filter.h
        │   │   ├── http_filter_integration_test.cc
        │   │   ├── http_filter_test.cc
        │   │   ├── origin_authenticator.cc
        │   │   ├── origin_authenticator.h
        │   │   ├── origin_authenticator_test.cc
        │   │   ├── peer_authenticator.cc
        │   │   ├── peer_authenticator.h
        │   │   ├── peer_authenticator_test.cc
        │   │   ├── sample
        │   │   │   └── APToken
        │   │   │       ├── aptoken-envoy.conf
        │   │   │       ├── APToken-example1.jwt
        │   │   │       └── guide.txt
        │   │   └── test_utils.h
        │   ├── connect_baggage
        │   │   ├── BUILD
        │   │   ├── config.proto
        │   │   ├── filter.cc
        │   │   └── filter.h
        │   └── istio_stats
        │       ├── BUILD
        │       ├── istio_stats.cc
        │       └── istio_stats.h
        ├── listener
        │   └── set_internal_dst_address
        │       ├── BUILD
        │       ├── config.proto
        │       ├── filter.cc
        │       └── filter.h
        └── network
            ├── forward_downstream_sni
            │   ├── BUILD
            │   ├── config.cc
            │   ├── config.h
            │   ├── config.proto
            │   ├── forward_downstream_sni.cc
            │   ├── forward_downstream_sni.h
            │   └── forward_downstream_sni_test.cc
            ├── istio_authn
            │   ├── BUILD
            │   ├── config.cc
            │   ├── config.h
            │   ├── config.proto
            │   └── config_test.cc
            ├── metadata_exchange
            │   ├── BUILD
            │   ├── config
            │   │   ├── BUILD
            │   │   └── metadata_exchange.proto
            │   ├── config.cc
            │   ├── config.h
            │   ├── metadata_exchange.cc
            │   ├── metadata_exchange.h
            ├── sni_verifier
            │   ├── BUILD
            │   ├── config.cc
            │   ├── config.h
            │   ├── config.proto
            │   ├── sni_verifier.cc
            │   ├── sni_verifier.h
            │   └── sni_verifier_test.cc
            └── tcp_cluster_rewrite
                ├── BUILD
                ├── config.cc
                ├── config.h
                ├── config_test.cc
                ├── tcp_cluster_rewrite.cc
                ├── tcp_cluster_rewrite.h
                └── tcp_cluster_rewrite_test.cc
```

### /extensions
这里放 Istio-proxy 自带的 Wasm 插件。 嵌入到生成的 evnoy ELF 文件中。

```
.
├── access_log_policy
│   ├── BUILD
│   ├── config
│   │   └── v1alpha1
│   │       ├── access_log_policy_config.pb.html
│   │       ├── access_log_policy_config.proto
│   │       └── BUILD
│   ├── config.cc
│   ├── plugin.cc
│   └── plugin.h
├── attributegen
│   ├── BUILD
│   ├── config.pb.html
│   ├── config.proto
│   ├── plugin.cc
│   ├── plugin.h
│   ├── plugin_test.cc
│   └── testdata
│       ├── BUILD
│       ├── operation.json
│       ├── responseCode.json
│       └── server.yaml
├── BUILD
├── common
│   ├── BUILD
│   ├── context.cc
│   ├── context.h
│   ├── istio_dimensions.h
│   ├── istio_dimensions_test.cc
│   ├── metadata_object.cc
│   ├── metadata_object.h
│   ├── metadata_object_test.cc
│   ├── node_info.fbs
│   ├── proto_util.cc
│   ├── proto_util.h
│   ├── proto_util_speed_test.cc
│   ├── proto_util_test.cc
│   ├── util.cc
│   ├── util.h
│   ├── util_test.cc
│   └── wasm
│       ├── base64.h
│       ├── BUILD
│       ├── json_util.cc
│       └── json_util.h
├── metadata_exchange
│   ├── BUILD
│   ├── config.cc
│   ├── config.pb.html
│   ├── config.proto
│   ├── declare_property.pb.html
│   ├── declare_property.proto
│   ├── plugin.cc
│   └── plugin.h
├── stackdriver
│   ├── BUILD
│   ├── common
│   │   ├── BUILD
│   │   ├── constants.h
│   │   ├── metrics.cc
│   │   ├── metrics.h
│   │   ├── utils.cc
│   │   ├── utils.h
│   │   └── utils_test.cc
│   ├── config
│   │   └── v1alpha1
│   │       ├── BUILD
│   │       ├── stackdriver_plugin_config.pb.html
│   │       └── stackdriver_plugin_config.proto
│   ├── log
│   │   ├── BUILD
│   │   ├── exporter.cc
│   │   ├── exporter.h
│   │   ├── logger.cc
│   │   ├── logger.h
│   │   └── logger_test.cc
│   ├── metric
│   │   ├── BUILD
│   │   ├── record.cc
│   │   ├── record.h
│   │   ├── registry.cc
│   │   ├── registry.h
│   │   └── registry_test.cc
│   ├── README.md
│   ├── stackdriver.cc
│   ├── stackdriver.h
│   ├── stackdriver_plugin_factory.cc
│   └── testdata
│       └── stackdriver_filter.yaml
└── stats
    ├── BUILD
    ├── config.pb.html
    ├── config.proto
    ├── plugin.cc
    ├── plugin.h
    ├── plugin_test.cc
    ├── run_test.sh
    └── testdata
        ├── client.yaml
        ├── istio
        │   ├── metadata-exchange_filter.yaml
        │   └── stats_filter.yaml
        └── server.yaml
```


## Build 输出目录

```bash
bazel-bin -> /home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin
bazel-out -> /home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out
bazel-proxy -> /home/.cache/bazel/_bazel_root/9fdd49e4743c3f8ee04d8f2b39e01600/execroot/io_istio_proxy
bazel-testlogs -> /home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/testlogs
bazel-work -> /home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy

# 主依赖下载目录：
bazel-work/external

# 依赖的 envoy 源码 目录
bazel-work/external/envoy
```