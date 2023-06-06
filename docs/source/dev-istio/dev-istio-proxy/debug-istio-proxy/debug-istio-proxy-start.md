# 调试与观察 istio-proxy Envoy sidecar 的启动过程

学习 Istio 下 Envoy sidecar 的初始化过程，有助于理解 Envoy 是如何构建起整个事件驱动和线程互动体系的。其中 Listener socket 事件监初始化是重点。而获取这个知识最直接的方法是 debug Envoy 启动初始化过程，这样可以直接观察运行状态的 Envoy 代码，而不是只读无聊的 OOP 代码去猜现实行为。debug sidecar 初始化有几道砍要过。本文记录了我的通关打怪的过程。



## debug 初始化之难

有经验的程序员都知道，debug 的难度和要 debug 的目标场景出现频率成反比。而 sidecar 的初始化只有一次。

要 debug istio-proxy(Envoy) 的启动过程，需要经过几道砍：

 1. Istio auto inject sidecar 在容器启动时就自动启动 Envoy，很难在初始化前完成 remote debug attach 和 breakpoint 设置。
 2. `/usr/local/bin/pilot-agent` 负责运行 `/usr/local/bin/envoy` 进程，并作为其父进程，即不可以直接控制 envoy 进程的启动。

下面我解释一下如何避坑。



## Envoy 的启动 attach 方法

下面研究一下，两种场景下，Envoy 的启动 attach 方法：

1. Istio auto inject 的 istio-proxy container
2. 手工 inject 的 istio-proxy container

### Istio auto inject 的 sidecar container

对于 Istio auto inject 的 sidecar container，是很难在 envoy 初始化前 attach 到刚启动的 envoy 进程的。理论上有个可能的方法：



- 在 worker node 上，让 gdb/lldb 不断扫描进程列表，发现 envoy 立即 attach

