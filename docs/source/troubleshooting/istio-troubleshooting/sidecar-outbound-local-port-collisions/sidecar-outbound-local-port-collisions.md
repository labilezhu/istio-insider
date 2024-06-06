# App outbound connecting timed out because App selected a ephemeral port which collisions with the existing socket on 15001(outbound) listener



Sidecar intercept and TCP proxying all outbound TCP connection by default:
`(app --[conntrack DNAT]--> sidecar) -----> upstream-tcp-service`

But in some scenarios, App just get a connect timed out error when connecting to the sidecar 15001(outbound) listener.

Scenarios:

1. When sidecar has a half-open connection to App. e.g: 

   ```
   $ ss
   tcp FIN-WAIT-2 0 0 127.0.0.1:15001  172.29.73.7:44410(POD_IP:ephemeral_port)
   ```

    This can happen, eg:  [TCP Proxy half-closed connection leak for 1 hour in some scenarios #43297](https://github.com/istio/istio/issues/43297)

   There is no track entry in conntrack table because `nf_conntrack_tcp_timeout_close_wait` time out and expired.

2. App invoke syscall `connect(sockfd, peer_addr)` , kernel allocation a `ephemeral port`(44410 in this case) , bind the new socket to that  `ephemeral port` and sent `SYN` packet to peer.

3.  `SYN` packet reach conntrack and it create a `track entry` in `conntrack table`:

   ```
   $ conntrack -L
   tcp  6 108 SYN_SENT src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410
   ```

   

4.  `SYN` packet DNAT to `127.0.0.1:15001`

5. `SYN` packet reach the already existing `FIN-WAIT-2 127.0.0.1:15001  172.29.73.7:44410` socket, then sidecar reply a `TCP Challenge ACK` (TCP seq-no is from the old `FIN-WAIT-2`) packet to App

6. App reply the  `TCP Challenge ACK` with a `RST`(TCP seq-no is from the `TCP Challenge ACK`)

7. `Conntrack` get the `RST` packet and check it. In some kernel version, `conntrack` just `invalid` the `RST` packet because the `seq-no` is out of the  `track entry` in `conntrack table` which created in step 3.

8. App will retransmit `SYN` but all without an expected `SYN/ACK` reply.  Connect timed out will happen on App user space.



Different kernel version may have different packet validate rule in step 7:

```bash
RST packet mark as invalid:
  SUSE Linux Enterprise Server 15 SP4:
    5.14.21-150400.24.21-default

# cat /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst
0

####################
    
RST packet passed check and NATed:
  Ubuntu 20.04.2:
    5.4.0-137-generic
    
# cat /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst
cat: /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst: No such file or directory    
```



It seems related to kernel patch: [Add tcp_ignore_invalid_rst sysctl to allow to disable out of
   segment RSTs](https://github.com/torvalds/linux/commit/d7fba8ff3e50fb25ffe583bf945df052f6caffa2) which merge to kernel after kernel v5.14

Good news is that, someone will fix the problem at kernel v6.2-rc7: [netfilter: conntrack: handle tcp challenge acks during connection reuse](https://github.com/torvalds/linux/commit/c410cb974f2ba562920ecb8492ee66945dcf88af):

```
When a connection is re-used, following can happen:
[ connection starts to close, fin sent in either direction ]
 > syn   # initator quickly reuses connection
 < ack   # peer sends a challenge ack
 > rst   # rst, sequence number == ack_seq of previous challenge ack
 > syn   # this syn is expected to pass

Problem is that the rst will fail window validation, so it gets
tagged as invalid.

If ruleset drops such packets, we get repeated syn-retransmits until
initator gives up or peer starts responding with syn/ack.
```



But in some scenarios and kernel version, it will be an issue anyway.



Github issue: [App outbound connecting timed out because sidecar select ephemeral port collisions with socket on 15001(outbound) listener #43301](https://github.com/istio/istio/issues/43301)



## Base knowledge

### TCP

#### TCP Challenge ACK

- [What is TCP Challenge ACK](https://www.networkdefenseblog.com/post/wireshark-tcp-challenge-ack)
- [RFC 5961 Sec 3 and 4](https://www.rfc-editor.org/rfc/rfc5961#section-4)

### Conntrack table

- list conntrack table command and output explain:

  ```bash
  conntrack -L 
  
  tcp  6 54(entry expire seconds) CLOSE_WAIT(entry state) 
  (local endpoint):src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 
  (remote endpoint)src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410 [ASSURED] mark=0 use=1
  ```



Conntrack by default will not DNAT any invalid(Not in tcp connection window) tcp RST packet.



## Environment

```
$ ./istioctl version
client version: 1.16.2
control plane version: 1.16.2
data plane version: 1.16.2 (4 proxies)

$ kubectl version --short
Flag --short has been deprecated, and will be removed in the future. The --short output will become the default.
Client Version: v1.25.3
Kustomize Version: v4.5.7
Server Version: v1.25.6
```

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

```bash
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



## New connection timeout

### App build connection on the same ephemeral port

- Make a connection by specified ephemeral port. e.g:

  ```bash
  nc -p 44410 172.21.206.198 7777
  ```


- List sockets with timer(state/retry timeout) info. e.g:

  ```bash
  ss -naoep
  
  tcp   SYN-SENT    0  1  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=144426,fd=3)) timer:(on,1.684ms(timeout),2(retry counter)) ino:2024378629 sk:aa4e2 <->
  ```

#### Case 1: connect timed out by collision ephemeral port



![](./5-1-connect-timed-out-by-collision-ephemeral-port.drawio.svg)

**[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fen%2Flatest%2F_images%2F5-1-connect-timed-out-by-collision-ephemeral-port.drawio.svg)**



```bash
fortio-server-l2-0:/ # nc -p 44410 172.21.206.198 7777 #pid=144426

fortio-server-l2-0:/ # ss -naoep | egrep '44410|7777'

tcp   SYN-SENT    0  1  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=144426,fd=3)) timer:(on,1.684ms,2) ino:2024378629 sk:aa4e2 <->
tcp   FIN-WAIT-2  0  0     127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121)) ino:2023763691 sk:aa125 <--

