# macOS 系统入口路线图

定位：让 Agent 正确生成并安装 macOS 系统入口。任务脚本按用户需求编写；复用知识集中在包格式、系统动作参数、服务声明、安装刷新、目录绑定及权限宿主。

| Issue | 实现 | 提交 | 验证 |
| --- | --- | --- | --- |
| [#1](https://github.com/fullac/AutoAutomator/issues/1) | 稳定 bundle ID、日志及重建参数 | `971b64f` | 同名/显式 ID、严格签名；TCC 授权继承未测 |
| [#2](https://github.com/fullac/AutoAutomator/issues/2) | 文件/文本/无输入、适用应用、文本替换 | `ac870eb` | TextEdit 与 Boop 服务菜单替换/非替换 |
| [#3](https://github.com/fullac/AutoAutomator/issues/3) | Shell 应用的 run/open 入口、文件类型声明 | `ac5059a` | Open Documents 多文件/目录、特殊路径及无输入启动；鼠标拖放未测 |
| [#4](https://github.com/fullac/AutoAutomator/issues/4) | 安装记录、拒绝覆盖、解绑卸载及状态恢复 | `8660a18` | 服务菜单及真实目录新增触发、卸载恢复；快捷键手动配置 |
| [#6](https://github.com/fullac/AutoAutomator/issues/6) | 命令决策表、精简示例、开发记录移出 Skill、删除构建哈希校验 | `f362f2f` | Skill 校验、文档链接及回归 |
| [#5](https://github.com/fullac/AutoAutomator/issues/5) | 原生 AppleScript / JXA 动作及语法检查 | `b71c2b9` | Automator GUI、CLI 与文本服务菜单；首次控制其他应用权限弹窗未测 |
| [#7](https://github.com/fullac/AutoAutomator/issues/7) | 同步 README、Skill 描述及调用元信息 | 本次定位提交 | 内容、命令与当前能力一致 |

实现顺序为 #1 → #2 → #3 → #4 → #6 → #5 → #7，每个 Issue 一个提交。详细运行证据见[验证记录](verification.md)。GitHub Issue 状态由后续发布/合并流程更新；此表记录本地实现，不代表已发布。

不将 Automator 所有工作流类型扩展为默认范围。其他入口、Developer ID/公证及跨系统兼容按具体任务验证。目录监控需要由任务自己处理文件就绪和重复事件，无限重试不能代替正确的任务设计。
