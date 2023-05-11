# Build 配置

## envoy_cc_binary

### src/envoy/BUILD
> https://cloudnative.to/blog/use-clion-read-envoy-source/
> istio-proxy 代码库中主要只包含了在 istio 里用到的一些 envoy 扩展，代码量不大，源码主要分布在 src 与 extensions 目录，但编译需要很久，因为它实际编译的是 envoy，只是利用 bazel 将自身代码作为扩展编译进 envoy（得益于 envoy 的扩展机制），从这个 bazel 的 BUILD 文件 就能看得出来：

```
load("@rules_pkg//:pkg.bzl", "pkg_tar")
load(
    "@envoy//bazel:envoy_build_system.bzl",
    "envoy_cc_binary",
)

envoy_cc_binary(
    name = "envoy",
    repository = "@envoy",
    visibility = ["//visibility:public"],
    deps = [
        "//extensions/access_log_policy:access_log_policy_lib",
        "//extensions/attributegen:attributegen_plugin",
        "//extensions/metadata_exchange:metadata_exchange_lib",
        "//extensions/stackdriver:stackdriver_plugin",
        "//extensions/stats:stats_plugin",
        "//src/envoy/http/alpn:config_lib",
        "//src/envoy/http/authn:filter_lib",
        "//src/envoy/tcp/forward_downstream_sni:config_lib",
        "//src/envoy/tcp/metadata_exchange:config_lib",
        "//src/envoy/tcp/sni_verifier:config_lib",
        "//src/envoy/tcp/tcp_cluster_rewrite:config_lib",
        "@envoy//source/exe:envoy_main_entry_lib",
    ],
)
```

其中 `@envoy` 表示引用 envoy 代码库， `main` 函数也位于 envoy 代码库中。那么 envoy 代码库从哪儿来的呢？bazel 在构建时会自动下载指定的依赖，envoy 的代码来源在 `./WORKSPACE` 中有指定：


## Envoy 依赖代码库
### /WORKSPACE


依赖的 Envoy 版本在文件 `/WORKSPACE` 中指定。

指定 依赖的 Envoy 的源码 repo 指纹：
```bash
ENVOY_SHA = "f2404ab4c067be83101a26d9b94ebe9d152bd033"

ENVOY_SHA256 = "e9bc6584e2e726304707b6a4245a3452312657cbf98677fad4299f40c3bd5cd3"

ENVOY_ORG = "envoyproxy"

ENVOY_REPO = "envoy"

# To override with local envoy, just pass `--override_repository=envoy=/PATH/TO/ENVOY` to Bazel or
# persist the option in `user.bazelrc`.
http_archive(
    name = "envoy",
    sha256 = ENVOY_SHA256,
    strip_prefix = ENVOY_REPO + "-" + ENVOY_SHA,
    url = "https://github.com/" + ENVOY_ORG + "/" + ENVOY_REPO + "/archive/" + ENVOY_SHA + ".tar.gz",
)
```

bazel 会自动下载指定版本的源码包来编译。


可以用这个 `repo 指纹` 手工下载源码：
```bash
curl -L -O https://github.com/envoyproxy/envoy/archive/f2404ab4c067be83101a26d9b94ebe9d152bd033.tar.gz
```

然后解压，可以看到依赖的 Envoy 版本号：
```bash
$ tar -xvf f2404ab4c067be83101a26d9b94ebe9d152bd033.tar.gz
...
$ cat VERSION.txt

1.22.7-dev
```

## Ref.
 - https://cloudnative.to/blog/use-clion-read-envoy-source/