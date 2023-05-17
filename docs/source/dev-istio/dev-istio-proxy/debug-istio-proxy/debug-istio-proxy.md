# Debug runing istio-proxy on mesh



For a more in-depth study of the underlying behavior of sidecar (istio-proxy) under Istio service mesh. In order to write my book [Istio Insider](http://istio-insider.mygraphql.com/) better, I use the (lldb/gdb) + VSCode to debug the  Envoy(C++ code) which running on Istio service mesh. This article records my method of debugging Envoy(istio-proxy) sidecar in Istio service mesh, and I hope it can be useful to readers.

<!-- 为更深入研究 Istio service mesh 下， sidecar(istio-proxy) 的底层行为。也为更好更靠普地编写我的书《Istio 内幕》，我用 debug 工具(lldb/gdb) + VSCode 去调试 Istio 下 Envoy 的底层实现(即 C++ 代码)。这篇文章记录了我 debug 在 Istio service mesh 中的 Envoy(istio-proxy) sidecar 的方法，希望也能对读者有用。 -->



## Architecture

![](remote-lldb-istio-proxy.drawio.svg)
*Remote lldb debug istio-proxy*


## Environment Assumption

Istio verion: 1.17.2

Environment assumption:

- a k8s cluster
  - node network CIDR: 192.168.122.0/24
  - Istio 1.17.2 installed
  - tested k8s namespace: mark
  - tested pod run on node: 192.168.122.55
- a Linux developer node
  - IP addr: 192.168.122.1
  - hostname: `labile-T30`
  - OS: Ubuntu 22.04.2 LTS
  - user home: /home/labile
  - Can reach k8s cluster node network
  - with X11 GUI
  - VSCode 
  - Docker installed
  - with Internet connection



## Steps

### 1. Build istio-proxy with debug info

#### 1.1 Clone source code

Run on `labile-T30`
```bash
mkdir -p $HOME/istio-testing/
cd $HOME/istio-testing/
git clone https://github.com/istio/proxy.git work
cd work
git checkout tags/1.17.2 -b 1.17.2
```


#### 1.2 start istio-proxy-builder container

Compiling a large project like istio-proxy is an environment-related job. For a novice like me, I would like to use the official Istio CI compilation container directly. Benefits are:
1. The environment is consistent with the official Istio version to avoid version pitfalls. Theoretically the generated executable is the same
2. Built-in tools, easy to use

> Note: The build-tools-proxy container image list can be found at [https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy](https://console.cloud.google.com/gcr/images/istio-testing/global/build-tools-proxy) available. Please select the image corresponding to the version of istio-proxy you want to compile. The method is to use the Filter function in the web page. The following only takes release-1.17 as an example.

```bash
# optional
docker network create --subnet=172.18.0.0/16 router

docker stop istio-proxy-builder
docker rm istio-proxy-builder

mkdir -p $HOME/istio-testing/home/.cache

# run istio-proxy-builder container
docker run --init  --privileged --name istio-proxy-builder --hostname istio-proxy-builder \
    --network router \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v $HOME/istio-testing/work:/work \
    -v $HOME/istio-testing/home/.cache:/home/.cache \
    -w /work \
    -d gcr.io/istio-testing/build-tools-proxy:release-1.17-latest-amd64 bash -c '/bin/sleep 300d'
```


#### 1.3 build istio-proxy
```bash
## goto istio-proxy-builder container
docker exec -it istio-proxy-builder bash

## build istio-proxy with debug info in output ELF
cd /work
make build BAZEL_STARTUP_ARGS='' BAZEL_BUILD_ARGS='-s  --explain=explain.txt --config=debug' BAZEL_TARGETS=':envoy'
```

It took me 3 hours to build it on my 2 cores CPU and 64GB ram machine. More core will be faster.

You can check the output ELF after build finished：
```bash
## goto istio-proxy-builder container
docker exec -it istio-proxy-builder bash

build-tools: # ls -lh /work/bazel-out/k8-dbg/bin/src/envoy/envoy
-r-xr-xr-x 1 root root 1.2G Feb 18 21:46 /work/bazel-out/k8-dbg/bin/src/envoy/envoy
```

### 2. Setup testing pod

#### 2.1 Build debug istio-proxy docker image

Run on `labile-T30`

```bash
# start local private plain http docker image registry
docker run -d -p 5000:5000 --restart=always --name image-registry --hostname image-registry registry:2

cd mkdir -p image/gdb-istio-proxy
cd image/gdb-istio-proxy

# NOTICE: replae 1e0bb3bee2d09d2e4ad3523530d3b40c with the real path in your environment
sudo ln $HOME/istio-testing/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin/envoy ./envoy

cat > proxyv2:1.17.2-debug.Dockerfile <<"EOF"
FROM docker.io/istio/proxyv2:1.17.2

COPY envoy /usr/local/bin/envoy

RUN apt-get -y update \
  && sudo apt -y install lldb
EOF

# build docker image
docker build . -f ./proxyv2:1.17.2-debug.Dockerfile -t proxyv2:1.17.2-debug

docker tag proxyv2:1.17.2-debug localhost:5000/proxyv2:1.17.2-debug
# push image to local image registry
docker push localhost:5000/proxyv2:1.17.2-debug
```

Total size of image:
- Envoy elf: 1.4G
- lldb package: 700Mb
- others

#### 2.2 run target pod

```yaml
kubectl -n mark apply -f - <<"EOF"

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
        sidecar.istio.io/inject: "true"
        sidecar.istio.io/proxyMemoryLimit: "4Gi"
        sidecar.istio.io/proxyMemory: "512Mi"
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

      - name: istio-proxy
        image: auto
        imagePullPolicy: IfNotPresent
EOF
```

#### 2.3 start lldb server
```bash
ssh 192.168.122.55

sudo su

# get PID of envoy
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
```

##### Test lldb-server(Optional)

Run on `labile-T30`:

```bash
sudo lldb
# commands run in lldb:
platform select remote-linux
platform connect connect://192.168.122.55:2159

# list process of istio-proxy container
platform process list

file /home/labile/istio-testing/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin/envoy

# Assuming pid of envoy is 15
attach --pid 15

# wait, please the big evnoy ELF

exit
```

### 3. Attach testing istio with debuger

#### 3.1 start lldb-vscode-server container

Run on `labile-T30`:


1. start `lldb-vscode-server` container

```bash
docker stop lldb-vscode-server
docker rm lldb-vscode-server
docker run \
--entrypoint /bin/bash \
--init  --privileged --name lldb-vscode-server --hostname lldb-vscode-server \
    --network router \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v $HOME/istio-testing/work:/work \
    -v $HOME/istio-testing/home/.cache:/home/.cache \
    -w /work \
    -d localhost:5000/proxyv2:1.17.2-debug \
    -c '/bin/sleep 300d'
```


#### 3.2 VSCode attach `lldb-vscode-server` container

1. Start VSCode GUI on `labile-T30`. 
2. Run vscode command: `Remote Containers: Attach to Running Container`, select `lldb-vscode-server` container.
3. After attached to container, open folder: `/work`.
4. Install VSCode extensions:
   - CodeLLDB
   - clangd (Optional)


#### 3.3 lldb remote attach Envoy process

##### 3.3.1 Create `launch.json`

Create `.vscode/launch.json` in `/work`

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "AttachLLDBRemote",
            "type": "lldb",
            "request": "attach",
            "program": "/work/bazel-out/k8-dbg/bin/envoy",
            "pid": "15", //pid of envoy in istio-proxy container
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

##### 3.3.2 Attach remote process

Run and debug: `AttachLLDBRemote`.

It may took about 1 minute to load the 1GB ELF. Please be patient.


### 4. Debuging

![image-20230517225030845](debug-istio-proxy.assets/vscode-debuging.png)





## FAQ

### `containerd` allow pull image from plain http docker image registry

Update `/etc/containerd/config.toml` of the node in k8s cluster:

```ini
sudo vi /etc/containerd/config.toml

version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri".registry]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors."192.168.122.1:5000"]
        endpoint = ["http://192.168.122.1:5000"]
```

### Dynamic path

Please update `/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c` path according to your environment.



### Why use `lldb` not `gdb`

I was hit by many issues when use `gdb`.

