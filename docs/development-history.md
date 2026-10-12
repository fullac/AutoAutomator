# AutoAutomator 开发约定

本文面向参与 AutoAutomator 开发的 Agent 和开发者，记录开发目的、实施计划与规范。仓库介绍见 [README.md](../README.md)。

## 开发目的

将 AutoAutomator 做成一个可复用的 Skill，让 Agent 在 macOS 上把用户的自动化需求转化为可使用的脚本、`.app` 或 `.workflow`，并完成构建、验证和交付。

开发应围绕三项结果展开：

- **能生成**：理解任务的输入、输出和触发方式，选择合适的实现并生成产物。
- **能运行**：通过实际入口执行任务，验证结果，暴露失败原因和必要依赖。
- **能维护**：保留源码和构建方式，让用户或后续 Agent 能修改、重新生成和排查问题。

首期优先打通简单本地任务的完整闭环。复杂图形界面、跨机器分发、签名与公证、长期后台运行能力，按实际需求另行安排。

## 实施计划

以下阶段是开发顺序建议，每个阶段以产物和验证证据完成验收。

| 阶段 | 工作内容 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| 0：仓库文档 | 编写仓库介绍、开发目的、计划和规范 | README 与 Agent.md 分工明确，区分当前能力和计划能力 | 已完成并提交 |
| 1：Skill 入口 | 编写 `SKILL.md`，定义触发场景、需求识别、产物选择和交付流程 | 入口可被目标 Agent 加载，能指引完成一个简单脚本任务 | 已完成：入口、元信息与脚本实测 |
| 2：`.app` 闭环 | 实现轻量应用的构建方式，保留源码、构建记录和错误反馈 | 一个示例应用可从 Finder 双击运行，结果符合预期 | 已完成：源码保留、构建记录及 Finder 实测 |
| 3：`.workflow` 与系统入口 | 先验证普通工作流，再补充快速操作与文件夹操作的安装、绑定和输入传递 | 示例可在 Automator 运行；快速操作从真实菜单调用；文件夹操作由新增样例文件触发 | 已完成：三类生成与真实入口验收 |
| 4：可靠交付 | 补充失败处理、路径兼容、依赖检查和按需安装说明 | 核心示例覆盖正常路径与代表性失败，交付说明可复现 | 已完成：15 项回归、签名与完整性、权限边界说明 |
| 5：按需扩展 | 按需求加入打印插件、日历提醒、图像捕捉插件和听写命令 | 每种类型分别验证封装、安装或注册及真实触发入口 | 待安排 |

第一条完整链路建议使用低副作用任务，例如将指定目录中的文件名输出到新文本文件；先验证脚本，再封装 `.app`，最后复用任务验证 `.workflow`。

## 产物类型与系统集成

开发时分别记录任务逻辑、工作流类型、文件封装和触发入口。`.workflow` 后缀不能区分普通工作流、快速操作、打印插件或文件夹操作；`.app` 后缀也不能区分 Automator 应用、AppleScript 应用和其他应用实现。

下表列出常见的用户级安装位置与配套状态。路径来源包括社区实测和 Apple 归档说明，实施时需在目标 macOS 上重新确认，不能作为跨版本兼容承诺。

| 类型 | 常见保存或安装位置 | 文件之外需要处理的状态 |
| --- | --- | --- |
| Workflow | 用户选择的输出目录 | 明确执行入口；普通工作流文件不等同于可双击自运行的应用 |
| Application | 用户选择的输出目录 | 启动和拖入文件的输入契约、依赖与运行权限 |
| Quick Action | `~/Library/Services/` | 输入类型、适用应用、菜单启用状态；快捷键按需配置 |
| Print Plugin | `~/Library/PDF Services/` | PDF 菜单入口、打印输入与临时文件的处理 |
| Folder Action | `~/Library/Workflows/Applications/Folder Actions/` | 目标目录绑定、文件夹操作启用状态、实际后台宿主的权限 |
| Calendar Alarm | `~/Library/Workflows/Applications/Calendar/` | 日历事件及打开文件提醒的关联；旧资料可能使用 `iCal` 目录 |
| Image Capture Plugin | `~/Library/Workflows/Applications/Image Capture/` | 图像捕捉中的入口选择、导入数据和设备条件 |
| Dictation Command | 旧版为 `~/Library/Speech/Speakable Items/` | 命令短语、启用状态和语音功能注册；新版行为需单独实测 |

