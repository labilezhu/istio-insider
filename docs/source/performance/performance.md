# Istio/Envoy 性能




## 影响性能的因素 - 设计容量

> [https://github.com/istio/istio/wiki/Performance-Questionnaire](https://github.com/istio/istio/wiki/Performance-Questionnaire)



When deploying Istio in production it is important to know the scale of the deployment. It is useful to have answers to the following questions when talking about scale.

Scale is split across several axes

1. Services and endpoints
    - Number of sidecars
    - Number of endpoints
    - Number of services
    - Number of nodes in the cluster
2. Amount of ingress traffic
3. Amount of egress traffic
4. Amount of traffic flowing through the system
    - HTTP / HTTP2
        - request per second
        - payload size
        - connections per second
        - active connections
    - TCP
        - connections per second
        - active connections
        - bytes transferred per second
5. Amount of configuration
    - Number of virtual services
    - Number of destination rules
    - Number of gateways
    - Number of metrics being collected
    - Number of Istio Rbac rules
6. Rate of change of deployment How often are deployments updated.
7. Rate of change of configuration How often does new configuration get pushed.


## Benchmark

- [Istio Release benchmark](https://istio.io/latest/docs/ops/deployment/performance-and-scalability/)
- [ Python scripts to benchmark Istio's data plane performance](https://github.com/istio/tools/tree/master/perf/benchmark)


## Analyzing Istio Performance

 - [Analyzing Istio Performance](https://github.com/istio/istio/wiki/Analyzing-Istio-Performance)



