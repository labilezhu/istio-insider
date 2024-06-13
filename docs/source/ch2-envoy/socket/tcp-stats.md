# TCP 底层监控指标

SRE / Supporting / Performance test teams 问题定位遇事不决三件宝：

- 网络问题
- 重启
- 硬件故障

这时如果遇上一个精明校真，又不遵守儒家职场尊老爱幼，凡事留一线，日后好相见的＂优良传统＂的对手，他／她会追问：＂请用数据证明你的说法＂。如果你说是个网络问题，怎么证明？

直线思维当然是找网络问题测量工具（如 iPerf）去测试网络质量和丢包率。如果报告能证明当然很好，但我的经验是只有在运维犯低级错误如 MTU 配置错误时，才有明显的问题。我叫这种不直接测量业务有效流量的工具为 offline 测量工具。其最大的问题是与现实场景差并过大，很难保证测量结果与现实问题一致。在 k8s 环境，网络拓扑更复杂，offline 测量更难靠谱。

相反的当然就是直接测量业务流量的 online 测量工具了。注意，online 不等于只在生产线上，也可以是测试环境，可以是压力测试，Chaos 混沌测试，干扰/破坏性 disruptive 测试环境。有很多这类型的 TCP 连接质量测量/可视察性工具：

- 连接级别的 `ss` ： 见我之前写的 [《可能是最完整的 TCP 连接健康指标工具 ss 的说明》](https://blog.mygraphql.com/zh/notes/low-tec/network/tcp-inspect/)
- 容器级别的 `nstat` : 见我之前写的 [《从性能问题定位，扯到性能模型，再到 TCP - 都微服务云原生了，还学 TCP 干嘛系列 Part 1》](https://blog.mygraphql.com/zh/posts/low-tec/network/tcp-flow-control-part1/#采集-tcp-指标)
- 基于 ebpf 的 tcp stats inspect 工具
  - [cloudflare/ebpf_exporter](https://github.com/cloudflare/ebpf_exporter)
  - [tcpdog](https://github.com/mehrdadrad/tcpdog)
  - [ebpf-network-viz](https://github.com/iogbole/ebpf-network-viz)
  - [BCC - tcpretrans](https://github.com/iovisor/bcc/blob/master/tools/tcpretrans.py)

不过本文打算用我比较熟识的 原生 Envoy 作为 connection 级别的 tcp stats inspect 工具。(注意，是 [原生 Envoy](https://github.com/envoyproxy/envoy) ，不是 [Istio Proxy](https://github.com/istio/proxy)，后面会解释为何)。

大概的架构如下：
```
[client(Traffic Generator)] --> [Envoy Proxy] -----external network may drop packets-----> [Application Cluster Gateway]
```

在测试环境中，Envoy 比起以上工具，在一些情况下有一些优点：
- 自带 L7(HTTP) 层的成熟多样的监控 metrics
  - 作为 client 端（测试时的流量产生端，如 JMeter）。我们时常怀疑它的实际并发数，TPS等等。有了专业 http 的 sidecar metrics，一切指标都显得更透明和可控了。
- 自带 L4/L3(TCP/IP) 层的 metrics，tcp-stats，这是本文的重点
- 自带各种成熟的流量控制技术



## 失落的 Envoy sidecar 可视察性初心

Istio 当年其中一个吹上天的特性就是 Observability(可视察性) 。但从我这几年的观察来看，在现实环境中，可视察性很少被深度使用和研究。因为很多指标其实不是阅读一行说明文字就可以理解的。

### 更失落的 tcp_stats

下面以原生 Envoy 的 [TCP statistics](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats#config-cluster-manager-cluster-stats-tcp) 为例：



| Name                                 | Type      | Description                                                  |
| ------------------------------------ | --------- | ------------------------------------------------------------ |
| cx_tx_segments                       | Counter   | Total TCP segments transmitted                               |
| cx_rx_segments                       | Counter   | Total TCP segments received                                  |
| cx_tx_data_segments                  | Counter   | Total TCP segments with a non-zero data length transmitted   |
| cx_rx_data_segments                  | Counter   | Total TCP segments with a non-zero data length received      |
| cx_tx_retransmitted_segments         | Counter   | Total TCP segments retransmitted                             |
| cx_rx_bytes_received                 | Counter   | Total payload bytes received for which TCP acknowledgments have been sent. |
| cx_tx_bytes_sent                     | Counter   | Total payload bytes transmitted (including retransmitted bytes). |
| cx_tx_unsent_bytes                   | Gauge     | Bytes which Envoy has sent to the operating system which have not yet been sent |
| cx_tx_unacked_segments               | Gauge     | Segments which have been transmitted that have not yet been acknowledged |
| cx_tx_percent_retransmitted_segments | Histogram | Percent of segments on a connection which were retransmistted |
| cx_rtt_us                            | Histogram | Smoothed round trip time estimate in microseconds            |
| cx_rtt_variance_us                   | Histogram | Estimated variance in microseconds of the round trip time. Higher values indicated more variability. |



可以看到， Envoy 有能力获取 upstream/downstream 的 TCP 级别的一些与网络质量相关的指标。

它是由一个 [TCP Stats Transport Socket wrapper](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/tcp_stats/v3/tcp_stats.proto#envoy-v3-api-msg-extensions-transport-sockets-tcp-stats-v3-config)  实现的。如果你对实现有兴趣，可见：[源码](https://github.com/envoyproxy/envoy/blob/6b9db09c69965d5bfb37bdd29693f8b7f9e9e9ec/source/extensions/transport_sockets/tcp_stats/tcp_stats.cc#L81)。需要注意的是，使用这个功能需要 linux kernel >= 4.6 。这也是 Istio Proxy 默认构建不带 tcp stats 的原因：

https://github.com/istio/proxy/blob/2320d000121a42ac5e423c0b29e4ae210174a474/bazel/extension_config/extensions_build_config.bzl#L505

```
ISTIO_DISABLED_EXTENSIONS = [
    # ISTIO disable tcp_stats by default because this plugin must be built and running on kernel >= 4.6
    "envoy.transport_sockets.tcp_stats",
]
```



可能上面一下说得太深入，赶跑了部分读者了。下面还是说说简单的使用示例吧。





## 简单使用 TCP Stats Transport Socket wrapper

以下以这个拓扑为示例：
```
[curl(to www.example.com:80) --(redirect to 8080)--> Envoy Proxy:8080(L7 proxy to www.example.com:443)] -----external network may drop packets-----> [www.example.com:443]
```

### Envoy 的配置文件

首先看看 Envoy 的配置文件 `envoy-demo-simple-http-proxy-tcp-stats.yaml`：
```yaml
"admin": {
     "address": {
      "socket_address": {
       "address": "127.0.0.1",
       "port_value": 15000
      }
     }
}

static_resources:

  listeners:
  - name: listener_0
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 8080
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          access_log:
          - name: envoy.access_loggers.stdout
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
          http_filters:
          - name: envoy.filters.http.router
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router
          route_config:
            name: local_route
            virtual_hosts:
            - name: local_service
              domains: ["*"]
              routes:
              - match:
                  prefix: "/"
                route:
                  cluster: www.example.com
      transport_socket:
        name: envoy.transport_sockets.tcp_stats
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tcp_stats.v3.Config
          update_period: 5s            
          transport_socket:
            name: envoy.transport_sockets.raw_buffer
            typed_config: 
              "@type": type.googleapis.com/envoy.extensions.transport_sockets.raw_buffer.v3.RawBuffer


  clusters:
  - name: www.example.com
    type: LOGICAL_DNS
    dns_lookup_family: V4_ONLY
    connect_timeout: 1000s
    typed_extension_protocol_options:
      envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
        "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
        explicit_http_config:
          http2_protocol_options:
            max_concurrent_streams: 100
    transport_socket:
      name: envoy.transport_sockets.tcp_stats
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tcp_stats.v3.Config
        update_period: 5s            
        transport_socket:
          name: envoy.transport_sockets.tls
          typed_config: 
            "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
            common_tls_context:
            sni: www.example.com
    load_assignment:
      cluster_name: www.example.com
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: www.example.com
                port_value: 443
```

### 本地 Linux 与网络环境

```bash
export ENVOY_PORT=8080

# create a new user u202406 to label the TCP traffic
sudo useradd -u 202406 u202406
sudo --user=u202406 id

# Redirect all connections which target at 80 to 8080. Limit redirect TCP connection only from user u202406
sudo iptables -t nat -A OUTPUT  -m owner --uid-owner 202406 -p tcp --dport 80 -j REDIRECT --to-ports "$ENVOY_PORT"

curl -v www.example.com
# success

sudo --user=u202406 time curl www.example.com
# connection refuse
```

### 启动 Envoy 和简单测试

开启三个终端，分别执行：

```bash
./envoy-1.30.2-linux-x86_64  -c ./envoy-demo-simple-http-proxy-tcp-stats.yaml -l debug
```

```bash
watch -d -n 0.5 "curl http://localhost:15000/stats | grep tcp"
```

```bash
sudo --user=u202406 time curl -v www.example.com
```

其中，watch 的终端会输出类似这样的数据：
```
cluster.www.example.com.tcp_stats.cx_rx_bytes_received: 5616
cluster.www.example.com.tcp_stats.cx_rx_data_segments: 10
cluster.www.example.com.tcp_stats.cx_rx_segments: 13
cluster.www.example.com.tcp_stats.cx_tx_bytes_sent: 548
cluster.www.example.com.tcp_stats.cx_tx_data_segments: 4
cluster.www.example.com.tcp_stats.cx_tx_retransmitted_segments: 0
cluster.www.example.com.tcp_stats.cx_tx_segments: 12
cluster.www.example.com.tcp_stats.cx_tx_unacked_segments: 0
cluster.www.example.com.tcp_stats.cx_tx_unsent_bytes: 0
cluster.www.example.com.tcp_stats.cx_rtt_us: P0(nan,200000) P25(nan,202500) P50(nan,205000) P75(nan,207500) P90(nan,209000) P95(nan,209500) P99(nan,209900) P99.5(nan,209950) P99.9(nan,209990) P100(nan,210000)
cluster.www.example.com.tcp_stats.cx_rtt_variance_us: P0(nan,59000) P25(nan,59250) P50(nan,59500) P75(nan,59750) P90(nan,59900) P95(nan,59950) P99(nan,59990) P99.5(nan,59995) P99.9(nan,59999) P100(nan,60000)
cluster.www.example.com.tcp_stats.cx_tx_percent_retransmitted_segments: P0(nan,0) P25(nan,0) P50(nan,0) P75(nan,0) P90(nan,0) P95(nan,0) P99(nan,0) P99.5(nan,0) P99.9(nan,0) P100(nan,0)
listener.0.0.0.0_8080.tcp_stats.cx_rtt_us: P0(nan,19) P25(nan,19.25) P50(nan,19.5) P75(nan,19.75) P90(nan,19.9) P95(nan,19.95) P99(nan,19.99) P99.5(nan,19.995) P99.9(nan,19.999) P100(nan,20)
listener.0.0.0.0_8080.tcp_stats.cx_rtt_variance_us: P0(nan,8) P25(nan,8.025) P50(nan,8.05) P75(nan,8.075) P90(nan,8.09) P95(nan,8.095) P99(nan,8.099) P99.5(nan,8.0995) P99.9(nan,8.0999) P100(nan,8.1)
listener.0.0.0.0_8080.tcp_stats.cx_tx_percent_retransmitted_segments: P0(nan,0) P25(nan,0) P50(nan,0) P75(nan,0) P90(nan,0) P95(nan,0) P99(nan,0) P99.5(nan,0) P99.9(nan,0) P100(nan,0)
```

### 模拟外网丢包

```bash
export EXAMPLE_COM_IP=93.184.215.14

# drop 50% packet
sudo iptables -D INPUT --src "$EXAMPLE_COM_IP" -m statistic --mode random --probability 0.5 -j DROP
```

```bash
watch -d -n 0.5 "curl http://localhost:15000/stats | grep tcp"
```

```bash
sudo --user=u202406 time curl -v www.example.com
```

这时，可见 `time curl` 的用时比丢包前大。 如果写个脚本 loop curl，从 watch 输出中可见 `cx_tx_unacked_segments` 与 `cx_tx_unsent_bytes` 两上 Gauge 类型的 metrics 有非 0 的情况出现。

### 数据与可视化图表

如果用 `http://localhost:15000/stats?format=prometheus`，把数据导入 Prometheus，就可以做时序的网络质量与丢包情况、RTT 的 Dashboard 仪表盘和折线图了。这些图再叠加上其它 API TPS、 Latency 图，就可以印证底层网络质量与 TPS 与 Latency 的影响了。


## downstream TCP 监控

上面主要讲 upstream cluster 的 TCP 监控。下面说说 downstream。 其实上面的 Envoy 的配置文件 `envoy-demo-simple-http-proxy-tcp-stats.yaml` 中，已经加入了 listeners 的 tcp stats 了，所以是可以监控 downstream TCP 的，这个功能对于 Istio Gateway 端的网络质量监控由为实用。不过，可惜的是，Istio Proxy 默认的构建没带 tcp stats 功能，只能自己 build 了。


## TCP Proxy

如果你的 client side 应用不是走 plain text http。那么就只能用 Envoy 代理 TCP 层了。这时用 Envoy TCP Proxy Filter 代替上面 Envoy 的配置文件 `envoy-demo-simple-http-proxy-tcp-stats.yaml` 中的 `http_connection_manager` 可能也是个可选方案。



## 我思故我在 - Je pense, donc je suis

学习一个开源项目，有人止于按示例使用，有人止于记录下它的设计理念，有人把这个设计理念融入自己的学习、生活、工作中。在不经意间应用了。当我们学习 Istio 时，其中精彩特性是原有应用无侵入、0 编码情况下，通过透明流量拦截，生成可视化流量指标。那么同样的思想其实可以融会贯通到很多场景中。这种能力或者就是未来架构师或程序员不致于被 AI 轻易取代的基本素质之一。

> 如果未来有人问你，你为何还能在这岗位上班而未被 AI 取代，回答是，因为 笛卡尔 说了：我思故我在！



> [伯特兰·罗素](https://zh.wikipedia.org/wiki/伯特兰·罗素)在其《[西方哲学史](https://zh.wikipedia.org/wiki/西方哲学史_(罗素))》“笛卡尔”一章是这样解释“我思故我在”：据我思考这一事实推断出“我”的存在。 因此，我思考时我也存在，也只有那时我存在。 如果我停止思考，就不会有我存在的证据。
