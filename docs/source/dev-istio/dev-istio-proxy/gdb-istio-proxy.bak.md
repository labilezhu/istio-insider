# gdb 调试 istio proxy (envoy)"


出于各种原因，需要 debug istio-proxy (envoy)，记录一下步骤，希望地球上的有缘人有用。

## 编译生成执行文件

### 下载 code

我用的是 release-1.14。

```bash
mkdir -p $HOME/istio-testing/
cd $HOME/istio-testing/
git clone https://github.com/istio/proxy.git work
cd work
export PROXY_HOME=`pwd`
git checkout tags/1.17.2 -b 1.17.2
```

### 容器中编译

编译大项目，是个环境相关的工作。对于我这小白，还是直接用 Istio 官方 CI 的编译用的容器。好处是：
1. 环境和 Istio 官方 一致，避免各位版本坑。理论上生成的可执行文件是一样的
2. 内置工具，使用方便，


> 注：build-tools-proxy 容器 image 列表可以在 [https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy](https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy) 获得。请对应你要编译的 istio-proxy 版本来选择 image。方法是用网页中的 Filter 功能。 以下仅以 release-1.17 为例子。




```bash
docker stop istio-testing
docker rm istio-testing

mkdir -p $HOME/istio-testing/home/.cache
docker run --init  --log-driver none --privileged --name istio-testing --hostname istio-testing \
    --network router \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v $PROXY_HOME:/work \
    -v $HOME/istio-testing/home/.cache:/home/.cache \
    -w /work \
    -d gcr.io/istio-testing/build-tools-proxy:release-1.17-latest-amd64 bash -c '/bin/sleep 300d'

#进入容器
docker exec -it istio-testing bash

# 开始编译
cd /work
make build BAZEL_STARTUP_ARGS='' BAZEL_BUILD_ARGS='-s  --explain=explain.txt --config=debug' BAZEL_TARGETS=':envoy'

```


进入慢长的等待，我的机器要 3 小时。。。

完成后，查看生成文件：
```bash
build-tools: # ls -lh $PROXY_HOME/bazel-out/k8-dbg/bin/src/envoy/envoy
-r-xr-xr-x 1 root root 1.2G Feb 18 21:46 $PROXY_HOME/bazel-out/k8-dbg/bin/src/envoy/envoy
```

debug执行文件中包含大量信息，size 很大。

## 启动和 debug

```yaml
#进入容器
docker exec -it istio-testing bash

#一个简单的 envoy 配置文件

cat > envoy-demo.yaml <<"EOF"

admin:
  address:
    socket_address: { address: 127.0.0.1, port_value: 9901 }

static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address: { address: 127.0.0.1, port_value: 10000 }
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          codec_type: AUTO
          route_config:
            name: local_route
            virtual_hosts:
            - name: local_service
              domains: ["*"]
              routes:
              - match: { prefix: "/" }
                route: { cluster: some_service }
          http_filters:
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
  clusters:
  - name: some_service
    connect_timeout: 0.25s
    type: STATIC
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: some_service
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: 127.0.0.1
                port_value: 1234
EOF
```

```
#运行
/usr/local/bin/envoy -c envoy-demo.yaml

#调试 attach
gdb -p `pgrep envoy`

```

## Debug in mesh
```
k -n istio-system edit configmaps istio-sidecar-injector
```

```yaml
          {{ template "resources" . }}
            securityContext:
              allowPrivilegeEscalation: true #{{ .Values.global.proxy.privileged }}
              privileged: true #{{ .Values.global.proxy.privileged }}
              capabilities: 
            {{- if not .Values.istio_cni.enabled }}
                add:
                - ALL
                #- NET_ADMIN
                #- NET_RAW
            {{- end }}
                #drop:
                #- ALL
            {{- if not .Values.istio_cni.enabled }}
              readOnlyRootFilesystem: false
              runAsGroup: 0
              runAsNonRoot: false
              runAsUser: 0
            {{- else }}
              readOnlyRootFilesystem: false #true
              runAsGroup: 1337
              runAsUser: 1337
              runAsNonRoot: true
            {{- end }}
            restartPolicy: Always
          {{ end -}}
```

```bash
apt  update
```

```bash
ssh $WORKER_NODE
sudo su

export POD="fortio-server-0"
ENVOY_PIDS=$(pgrep envoy)
while IFS= read -r ENVOY_PID; do
    HN=$(sudo nsenter -u -t $ENVOY_PID hostname)
    if [[ "$HN" = "$POD" ]]; then # space between = is important
        sudo nsenter -u -t $ENVOY_PID hostname
        export POD_PID=$ENVOY_PID
    fi
done <<< "$ENVOY_PIDS"
echo $POD_PID
export PID=$POD_PID

nsenter -t $PID -a
```

```
mkdir  /home/.cache
mount -t nfs 192.168.122.1:/home/labile/istio-testing/home/.cache /home/.cache
mkdir  /work
mount -t nfs 192.168.122.1:/home/labile/istio-testing/work /work

cd /work
gdb -p $PID
```


### istio-proxy image patch
```bash
docker pull docker.io/istio/proxyv2:1.17.2

docker stop istio-proxy-gdb
docker rm istio-proxy-gdb
docker run \
--entrypoint /bin/bash \
--init  --privileged --name istio-proxy-gdb --hostname istio-proxy-gdb \
    --network router \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v $HOME/istio-testing/work:/work \
    -v $HOME/istio-testing/home/.cache:/home/.cache \
    -w /work \
    -d docker.io/istio/proxyv2:1.17.2 \
    -c '/bin/sleep 300d'
```

```bash
docker exec -it istio-proxy-gdb bash
rm /usr/local/bin/envoy
ln -s /home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin/envoy /usr/local/bin/envoy

sudo passwd

apt update
apt install gdb
apt install gdbserver
apt install g++
apt install sshd
apt install tmux

tmux

mkdir /run/sshd
/usr/sbin/sshd -e -o PermitRootLogin=yes
```

```
export CONTAINER_IP=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' istio-proxy-gdb`

ssh-copy-id root@$CONTAINER_IP
```



```
@vscode

Remote-ssh: Add new ssh host: 172.17.0.2
```


```
docker commit istio-proxy-gdb  mark/istio-proxy-gdb
```

```yaml
#进入容器
docker exec -it istio-proxy-gdb bash

#一个简单的 envoy 配置文件

cat > envoy-demo.yaml <<"EOF"

admin:
  address:
    socket_address: { address: 127.0.0.1, port_value: 9901 }

static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address: { address: 127.0.0.1, port_value: 10000 }
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          codec_type: AUTO
          route_config:
            name: local_route
            virtual_hosts:
            - name: local_service
              domains: ["*"]
              routes:
              - match: { prefix: "/" }
                route: { cluster: some_service }
          http_filters:
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
  clusters:
  - name: some_service
    connect_timeout: 0.25s
    type: STATIC
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: some_service
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: 127.0.0.1
                port_value: 1234
EOF

#运行
/usr/local/bin/envoy -c envoy-demo.yaml

gdbserver :2159 --attach `pgrep envoy`
```

### gdb client

```bash
apt install gdb

cd /work
gdb
file /work/bazel-out/k8-dbg/bin/envoy
target remote 172.18.0.4:2159 
```

```
@vscode install `Native Debug` extension.
```


## Ref.

- [How to build istio/proxy#28476](https://github.com/istio/istio/issues/28476)
- [How to build istio/proxy part 2#37471](https://github.com/istio/istio/issues/37471)