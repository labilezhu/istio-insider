


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
```

```bash
export netshoot_0=172.21.206.198
export fortio_server_l2_0=172.29.73.7

```

### env

```log
➜  ~ uname -a 
Linux worknode5 5.4.0-137-generic #154-Ubuntu SMP Thu Jan 5 17:03:22 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux
➜  ~ cat  /etc/os-release 
NAME="Ubuntu"
VERSION="20.04.2 LTS (Focal Fossa)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 20.04.2 LTS"
VERSION_ID="20.04"
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
VERSION_CODENAME=focal
UBUNTU_CODENAME=focal

➜  ~ cat /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst
cat: /proc/sys/net/netfilter/nf_conntrack_tcp_ignore_invalid_rst: No such file or directory

➜  ~ cat /proc/sys/net/netfilter/nf_conntrack_tcp_be_liberal        
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


root@fortio-server-0:/home/labile# 

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
Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-0: Fri Feb 10 06:45:02 2023

tcp      6 55 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=39644 dport=7777 src=172.21.206.198 dst=172.21.206.199 sport=7777 dport=39644 [ASSURED] mark=0 use=1
tcp      6 55 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.21.206.199 sport=15001 dport=44410 [ASSURED] mark=0 use=1
```

```log
Every 2.0s: ss -naoep | egrep '44410|7777'                                                                                                                                                            fortio-server-0: Fri Feb 10 06:45:30 2023

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:39644                                      172.21.206.198:7777                   users:(("envoy",pid=11084,fd=39)) uid:1337 ino:244840 sk:5b -->

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:44410                                      172.21.206.198:7777                   users:(("nc",pid=47535,fd=3)) ino:244838 sk:5c -->

tcp   FIN-WAIT-2  0       0                                           127.0.0.1:15001                                      172.21.206.199:44410                  users:(("envoy",pid=11084,fd=37)) uid:1337 ino:244839 sk:5d <--

```

###  3. after 60s, conntrack table CLOSE_WAIT entry timeout

```log
Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-0: Fri Feb 10 06:46:45 2023
```

### 4. pod main-app(nc) close connection - FIN not reach peer


Pod main-app(nc) close connection - FIN not reach peer. So  socket `127.0.0.1:15001  172.21.206.199:44410    users:(("envoy"` stuck in `FIN-WAIT-2`.

```bash

root@fortio-server-0:/home/labile# nc -p 44410 $netshoot_0 7777
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

Every 2.0s: conntrack -L 2>&1 | egrep "44410|172.21.206.198"                                                                                                                                          fortio-server-0: Fri Feb 10 06:56:27 2023

tcp      6 34 CLOSE_WAIT src=172.21.206.199 dst=172.21.206.198 sport=44410 dport=7777 src=127.0.0.1 dst=172.21.206.199 sport=15001 dport=44410 [ASSURED] mark=0 use=1

```


```
Every 2.0s: ss -naoep | egrep '44410|7777'                                                                                                                                                            fortio-server-0: Fri Feb 10 07:14:46 2023

tcp   CLOSE-WAIT  0       0                                      172.21.206.199:44410                                      172.21.206.198:7777                   users:(("nc",pid=75940,fd=3)) ino:508121 sk:654 -->

tcp   FIN-WAIT-2  0       0                                           127.0.0.1:15001                                      172.21.206.199:44410                  timer:(timewait,48sec,0) ino:0 sk:655
```

