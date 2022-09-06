# Envoy 指标(草稿)

> 这节未开始编写。
> 以下只是本书的参考。

## Statistics Overview[¶](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/observability/statistics#statistics)

One of the primary goals of Envoy is to make the network understandable. Envoy emits a large number of statistics depending on how it is configured. Generally the statistics fall into three categories:

- **Downstream**: Downstream statistics relate to incoming connections/requests. They are emitted by listeners, the HTTP connection manager, the TCP proxy filter, etc.
- **Upstream**: Upstream statistics relate to outgoing connections/requests. They are emitted by connection pools, the router filter, the TCP proxy filter, etc.
- **Server**: Server statistics describe how the Envoy server instance is working. Statistics like server uptime or amount of allocated memory are categorized here.

A single proxy scenario typically involves both downstream and upstream statistics. The two types can be used to get a detailed picture of that particular network hop. Statistics from the entire mesh give a very detailed picture of each hop and overall network health. The statistics emitted are documented in detail in the operations guide.

As of the v2 API, Envoy has the ability to support custom, pluggable sinks. [A few standard sink implementations](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statssink) are included in Envoy. Some sinks also support emitting statistics with tags/dimensions.

Within Envoy and throughout the documentation, <mark>statistics are identified by a canonical string representation. The dynamic portions of these strings are stripped to become tags. Users can configure this behavior via [the Tag Specifier configuration](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier).</mark>

Envoy emits three types of values as statistics:

- **Counters**: Unsigned integers that only increase and never decrease. E.g., total requests.
- **Gauges**: Unsigned integers that both increase and decrease. E.g., currently active requests.
- **Histograms**: Unsigned integers that are part of a stream of values that are then aggregated by the collector to ultimately yield summarized percentile values. E.g., upstream request time.

Internally, counters and gauges are batched and periodically flushed to improve performance. Histograms are written as they are received. Note: what were previously referred to as timers have become histograms as the only difference between the two representations was the units.

