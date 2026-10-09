# 开发验证记录

## 阶段 1 — 2026-10-09

环境：macOS 26.6.2（25G83），系统 zsh；测试使用 Python 3.13。

- 读取 `SKILL.md` 可找到触发条件、类型选择、验证与交付要求；`agents/openai.yaml` 提供调用元信息。仓库目录安装时命名为 `amcreate`。
- `python3 -m unittest discover -s tests -v`：1 项通过。真实执行脚本，中文、空格、引号与 `$` 文件名完整输出；目录不被列出；第二次执行退出 73，输出保持原内容。
- 未安装到用户技能目录；未声称新会话自动发现已实测。

## 阶段 2 — 2026-10-09

- `build_app.py` 用系统 `osacompile` 构建 AppleScript 应用，保留 Shell/AppleScript 源码、参数、源码 SHA-256、重建命令和日志位置。
- 测试累计 3 项通过：特殊字符参数可编译；拒绝已有交付目录且保留原文件；AppleScript 编译失败不留下半成品。
- GUI 实测：在 Finder 打开临时 `app-delivery`，双击 `文件清单.app`。输出 `app-result.txt` 与输入的中文、空格、引号和 `$` 三个文件名一致；应用日志记录输出路径。`Info.plist` 通过 `plutil -lint`。
- 临时产物位于 `/tmp/AMCreate 验收/`，不作为仓库内发布包。未验证拖入文件、签名、公证、其他 Mac 或受保护目录授权。
