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


### fortio


```yaml

kubectl -n mark delete pod fortio-server

kubectl -n mark apply -f - <<"EOF"
apiVersion: v1
kind: Pod
metadata:
    name: fortio-server
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

kubectl -n mark apply -f - <<"EOF"
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
      args: ["server"]
      ports:
      - containerPort: 8080
        protocol: TCP
        name: http
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