#tcp   CLOSE-WAIT  0  0  172.29.73.7:38076    172.21.206.198:7777         users:(("envoy",pid=51435,fd=135)) ino:2023763692 sk:aa123 -->
#tcp   CLOSE-WAIT  0  0  172.29.73.7:38078    172.21.206.198:7777         users:(("nc",pid=88235,fd=3)) ino:2024198076 sk:aa3d7 -->

fortio-server-l2-0:/ # conntrack -L 2>&1 | egrep "192.168.7.|10.96.94.44|172.21.206.198"

tcp  6 108 SYN_SENT src=172.29.73.7 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.29.73.7 sport=15001 dport=44410 mark=0 use=1


fortio-server-l2-0:/ # nstat -zas | egrep -i 'retr|cha'

TcpRetransSegs        165296        0.0
TcpExtTCPLostRetransmit    842      0.0
TcpExtTCPChallengeACK ￪     140      0.0
TcpExtTCPSYNChallenge ￪     140      0.0
TcpExtTCPSynRetrans ￪       295      0.0


sle:/ $ dmesg --follow-new -T -l debug

[Sat Feb  4 16:46:40 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:46:41 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:46:43 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:46:47 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:46:55 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:47:11 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 
[Sat Feb  4 16:47:43 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=172.21.206.198 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=44410 DPT=7777 WINDOW=0 RES=0x00 RST URGP=0 




fortio-server-l2-0:/ # sudo tcpdump -i lo -n -v "port 44410"
tcpdump: listening on lo, link-type EN10MB (Ethernet), capture size 262144 bytes
16:47:16.343525 IP (tos 0x0, ttl 64, id 20177, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x3d28), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250779694 ecr 0,nop,wscale 11], length 0

# TcpExtTCPChallengeACK: (from sidecar)
16:47:16.343547 IP (tos 0x0, ttl 64, id 40356, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x0bf4), ack 1382665639, win 32, options [nop,nop,TS val 2150755275 ecr 1250324922], length 0

16:47:17.356027 IP (tos 0x0, ttl 64, id 20178, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x3934), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250780706 ecr 0,nop,wscale 11], length 0
16:47:17.356051 IP (tos 0x0, ttl 64, id 40357, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x0800), ack 1, win 32, options [nop,nop,TS val 2150756287 ecr 1250324922], length 0
16:47:19.372023 IP (tos 0x0, ttl 64, id 20179, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x3154), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250782722 ecr 0,nop,wscale 11], length 0
16:47:19.372063 IP (tos 0x0, ttl 64, id 40358, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x0020), ack 1, win 32, options [nop,nop,TS val 2150758303 ecr 1250324922], length 0
16:47:23.440028 IP (tos 0x0, ttl 64, id 20180, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x2170), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250786790 ecr 0,nop,wscale 11], length 0
16:47:23.440068 IP (tos 0x0, ttl 64, id 40359, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0xf03a), ack 1, win 32, options [nop,nop,TS val 2150762372 ecr 1250324922], length 0
16:47:31.628034 IP (tos 0x0, ttl 64, id 20181, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x0174), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250794978 ecr 0,nop,wscale 11], length 0
16:47:31.628066 IP (tos 0x0, ttl 64, id 40360, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0xd03e), ack 1, win 32, options [nop,nop,TS val 2150770560 ecr 1250324922], length 0
16:47:47.756038 IP (tos 0x0, ttl 64, id 20182, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0xc273), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250811106 ecr 0,nop,wscale 11], length 0
16:47:47.756096 IP (tos 0x0, ttl 64, id 40361, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x913e), ack 1, win 32, options [nop,nop,TS val 2150786688 ecr 1250324922], length 0
16:48:20.016036 IP (tos 0x0, ttl 64, id 20183, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x446f), seq 66001914, win 62720, options [mss 8960,sackOK,TS val 1250843366 ecr 0,nop,wscale 11], length 0
16:48:20.016066 IP (tos 0x0, ttl 64, id 40362, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x133a), ack 1, win 32, options [nop,nop,TS val 2150818948 ecr 1250324922], length 0



