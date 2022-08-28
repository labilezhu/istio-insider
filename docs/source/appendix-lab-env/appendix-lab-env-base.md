# 简单分层实验环境

## set default namesapce

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

## install istio

```bash
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.14.3/bin

./istioctl x precheck

./istioctl x uninstall --purge
./istioctl install

export ISTIO_HOME=$HOME/istio/istio-1.14.3
export PATH=$ISTIO_HOME/bin:$PATH
```


## setup services


### fortio


```yaml

kubectl -n mark delete pod fortio-server

kubectl -n mark apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
    name: fortio-server
    labels:
        app.kubernetes.io/name: fortio-server
        app: fortio-server
spec:
    restartPolicy: Always
    imagePullSecrets:
    - name: docker-registry-key
    containers:
    - name: main-app
      image: docker.io/fortio/fortio
      imagePullPolicy: Always
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
    nodeSelector:
        topology.kubernetes.io/region: us-east-1
        topology.kubernetes.io/zone: worker005
        topology.istio.io/subzone: worker005

---

apiVersion: v1
kind: Service
metadata:
  labels:
    app.kubernetes.io/name: fortio-server
    app.kubernetes.io/instance: fortio-server
    app.kubernetes.io/version: 3.2.0-SNAPSHOT.10
  name: fortio-server
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: fortio-server
  sessionAffinity: None
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: 8080
    - name: http-m
      protocol: TCP
      port: 8070
      targetPort: 8070
    - name: grpc
      protocol: TCP
      port: 8079
      targetPort: 8079
EOF

```


```yaml

kubectl -n mark delete pod fortio-server-l2

kubectl -n mark apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
    name: fortio-server-l2
    annotations:
      sidecar.istio.io/inject: "true"
    labels:
      app.kubernetes.io/name: fortio-server-l2
      app: fortio-server-l2
      sidecar.istio.io/inject: "true"
spec:
    restartPolicy: Always
    imagePullSecrets:
    - name: docker-registry-key
    containers:
    - name: main-app
      image: docker.io/fortio/fortio
      imagePullPolicy: Always
      command: ["/usr/bin/fortio"]
      args: ["server"]
      ports:
      - containerPort: 8080
        protocol: TCP
        name: http
      - containerPort: 8079
        protocol: TCP
        name: grpc   
    nodeSelector:
        topology.kubernetes.io/zone: worker005

---

apiVersion: v1
kind: Service
metadata:
  labels:
    app.kubernetes.io/name: fortio-server-l2
    app.kubernetes.io/instance: fortio-server-l2
    app.kubernetes.io/version: 3.2.0-SNAPSHOT.10
  name: fortio-server-l2
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: fortio-server-l2
  sessionAffinity: None
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: 8080
    - name: grpc
      protocol: TCP
      port: 8079
      targetPort: 8079
EOF

```


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
  nodeSelector:
    kubernetes.io/hostname: worknode5
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


## get gateway & node port


```bash
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')
export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')
```


