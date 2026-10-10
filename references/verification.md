# 开发验证记录

## Issue #1 / #2 — 2026-10-10

- 环境：macOS 26.6.2（25G83），Automator 2.10。
- #1：同名应用重建两次，bundle ID 和日志位置一致；显式 ID、重建记录、非法 ID 拒绝及严格签名校验通过。未验证受保护目录的 TCC 授权继承；ad-hoc 签名改变仍可能重新授权。
- #2：原生 Automator 保存的文本快速操作用于核对输入输出元数据。TextEdit 与非 Apple 应用 Boop 均从“服务”菜单实测：`hello 中文 "quote"` 加换行第二行，在替换模式下变成 `HELLO`，非替换模式保留原文；任务收到中文、换行和引号。文本 stdin、无输入服务、指定应用及非法替换组合的回归通过。
- 临时服务均已移出 `~/Library/Services/` 并刷新缓存；样本与收据保留在 `~/.local/share/autoautomator-issues-20261010/`。

## Issue #3 — 2026-10-10

- macOS 26.6.2：`open -W -n -a <app> <files...>` 发送真实 Open Documents 事件，单/双引号、中文、空格、多文件及文件夹的 NUL 参数收据核对通过；固定参数在前。Finder/AppleScript alias 解析后路径规范化，目录可能附加 `/`。
- 无输入启动只收到固定参数；应用构建、签名、重建记录和 4 项应用回归通过。Finder 鼠标拖放未完成验收，不将系统 Open Documents 回归等同于鼠标操作。

项目于 2026-10-10 更名为 AutoAutomator，Skill 调用名为 `autoautomator`。以下 2026-10-09 记录保留当时的 AMCreate / amcreate 名称、路径和菜单项，以便核对原始运行证据。

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

## 阶段 3 — 2026-10-09

环境：macOS 26.6.2，Automator 2.10，系统 Run Shell Script 2.0.3。

- 普通工作流：生成后通过 Finder 打开，Automator 显示 Shell 动作和“作为自变量”输入；点击运行，日志显示动作及工作流程已完成，输出文件包含三个预期名称。
- 快速操作：临时安装 `AMCreate 验收路径.workflow`，更新服务缓存；Finder 选中 `中文.txt` 后从“访达 → 服务 → AMCreate 验收路径”调用。NUL 收据与所选完整路径字节一致。
- 文件夹操作：系统“文件夹操作设置”原状态为未启用且无绑定。临时安装并附加 `AMCreate 验收新增.workflow` 到仓库 `build/验收/watched`，启用后新增 `新增 中文 quote'$.txt`；20 秒上限内收到路径收据，字节核对通过。
- 验收结束：GUI 移除测试绑定，恢复全局未启用且无绑定；只移除两份 AMCreate 测试安装副本并刷新服务缓存。工作流交付包与收据保留在仓库 `build/验收/`（不纳入 Git）。
- 初次用 Automator 的“选取文件夹”对话框时按钮不可用；通过系统“文件夹操作设置”完成绑定与真实触发，无需改变安全权限。
- 自动化回归新增三种类型的真实命令行参数传递与任务失败检查。GUI 入口验收是本次人工驱动检查，不宣称回归测试自动覆盖系统菜单或绑定。

## 阶段 4 — 2026-10-09

- `python3 -m unittest discover -s tests -v`：15 项通过。覆盖正常与空目录、中文/空格/特殊字符、换行路径收据、换行名称拒绝、缺少输入、不可读取输入、已有输出、悬空符号链接、两进程并发输出、错误 Shell、错误源码清理、工作流真实执行失败、产物缺失及源码改动检测。
- 发现并修复：应用装配 Shell 资源后旧签名无效。现在在资源装配完成后做 ad-hoc 签名，`codesign --verify --deep --strict` 通过。此签名仅用于本机完整性，不是 Developer ID 签名或公证。
- 发现并修复：清单路径解析会跟随悬空符号链接；现在拒绝链接，以同目录临时文件和独占硬链接发布，拒绝覆盖及并发替换。不可读取目录返回 77，避免被当成空目录。
- 最终应用 `build/验收/最终应用/文件清单.app` 从 Finder 双击成功。输入目录包含中文、空格、单/双引号、`$()` 和反引号，输出核对通过。再次双击只显示一个错误窗口，包含日志位置和状态 73；日志明确说明输出已存在，原输出保持不变。
- macOS 文稿权限边界：首次将最终应用样例数据置于仓库目录时，`tccd` 记录 `kTCCServiceSystemPolicyDocumentsFolder` 授权等待，进程停在目录读取。终止本次测试进程后，把样例数据置于 `~/.local/share/amcreate-validation-20261009/` 完成验收。未授予新的文稿访问权限；文稿目录场景仍需用户授权。源码与应用包保留在仓库。
- 最终普通工作流通过 `/usr/bin/automator` 执行，结果核对通过；GUI 和系统入口证据见阶段 3。阶段 4 未重复修改服务/文件夹绑定，后台宿主及用户权限仍按实际入口区分。
- 四类最终交付目录均通过 `verify_delivery.py`；`doctor.py` 三类依赖检查通过。Skill 官方 `quick_validate.py` 通过；仅校验工具在临时 venv 使用 PyYAML，项目构建、测试及产物均不依赖它。
- 所有最终本机产物保留在仓库 `build/验收/` 下的 `最终*` 目录，早期应用移到 `历史阶段`。构建参数和源码均可查看。没有安装到用户 Skill 目录，没有推送远端；阶段 5 的四类按需扩展未实现。

## 项目更名 — 2026-10-10

- 本地仓库目录改为 `/Users/raymondzhang/Documents/AutoAutomator`，远程为 `fullac/AutoAutomator`；Skill 名称和调用名改为 `autoautomator` / `$autoautomator`。
- 当前文档、UI 元信息、默认产物名称、Shell 参数标识、临时文件前缀及新应用日志目录统一使用新名称。旧验收记录和旧构建包保留当时的名称及固定参数，新示例单独重建，不修改已有签名包。
- 在新目录运行 15 项回归测试全部通过；Skill 官方校验和本地文档链接检查通过。
- 更名示例保留在 `build/验收/20261010-更名/`。四类交付目录均通过完整性检查；新应用通过 `/usr/bin/open -W -n` 启动，输出核对通过，日志实际写入 `~/Library/Logs/AutoAutomator/`。普通工作流通过系统 CLI 执行；快速操作和文件夹操作的参数传递通过系统 CLI 收据核对。
- 样例数据位于 `~/.local/share/autoautomator-validation-20261010/`。本次未重新安装服务、绑定文件夹或进行 GUI 菜单验收；原始真实入口证据见 2026-10-09 记录。
