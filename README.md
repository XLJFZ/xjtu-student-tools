# XJTU Student Tools

**西安交通大学学生工具集** —— 面向西安交通大学学生的非官方开源工具集合。

> **非官方项目。** 本仓库由学生个人维护，与西安交通大学官方无隶属、授权或合作关系。

在线入口：<https://xljfz.github.io/xjtu-student-tools/>

## 项目定位

本仓库是一个**门户 / 项目索引 / 使用入口**，不是 monorepo，也不包含任何工具的业务代码。

- 本仓库只负责：导航、项目介绍、文档入口与统一品牌
- 每个工具都拥有自己的独立仓库、独立 release 与独立版本号
- 本仓库不复制、不内联任何子项目的源码
- 本站不接收、不存储、不处理账号、密码、Cookie、Token 或统一身份认证凭据

## Tools

| 工具 | 说明 | 状态 | 仓库 |
| --- | --- | --- | --- |
| 课程表同步 | 将 eHall 课程表转换为 ICS 日历，方便同步到手机、电脑和系统日历 | 开发中（尚无可用版本） | [xjtu-timetable-calendar](https://github.com/XLJFZ/xjtu-timetable-calendar) |
| 思源学堂工具 | 下载思源学堂课程资源与课程回放，并提供更可靠的资源管理和下载流程 | 可用 | [xjtu-siyuanxuetang-grab](https://github.com/XLJFZ/xjtu-siyuanxuetang-grab) |

### 课程表同步

状态：**开发中**

将西安交通大学 eHall 个人课表导出为标准 iCalendar（`.ics`）文件，便于导入手机、电脑或其他日历应用。

- 仓库：<https://github.com/XLJFZ/xjtu-timetable-calendar>
- 该仓库目前仅包含项目说明，尚无可用版本或 release

### 思源学堂工具

状态：**可用**

下载思源学堂课程资源与课程回放，并提供更可靠的资源管理和下载流程。

- 仓库：<https://github.com/XLJFZ/xjtu-siyuanxuetang-grab>
- 使用说明：<https://xljfz.github.io/xjtu-siyuanxuetang-grab/>

## 为什么拆成多个仓库

- **生命周期不同**：各工具的开发、维护与停止计划互相独立
- **release 独立**：各自发布版本，不需要为门户统一版本号
- **issue 独立**：问题追踪归属到具体项目，避免混淆
- **权限边界清晰**：不同工具对账号、会话与数据的处理方式不同，分离仓库便于单独说明与审计
- **门户职责单一**：本仓库只负责聚合与导航

## 技术实现

纯静态站点，无框架、无构建步骤、无第三方依赖：

```text
index.html            门户首页
assets/css/style.css  样式（CSS 变量 + prefers-color-scheme）
assets/images/        站点图标与 Open Graph 图片
```

- 零 JavaScript：所有导航与折叠内容均使用原生 HTML 实现，禁用 JavaScript 后功能完整
- 不使用 CDN，不加载任何外部资源
- 响应式布局，支持桌面端与移动端
- 跟随系统浅色 / 深色模式

本地预览：直接双击打开 `index.html` 即可，无需任何环境准备。

## 部署

使用 GitHub Pages 的**分支部署**方式（Deploy from a branch）：`main` 分支根目录，无需自定义 GitHub Actions workflow —— 部署由 GitHub Pages 内置的构建流程完成。

根目录的 `.nojekyll` 是一个空文件，用于显式关闭 Jekyll 处理，确保静态文件按原样提供服务。

## Security

**请勿在任何公开位置提交以下内容：**

- Password（账号密码）
- Cookie
- Token
- Session
- 临时下载 URL
- 身份认证响应

其他要求：

- 本站不要求输入西安交通大学账号或密码
- 使用各子项目时，请先阅读对应项目的安全说明与使用范围
- 所有工具都应尽量在用户本地处理认证信息与数据
- 如发现安全问题，请勿公开披露敏感信息，优先通过仓库提供的私密联系方式报告

## Disclaimer

本项目为学生个人维护的非官方开源项目，与西安交通大学官方无隶属、授权或合作关系。

“西安交通大学”“思源学堂”等名称仅用于说明对应的服务与兼容对象，不代表任何官方背书。

## License

[MIT](./LICENSE)
