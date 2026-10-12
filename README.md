# AutoAutomator

让 Agent 把任务脚本接入 macOS：在 Finder 右键调用、选中文本后转换、向文件夹新增文件时运行，或把文件拖到应用图标上处理。

任务逻辑由 Agent 按需求编写，AutoAutomator 负责包格式、服务输入输出声明、安装刷新、目录绑定与卸载恢复。支持 Shell、AppleScript 和 JXA；工作流构建器生成单个脚本动作，应用构建器生成 AppleScript 应用。

## 能做什么

| 入口 | 用法 | 当前支持 |
| --- | --- | --- |
| Finder 快速操作 | 选中文件或文件夹 → 服务菜单 | 路径逐个作为任务参数传入，可限定适用应用 |
| 文本快速操作 | 选中文字 → 服务菜单 | stdin 输入、stdout 输出，可替换选中文本 |
| 文件夹操作 | 向指定目录新增文件 | 安装、绑定、记录原状态，按安装 ID 卸载恢复 |
| 应用 | 双击或拖入文件、文件夹 | 固定参数、拖放参数、稳定 bundle ID、Shell 任务日志 |
| 普通工作流 | 在 Automator 中打开、运行 | Shell / AppleScript / JXA 动作、源码保留及重建参数 |

仅需终端执行时直接用脚本。后台目录监控可评估 `launchd WatchPaths`；已有快捷指令的任务可沿用其入口。实现与验收范围见[路线图](docs/roadmap.md)。

## 安装 Skill

以 Codex 为例，在目标目录不存在时执行：

```sh
mkdir -p "$HOME/.codex/skills"
git clone https://github.com/fullac/AutoAutomator.git \
  "$HOME/.codex/skills/autoautomator"
```

已有本地仓库时，也可将它链接到 Agent 的技能目录，目录名为 `autoautomator`。只需复制的文件为 `SKILL.md`、`agents/`、`scripts/`、`references/`；目标已存在时先核对。

在 Agent 中调用 `$autoautomator`，说明任务、触发入口和输入输出，例如：

> 用 $autoautomator 创建一个文本快速操作：选中英文后转为大写并替换原文，安装到服务菜单。

## 命令行示例

在仓库目录运行以下命令，构建一个文本快速操作。构建输出目录必须不存在，父目录必须存在。

```sh
WORK="$(mktemp -d)"
cat > "$WORK/uppercase.sh" <<'SH'
/usr/bin/tr '[:lower:]' '[:upper:]'
SH

python3 scripts/build_workflow.py --script "$WORK/uppercase.sh" --type quick-action \
  --input text --app any --output-replaces-selection \
  --name '英文转大写' --output "$WORK/delivery"
python3 scripts/install.py "$WORK/delivery/英文转大写.workflow"
```

在 TextEdit 中选中英文，通过“服务 → 英文转大写”调用并核对结果。安装命令返回 ID、安装位置及记录，保留该 ID；需要移除时执行：

```sh
python3 scripts/uninstall.py '<安装返回的 ID>'
```

交付目录包含 `.workflow` 或 `.app`、可编辑的 `source/` 及记录重建参数的 `build.json`。安装器拒绝覆盖已有目标；卸载只处理安装记录对应的副本，被修改的副本会保留。

## 环境与验证

- 构建和安装需要 macOS、Python 3.9+ 标准库及系统 Automator / AppleScript 工具。产物本身无需 Python，任务脚本的额外依赖需另行安装。
- 应用采用 ad-hoc 签名用于本机运行。稳定 bundle ID 不保证重建后免于重新授权；Developer ID、公证及跨 Mac 分发未覆盖。
- 权限由最终执行宿主请求，例如 `.app` 或 `FolderActionsDispatcher`。文本服务能否作用于所选控件由宿主应用决定；文件夹任务需自行处理文件未复制完成、重复触发和输出递归。
- 本机入口验证记录来自 macOS 26.6.2；构建、CLI 回归和真实系统入口分别记录。权限继承、Finder 鼠标拖放及首次跨应用权限弹窗仍待验收，详见[验证记录](docs/verification.md)。

开发回归：

```sh
python3 -m unittest discover -s tests -v
```

## 文档

- [命令决策表](SKILL.md)
- [应用与拖放](references/applications.md)
- [工作流、文本服务及安装](references/workflows.md)
- [权限、重建与恢复](references/delivery.md)
- [开发约定](Agent.md)、[路线图](docs/roadmap.md)及[验证记录](docs/verification.md)
