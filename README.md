# AutoAutomator

让 Agent 正确生成并安装 macOS 系统入口：Finder / 文本快速操作、文件夹操作、可拖放应用。任务脚本由 Agent 按业务需求编写；本 Skill 处理 Automator 包格式、服务输入输出声明、安装刷新、目录绑定与权限宿主。

核心入口已有构建工具及本机验证；普通工作流用于手动编排，纯终端任务直接用脚本。后台目录监控可评估 `launchd WatchPaths`，用户已有快捷指令时按其入口实现。各项实现与验收范围见[路线图](docs/roadmap.md)。

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
