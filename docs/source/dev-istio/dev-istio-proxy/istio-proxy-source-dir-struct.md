## Envoy 依赖

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