# AutoAutomator

macOS 自动化 Agent Skill，生成 AppleScript 应用、Automator 工作流、文件/文本快速操作和文件夹操作，保留源码并提供安装、卸载命令。

安装到 Agent 的技能目录，目录名使用 `autoautomator`。只复制 `SKILL.md`、`agents/`、`scripts/`、`references/`；目标已存在时先核对。也可链接整个仓库。调用 `$autoautomator`，描述任务及触发入口。

```sh
python3 scripts/build_workflow.py --script text.sh --type quick-action \
  --input text --app any --output-replaces-selection \
  --name '转换文本' --output '/path/to/new-delivery'
python3 scripts/install.py '/path/to/new-delivery/转换文本.workflow'
python3 scripts/uninstall.py '<安装返回的 ID>'
```

构建/安装工具需要 macOS 和 Python 3.9+ 标准库；产物本身无需 Python，业务脚本的额外依赖另行说明。应用采用 ad-hoc 签名用于本机运行；未覆盖 Developer ID、公证或跨 Mac 分发。

- [命令决策表](SKILL.md)
- [应用与拖放](references/applications.md)
- [工作流、文本服务及安装](references/workflows.md)
- [权限、重建与恢复](references/delivery.md)
- [开发约定](Agent.md)及[验证记录](docs/verification.md)

开发回归：`python3 -m unittest discover -s tests -v`。本机验证环境为 macOS 26.6.2；具体入口证据和未测范围见验证记录。