- [v3 API reference](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/bootstrap/v3/bootstrap.proto#envoy-v3-api-field-config-bootstrap-v3-bootstrap-stats-sinks).







## Config Spec

> https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto



##### config.bootstrap.v3.Bootstrap[¶](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/bootstrap/v3/bootstrap.proto#config-bootstrap-v3-bootstrap)

[[config.bootstrap.v3.Bootstrap proto\]](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/config/bootstrap/v3/bootstrap.proto#L44)

Bootstrap [configuration overview](https://www.envoyproxy.io/docs/envoy/latest/configuration/overview/bootstrap#config-overview-bootstrap).

```json
{
  "node": {...},
  "static_resources": {...},
  "dynamic_resources": {...},
  "cluster_manager": {...},
  "hds_config": {...},
  "flags_path": ...,
  "stats_sinks": [],
  "stats_config": {...},
  "stats_flush_interval": {...},
  "stats_flush_on_admin": ...,
...
}
```



##### config.metrics.v3.StatsConfig[¶](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#config-metrics-v3-statsconfig)

```json
{
  "stats_tags": [],
  "use_all_default_tags": {...},
  "stats_matcher": {...},
  "histogram_bucket_settings": []
}
```

- stats_tags - 维度注入（label 注入）

  (**repeated** [config.metrics.v3.TagSpecifier](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier)) Each stat name is independently processed through these tag specifiers. When a tag is matched, the first capture group is not immediately removed from the name, so later [TagSpecifiers](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-tagspecifier) can also match that same portion of the match. After all tag matching is complete, a tag-extracted version of the name is produced and is used in stats sinks that represent tags, such as Prometheus.

- use_all_default_tags

  ([BoolValue](https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#boolvalue)) Use all default tag regexes specified in Envoy. These can be combined with custom tags specified in [stats_tags](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsconfig-stats-tags). They will be processed before the custom tags.

  > Note: If any default tags are specified twice, the config will be considered invalid.See [well_known_names.h](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/source/common/config/well_known_names.h) for a list of the default tags in Envoy.If not provided, the value is assumed to be true.

- stats_matcher

  ([config.metrics.v3.StatsMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-msg-config-metrics-v3-statsmatcher)) Inclusion/exclusion matcher for stat name creation. If not provided, all stats are instantiated as normal. Preventing the instantiation of certain families of stats can improve memory performance for Envoys running especially large configs.

  > Warning: Excluding stats may affect Envoy’s behavior in undocumented ways. See [issue #8771](https://github.com/envoyproxy/envoy/issues/8771) for more information. If any unexpected behavior changes are observed, please open a new issue immediately.

##### config.metrics.v3.StatsMatcher[¶](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#config-metrics-v3-statsmatcher)

[[config.metrics.v3.StatsMatcher proto\]](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/config/metrics/v3/stats.proto#L114)

Configuration for disabling stat instantiation.

```
{
  "reject_all": ...,
  "exclusion_list": {...},
  "inclusion_list": {...}
}
```

- reject_all

  ([bool](https://developers.google.com/protocol-buffers/docs/proto#scalar)) If `reject_all` is true, then all stats are disabled. If `reject_all` is false, then all stats are enabled.Precisely one of [reject_all](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-reject-all), [exclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-exclusion-list), [inclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-inclusion-list) must be set.

- exclusion_list

  ([type.matcher.v3.ListStringMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-msg-type-matcher-v3-liststringmatcher)) Exclusive match. All stats are enabled except for those matching one of the supplied StringMatcher protos.Precisely one of [reject_all](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-reject-all), [exclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-exclusion-list), [inclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-inclusion-list) must be set.

- inclusion_list

  ([type.matcher.v3.ListStringMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-msg-type-matcher-v3-liststringmatcher)) Inclusive match. No stats are enabled except for those matching one of the supplied StringMatcher protos.Precisely one of [reject_all](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-reject-all), [exclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-exclusion-list), [inclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-inclusion-list) must be set.

Precisely one of [reject_all](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-reject-all), [exclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-exclusion-list), [inclusion_list](https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/metrics/v3/stats.proto#envoy-v3-api-field-config-metrics-v3-statsmatcher-inclusion-list) must be set.

##### type.matcher.v3.ListStringMatcher[¶](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#type-matcher-v3-liststringmatcher)

[[type.matcher.v3.ListStringMatcher proto\]](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/type/matcher/v3/string.proto#L72)

Specifies a list of ways to match a string.

```
{
  "patterns": []
}
```

- patterns

  (**repeated** [type.matcher.v3.StringMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-msg-type-matcher-v3-stringmatcher), *REQUIRED*)

##### type.matcher.v3.StringMatcher[¶](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#type-matcher-v3-stringmatcher)

[[type.matcher.v3.StringMatcher proto\]](https://github.com/envoyproxy/envoy/blob/255af425e1d51066cc8b69a39208b70e18d07073/api/envoy/type/matcher/v3/string.proto#L20)

Specifies the way to match a string.

```
{
  "exact": ...,
  "prefix": ...,
  "suffix": ...,
  "safe_regex": {...},
  "contains": ...,
  "ignore_case": ...
}
```

- exact

  ([string](https://developers.google.com/protocol-buffers/docs/proto#scalar)) The input string must match exactly the string specified here.Examples:`abc` only matches the value `abc`.Precisely one of [exact](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-exact), [prefix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-prefix), [suffix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-suffix), [safe_regex](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-safe-regex), [contains](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-contains) must be set.

- prefix

  ([string](https://developers.google.com/protocol-buffers/docs/proto#scalar)) The input string must have the prefix specified here. Note: empty prefix is not allowed, please use regex instead.Examples:`abc` matches the value `abc.xyz`Precisely one of [exact](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-exact), [prefix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-prefix), [suffix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-suffix), [safe_regex](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-safe-regex), [contains](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-contains) must be set.

- suffix

  ([string](https://developers.google.com/protocol-buffers/docs/proto#scalar)) The input string must have the suffix specified here. Note: empty prefix is not allowed, please use regex instead.Examples:`abc` matches the value `xyz.abc`Precisely one of [exact](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-exact), [prefix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-prefix), [suffix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-suffix), [safe_regex](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-safe-regex), [contains](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-contains) must be set.

- safe_regex

  ([type.matcher.v3.RegexMatcher](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/regex.proto#envoy-v3-api-msg-type-matcher-v3-regexmatcher)) The input string must match the regular expression specified here.Precisely one of [exact](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-exact), [prefix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-prefix), [suffix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-suffix), [safe_regex](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-safe-regex), [contains](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-contains) must be set.

- contains

  ([string](https://developers.google.com/protocol-buffers/docs/proto#scalar)) The input string must have the substring specified here. Note: empty contains match is not allowed, please use regex instead.Examples:`abc` matches the value `xyz.abc.def`Precisely one of [exact](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-exact), [prefix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-prefix), [suffix](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-suffix), [safe_regex](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-safe-regex), [contains](https://www.envoyproxy.io/docs/envoy/latest/api-v3/type/matcher/v3/string.proto#envoy-v3-api-field-type-matcher-v3-stringmatcher-contains) must be set.

- ignore_case

  ([bool](https://developers.google.com/protocol-buffers/docs/proto#scalar)) If true, indicates the exact/prefix/suffix/contains matching should be case insensitive. This has no effect for the safe_regex match. For example, the matcher `data` will match both input string `Data` and `data` if set to true.

## Statistics README

## cluster_manager/cluster_stats

> https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats

## http_conn_man/stats

> https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/stats#config-http-conn-man-stats

可以认为，这是 downstream 的 HTTP(L7) 层的指标。

## listeners/stats

可以认为，这是 downstream 的 L4 层的指标。

> https://www.envoyproxy.io/docs/envoy/latest/configuration/listeners/stat



## server

> https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/statistics
