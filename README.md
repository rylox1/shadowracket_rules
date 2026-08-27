# Shadowrocket 规则集

本仓库把 [GMOogway/shadowrocket-rules](https://github.com/GMOogway/shadowrocket-rules) 提供的三个 Shadowrocket 模块转换为 `RULE-SET` 可用的规则集:

- `direct.list`
- `proxy.list`
- `reject.list`

来源模块:

- `https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_direct_list.module`
- `https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_proxy_list.module`
- `https://raw.githubusercontent.com/GMOogway/shadowrocket-rules/master/sr_reject_list.module`

转换由 GitHub Actions 每天自动执行,也可以在 Actions 页面手动运行。

## Shadowrocket 引用地址

### 黑名单模式（无需配置 `direct.list`）

未命中的请求默认直连,只将代理列表中的域名交给代理,并拦截广告或追踪域名:

```ini
[Rule]
GEOIP,LAN,DIRECT

RULE-SET,https://raw.githubusercontent.com/rylox1/shadowracket_rules/main/reject.list,REJECT
RULE-SET,https://raw.githubusercontent.com/rylox1/shadowracket_rules/main/proxy.list,PROXY

FINAL,DIRECT
```

黑名单模式不需要配置 `direct.list`,因为 `FINAL,DIRECT` 已经会让未命中的请求直连。自定义规则应放在上游规则集之前。

### 白名单模式

未命中的请求默认代理,使用 `direct.list` 指定需要直连的域名:

```ini
[Rule]
GEOIP,LAN,DIRECT

RULE-SET,https://raw.githubusercontent.com/rylox1/shadowracket_rules/main/reject.list,REJECT
RULE-SET,https://raw.githubusercontent.com/rylox1/shadowracket_rules/main/direct.list,DIRECT

GEOIP,CN,DIRECT
FINAL,PROXY
```

白名单模式通常不需要配置 `proxy.list`,因为 `FINAL,PROXY` 已经会代理未命中的请求。若希望显式维护代理规则,可以在 `direct.list` 后追加:

```ini
RULE-SET,https://raw.githubusercontent.com/rylox1/shadowracket_rules/main/proxy.list,PROXY
```

规则按从上到下匹配,命中后停止。上面的示例把拦截规则放在直连规则之前,这样同时出现在两个列表中的域名会优先拦截。

## 手动更新

打开 GitHub 仓库的 **Actions** > **更新 Shadowrocket 规则集** > **Run workflow**。

工作流会先下载三个上游模块并校验规则数量,全部成功后才替换 `.list` 文件。上游下载失败或规则数量异常时不会提交空规则集。

本地备份文件 `rule.conf.bak` 不会提交。