fortio-server-l2-0:/ # sudo tcpdump -i eth0 -n -v "port 44410"
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
# RST from 172.29.73.7.44410 (Conntrack Invalid)
16:47:16.343564 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:47:17.356068 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:47:19.372085 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:47:23.440094 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:47:31.628082 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:47:47.756113 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
16:48:20.016082 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 172.21.206.198.7777: Flags [R], cksum 0x47ee (correct), seq 1382665639, win 0, length 0
```



#### Case 2: connect by collision ephemeral port but seq-no happens to be in the TCP window of the old connection

When connect by collision ephemeral port but seq-no happens to be in the TCP window of the old connection(FIN-WAIT-2 state). Connect successed.



```bash
fortio-server-l2-0:/home/eccd # sudo tcpdump -i lo -n -v "port 44410"
tcpdump: listening on lo, link-type EN10MB (Ethernet), capture size 262144 bytes
# SYN retrans
16:23:32.466286 IP (tos 0x0, ttl 64, id 6422, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0xef14), seq 3587723838, win 62720, options [mss 8960,sackOK,TS val 1249355817 ecr 0,nop,wscale 11], length 0
# TcpExtTCPChallengeACK: (from sidecar)
16:23:32.466309 IP (tos 0x0, ttl 64, id 19983, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [.], cksum 0x7c2c (incorrect -> 0x176f), ack 2082340714, win 32, options [nop,nop,TS val 2149331398 ecr 1248029014], length 0
# RST from 172.29.73.7.44410 (Conntrack Valid)
16:23:32.466320 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [R], cksum 0x0876 (correct), seq 2082340714, win 0, length 0
# SYN retrans
16:23:33.484037 IP (tos 0x0, ttl 64, id 6423, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0xeb1b), seq 3587723838, win 62720, options [mss 8960,sackOK,TS val 1249356834 ecr 0,nop,wscale 11], length 0
# syn/ack from   172.21.206.198.7777(sidecar)
16:23:33.484060 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 60)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [S.], cksum 0x7c34 (incorrect -> 0xa6d3), seq 3731074132, ack 3587723839, win 65483, options [mss 65495,sackOK,TS val 2149332416 ecr 1249356834,nop,wscale 11], length 0
# ack from 172.29.73.7.44410    
16:23:33.484072 IP (tos 0x0, ttl 64, id 6424, offset 0, flags [DF], proto TCP (6), length 52)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [.], cksum 0x43f5 (incorrect -> 0xeb72), ack 3731074133, win 31, options [nop,nop,TS val 1249356835 ecr 2149332416], length 0
# fin from 172.21.206.198.7777(sidecar, because upstream pod(172.21.206.198) not listen on 7777)
16:23:33.484498 IP (tos 0x0, ttl 64, id 49188, offset 0, flags [DF], proto TCP (6), length 52)
    172.21.206.198.7777 > 172.29.73.7.44410: Flags [F.], cksum 0x7c2c (incorrect -> 0xcf71), seq 1, ack 1, win 32, options [nop,nop,TS val 2149332416 ecr 1249356835], length 0
16:23:33.488011 IP (tos 0x0, ttl 64, id 6425, offset 0, flags [DF], proto TCP (6), length 52)
    172.29.73.7.44410 > 127.0.0.1.15001: Flags [.], cksum 0x43f5 (incorrect -> 0xeb6e), ack 2, win 31, options [nop,nop,TS val 1249356838 ecr 2149332416], length 0
```



## Skills




```bash
ssh $WORKER_NODE_OF_POD

export POD="fortio-server-0"
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
```


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
```