# vscode 调试 istio proxy

- 调试本地 istio proxy - envoy 代理
- 调试 Istio 网格中的 istio-proxy sidecar

## 调试本地 istio proxy - envoy 代理


出于各种原因，需要 debug istio-proxy (envoy)，记录一下步骤，希望地球上的有缘人有用。

### 编译生成执行文件

#### 下载 code

我用的是 release-1.14。

```bash
mkdir -p $HOME/istio-testing/
cd $HOME/istio-testing/
git clone https://github.com/istio/proxy.git work
cd work
export PROXY_HOME=`pwd`
git checkout tags/1.17.2 -b 1.17.2
```

#### 容器中编译

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

##进入容器
docker exec -it istio-testing bash

## 开始编译
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

### 启动和 debug

```yaml
##进入容器
docker exec -it istio-testing bash

##一个简单的 envoy 配置文件

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
##运行
/usr/local/bin/envoy -c envoy-demo.yaml

##调试 attach
gdb -p `pgrep envoy`

```

## 调试 Istio 网格中的 istio-proxy sidecar

```
docker run -d -p 5000:5000 --restart=always --name image-registry --hostname image-registry registry:2
```


```bash
cd mkdir -p image/gdb-istio-proxy
cd image/gdb-istio-proxy

sudo ln $HOME/istio-testing/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin/envoy ./

cat > gdb-istio-proxy.Dockerfile <<"EOF"
FROM docker.io/istio/proxyv2:1.17.2

COPY envoy /usr/local/bin/envoy

RUN apt-get -y update \
  && sudo apt install lldb
EOF

docker build . -f ./gdb-istio-proxy.Dockerfile -t proxyv2:1.17.2-debug

docker tag proxyv2:1.17.2-debug 192.168.122.1:5000/proxyv2:1.17.2-debug
docker push 192.168.122.1:5000/proxyv2:1.17.2-debug

```

### Optional: Test with native gdb

Optional: Inspect docker image layer:
```
docker pull wagoodman/dive
docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest 192.168.122.1:5000/proxyv2:1.17.2-debug
```


```
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
    -d localhost:5000/proxyv2:1.17.2-debug \
    -c '/bin/sleep 300d'
```


```yaml
##进入容器
docker exec -it istio-proxy-gdb bash

##一个简单的 envoy 配置文件

cat > /tmp/envoy-demo.yaml <<"EOF"

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

##运行
/usr/local/bin/envoy -c /tmp/envoy-demo.yaml &
```

```bash
sudo nsenter -t `pgrep envoy` -p -u -m bash #no -n 
gdbserver :2159 --attach `pgrep envoy`
```

#### gdb client

```bash
export CONTAINER_IP=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' istio-proxy-gdb`
echo $CONTAINER_IP

docker exec -it istio-testing bash

apt install gdb

cd /work
gdb
file /work/bazel-out/k8-dbg/bin/envoy
target remote 192.168.1.14:2159
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

### remote debug sidecar with vscode

#### test POD
```bash
ssh $workernode
```

##### enable plain http image registry
```ini
sudo vi /etc/containerd/config.toml
version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri".registry]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."192.168.122.1:5000"]
        endpoint = ["http://192.168.122.1:5000"]

```

```
sudo systemctl restart containerd
```

##### run test pod

```yaml

#kubectl -n mark apply -f - <<"EOF"

cat > fortio-server.yaml <<"EOF"

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: fortio-server
  labels:
    app: fortio-server
spec:
  serviceName: fortio-server
  replicas: 1
  selector:
    matchLabels:
      app: fortio-server
  template:
    metadata:
      annotations:
        sidecar.istio.io/proxyImage: 192.168.122.1:5000/proxyv2:1.17.2-debug
        # sidecar.istio.io/inject: "false"        
      labels:
        app.kubernetes.io/name: fortio-server
        app: fortio-server
    spec:
      restartPolicy: Always
      containers:
      - name: main-app
        image: docker.io/fortio/fortio
        imagePullPolicy: IfNotPresent
        command: ["/usr/bin/fortio"]
        args: ["server", "-M", "8070 http://fortio-server-l2:8080"]
        ports:
        - containerPort: 8080
          protocol: TCP
          name: http      
        - containerPort: 8070
          protocol: TCP
          name: http-m   
        - containerPort: 8079
          protocol: TCP
          name: grpc   

      - name: istio-proxy
        image: auto
        imagePullPolicy: IfNotPresent
EOF



./istioctl kube-inject -f fortio-server.yaml > fortio-server-injected.yaml

vi fortio-server-injected.yaml
      annotations:
        sidecar.istio.io/inject: "false" 

        securityContext:
          allowPrivilegeEscalation: true
          capabilities:
            add:
            - ALL
          privileged: true
          readOnlyRootFilesystem: false
          runAsGroup: 1337
          runAsNonRoot: true
          runAsUser: 1337

kubectl -n mark apply -f fortio-server-injected.yaml

```

##### start gdbserver
```bash
export WORKER_NODE=192.168.122.55
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

sudo nsenter -t $PID -u -p -m bash #NO -n

sudo lldb-server platform --server --listen *:2159

# gdbserver --debug --remote-debug :2159  --attach  `pgrep envoy`

# /usr/bin/gdbserver --multi :2159

# gdb
# file /usr/local/bin/envoy
# target extended-remote localhost:2159
# attach 14


## set remote exec-file /usr/local/bin/envoy

sudo iptables -t nat -I ISTIO_INBOUND -p tcp -m tcp --dport 2159 -j RETURN
sudo iptables -t nat -I ISTIO_OUTPUT -p tcp -m tcp --sport 2159 -j RETURN

```

##### test gdb client
```bash
cd /work
gdb
file /work/bazel-out/k8-dbg/bin/envoy
target remote 192.168.122.55:2159
```

#### vscode

/work/.vscode/launch.json :

```json
{
    "version": "0.2.0",
    "configurations": [

        {
            "name": "AttachLLDBLocal",
            "type": "lldb",
            "request": "attach",
            "program": "/work/bazel-out/k8-dbg/bin/envoy",
            "pid": "2694",
            "sourceMap": {
                "/proc/self/cwd": "/work/bazel-work",
                "/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/sandbox/linux-sandbox/263/execroot/io_istio_proxy": "/work/bazel-work"
            }         
        } ,
        {
            "name": "AttachLLDBRemote",
            "type": "lldb",
            "request": "attach",
            "program": "/work/bazel-out/k8-dbg/bin/envoy",
            "pid": "20",
            "sourceMap": {
                "/proc/self/cwd": "/work/bazel-work",
                "/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/sandbox/linux-sandbox/263/execroot/io_istio_proxy": "/work/bazel-work"
            },
            "initCommands": [
                "platform select remote-linux", // Execute `platform list` for a list of available remote platform plugins.
                "platform connect connect://192.168.122.55:2159"
            ],                              
        }                         
    ]
}
```


### 可能用到的东西
```
k -n istio-system edit configmaps istio-sidecar-injector
```

```yaml
                add:
                - ALL
                #- NET_ADMIN
                #- NET_RAW


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


## Ref.

- [How to build istio/proxy#28476](https://github.com/istio/istio/issues/28476)
- [How to build istio/proxy part 2#37471](https://github.com/istio/istio/issues/37471)