以上分类于 2026-10-09 核对：Apple macOS 15 版手册列出 8 种类型，本机 macOS 26.6.2、Automator 2.10 的新建窗口也列出 8 种类型。本机 `Automator.app/Contents/Info.plist` 将 `.workflow` 与 `.app` 声明为可编辑的包类型；未逐类执行保存、安装和触发测试。

`.action` 是供 Automator 工作流调用的动作组件。Apple 的 Automator 框架支持开发这类组件，但它属于扩展开发，首期使用现有动作组合任务即可。独立脚本、快捷指令和 launchd 配置应各自明确实现方式，避免混入 Automator 工作流类型。

社区实践对实现的约束：

- [Sparanoid 的工作流源码](https://github.com/sparanoid/automator-workflows/blob/master/Compress%20Images.workflow/Contents/document.wflow)包含动作参数、Shell 输入方式和 `workflowMetaData`；其[安装说明](https://github.com/sparanoid/automator-workflows)使用 `~/Library/Services/`。生成快速操作时，应维护真实工作流元数据与服务声明，验证输入类型和菜单上下文。
- [文件夹操作实例](https://www.macosxautomation.com/automator/folder-action/index.html)说明实际宿主为 `FolderActionsDispatcher`，并针对网络复制和 AirDrop 加入等待。开发时检查文件就绪条件、重复触发和实际宿主权限，避免只在 Automator 内测试。
- [打印插件实例](https://joshbduncan.com/printing-pdfs-to-dropzone-drop-bar.html)通过 PDF 菜单接收临时文件，并使用工具绝对路径。生成产物时检查非交互式运行环境，避免依赖终端的 PATH。
- [2023 年 Ventura 转换故障报告](https://talk.tidbits.com/t/ventura-automator-bug-converting-a-workflow-to-an-app-corrupts-the-resulting-app/20953)记录过工作流转应用后无法启动的情况。这是特定版本的历史报告；据此要求对最终应用实际启动验收，不预设当前系统也有同样故障。

## Skill 组织

计划以 `autoautomator` 作为 Skill 名称。实现阶段按实际需要加入以下资源，避免提前创建空目录或占位文件：

| 路径 | 职责 |
| --- | --- |
| `SKILL.md` | Skill 元信息、触发条件、共用流程和资源索引 |
| `scripts/` | 有明确复用价值的生成、构建或验证辅助脚本 |
| `references/` | 按产物类型拆分的技术细节、兼容说明和故障处理 |
| `assets/` | 已验证且用于生成产物的模板或资源 |

`Agent.md` 用于开发仓库；`SKILL.md` 用于指导安装后的 Skill 执行用户任务。两者按职责维护，避免复制整份开发计划到 Skill 入口。

## 开发规范

### 需求与实现选择

- 开始生成前，明确任务、输入输出、触发方式、输出位置和目标环境。仅在缺失信息影响实现时询问用户。
- 优先使用能够完成任务的系统工具、应用脚本接口或可验证模板。需要界面操作时，说明其对目标应用和界面状态的依赖。
- 用户指定产物类型时遵循其选择；未指定时，根据实际使用方式选择脚本、`.app` 或 `.workflow`。
- 首期尽量复用 macOS 能力；引入额外运行时前说明理由，不假定用户已安装 Homebrew、Python 或其他第三方依赖。

### 源码与构建

- 生成产物时保留可编辑源码和可复现的构建方式。配置、任务逻辑与封装逻辑在有复用需要时分离。
- 正确处理空格、中文和特殊字符路径；参数以数据形式传递，避免将用户输入直接拼入可执行代码。
- 不依赖开发者机器上的固定用户名、绝对工作目录或交互式终端配置。明确工作目录、必要环境变量和依赖路径。
- `.app` 需要真实的应用结构和启动入口；`.workflow` 需要真实的 Automator 工作流结构，不能用重命名文件代替构建。
- 工作流生成方式以目标 macOS 环境中的实测为依据。模板和结构变更必须验证能被 Automator 识别并运行。
- 为失败提供可观察的错误信息或日志；区分取消、依赖缺失、权限拒绝和任务执行失败。

### 权限与副作用

- 按任务需要说明自动化控制、辅助功能或文件访问权限，并明确实际执行入口所需的授权。
- 不通过关闭系统安全机制解决生成或运行问题。
- 默认在独立输出目录生成文件；覆盖用户已有产物前检查内容并保留恢复方式。
- 验证使用临时目录和样例数据。删除、覆盖、移动真实数据或修改系统配置时，遵循用户授权范围；测试本身不扩大授权。
- 签名、公证和安装按交付需求处理。本机运行验证不代表其他 Mac 已通过验证。

### 验证与交付

验证按产物实际入口展开：

| 产物 | 验证重点 |
| --- | --- |
| 脚本 | 从约定入口执行，检查输出、退出状态和副作用 |
| `.app` | 检查构建结果，从 Finder 双击启动；声明支持拖入文件时验证拖入行为 |
| `.workflow` | 在 Automator 中打开并运行，检查动作、输入传递和输出；声明特定触发器时验证该入口 |

每次实现至少验证一个正常场景，并针对实际改动选择有意义的边界或失败场景，例如空输入、包含空格的路径、目标文件已存在或缺少依赖。只改文档时检查内容、链接和差异即可。

交付说明包含：产物与源码位置、启动方式、输入输出、依赖和权限、实际验证的 macOS 环境，以及已验证和未验证的行为。未完成的入口测试应明确标注，不以构建成功代替可用性结论。

### Git 与文档维护

- 开发前检查当前分支、工作区和已有文件，保留用户已有修改。
- 新分支默认使用 `feat/` 前缀，一次变更围绕一个明确目标。
- README 只记录仓库说明和真实进展；开发计划与规范维护在本文；运行时使用指导维护在 `SKILL.md` 及其引用资源中。
- 新增能力时同步更新状态和使用说明，保留验证证据，避免把计划能力写成已实现能力。

## 技术参考

- [Apple：在 Automator 中创建工作流](https://support.apple.com/guide/automator/create-a-workflow-aut7cac58839/mac)
- [Apple：在 Automator 中使用脚本](https://support.apple.com/guide/automator/use-scripts-aut4bb6b2b4f/mac)
- [Apple：运行脚本及脚本应用](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/RunaScript.html)
- [Apple：完整工作流类型分类（macOS 15 版）](https://support.apple.com/en-euro/guide/automator/aut7cac58839/2.10/mac/15.0)
- [Apple：Automator 框架与动作组件](https://developer.apple.com/documentation/Automator)
- [Apple：听写命令工作流（归档）](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/UseDictationtoRunScripts.html)
- [社区：快速操作的上下文与安装](https://www.macosxautomation.com/automator/services/index.html)
- [社区：日历提醒应用与事件关联](https://www.macosxautomation.com/automator/calendar/index.html)
- [社区：工作流保存位置实测（OS X 10.7.1）](https://apple.stackexchange.com/questions/24023/what-are-the-storage-locations-of-the-various-types-of-automator-workflows)

Apple 开发者归档文档用于技术背景，具体实现需结合目标系统工具和实际运行结果确认。
