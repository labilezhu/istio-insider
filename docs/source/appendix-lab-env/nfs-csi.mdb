# NFS CSI

## Base NFS
> https://microk8s.io/docs/nfs

### NFS server


```
sudo systemctl restart nfs-kernel-server

```

```
vi /etc/exports 

/home/labile    *(rw,async,no_root_squash,no_subtree_check)
```

## CSI

### Install NFS CSI driver

> https://github.com/kubernetes-csi/csi-driver-nfs/blob/master/docs/install-csi-driver-v4.2.0.md


### Storage Class
```yaml
cat <<"EOF" | kubectl -n mark apply -f -

apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-csi
provisioner: nfs.csi.k8s.io
parameters:
  server: 192.168.122.1
  share: /home/labile
  onDelete: retain
  # csi.storage.k8s.io/provisioner-secret is only needed for providing mountOptions in DeleteVolume
  # csi.storage.k8s.io/provisioner-secret-name: "mount-options"
  # csi.storage.k8s.io/provisioner-secret-namespace: "default"
reclaimPolicy: Retain
volumeBindingMode: Immediate
# mountOptions:
#   - nfsvers=4.1

EOF
```

### istio-testing/work PV
```yaml

cat <<"EOF" | kubectl -n mark apply -f -

---
apiVersion: v1
kind: PersistentVolume
metadata:
  annotations:
    pv.kubernetes.io/provisioned-by: nfs.csi.k8s.io
  name: istio-testing-work
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-csi
#   mountOptions:
#     - nfsvers=4.1
  csi:
    driver: nfs.csi.k8s.io
    readOnly: false
    # volumeHandle format: {nfs-server-address}#{sub-dir-name}#{share-name}
    # make sure this value is unique for every share in the cluster
    volumeHandle: 192.168.122.1/home/labile/istio-testing/work##
    volumeAttributes:
      server: 192.168.122.1
      share: /home/labile/istio-testing/work


---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc-istio-testing-work
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  volumeName: istio-testing-work
  storageClassName: nfs-csi


EOF


```

### istio-testing/home/.cache PV
```yaml

cat <<"EOF" | kubectl -n mark apply -f -

---
apiVersion: v1
kind: PersistentVolume
metadata:
  annotations:
    pv.kubernetes.io/provisioned-by: nfs.csi.k8s.io
  name: istio-testing-cache
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-csi
#   mountOptions:
#     - nfsvers=4.1
  csi:
    driver: nfs.csi.k8s.io
    readOnly: false
    # volumeHandle format: {nfs-server-address}#{sub-dir-name}#{share-name}
    # make sure this value is unique for every share in the cluster
    volumeHandle: 192.168.122.1/home/labile/istio-testing/home/.cache##
    volumeAttributes:
      server: 192.168.122.1
      share: /home/labile/istio-testing/home/.cache


---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc-istio-testing-cache
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  volumeName: istio-testing-cache
  storageClassName: nfs-csi


EOF


```


### /usr/local/bin/envoy PV
```yaml

cat <<"EOF" | kubectl -n mark apply -f -

---
apiVersion: v1
kind: PersistentVolume
metadata:
  annotations:
    pv.kubernetes.io/provisioned-by: nfs.csi.k8s.io
  name: istio-testing-envoy-elf
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-csi
#   mountOptions:
#     - nfsvers=4.1
  csi:
    driver: nfs.csi.k8s.io
    readOnly: false
    # volumeHandle format: {nfs-server-address}#{sub-dir-name}#{share-name}
    # make sure this value is unique for every share in the cluster
    volumeHandle: 192.168.122.1/envoy-debug-elf##
    volumeAttributes:
      server: 192.168.122.1
      share: /home/labile/istio-testing/home/.cache/bazel/_bazel_root/1e0bb3bee2d09d2e4ad3523530d3b40c/execroot/io_istio_proxy/bazel-out/k8-dbg/bin


---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc-istio-testing-envoy-elf
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  volumeName: istio-testing-envoy-elf
  storageClassName: nfs-csi


EOF


```

## test POD
```yaml

cat <<"EOF" | kubectl -n mark apply -f -

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: test-pvc-istio-testing-work
  labels:
    app: test-pvc-istio-testing-work
spec:
  serviceName: test-pvc-istio-testing-work
  replicas: 1
  selector:
    matchLabels:
      app: test-pvc-istio-testing-work
  template:
    metadata:
      annotations:
        sidecar.istio.io/inject: "false"    
      labels:
        app: test-pvc-istio-testing-work
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

        volumeMounts:
          - name: istio-testing-work
            mountPath: "/work"

          - name: istio-testing-cache
            mountPath: "/home/.cache"
          - name: istio-testing-envoy-elf 
            mountPath: "/debug-envoy"
      volumes:
        - name: istio-testing-work
          persistentVolumeClaim:
            claimName: pvc-istio-testing-work     
        - name: istio-testing-cache
          persistentVolumeClaim:
            claimName: pvc-istio-testing-cache 
        - name: istio-testing-envoy-elf 
          persistentVolumeClaim:
            claimName: pvc-istio-testing-envoy-elf 

EOF

```


## test istio-proxy
```yaml
kubectl -n mark delete StatefulSet fortio-server

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
        securityContext:
          allowPrivilegeEscalation: true
          capabilities:
            add:
            - ALL
          privileged: true
          readOnlyRootFilesystem: false
          runAsNonRoot: false
        command: [ "bash", "-c", "sudo rm /usr/local/bin/envoy;sudo ln -s /debug-envoy/envoy /usr/local/bin/envoy; export PATH=/debug-envoy:$(PATH);/usr/local/bin/pilot-agent proxy sidecar --domain $(POD_NAMESPACE).svc.cluster.local --proxyLogLevel=warning --proxyComponentLogLevel=misc:error --log_output_level=default:info --concurrency 2" ]
        args: []
        volumeMounts:
          - name: istio-testing-work
            mountPath: "/work"
          - name: istio-testing-cache
            mountPath: "/home/.cache"
          - name: istio-testing-envoy-elf 
            mountPath: "/debug-envoy"
      volumes:
        - name: istio-testing-work
          persistentVolumeClaim:
            claimName: pvc-istio-testing-work     
        - name: istio-testing-cache
          persistentVolumeClaim:
            claimName: pvc-istio-testing-cache 
        - name: istio-testing-envoy-elf
          persistentVolumeClaim:
            claimName: pvc-istio-testing-envoy-elf 

EOF
```


