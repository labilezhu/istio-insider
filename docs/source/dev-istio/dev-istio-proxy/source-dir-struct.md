# Istio Proxy 源码目录结构

## istio proxy 在 Evnoy 上增加的源码

### /src
这里放 与 Envoy 一起构建的 Native C++ 代码。

```
├── envoy
│   ├── BUILD
│   ├── extensions
│   │   └── wasm
│   │       ├── BUILD
│   │       └── wasm.cc
│   ├── http
│   │   ├── alpn
│   │   │   ├── alpn_filter.cc
│   │   │   ├── ...
│   │   └── authn
│   │       ├── authenticator_base.cc
│   │       ├── ...
│   ├── tcp
│   │   ├── forward_downstream_sni
│   │   │   ├── BUILD
│   │   │   ├── config.cc
│   │   │   ├── ...
│   │   ├── metadata_exchange
│   │   │   ├── BUILD
│   │   │   ├── config
│   │   │   │   ├── BUILD
│   │   │   │   └── metadata_exchange.proto
│   │   │   ├── ...
│   │   ├── sni_verifier
│   │   │   ├── BUILD
│   │   │   ├── config.cc
│   │   │   ├── ...
│   │   └── tcp_cluster_rewrite
│   │       ├── BUILD
│   │       ├── config.cc
│   │       ├── ...
│   └── utils
│       ├── authn.cc
│       ├── authn.h
│       ├── authn_test.cc
│       ├── BUILD
│       ├── filter_names.cc
│       ├── filter_names.h
│       ├── ..
└── istio
    ├── authn
    │   ├── BUILD
    │   └── context.proto
    └── utils
        ├── attribute_names.cc
        ├── attribute_names.h
        ├── BUILD
        ├── utils.cc
        ├── ...
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
├── BUILD
├── common
│   ├── BUILD
│   ├── context.cc
│   ├── context.h
│   ├── istio_dimensions.h
│   ├── istio_dimensions_test.cc
│   ├── node_info.fbs
│   ├── ...
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