对于 gdb， [网上](https://stackoverflow.com/a/11147567) 有个 script:

```bash
#!/bin/sh
# 以下脚本启动前，要求 pid namespace(这里为 worker node) 下未有 envoy 进程运行
progstr=envoy
progpid=`pgrep -o $progstr`
while [ "$progpid" = "" ]; do
  progpid=`pgrep -o $progstr`
done
gdb -ex continue -p $progpid
```

对于 本文的主角 lldb，有内置的方法：

```
(lldb) process attach --name /usr/local/bin/envoy --waitfor
```

这个方法由于让 debugger(gdb/lldb) 和 envoy 不在同一个 pid namespace 和 mount namespace，所以不建议使用。





### 手工 inject 的 istio-proxy container



1. envoy 进程是由 `pilot-agent`  fork & execv 出来的，可以用 gdb/lldb  debug 启动  `pilot-agent`  ，然后开启 `follow-fork-mode child` 模式，这样就可以，debug 和挂停新 envoy 进程。



```bash
./istioctl kube-inject -f fortio-server.yaml > fortio-server-injected.yaml

vi fortio-server-injected.yaml
      annotations:
        sidecar.istio.io/inject: "false" 

```

### 定制手工拉起的 istio-proxy 

```yaml
kubectl -n mark apply -f - <<"EOF"

apiVersion: apps/v1
kind: StatefulSet
metadata:
  creationTimestamp: null
  labels:
    app: fortio-server
  name: fortio-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fortio-server
  serviceName: fortio-server
  template:
    metadata:
      annotations:
        kubectl.kubernetes.io/default-container: main-app
        kubectl.kubernetes.io/default-logs-container: main-app
        prometheus.io/path: /stats/prometheus
        prometheus.io/port: "15020"
        prometheus.io/scrape: "true"
        sidecar.istio.io/proxyImage: 192.168.122.1:5000/proxyv2:1.17.2-debug
        sidecar.istio.io/status: '{"initContainers":["istio-init"],"containers":["istio-proxy"],"volumes":["workload-socket","credential-socket","workload-certs","istio-envoy","istio-data","istio-podinfo","istio-token","istiod-ca-cert"],"imagePullSecrets":null,"revision":"default"}'
        sidecar.istio.io/inject: "false" 
      creationTimestamp: null
      labels:
        app: fortio-server
        app.kubernetes.io/name: fortio-server
        security.istio.io/tlsMode: istio
        service.istio.io/canonical-name: fortio-server
        service.istio.io/canonical-revision: latest
    spec:
      containers:
      - args:
        - 10d
        command:
        - /bin/sleep
        image: docker.io/nicolaka/netshoot:latest
        imagePullPolicy: IfNotPresent
        name: main-app
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        resources: {}
      - args:
        - 20d
        command:
        - /usr/bin/sleep
        env:
        - name: JWT_POLICY
          value: third-party-jwt
        - name: PILOT_CERT_PROVIDER
          value: istiod
        - name: CA_ADDR
          value: istiod.istio-system.svc:15012
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: INSTANCE_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: SERVICE_ACCOUNT
          valueFrom:
            fieldRef:
              fieldPath: spec.serviceAccountName
        - name: HOST_IP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
        - name: PROXY_CONFIG
          value: |
            {}
        - name: ISTIO_META_POD_PORTS
          value: |-
            [
                {"name":"http","containerPort":8080,"protocol":"TCP"}
                ,{"name":"http-m","containerPort":8070,"protocol":"TCP"}
                ,{"name":"grpc","containerPort":8079,"protocol":"TCP"}
            ]
        - name: ISTIO_META_APP_CONTAINERS
          value: main-app
        - name: ISTIO_META_CLUSTER_ID
          value: Kubernetes
        - name: ISTIO_META_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: ISTIO_META_INTERCEPTION_MODE
          value: REDIRECT
        - name: ISTIO_META_MESH_ID
          value: cluster.local
        - name: TRUST_DOMAIN
          value: cluster.local
        image: 192.168.122.1:5000/proxyv2:1.17.2-debug
        name: istio-proxy
        ports:
        - containerPort: 15090
          name: http-envoy-prom
          protocol: TCP
        - containerPort: 2159
          name: http-m
          protocol: TCP
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
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
        volumeMounts:
        - mountPath: /var/run/secrets/workload-spiffe-uds
          name: workload-socket
        - mountPath: /var/run/secrets/credential-uds
          name: credential-socket
        - mountPath: /var/run/secrets/workload-spiffe-credentials
          name: workload-certs
        - mountPath: /var/run/secrets/istio
          name: istiod-ca-cert
        - mountPath: /var/lib/istio/data
          name: istio-data
        - mountPath: /etc/istio/proxy
          name: istio-envoy
        - mountPath: /var/run/secrets/tokens
          name: istio-token
        - mountPath: /etc/istio/pod
          name: istio-podinfo
      restartPolicy: Always
      volumes:
      - name: workload-socket
      - name: credential-socket
      - name: workload-certs
      - emptyDir:
          medium: Memory
        name: istio-envoy
      - emptyDir: {}
        name: istio-data
      - downwardAPI:
          items:
          - fieldRef:
              fieldPath: metadata.labels
            path: labels
          - fieldRef:
              fieldPath: metadata.annotations
            path: annotations
        name: istio-podinfo
      - name: istio-token
        projected:
          sources:
          - serviceAccountToken:
              audience: istio-ca
              expirationSeconds: 43200
              path: istio-token
      - configMap:
          name: istio-ca-root-cert
        name: istiod-ca-cert
  updateStrategy: {}
status:
  availableReplicas: 0
  replicas: 0


EOF
```

```bash
k exec -it fortio-server-0 -c istio-proxy -- bash
sudo apt install -y tmux
tmux

bash
```


```bash
k exec -it fortio-server-0 -c main-app -- bash

adduser -u 1000 app
su app
```


```bash

k exec -it fortio-server-0 -c istio-proxy -- bash


sudo iptables-restore <<"EOF"
# Generated by iptables-save v1.8.7 on Fri Jun  2 19:32:04 2023
*nat
:PREROUTING ACCEPT [8947:536820]
:INPUT ACCEPT [8947:536820]
:OUTPUT ACCEPT [713:63023]
:POSTROUTING ACCEPT [713:63023]
:ISTIO_INBOUND - [0:0]
:ISTIO_IN_REDIRECT - [0:0]
:ISTIO_OUTPUT - [0:0]
:ISTIO_REDIRECT - [0:0]
-A PREROUTING -p tcp -j ISTIO_INBOUND
-A OUTPUT -p tcp -j ISTIO_OUTPUT
-A ISTIO_INBOUND -p tcp -m tcp --dport 15008 -j RETURN
-A ISTIO_INBOUND -p tcp -m tcp --dport 15090 -j RETURN
-A ISTIO_INBOUND -p tcp -m tcp --dport 15021 -j RETURN
-A ISTIO_INBOUND -p tcp -m tcp --dport 15020 -j RETURN
# remote lldb inbound
-A ISTIO_INBOUND -p tcp -m tcp --dport 2159 -j RETURN
-A ISTIO_INBOUND -p tcp -j ISTIO_IN_REDIRECT
-A ISTIO_IN_REDIRECT -p tcp -j REDIRECT --to-ports 15006
-A ISTIO_OUTPUT -s 127.0.0.6/32 -o lo -j RETURN
-A ISTIO_OUTPUT ! -d 127.0.0.1/32 -o lo -m owner --uid-owner 1337 -j ISTIO_IN_REDIRECT
-A ISTIO_OUTPUT -o lo -m owner ! --uid-owner 1337 -j RETURN
-A ISTIO_OUTPUT -m owner --uid-owner 1337 -j RETURN
# only app user outbound redirct
-A ISTIO_OUTPUT -m owner ! --uid-owner 1000 -j RETURN
-A ISTIO_OUTPUT ! -d 127.0.0.1/32 -o lo -m owner --gid-owner 1337 -j ISTIO_IN_REDIRECT
-A ISTIO_OUTPUT -o lo -m owner ! --gid-owner 1337 -j RETURN
# only app user outbound redirct
-A ISTIO_OUTPUT -m owner ! --gid-owner 1000 -j RETURN
-A ISTIO_OUTPUT -m owner --gid-owner 1337 -j RETURN
-A ISTIO_OUTPUT -d 127.0.0.1/32 -j RETURN
-A ISTIO_OUTPUT -j ISTIO_REDIRECT
-A ISTIO_REDIRECT -p tcp -j REDIRECT --to-ports 15001
COMMIT
# Completed on Fri Jun  2 19:32:04 2023
EOF

```

```json
        {
            "name": "AttachLLDBWaitRemote",
            "type": "lldb",
            "request": "attach",
            "program": "/usr/local/bin/envoy",
            // "stopOnEntry": true,
            "waitFor": true,
            "sourceMap": {
                "/proc/self/cwd": "/work/bazel-work",
                "/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/sandbox/linux-sandbox/263/execroot/io_istio_proxy": "/work/bazel-work"
            },
            "initCommands": [
                // "log enable lldb commands",
                "platform select remote-linux", // Execute `platform list` for a list of available remote platform plugins.
                "platform connect connect://192.168.122.55:2159",
            ],                              
        } 
```


```
9: file = '/proc/self/cwd/external/envoy/source/exe/main_common.cc', line = 87, exact_match = 0, locations = 1, resolved = 1, hit count = 0

  9.1: where = envoy`Envoy::MainCommon::main(int, char**, std::__1::function<void (Envoy::Server::Instance&)>) + 25 at main_common.cc:91:30, address = 0x000055555a21d329, resolved, hit count = 0 

10: file = '/proc/self/cwd/external/envoy/source/exe/main.cc', line = 16, exact_match = 0, locations = 1, resolved = 1, hit count = 1

  10.1: where = envoy`main + 38 at main.cc:24:34, address = 0x000055555a21c336, resolved, hit count = 1 

11: file = '/proc/self/cwd/external/envoy/source/exe/main.cc', line = 24, exact_match = 0, locations = 1, resolved = 1, hit count = 1

  11.1: where = envoy`main + 38 at main.cc:24:34, address = 0x000055555a21c336, resolved, hit count = 1 
```



```bash
export POD="fortio-server-0"
ENVOY_PIDS=$(pgrep sleep)
while IFS= read -r ENVOY_PID; do
    HN=$(sudo nsenter -u -t $ENVOY_PID hostname)
    if [[ "$HN" = "$POD" ]]; then # space between = is important
        sudo nsenter -u -t $ENVOY_PID hostname
        export POD_PID=$ENVOY_PID
    fi
done <<< "$ENVOY_PIDS"
echo $POD_PID
export PID=$POD_PID

sudo nsenter -t $PID -u -p -m bash -c 'lldb-server platform --server --listen *:2159' #NO -n: 
```


<!-- ```bash
lldb-server platform --server --listen *:2159
``` -->

<!-- ```bash
kubectl port-forward --address 0.0.0.0 pods/fortio-server-0 2159:2159
``` -->


```bash
/usr/local/bin/pilot-agent proxy sidecar --domain ${POD_NAMESPACE}.svc.cluster.local --proxyLogLevel=warning --proxyComponentLogLevel=misc:error --log_output_level=default:info --concurrency 2


2023-06-05T08:04:25.267206Z     info    Effective config: binaryPath: /usr/local/bin/envoy
concurrency: 2
configPath: ./etc/istio/proxy
controlPlaneAuthPolicy: MUTUAL_TLS
discoveryAddress: istiod.istio-system.svc:15012
drainDuration: 45s
proxyAdminPort: 15000
serviceCluster: istio-proxy
statNameLength: 189
statusPort: 15020
terminationDrainDuration: 5s
tracing:
  zipkin:
    address: zipkin.istio-system:9411
...
2023-06-05T08:04:25.754381Z     info    Starting proxy agent
2023-06-05T08:04:25.755875Z     info    starting
2023-06-05T08:04:25.758098Z     info    Envoy command: [-c etc/istio/proxy/envoy-rev.json --drain-time-s 45 --drain-strategy immediate --local-address-ip-version v4 --file-flush-interval-msec 1000 --disable-hot-restart --allow-unknown-static-fields --log-format %Y-%m-%dT%T.%fZ       %l      envoy %n %g:%#  %v      thread=%t -l warning --component-log-level misc:error --concurrency 2]
```

```bash
k exec -it fortio-server-0 -c main-app -- bash

su app

```

```
breakpoint set --func-regex .*OsSysCallsImpl.*

breakpoint set --shlib libc.so.6 --func-regex 

breakpoint set --shlib libc.so.6 --func-regex 'epoll_create.*|epoll_wait|epoll_ctl'

breakpoint set --shlib libc.so.6 --basename 'epoll_create'
breakpoint set --shlib libc.so.6 --basename 'epoll_create1'
breakpoint set --shlib libc.so.6 --basename 'epoll_wait'
breakpoint set --shlib libc.so.6 --basename 'epoll_ctl'


breakpoint list 8
8: regex = 'epoll_create.*|epoll_wait|epoll_ctl', locations = 6, resolved = 6, hit count = 0
  8.1: where = envoy`do_epoll_wait(grpc_pollset*, grpc_core::Timestamp) + 34 at ev_epoll1_linux.cc:716:3, address = 0x000055555fc1c692, resolved, hit count = 0 
  8.2: where = envoy`epoll_create_and_cloexec() + 8 at ev_epoll1_linux.cc:98:12, address = 0x000055555fc1dd68, resolved, hit count = 0 
  8.3: where = libc.so.6`epoll_wait at epoll_wait.c:28:1, address = 0x00007ffff7dc1f80, resolved, hit count = 0 
  8.4: where = libc.so.6`epoll_create1 + 19, address = 0x00007ffff7dc2d03, resolved, hit count = 0 
  8.5: where = libc.so.6`epoll_ctl + 22, address = 0x00007ffff7dc2d36, resolved, hit count = 0 
  8.6: where = libc.so.6`epoll_create + 19, address = 0x00007ffff7dc2cd3, resolved, hit count = 0 

```




<!-- ```bash

192.168.122.1:5000/proxyv2:1.17.2-debug
```

```
sudo lldb
process attach --name pilot-agent --waitfor
```

```
platform process attach --name envoy --waitfor
```

```
        - '8080,8070' #updated,  inbound ports for which traffic is to be redirected to Envoy
        - -d
        - 15090,15021,15020,2159 #updated, inbound ports to be excluded from redirection to Envoy
``` -->

