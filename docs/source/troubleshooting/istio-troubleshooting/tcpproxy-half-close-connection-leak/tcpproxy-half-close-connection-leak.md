# TCP Proxy half-closed connection leak


## Base knowledge

- Make a connection by specified ephemeral port. e.g:

  ```bash
  nc -p 44410 172.21.206.198 7777
  ```


- List sockets with timer(state/retry timeout) info. e.g:

  ```bash
  ss -naoep
  
  tcp   SYN-SENT    0  1  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=144426,fd=3)) timer:(on,1.684ms(timeout),2(retry counter)) ino:2024378629 sk:aa4e2 <->
  ```

### Conntrack base knowledge

### TCP
//TODO

### Conntrack table

- list conntrack table command and output explain:

  ```bash
  conntrack -L 
  
  tcp  6 54(entry expire seconds) CLOSE_WAIT(entry state) 
  (local endpoint):src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 
  (remote endpoint)src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410 [ASSURED] mark=0 use=1
  ```



Conntrack by default will not DNAT some invalid tcp packet.

## Environment

Istio: istio-1.16.2

Kubernetes: 1.25

CNI: Calico

### Testing POD

```
IP: 172.29.73.7
POD Name: fortio-server-l2-0
pod running at worker node: sle

Worker Node:
Kernel: 5.14.21-150400.24.21-default
Linux distros: SUSE Linux Enterprise Server 15 SP4
```

### TCP service pod

```
IP: 172.21.206.198
POD Name: netshoot-0
```

```bash
# listen on port 7777

kubectl -it exec netshoot-0 -- nc -l -k 7777
```

### enable conntrack's invalid packet log on Testing POD

enable `nf_log_all_netns` on worker node:

```bas
sle:/proc/sys # sudo su
sle:/proc/sys # echo 1 > /proc/sys/net/netfilter/nf_log_all_netns
```

add iptables rule on container:

```bash
fortio-server-l2-0:/ $

iptables -t mangle -N ISTIO_INBOUND_LOG
iptables -t mangle -A ISTIO_INBOUND_LOG -m conntrack --ctstate INVALID -j LOG --log-level debug --log-prefix 'ISTIO_INBOUND_INVALID: '
iptables -t mangle -A PREROUTING -p tcp -j ISTIO_INBOUND_LOG 

iptables -t mangle -N ISTIO_OUTBOUND_LOG
iptables -t mangle -A ISTIO_OUTBOUND_LOG -m conntrack --ctstate INVALID -j LOG --log-level debug --log-prefix 'ISTIO_OUTBOUND_INVALID: '
iptables -t mangle -A OUTPUT -p tcp -j ISTIO_OUTBOUND_LOG 
```

### skills
#### nsenter network namespace

```bash
ssh $WORKER_NODE_OF_POD

export POD="fortio-server-l2-0"
ENVOY_PIDS=$(pgrep envoy)
while IFS= read -r ENVOY_PID; do
    HN=$(sudo nsenter -u -t $ENVOY_PID hostname)
    if [[ "$HN" = "$POD" ]]; then # space between = is important
        sudo nsenter -u -t $ENVOY_PID hostname
        export POD_PID=$ENVOY_PID
    fi
done <<< "$ENVOY_PIDS"
echo $POD_PID
export PID=$POD_PID

sudo nsenter -t $PID -n -u

export netshoot_0=172.21.206.198
export fortio_server_l2_0=172.29.73.7

```


## socket leak & occupy on FIN_WAIT2

socket leak & occupy on FIN_WAIT2 between (ephemeral port) <-> 15001

Only happens in these cases:
- TCP level proxy(TCPProxy)

### 1. TCPProxy: connections ESTABLISHED

![](./1-TCPProxy-connections-ESTABLISHED.drawio.svg)


```bash
fortio-server-l2-0:/ $ nc -p 44410 172.21.206.198 7777

fortio-server-l2-0:/ $ conntrack -L 2>&1 | egrep "172.21.206.198"

tcp  6 431954 ESTABLISHED src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410 [ASSURED] mark=0 use=1
tcp  6 431954 ESTABLISHED src=172.29.73.7 dst=172.21.206.198 sport=38072 dport=7777 src=172.21.206.198 dst=172.29.73.7 sport=7777 dport=38072 [ASSURED] mark=0 use=1


fortio-server-l2-0:/ $  ss -naoep | egrep '44410|7777'

tcp   ESTAB  0  0  172.29.73.7:38072    172.21.206.198:7777         users:(("envoy",pid=51435,fd=135)) uid:201507 ino:2020910283 sk:a8d07 <->
tcp   ESTAB  0  0  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=129742,fd=3)) ino:2020879009 sk:a8d08 <->
tcp   ESTAB  0  0     127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121)) uid:201507 ino:2020910282 sk:a8d09 <->

```



### 2. TCPProxy: upstream service active close connection

![](./2-TCPProxy-upstream-service-active-close-connection.drawio.svg)


