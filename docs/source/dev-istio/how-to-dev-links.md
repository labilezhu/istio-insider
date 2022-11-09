# Istio 开发入门参考列表

## 代码说明

- [Using the Code Base](https://github.com/istio/istio/wiki/Using-the-Code-Base)

## 设计文档

> - [Istio Community Google Driver - Design Docs](https://drive.google.com/drive/folders/0ADmbrU7ueGOUUk9PVA)
>
> - [https://github.com/istio/community/blob/master/CONTRIBUTING.md#design-documents](https://github.com/istio/community/blob/master/CONTRIBUTING.md#design-documents)

Any substantial design deserves a design document. Design documents are written with Google Docs and should be shared with the community by adding the doc to our [shared Drive](https://drive.google.com/corp/drive/folders/0ADmbrU7ueGOUUk9PVA) and sending a note to the appropriate working group to let people know the doc is there. To get write access to the drive, you'll need to be a [member](https://github.com/istio/community/blob/master/ROLES.md#member) of the Istio organization.

Anybody can access the shared Drive for reading. To get access to comment, join the [istio-team-drive-access@](https://groups.google.com/forum/#!forum/istio-team-drive-access) group. Once you've done that, head to the [shared Drive](https://drive.google.com/corp/drive/folders/0ADmbrU7ueGOUUk9PVA) and behold all the docs.

When documenting a new design, we recommend a 2-step approach:

1. Use the short-form [RFC template](https://docs.google.com/document/d/1ewJoCcw5-04crH-M0xw4zFxz1cfwVCPnNyW4K3m4Yyc/template/preview) to outline your ideas and get early feedback.
2. Once you have received sufficient feedback and consensus, you may use the longer-form [design doc template](https://docs.google.com/document/d/16FLQK8uhhic1ovKnnOG3OXJjFKs2aHnSmbximidpKwM/template/preview) to specify and discuss your design in more details.

To use either template, open the template and select "Use Template" in order to bootstrap your document.

## 开发环境

 - [Preparing for Development](https://github.com/istio/istio/wiki/Preparing-for-Development)

## Istio 项目健康监控

The CNCF maintains a large number of dashboards helping us understand the overall health of the Istio project. Head to [https://istio.teststats.cncf.io](https://istio.teststats.cncf.io) for the goodies.



## 论坛

[https://discuss.istio.io/latest](https://discuss.istio.io/latest)





## 参与开发 Istio

 - [Get involved](https://istio.io/latest/get-involved/)
 - [开通开发文档协同 Google Driver](https://groups.google.com/g/istio-team-drive-access)
 - [开发文档协同 Google Driver](https://drive.google.com/drive/folders/0ADmbrU7ueGOUUk9PVA)



### 工作组

> [https://github.com/istio/community/blob/master/WORKING-GROUPS.md](https://github.com/istio/community/blob/master/WORKING-GROUPS.md)

Most community activity is organized into _working groups_.

- [Working group meetings](https://github.com/istio/community/blob/master/WORKING-GROUPS.md#working-group-meetings)
- [Working group leads](https://github.com/istio/community/blob/master/WORKING-GROUPS.md#working-group-leads)
- [Getting in touch](https://github.com/istio/community/blob/master/WORKING-GROUPS.md#getting-in-touch)

Working groups follow the [contributing](https://github.com/istio/community/blob/master/CONTRIBUTING.md) guidelines although each of these groups may operate a little differently depending on their needs and workflow.

When the need arises, a new working group can be created, please post to [technical-oversight-committee](https://discuss.istio.io/c/technical-oversight-committee) working group if you think a new group is necessary.

The working groups generate design docs which are kept in a shared Google Drive. Anybody can access the drive for reading and commenting. To get access simply join the [istio-team-drive-access@](https://groups.google.com/forum/#!forum/istio-team-drive-access) group. Once you've done that, head to the [Community Drive](https://drive.google.com/drive/folders/0ADmbrU7ueGOUUk9PVA) and behold all the docs.

The current working groups are:



| Group                    | Design Docs     | Discussion Forum       | Slack Channel            | Meeting Notes | Meeting Link                                    | Meeting Recordings | Description                                                  |
| ------------------------ | --------------- | ---------------------- | ------------------------ | ------------- | ----------------------------------------------- | ------------------ | ------------------------------------------------------------ |
| Docs                     | Folder          | Forum                  | #docs                    | Notes         | Hangouts Meet                                   | n/a                | User docs, information architecture, istio.io infrastructure |
| Environments             | Folder          | Forum                  | #environments            | Notes         | Hangouts Meet                                   | YouTube            | Raw VM support, Hybrid Mesh, Mac/Windows support, Cloud Foundry integration |
| Networking               | Folder          | Forum                  | #networking              | Notes         | Hangouts Meet                                   | YouTube            | Traffic Management, TCP Support, Additional L7 protocols, Proxy injection |
| Extensions and Telemetry | Folder          | Forum                  | #extensions-telemetry    | Notes         | Main Group Hangouts Meet, Wasm SIG Hangout Meet | YouTube            | WebAssembly based extensibility, Istio extensions for features such as Rate Limiting, Tracing, Monitoring, Logging |
| Product Security         | Folder          | Report a vulnerability |                          | Notes         | Hangouts Meet                                   |                    | Product Security: Vulnerability, security guidelines, threats |
| Security                 | Folder          | Forum                  | #security                | Notes         | Hangouts Meet                                   | YouTube            | Service-to-service Auth, Identity/CA/SecretStore plugins, Identity Federation, End User Auth, Authority Delegation, Auditing |
| Test and Release         | Folder          | Forum                  | #test-and-release        | Notes         | Hangouts Meet                                   | YouTube            | Build, test, release                                         |
| User Experience          | UX Config (old) | Forum                  | #user-experience #config | Notes         | WebEx                                           | YouTube            | User experience across Istio, API and CLI guidelines and support |



