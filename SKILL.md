---
name: autoautomator
description: 在 macOS 上生成、构建和验证自动化脚本、AppleScript 应用及 Automator 工作流。
---

# AutoAutomator

先根据触发入口选命令。任务脚本由 Agent 按用户需求编写；`S` 表示本 Skill 的绝对目录，输出目录 `OUT` 必须不存在。

| 需求 | 构建命令（Python 3.9+） | 安装 | 验收入口 |
| --- | --- | --- | --- |
| 终端执行 | 直接编写 Shell 脚本 | 无 | 终端 |
| 双击应用 | `python3 S/scripts/build_app.py --shell-script TASK --name NAME --output OUT` | 移到用户指定目录 | Finder 双击 |
| 拖入文件/文件夹 | 上一命令加 `--accept-drops` | 同上 | 拖到应用图标 |
| Finder 文件快速操作 | `python3 S/scripts/build_workflow.py --script TASK --type quick-action --name NAME --output OUT` | `python3 S/scripts/install.py OUT/NAME.workflow` | Finder 服务菜单 |
| 文本快速操作 | 上一构建命令加 `--input text --app any --output-replaces-selection` | 同上 | TextEdit 及目标应用服务菜单 |
| 文件夹操作 | `python3 S/scripts/build_workflow.py --script TASK --type folder-action --name NAME --output OUT` | `python3 S/scripts/install.py OUT/NAME.workflow --folder DIR` | 向目录新增文件 |
| Automator 手动编排 | `python3 S/scripts/build_workflow.py --script TASK --name NAME --output OUT` | 无 | Automator 运行 |

仅需终端运行时用纯脚本；需要后台目录监控时评估 `launchd WatchPaths`；用户已有快捷指令或更适合快捷指令的任务，按其入口实现。

关键参数与系统行为：

- Shell 固定参数用重复的 `--arg=VALUE`，文件路径随后逐个追加；文本通过 stdin 输入，stdout 返回。非替换服务省略 `--output-replaces-selection`。
- 工作流添加 `--language applescript|jxa` 可用原生动作；AppleScript 接收 `on run {input, parameters}`，JXA 接收 `run(input, parameters)`，返回值作为输出。原生动作不使用 `--arg`。
- 应用从名称生成稳定 ID，也可 `--bundle-id com.example.task`；原生 AppleScript 用 `build_app.py --source TASK`。
- 权限属于最终 `.app`、服务宿主或 `FolderActionsDispatcher`；安装器的 System Events 权限属于运行安装器的宿主。终端成功不能证明最终宿主有权限。
- 菜单不出现时运行 `/System/Library/CoreServices/pbs -update`，核对输入类型和适用应用。
- 文件夹任务自行处理文件尚未复制完成、重复触发和输出递归；非交互环境使用绝对路径。
- 安装返回 ID 和记录；`python3 S/scripts/uninstall.py ID` 先解绑再删除，恢复原状态。记录不要丢弃；已有目标拒绝覆盖。
- 保留源码及 `build.json` 重建参数，按真实入口核对结果，记录 macOS 版本和未测范围。

需要具体参数时读取 [应用](references/applications.md)或[工作流与安装](references/workflows.md)；依赖、权限及恢复见[交付说明](references/delivery.md)。