```bash
fortio-server-l2-0:/ $  conntrack -L 2>&1 | egrep "10.104.76.163|172.21.206.198"

tcp  6 54(expire seconds) CLOSE_WAIT src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410 [ASSURED] mark=0 use=1
tcp  6 54 CLOSE_WAIT src=172.29.73.7 dst=172.21.206.198 sport=38072 dport=7777 src=172.21.206.198 dst=172.29.73.7 sport=7777 dport=38072 [ASSURED] mark=0 use=1


fortio-server-l2-0:/ $  ss -naoep | egrep '44410|7777'

tcp   CLOSE-WAIT  0  0  172.29.73.7:38072    172.21.206.198:7777         users:(("envoy",pid=51435,fd=135)) uid:201507 ino:2020910283 sk:a8d07 -->
tcp   CLOSE-WAIT  0  0  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=129742,fd=3)) ino:2020879009 sk:a8d08 -->
tcp   FIN-WAIT-2  0  0     127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121)) uid:201507 ino:2020910282 sk:a8d09 <--

```

### 3. after 60s, conntrack table CLOSE_WAIT entry timeout

After 60s, conntrack table CLOSE_WAIT entry timeout. Entry removed.

```bash
conntrack -L 2>&1 | egrep "10.104.76.163|172.21.206.198"

[None]
```

### 4. pod main-app(nc) close connection - FIN not reach peer

Pod main-app(nc) close connection - FIN not reach peer. So  socket `127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121))` stuck in `FIN-WAIT-2`.



![](./4-pod-main-app(nc)-close-connection-FIN-not-reach-peer.drawio.svg)




```bash
fortio-server-l2-0:/ $ nc -p 44410 172.21.206.198 7777
^C

fortio-server-l2-0:/ $ ss -naoep | egrep '44410|7777' 

tcp   LAST-ACK    0  1  172.29.73.7:44410    172.21.206.198:7777         timer:(on,2.056ms,5) ino:0 sk:a8d08 ---


fortio-server-l2-0:/ $ nstat -zas | egrep -i 'retr|cha'

TcpRetransSegs ￪        165172        0.0
TcpExtTCPLostRetransmit ￪   826      0.0


## conntrack invalid

fortio-server-l2-0:/# tcpdump -i eth0 -n -v "port 44410"
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes

16:10:45.360217 IP (tos 0x0, ttl 64, id 64473, offset 0, flags [DF], proto TCP (6), length 52)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [F.], cksum 0x7c2c (incorrect -> 0xcc2a), seq 2082340714, ack 2209788529, win 31, options [nop,nop,TS val 1248588711 ecr 2148004549], length 0
16:10:45.572031 IP (tos 0x0, ttl 64, id 64474, offset 0, flags [DF], proto TCP (6), length 52)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [F.], cksum 0x7c2c (incorrect -> 0xcb57), seq 0, ack 1, win 31, options [nop,nop,TS val 1248588922 ecr 2148004549], length 0
16:10:45.780034 IP (tos 0x0, ttl 64, id 64475, offset 0, flags [DF], proto TCP (6), length 52)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [F.], cksum 0x7c2c (incorrect -> 0xca87), seq 0, ack 1, win 31, options [nop,nop,TS val 1248589130 ecr 2148004549], length 0
16:10:46.220029 IP (tos 0x0, ttl 64, id 64476, offset 0, flags [DF], proto TCP (6), length 52)
...

sle:/ $ dmesg --follow-new -T -l debug
[Sat Feb  4 16:10:09 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=52 TOS=0x00 PREC=0x00 TTL=64 ID=64473 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=31 RES=0x00 ACK FIN URGP=0 
[Sat Feb  4 16:10:09 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=52 TOS=0x00 PREC=0x00 TTL=64 ID=64474 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=31 RES=0x00 ACK FIN URGP=0 
[Sat Feb  4 16:10:09 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=52 TOS=0x00 PREC=0x00 TTL=64 ID=64475 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=31 RES=0x00 ACK FIN URGP=0 
...


## two half-open connections(leak):
Every 1.0s: ss -naoep | egrep '44410|7777'   fortio-server-l2-0: Sat Feb  4 16:19:42 2023

tcp   CLOSE-WAIT  0  0  172.29.73.7:38072    172.21.206.198:7777         users:(("envoy",pid=51435,fd=135)) uid:201507 ino:2020910283 sk:a8d07 -->
tcp   FIN-WAIT-2  0  0     127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121)) uid:201507 ino:2020910282 sk:a8d09 <--

```



After timeout, socket `LAST-ACK 172.29.73.7:44410  172.21.206.198:7777 (own by nc)` will be closed and:

- socket `FIN-WAIT-2 127.0.0.1:15001   172.29.73.7:44410   users:(("envoy"))` which from sidecar to App leaked.
- socket `CLOSE-WAIT 172.29.73.7:38072  172.21.206.198:7777  users:(("envoy"))`  which from sidecar to upstream service leaked.
- Ephemeral port 44410 can be reused by new socket connection to 172.21.206.198:7777 .
  - When App create new connection and randomly selects the collision ephemeral port(44410) to connect any upstream service(including TCP/HTTP service), a `connect timed out` issue may be happen. Because of conntrack TCP window check and mark the RST response to `Challenge ACK` as  `Invalid` and wil not delivery to Envoy. I will explain why later.

Good news is:`Envoy TCPProxy Filter` has an [`idle_timeout`](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/network/tcp_proxy/v3/tcp_proxy.proto) setting which by default is 1 hour. So above problem will have a 1 hour leak window before being GC.

