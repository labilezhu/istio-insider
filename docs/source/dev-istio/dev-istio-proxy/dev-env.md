## clone code

我用的是 release-1.17。

```bash
mkdir -p $HOME/istio-testing/
cd $HOME/istio-testing/
git clone https://github.com/istio/proxy.git work
cd work
export PROXY_HOME=`pwd`
git checkout tags/1.17.2 -b 1.17.2
```


## 容器中编译

编译大项目，是个环境相关的工作。对于我这小白，还是直接用 Istio 官方 CI 的编译用的容器。好处是：
1. 环境和 Istio 官方 一致，避免各位版本坑。理论上生成的可执行文件是一样的
2. 内置工具，使用方便，


> 注：build-tools-proxy 容器 image 列表可以在 [https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy](https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy) 获得。请对应你要编译的 istio-proxy 版本来选择 image。方法是用网页中的 Filter 功能。 以下仅以 release-1.14 为例子。


```bash
docker stop istio-testing
docker rm istio-testing

mkdir -p $HOME/istio-testing/home/.cache
docker run --init  --log-driver none --privileged --name istio-testing --hostname istio-testing \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v $PROXY_HOME:/work \
    -v $HOME/istio-testing/home/.cache:/home/.cache \
    -w /work \
    -d gcr.io/istio-testing/build-tools-proxy:release-1.17-latest-amd64 bash -c '/bin/sleep 300d'

#进入容器
docker exec -it istio-testing bash

# 开始编译
cd /work
make build BAZEL_STARTUP_ARGS='' BAZEL_BUILD_ARGS='-s  --explain=explain.txt --config=debug' BAZEL_TARGETS='//src/envoy:envoy'

```


进入慢长的等待，我的机器要 3 小时。。。

完成后，查看生成文件：
```bash
build-tools: # ls -lh /work/bazel-out/k8-dbg/bin/envoy
-r-xr-xr-x 1 root root 1.2G Feb 18 21:46 /work/bazel-out/k8-dbg/bin/envoy
```

debug执行文件中包含大量信息，size 很大。

### Build 输出目录
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

## 运行 envoy

```bash
#进入容器
docker exec -it istio-testing bash

#下载一个简单的 envoy 配置文件
curl -L -O https://github.com/labilezhu/pub-diy/raw/main/low-tec/trace/trace-istio/bpftrace/envoy-demo.yaml

#运行
/work/bazel-out/k8-dbg/bin/envoy -c envoy-demo.yaml
```


## Coding on istio proxy container

因为在容器内 build istio-proxy 的过程下载的依赖源码、中间文件（在 /home/.cache ），均在容器中，所以，在容器中开启 vscode 才是最方便的代码浏览方法。

1. In VSCode: Run command: `Remote Containers: Attach to running container`
2. select `istio-testing` container.



### VSCode extensions

 - C++
 - C++ Extension Pack
 - Bazel

