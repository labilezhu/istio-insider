# Istio 里的 Envoy 配置(草稿)

要理解 Istio 数据面基理，首先要看懂 Side Car Proxy - Envoy 的配置。本节用一个例子，看看 istiod 是如何 “编程” 控制这个 “可编程的代理” —— Envoy 。

```{note}
本节的实验环境说明见于： {ref}`appendix-lab-env/appendix-lab-env-base:简单分层实验环境`
```

首先看看 Envoy 的配置：

```bash
kubectl exec fortio-server -c istio-proxy  -- \
curl 'localhost:15000/config_dump?include_eds' | \
yq eval -P > envoy@istio-conf-eg-inbound.envoy_conf.yaml
```


:::{figure-md} 图：Istio里的 Envoy Inbound 配置举例

<img src="envoy@istio-conf-eg.assets/envoy@istio-conf-eg-inbound.drawio.svg" alt="Inbound与Outbound概念">

*图：Istio里的 Envoy Inbound配置举例*
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fenvoy@istio-conf-eg-inbound.drawio.svg)*




