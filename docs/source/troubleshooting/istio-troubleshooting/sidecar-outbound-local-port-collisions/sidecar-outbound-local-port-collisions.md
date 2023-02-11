
# Story


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






## New connection timeout

### pod main-app(nc) build connection on same ephemeral port

#### 5.1 connect timed out by collision ephemeral port



![](./5-1-connect-timed-out-by-collision-ephemeral-port.drawio.svg)



```bash
fortio-server-l2-0:/ # nc -p 44410 172.21.206.198 7777 #pid=144426

fortio-server-l2-0:/ # ss -naoep | egrep '44410|7777'

tcp   SYN-SENT    0  1  172.29.73.7:44410    172.21.206.198:7777         users:(("nc",pid=144426,fd=3)) timer:(on,1.684ms,2) ino:2024378629 sk:aa4e2 <->
tcp   FIN-WAIT-2  0  0     127.0.0.1:15001  172.29.73.7:44410        users:(("envoy",pid=51435,fd=121)) uid:201507 ino:2023763691 sk:aa125 <--

#tcp   CLOSE-WAIT  0  0  172.29.73.7:38076    172.21.206.198:7777         users:(("envoy",pid=51435,fd=135)) uid:201507 ino:2023763692 sk:aa123 -->
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

##### 5.1.1 Java to service connect timed out(HTTP)

precondition: have a half-open FIN_WAIT2 socket on port 38120

![](./5-1-1-java-connect-timed-out-by-collision-ephemeral-port.drawio.svg)





```bash
fortio-server-l2-0:/ cd /tmp
cat <<"EOF" > /tmp/Main.java
...
EOF
javac Main.java


export eric_idm_client_ClusterIP=10.96.94.44
export addressPrefix=$eric_idm_client_ClusterIP
export threadCount=1
export connectTimeout=10000
export keepLoopSocketOpenMilliSec=10
export closeByRST=true
java Main $addressPrefix $threadCount $connectTimeout $keepLoopSocketOpenMilliSec $closeByRST

...Runing a long time....

connect IOException:, localPort:-1, exceptionMsg: connect timed out
java.net.SocketTimeoutException: connect timed out
   at java.net.PlainSocketImpl.socketConnect(Native Method)
   at java.net.AbstractPlainSocketImpl.doConnect(AbstractPlainSocketImpl.java:350)
   at java.net.AbstractPlainSocketImpl.connectToAddress(AbstractPlainSocketImpl.java:206)
   at java.net.AbstractPlainSocketImpl.connect(AbstractPlainSocketImpl.java:188)
   at java.net.SocksSocketImpl.connect(SocksSocketImpl.java:392)
   at java.net.Socket.connect(Socket.java:607)
   at Main$Task.call(Main.java:55)
   at Main$Task.call(Main.java:27)
   at java.util.concurrent.FutureTask.run(FutureTask.java:266)
   at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
   at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
   at java.lang.Thread.run(Thread.java:750)

```



```bash
fortio-server-l2-0:/home/eccd # sudo tcpdump -i lo -n -v "port 38120"       
tcpdump: listening on lo, link-type EN10MB (Ethernet), capture size 262144 bytes
15:09:24.112919 IP (tos 0x0, ttl 64, id 52558, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.38120 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x9cff), seq 2101091510, win 62720, options [mss 8960,sackOK,TS val 3391168843 ecr 0,nop,wscale 11], length 0

# TcpExtTCPChallengeACK: (from sidecar)
15:09:24.112939 IP (tos 0x0, ttl 64, id 17799, offset 0, flags [DF], proto TCP (6), length 52)
    10.96.94.44.8080 > 172.29.73.7.38120: Flags [.], cksum 0x2d80 (incorrect -> 0x1d17), ack 4204570456, win 32, options [nop,nop,TS val 2231283044 ecr 1330103382], length 0
    
15:09:25.132029 IP (tos 0x0, ttl 64, id 52559, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.38120 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x9904), seq 2101091510, win 62720, options [mss 8960,sackOK,TS val 3391169862 ecr 0,nop,wscale 11], length 0
15:09:25.132067 IP (tos 0x0, ttl 64, id 17800, offset 0, flags [DF], proto TCP (6), length 52)
    10.96.94.44.8080 > 172.29.73.7.38120: Flags [.], cksum 0x2d80 (incorrect -> 0x191b), ack 1, win 32, options [nop,nop,TS val 2231284064 ecr 1330103382], length 0
15:09:27.148043 IP (tos 0x0, ttl 64, id 52560, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.38120 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x9124), seq 2101091510, win 62720, options [mss 8960,sackOK,TS val 3391171878 ecr 0,nop,wscale 11], length 0
15:09:27.148073 IP (tos 0x0, ttl 64, id 17801, offset 0, flags [DF], proto TCP (6), length 52)
    10.96.94.44.8080 > 172.29.73.7.38120: Flags [.], cksum 0x2d80 (incorrect -> 0x113b), ack 1, win 32, options [nop,nop,TS val 2231286080 ecr 1330103382], length 0
15:09:31.308038 IP (tos 0x0, ttl 64, id 52561, offset 0, flags [DF], proto TCP (6), length 60)
    172.29.73.7.38120 > 127.0.0.1.15001: Flags [S], cksum 0x43fd (incorrect -> 0x80e4), seq 2101091510, win 62720, options [mss 8960,sackOK,TS val 3391176038 ecr 0,nop,wscale 11], length 0
15:09:31.308072 IP (tos 0x0, ttl 64, id 17802, offset 0, flags [DF], proto TCP (6), length 52)
    10.96.94.44.8080 > 172.29.73.7.38120: Flags [.], cksum 0x2d80 (incorrect -> 0x00fb), ack 1, win 32, options [nop,nop,TS val 2231290240 ecr 1330103382], length 0


fortio-server-l2-0:/home/eccd # sudo tcpdump -i eth0 -n -v "host 10.96.94.44"
# RST from 172.29.73.7.38120 (Conntrack Invalid)
15:09:24.112956 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.38120 > 10.96.94.44.8080: Flags [R], cksum 0x2c19 (correct), seq 4204570456, win 0, length 0
15:09:25.132084 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.38120 > 10.96.94.44.8080: Flags [R], cksum 0x2c19 (correct), seq 4204570456, win 0, length 0
15:09:27.148089 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.38120 > 10.96.94.44.8080: Flags [R], cksum 0x2c19 (correct), seq 4204570456, win 0, length 0
15:09:31.308090 IP (tos 0x0, ttl 64, id 0, offset 0, flags [DF], proto TCP (6), length 40)
    172.29.73.7.38120 > 10.96.94.44.8080: Flags [R], cksum 0x2c19 (correct), seq 4204570456, win 0, length 0


[Sun Feb  5 15:08:47 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=10.96.94.44 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=38120 DPT=8080 WINDOW=0 RES=0x00 RST URGP=0 
[Sun Feb  5 15:08:48 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=10.96.94.44 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=38120 DPT=8080 WINDOW=0 RES=0x00 RST URGP=0 
[Sun Feb  5 15:08:50 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=10.96.94.44 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=38120 DPT=8080 WINDOW=0 RES=0x00 RST URGP=0 
[Sun Feb  5 15:08:54 2023] ISTIO_OUTBOUND_INVALID: IN= OUT=eth0 SRC=172.29.73.7 DST=10.96.94.44 LEN=40 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=38120 DPT=8080 WINDOW=0 RES=0x00 RST URGP=0 
```



#### 5.2 connect by collision ephemeral port but seq-no happens to be in the TCP window of the old connection

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