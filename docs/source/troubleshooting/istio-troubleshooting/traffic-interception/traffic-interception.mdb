# Traffic Interception

## InboundInterceptionMode config

> [Global Mesh Options: https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/#ProxyConfig-InboundInterceptionMode](https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/#ProxyConfig-InboundInterceptionMode)

The mode used to redirect inbound traffic to Envoy. This setting has no effect on outbound traffic: iptables `REDIRECT` is always used for outbound connections.

| Name       | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| `REDIRECT` | The `REDIRECT` mode uses iptables `REDIRECT` to `NAT` and redirect to Envoy. This mode loses source IP addresses during redirection. |
| `TPROXY`   | The `TPROXY` mode uses iptables `TPROXY` to redirect to Envoy. This mode preserves both the source and destination IP addresses and ports, so that they can be used for advanced filtering and manipulation. This mode also configures the sidecar to run with the `CAP_NET_ADMIN` capability, which is required to use `TPROXY`. |
| `NONE`     | The `NONE` mode does not configure redirect to Envoy at all. This is an advanced configuration that typically requires changes to user applications. |



> [Github PR: Istio: Improve iptables tests #34061](https://github.com/istio/istio/pull/34061)
>
> This changes tests to follow a standard golden file test pattern. This makes seeing diffs, seeing expected output, making changes, etc all easier. Additionally, a ton of test code is deduplicated.
>
> The biggest change here is we always call `run()` instead of some tests which called targeted functions. IMO this is a better testing methodology, and the increased test output sizes are worth it to keep things simpler, more realistic, and detect any unexpected changes.
>
> For some of the tests, I modified the job to write the `expected []string` content to the golden file, to ensure the new test is identical. For a few that did non-standard things, I spot checked the result to ensure they were the same.



