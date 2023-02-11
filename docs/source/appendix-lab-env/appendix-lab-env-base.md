# 简单分层实验环境


```{note}
开始前，请确保您已经看过： {ref}`appendix-lab-env/index:实验环境总述`
```

安装成功后的架构图见：

:::{figure-md} 图:简单分层实验环境部署

<img src="/ch1-istio-arch/istio-data-panel-arch.assets/istio-data-panel-arch.drawio.svg" alt="Inbound与Outbound概念">

*图:简单分层实验环境部署*
:::
*[用 Draw.io 打开](https://app.diagrams.net/?ui=sketch#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-data-panel-arch.drawio.svg)*


## 安装过程

```bash
kubectl create secret docker-registry docker-registry-key --docker-server=https://index.docker.io/v1/ --docker-username=labile --docker-password=<your-pword> --docker-email=labile.zhu@gmail.com


kubectl get secret docker-registry-key --output=yaml

```

### fortio

#### fortio-server L1

```yaml

kubectl -n mark apply -f - <<"EOF"

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: fortio-server
  labels:
    app: fortio-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fortio-server
  template:
    metadata:
      labels:
          app.kubernetes.io/name: fortio-server
          app: fortio-server
      annotations:
        proxy.istio.io/config: |-
          proxyStatsMatcher:
            inclusionRegexps:
            - "cluster\\..*fortio.*" #proxy upstream(outbound)
            - "cluster\\..*inbound.*" #proxy upstream(inbound)
            - "http\\..*"
            - "listener\\..*"
    spec:
      restartPolicy: Always
      imagePullSecrets:
      - name: docker-registry-key
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

---

apiVersion: v1
kind: Service
metadata:
  labels:
    app.kubernetes.io/name: fortio-server
    app.kubernetes.io/instance: fortio-server
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

#### fortio-server L2

```yaml

kubectl -n mark apply -f - <<"EOF"

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: fortio-server-l2
  labels:
    app: fortio-server-l2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fortio-server-l2
  template:
    metadata:
      labels:
          app.kubernetes.io/name: fortio-server-l2
          app: fortio-server-l2
      annotations:
        proxy.istio.io/config: |-
          proxyStatsMatcher:
            inclusionRegexps:
            - "cluster\\..*fortio.*" #proxy upstream(outbound)
            - "cluster\\..*inbound.*" #proxy upstream(inbound)
            - "http\\..*"
            - "listener\\..*"
    spec:
      restartPolicy: Always
      imagePullSecrets:
      - name: docker-registry-key
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

---

apiVersion: v1
kind: Service
metadata:
  labels:
    app.kubernetes.io/name: fortio-server-l2
    app.kubernetes.io/instance: fortio-server-l2
  name: fortio-server-l2
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: fortio-server-l2
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


#### fortio-server-worknode6

```yaml

kubectl -n mark apply -f - <<"EOF"

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: fortio-server-worknode6
  labels:
    app: fortio-server-worknode6
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fortio-server-worknode6
  template:
    metadata:
      labels:
          app.kubernetes.io/name: fortio-server-worknode6
          app: fortio-server-worknode6
      annotations:
        proxy.istio.io/config: |-
          proxyStatsMatcher:
            inclusionRegexps:
            - "cluster\\..*fortio.*" #proxy upstream(outbound)
            - "cluster\\..*inbound.*" #proxy upstream(inbound)
            - "http\\..*"
            - "listener\\..*"
    spec:
      restartPolicy: Always
      imagePullSecrets:
      - name: docker-registry-key
      containers:
      - name: main-app
        image: docker.io/fortio/fortio
        imagePullPolicy: IfNotPresent
        command: ["/usr/bin/fortio"]
        args: ["server", "-M", "8070 http://fortio-server-worknode6:8080"]
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
          
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: "kubernetes.io/hostname"
                operator: In
                values:
                - "worknode6" 

EOF
```