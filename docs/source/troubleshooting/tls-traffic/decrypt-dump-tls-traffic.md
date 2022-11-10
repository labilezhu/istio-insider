# Decrypt and Dump TLS Traffic

## TLS key log feature

- [TLS key log feature #19182](https://github.com/envoyproxy/envoy/pull/19182)
- [export tls key by runtime configuration #17906](https://github.com/envoyproxy/envoy/pull/17906)
- [TLS keylog support #10377](https://github.com/envoyproxy/envoy/issues/10377)

Now more and more traffic will use TLS to encrypt the traffic for security consideration. When there are some network issues, we always use tcpdump tool to capture the packets to analyze the first hand traffic data to find the root cause. Although there are some logs, the first hand data (packets) is the most reliable one.

Use `SSLKEYLOGFILE`.

### Envoy Key Log 配置


- [Envoy Key Log 配置](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/tls/v3/tls.proto#:~:text=TLS%20handshaking%20behavior.-,key_log,-(extensions.transport_sockets)
- [Envoy Key Log 配置 envoy-v3-api-msg-extensions-transport-sockets-tls-v3-tlskeylog](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/tls/v3/tls.proto#envoy-v3-api-msg-extensions-transport-sockets-tls-v3-tlskeylog)

#### extensions.transport\_sockets.tls.v3.TlsKeyLog

[\[extensions.transport\_sockets.tls.v3.TlsKeyLog proto\]](https://github.com/envoyproxy/envoy/blob/f4144e8b02181d927fe4bea5eba0e95316b5ef7a/api/envoy/extensions/transport_sockets/tls/v3/tls.proto#L129)

TLS key log configuration. The key log file format is “format used by NSS for its SSLKEYLOGFILE debugging output” (text taken from openssl man page)

```
{
 "path": ...,
 "local\_address\_range": \[\],
 "remote\_address\_range": \[\]
}
```

- path

([string](https://developers.google.com/protocol-buffers/docs/proto#scalar), _REQUIRED_) The path to save the TLS key log.

- local\_address\_range

(**repeated** [config.core.v3.CidrRange](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/address.proto#envoy-v3-api-msg-config-core-v3-cidrrange)) The local IP address that will be used to filter the connection which should save the TLS key log If it is not set, any local IP address will be matched.

- remote\_address\_range

(**repeated** [config.core.v3.CidrRange](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/core/v3/address.proto#envoy-v3-api-msg-config-core-v3-cidrrange)) The remote IP address that will be used to filter the connection which should save the TLS key log If it is not set, any remote IP address will be matched.

## Decryption Tools

- [Wireshark using Key Log File](https://wiki.wireshark.org/TLS#:~:text=supplied%20via%20the-,Key%20Log%20File,-.%20The%20pre%2Dmaster)
- [tshark using key Log File(SSLKEYLOGFILE)](https://tshark.dev/export/export_tls/)



## Key Log Format

>  [NSS Key Log Format](https://firefox-source-docs.mozilla.org/security/nss/legacy/key_log_format/index.html)



Key logs can be written by NSS so that external programs can decrypt TLS connections. Wireshark 1.6.0 and above can use these log files to decrypt packets. You can tell Wireshark where to find the key file via *Edit→Preferences→Protocols→TLS→(Pre)-Master-Secret log filename*.

Key logging is enabled by setting the environment variable `SSLKEYLOGFILE` to point to a file. Note: starting with [NSS 3.24 release notes](https://firefox-source-docs.mozilla.org/security/nss/legacy/nss_releases/nss_3.24_release_notes/index.html#mozilla-projects-nss-nss-3-24-release-notes) (used by Firefox 48 and 49 only), the `SSLKEYLOGFILE` approach is disabled by default for optimized builds using the Makefile (those using gyp via `build.sh` are *not* affected). Distributors can re-enable it at compile time though (using the `NSS_ALLOW_SSLKEYLOGFILE=1` make variable) which is done for the official Firefox binaries. (See [bug 1188657](https://bugzilla.mozilla.org/show_bug.cgi?id=1188657).) Notably, Debian does not have this option enabled, see [Debian bug 842292](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=842292).

This key log file is a series of lines. Comment lines begin with a sharp character (‘#’) and are ignored. Secrets follow the format `<Label> <space> <ClientRandom> <space> <Secret>` where:

- `<Label>` describes the following secret.
- `<ClientRandom>` is 32 bytes Random value from the Client Hello message, encoded as 64 hexadecimal characters.
- `<Secret>` depends on the Label (see below).

The following labels are defined, followed by a description of the secret:

- `RSA`: 48 bytes for the premaster secret, encoded as 96 hexadecimal characters (removed in NSS 3.34)
- `CLIENT_RANDOM`: 48 bytes for the master secret, encoded as 96 hexadecimal characters (for SSL 3.0, TLS 1.0, 1.1 and 1.2)
- `CLIENT_EARLY_TRAFFIC_SECRET`: the hex-encoded early traffic secret for the client side (for TLS 1.3)
- `CLIENT_HANDSHAKE_TRAFFIC_SECRET`: the hex-encoded handshake traffic secret for the client side (for TLS 1.3)
- `SERVER_HANDSHAKE_TRAFFIC_SECRET`: the hex-encoded handshake traffic secret for the server side (for TLS 1.3)
- `CLIENT_TRAFFIC_SECRET_0`: the first hex-encoded application traffic secret for the client side (for TLS 1.3)
- `SERVER_TRAFFIC_SECRET_0`: the first hex-encoded application traffic secret for the server side (for TLS 1.3)
- `EARLY_EXPORTER_SECRET`: the hex-encoded early exporter secret (for TLS 1.3).
- `EXPORTER_SECRET`: the hex-encoded exporter secret (for TLS 1.3)

The `RSA` form allows ciphersuites using RSA key-agreement to be logged and was the first form supported by Wireshark 1.6.0. It has been superseded by `CLIENT_RANDOM` which also works with other key-agreement algorithms (such as those based on Diffie-Hellman) and is supported since Wireshark 1.8.0.

The TLS 1.3 lines are supported since NSS 3.34 ([bug 1287711](https://bugzilla.mozilla.org/show_bug.cgi?id=1287711)) and Wireshark 2.4 (`EARLY_EXPORTER_SECRET` exists since NSS 3.35, [bug 1417331](https://bugzilla.mozilla.org/show_bug.cgi?id=1417331)). The size of the hex-encoded secret depends on the selected cipher suite. It is 64, 96 or 128 characters for SHA256, SHA384 or SHA512 respectively.



## Ref

- [curl support SSLKEYLOGFILE](https://everything.curl.dev/usingcurl/tls/sslkeylogfile)
- [Get Istio pod's private key](https://blog.bossylobster.com/2020/09/istio-workload-secrets.html)









