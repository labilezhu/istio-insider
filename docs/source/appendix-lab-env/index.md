# 实验环境总述

这里列出了本书用到的实现环境和相关的重要配置。

- Istio: 1.14  
- Kubernetes: 1.20  
- 操作系统： Ubuntu 22.04.1 LTS
- shell: Oh My ZSH


shell 环境配置：
```bash
alias k=kubectl
```

## 基础环境安装


### 默认 namespace

```yaml
cat <<"EOF" | kubectl apply -f -

apiVersion: v1
kind: Namespace
metadata:
  labels:
    istio-injection: enabled
  name: mark
  
EOF
```


Or, Create a new context with namespace defined:
```bash
kubectl config set-context mark --user=kubernetes-admin --namespace=mark --cluster=kubernetes
kubectl config use-context mark
```

### 安装 istio

```bash
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.14.3/bin

./istioctl x precheck

./istioctl x uninstall --purge
./istioctl install

export ISTIO_HOME=$HOME/istio/istio-1.14.3
export PATH=$ISTIO_HOME/bin:$PATH
```

## 安装工具服务


### netshoot
```yaml

cat <<"EOF" | kubectl -n mark apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: netshoot
spec:
  containers:
  - name: netshoot
    image: docker.io/nicolaka/netshoot:latest
    command: ["/bin/sleep"]
    args: ["100d"]    
    ports:
    - containerPort: 9999
      name: tcp
      protocol: TCP
    - containerPort: 80
      name: http-80
      protocol: TCP
    securityContext:
        privileged: true
EOF

```


### httpbin

> Ref. https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/

```yaml

cat <<"EOF" | kubectl -n mark apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: httpbin
---
apiVersion: v1
kind: Service
metadata:
  name: httpbin
  labels:
    app: httpbin
    service: httpbin
spec:
  ports:
  - name: http
    port: 8000
    targetPort: 80
  selector:
    app: httpbin
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
      version: v1
  template:
    metadata:
      labels:
        app: httpbin
        version: v1
    spec:
      serviceAccountName: httpbin
      containers:
      - image: docker.io/kennethreitz/httpbin
        imagePullPolicy: IfNotPresent
        name: httpbin
        ports:
        - containerPort: 80
EOF


```

## 配置 Shell 环境

### istio gateway & node port


```bash
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
```


## 实验环境列表

```{toctree}
appendix-lab-env-base.md
```