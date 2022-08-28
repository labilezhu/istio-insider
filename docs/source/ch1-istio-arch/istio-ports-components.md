
# Istio 端口 与 组件

Istio 的每个组件都监听一堆端口。对于初学者，可能很难弄明白每个端口的作用。这里，用 {ref}`图：Istio端口与组件` 说明 Istio 在默认的部署下，各组件的通讯端口和相关的功能。


:::{figure-md} 图：Istio端口与组件

<img src="istio-ports-components.assets/istio-ports-components.drawio.svg" alt="Istio端口与组件">

*图：Istio 端口与组件*  
:::
*[用 Draw.io 打开](https://app.diagrams.net/#Uhttps%3A%2F%2Fistio-insider.mygraphql.com%2Fzh_CN%2Flatest%2F_images%2Fistio-ports-components.drawio.svg)*

上图需要说明的是：
- istio-proxy 容器与 应用容器(app container) 共享同一 Linux `network namespace`。 
- `network namespace` 是内核内用于隔离多个不同网络配置的技术。其中一个配置就是 netfilter，即我们常说的 iptables。我们将在后面说说它的故事。

可以用以下方式查看监听的端口：

```bash

$ nsenter -n -t $PID_OF_ENVOY
$ ss -ln

u_str    LISTEN     etc/istio/proxy/SDS 34782                        * 0            users:(("pilot-agent",pid=3406,fd=13))                                             
u_str    LISTEN     etc/istio/proxy/XDS 34783                        * 0            users:(("pilot-agent",pid=3406,fd=16))                                             
u_str    ESTAB      etc/istio/proxy/XDS 1379729                      * 1379728      users:(("pilot-agent",pid=3406,fd=8))                                              
u_str    ESTAB                        * 1379728                      * 1379729      users:(("envoy",pid=3555,fd=37))                                                   
u_str    ESTAB      etc/istio/proxy/SDS 45274                        * 46319        users:(("pilot-agent",pid=3406,fd=15))                                             
u_str    ESTAB                        * 46319                        * 45274        users:(("envoy",pid=3555,fd=19))                                                   
tcp      LISTEN                 0.0.0.0:15021                  0.0.0.0:*            users:(("envoy",pid=3555,fd=40),("envoy",pid=3555,fd=34),("envoy",pid=3555,fd=22)) 
tcp      LISTEN                 0.0.0.0:15090                  0.0.0.0:*            users:(("envoy",pid=3555,fd=39),("envoy",pid=3555,fd=33),("envoy",pid=3555,fd=21)) 
tcp      LISTEN               127.0.0.1:15000                  0.0.0.0:*            users:(("envoy",pid=3555,fd=18))                                                   
tcp      LISTEN                 0.0.0.0:15001                  0.0.0.0:*            users:(("envoy",pid=3555,fd=41),("envoy",pid=3555,fd=35),("envoy",pid=3555,fd=31)) 
tcp      LISTEN               127.0.0.1:15004                  0.0.0.0:*            users:(("pilot-agent",pid=3406,fd=17))                                             
tcp      LISTEN                 0.0.0.0:15006                  0.0.0.0:*            users:(("envoy",pid=3555,fd=42),("envoy",pid=3555,fd=36),("envoy",pid=3555,fd=32)) 
tcp      ESTAB           172.21.206.227:40560            10.108.217.90:15012        users:(("pilot-agent",pid=3406,fd=19))                                             
tcp      ESTAB           172.21.206.227:43240            10.108.217.90:15012        users:(("pilot-agent",pid=3406,fd=14))                                             
tcp      LISTEN                       *:15020                        *:*            users:(("pilot-agent",pid=3406,fd=12))                                             
tcp      ESTAB                127.0.0.1:35256                127.0.0.1:15020        users:(("envoy",pid=3555,fd=43))                                                   
tcp      ESTAB                127.0.0.1:35238                127.0.0.1:15020        users:(("envoy",pid=3555,fd=20))                                                   
tcp      ESTAB       [::ffff:127.0.0.1]:15020       [::ffff:127.0.0.1]:35238        users:(("pilot-agent",pid=3406,fd=6))                                              
tcp      ESTAB       [::ffff:127.0.0.1]:15020       [::ffff:127.0.0.1]:35256        users:(("pilot-agent",pid=3406,fd=18))                                             
```