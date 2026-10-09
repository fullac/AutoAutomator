# AMCreate

AMCreate 是一个面向 macOS 自动化的 Agent Skill 项目，目标是让 Agent 根据自然语言需求，在 Mac 上生成可运行、可验证、可继续修改的自动化产物。

用户描述要完成的任务，Agent 选择合适的实现方式，生成源文件和交付文件，并验证实际运行结果。目标产物包括自动化脚本、可双击运行的 `.app`，以及可在 Automator 中打开和执行的 `.workflow`。

## 当前状态

阶段 1–4 已完成：Skill 入口、脚本、AppleScript 应用及 Automator 普通工作流、快速操作、文件夹操作已有构建与交付指导。示例已在本机 macOS 26.6.2 验证 Finder 双击、Automator 运行、Finder 服务菜单和新增文件触发。15 项回归测试通过；应用资源签名、交付完整性、拒绝覆盖、并发写入及代表性失败已检查。阶段 5 保留为按需扩展。

本文描述项目定位和预期能力；开发目的、实施计划与规范见 [Agent.md](Agent.md)。

## 预期产物

Automator 有 8 种工作流类型，类型决定触发入口和安装方式，文件主要采用 `.workflow` 或 `.app` 两种封装。下表描述系统能力分类。AMCreate 当前生成普通工作流、快速操作和文件夹操作；当前 `.app` 构建采用 AppleScript 应用，Automator 应用和其他类型仍需按需求扩展。

| Automator 类型 | 常见文件封装 | 触发与使用方式 |
| --- | --- | --- |
| Workflow（工作流程） | `.workflow` | 在 Automator 或其他工作流执行入口中运行 |
| Application（应用程序） | `.app` | 双击运行，或将文件、文件夹拖到应用图标上 |
| Quick Action（快速操作，旧称 Service） | `.workflow` | Finder 快速操作、应用的服务菜单，按需绑定快捷键 |
| Print Plugin（打印插件） | `.workflow` | 从打印对话框的 PDF 菜单调用，接收打印系统生成的 PDF |
| Folder Action（文件夹操作） | `.workflow` | 绑定目录，在文件或文件夹加入该目录时触发 |
| Calendar Alarm（日历提醒） | `.app` | 由日历事件提醒启动，需要关联事件 |
| Image Capture Plugin（图像捕捉插件） | `.app` 工作流应用 | 在图像捕捉应用的导入流程中调用，接收图像文件 |
| Dictation Command（听写命令） | `.app` 工作流应用 | 通过配置的语音命令触发，需核对目标系统的语音功能与注册方式 |

类型分类来自 [Apple 的完整工作流类型说明（macOS 15 版）](https://support.apple.com/en-euro/guide/automator/aut7cac58839/2.10/mac/15.0)；应用封装与系统入口参考社区的[应用工作流实例](https://www.macosxautomation.com/automator/application/index.html)和[各类工作流应用说明](https://macosxautomation.com/automator/security.html)。2026-10-09 在本机 macOS 26.6.2、Automator 2.10 的新建窗口中确认仍列出上述 8 种类型；此分类核对不表示所有类型已实现；具体已验证能力见当前状态和验证记录。

AMCreate 也交付可独立执行的自动化脚本。脚本是任务逻辑的实现方式；Automator 的上述 8 种类型是任务的封装与系统入口。AppleScript 脚本应用与 Automator 应用都可以使用 `.app` 后缀，但内部结构和构建方式不同。

具体产物由用户指定，或由 Agent 根据触发方式、输入输出和目标环境选择。首期优先覆盖普通工作流程、应用程序、快速操作和文件夹操作；其他类型按需求扩展。系统集成类型需要同时处理文件生成、安装或注册、入口验证，才算完成交付。

## 使用场景

Skill 可用于以下需求；Agent 需为具体任务编写源码并验证结果，示例不代表预置了所有业务逻辑：

- “把选中的文件按日期整理到子目录，生成一个可以双击运行的应用。”
- “生成一个 Automator 工作流，把输入文件复制到指定目录，并输出处理结果。”
- “把这段 AppleScript 封装成 `.app`，保留源码并说明需要哪些权限。”

## 预期使用流程

1. 描述任务、输入、输出和触发方式，例如双击运行、拖入文件或手动执行工作流。
2. Agent 检查当前 Mac 的环境与依赖，确定实现和产物类型。
3. 生成可维护的源文件，并构建对应的脚本、`.app` 或 `.workflow`。
4. 使用样例输入验证真实入口和任务结果，记录验证范围。
5. 交付产物位置、使用方式、依赖、权限说明和验证结果。

“可用”意味着产物能在声明的目标环境和授权条件下完成任务，并有运行证据。仅生成文件或通过语法检查，不代表任务已经验证成功。

## 环境与依赖

生成和验证目标产物需要 macOS，以及能够读写本地文件、调用系统工具的 Agent。具体依赖随任务确定；需要额外运行时或第三方工具时，应在交付说明中列出。

Automator 支持通过 Shell、AppleScript 和 JavaScript 扩展工作流；脚本应用可以通过 Finder 双击运行。技术背景见 Apple 的 [Automator 脚本使用说明](https://support.apple.com/guide/automator/use-scripts-aut4bb6b2b4f/mac)和[脚本运行说明](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/RunaScript.html)。项目的具体兼容范围将随实现和实测补充。

## 仓库文档

| 文件 | 内容 |
| --- | --- |
| [README.md](README.md) | 仓库介绍、预期产物、使用场景和当前状态 |
| [Agent.md](Agent.md) | 开发目的、实施计划、开发与验证规范 |

## 安装与调用

把本仓库复制或链接到目标 Agent 的技能目录，以 `amcreate` 作为目录名。例如 Codex 使用 `~/.codex/skills/amcreate`。目标目录已存在时先核对内容，避免覆盖。此仓库自身就是 Skill 目录，`SKILL.md` 为入口，不需要嵌套另一层。

安装后以 `$amcreate` 调用，或描述 Mac 自动化任务。首个可执行示例：

```sh
/bin/zsh scripts/list_files.sh '/path/to/输入 目录' '/path/to/结果.txt'
```

此脚本使用系统 zsh，输出直属普通文件名称；不会覆盖已有文件。详细契约见 [脚本说明](references/scripts.md)。

构建工具和开发验证需要 Python 3.9+ 标准库，产物运行无需 Python：

```sh
python3 -m unittest discover -s tests -v
```

应用构建命令、依赖与使用方式见 [应用说明](references/applications.md)；普通工作流、快速操作、文件夹操作的构建与安装见 [工作流说明](references/workflows.md)。构建不会自动安装或绑定。

可靠交付检查：

```sh
python3 scripts/doctor.py --requires app
python3 scripts/verify_delivery.py '/path/to/delivery'
```

依赖、失败处理、权限和交付记录见 [可靠交付说明](references/delivery.md)。

可保留的最终验收产物在 `build/验收/最终应用`、`最终工作流`、`最终快速操作`、`最终文件夹操作`，由 Git 忽略。应用的最终样例输入输出位于 `~/.local/share/amcreate-validation-20261009/`，避免依赖文稿目录授权；访问文稿目录需由用户处理系统权限请求。早期产物保留为阶段证据，不作为最终交付。回归测试使用临时目录。

阶段验证证据见 [references/verification.md](references/verification.md)。
