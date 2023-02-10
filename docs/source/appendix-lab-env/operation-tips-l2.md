


```bash
ssh $WORKER_NODE_OF_POD

sudo su

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


```

```bash
nsenter -t $PID -n -u
export netshoot_0=172.21.206.198
export fortio_server_l2_0=172.29.73.7

```

### env


```log
fortio-server-l2-0:/home/labile # uname -r
5.14.21-150400.24.21-default


labile@sle:~> cat /etc/os-release
NAME="SLES"
VERSION="15-SP4"
VERSION_ID="15.4"
PRETTY_NAME="SUSE Linux Enterprise Server 15 SP4"

fortio-server-l2-0:/home/labile # cat /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst
0
fortio-server-l2-0:/home/labile # cat /proc/sys/net/netfilter/nf_conntrack_tcp_be_liberal        
0

```


```log
uname -rr                                                                 
5.3.18-150300.59.71.2.24366.1.PTF.1195504-default

eccd@control-plane-n4-vpod1-master-n3:~> cat /etc/os-release 
NAME="SLES"
VERSION="15-SP3"
VERSION_ID="15.3"
PRETTY_NAME="SUSE Linux Enterprise Server 15 SP3"


cat /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst
0
cat /proc/sys/net/netfilter/nf_conntrack_tcp_be_liberal
0
```

#### TCP service


```bash
netshoot-0:~# nc -k -l 7777
```




###  1. TCPProxy: connections ESTABLISHED

```bash
export netshoot_0=172.21.206.198
export fortio_server_l2_0=172.29.73.7


root@fortio-server-l2-0:/home/labile# 

watch -d "nstat -zas | egrep -i 'retr|cha' "


watch -d "conntrack -L 2>&1 | egrep \"44410|$netshoot_0\""

watch -d "ss -naoep | egrep '44410|7777'"

nc -p 44410 $netshoot_0 7777
```

###  2. TCPProxy: upstream service active close connection

```bash
netshoot-0:~# nc -k -l 7777
^C

```


```log
Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-l2-0: Fri Feb 10 06:45:02 2023

tcp      6 55 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=39644 dport=7777 src=172.21.206.198 dst=172.21.206.199 sport=7777 dport=39644 [ASSURED] mark=0 use=1
tcp      6 55 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.21.206.199 sport=15001 dport=44410 [ASSURED] mark=0 use=1
```

```log
Every 2.0s: ss -naoep | egrep '44410|7777'                                                                                                                                                            fortio-server-l2-0: Fri Feb 10 06:45:30 2023

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:39644                                      172.21.206.198:7777                   users:(("envoy",pid=11084,fd=39)) uid:1337 ino:244840 sk:5b -->

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:44410                                      172.21.206.198:7777                   users:(("nc",pid=47535,fd=3)) ino:244838 sk:5c -->

tcp   FIN-WAIT-2  0       0                                           127.0.0.1:15001                                      172.21.206.199:44410                  users:(("envoy",pid=11084,fd=37)) uid:1337 ino:244839 sk:5d <--

```

###  3. after 60s, conntrack table CLOSE_WAIT entry timeout

```log
Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-l2-0: Fri Feb 10 06:46:45 2023
```

### 4. pod main-app(nc) close connection - FIN not reach peer


Pod main-app(nc) close connection - FIN not reach peer. So  socket `127.0.0.1:15001  172.21.206.199:44410    users:(("envoy"` stuck in `FIN-WAIT-2`.

```bash

root@fortio-server-l2-0:/home/labile# nc -p 44410 $netshoot_0 7777
^C


watch -d "nstat -zas | egrep -i 'retr|cha' "

TcpRetransSegs                  10 ￪                0.0
TcpExtTCPLostRetransmit         7 ￪                 0.0

```

## New connection timeout

### pod main-app(nc) build connection on same ephemeral port

#### 5.1 connect timed out by collision ephemeral port

```bash
nc -p 44410 $netshoot_0 7777

Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-l2-0: Fri Feb 10 06:56:27 2023

tcp      6 34 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.21.206.199 sport=15001 dport=44410 [ASSURED] mark=0 use=1

```


```
Every 2.0s: ss -naoep | egrep '44410|7777'                                                                                                                                                            fortio-server-l2-0: Fri Feb 10 07:14:46 2023

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:44410                                      172.21.206.198:7777                   users:(("nc",pid=75940,fd=3)) ino:508121 sk:654 -->

tcp   FIN-WAIT-2  0       0                                           127.0.0.1:15001                                      172.21.206.199:44410                  timer:(timewait,48sec,0) ino:0 sk:655
```

