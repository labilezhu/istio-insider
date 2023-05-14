FROM docker.io/istio/proxyv2:1.17.2

COPY envoy /usr/local/bin/envoy

RUN apt-get -y update \
  && apt-get install -y gdbserver
