# AppleScript 应用

构建工具需要 macOS、Python 3.9+ 标准库、`/usr/bin/osacompile` 和 `/usr/bin/codesign`。产物是编译得到的 AppleScript 应用，不是 Automator 应用。运行 AppleScript 或系统 Shell 任务的产物无需 Python。

从 AppleScript 构建（用户源码自行负责任务逻辑、日志与权限）：

```sh
python3 scripts/build_app.py --source task.applescript --name 'My Task' --output '/path/to/new-delivery'
```

从 Shell 构建文件清单应用：

```sh
python3 scripts/build_app.py --shell-script scripts/list_files.sh \
  --arg='/path/to/输入 目录' --arg='/path/to/结果.txt' \
  --name '文件清单' --output '/path/to/new-delivery'
```

交付目录包含 `.app`、`source/` 和 `build.json`。从交付目录执行记录中的 `rebuild` 参数数组，将 `<skill>` 和新交付目录替换为实际位置；参数数组不可简单拼接成 Shell 字符串。输出目录必须不存在，父目录必须存在。修改源码后向新目录重建。

Shell 源码被复制到应用资源，启动器通过自身位置定位资源，可移动 `.app`。固定参数会保留原路径；移动应用不会搬动输入输出路径。双击执行一次，重复双击会再次执行任务。Shell 任务日志路径见 `build.json`，失败会弹出包含日志路径和退出状态的系统错误提示。当前包装器不支持拖入文件；需要此行为时编写带 `on open` 的 AppleScript 源码并单独验证。

先测试脚本，再从 Finder 双击最终 `.app`，核对输出与日志。需要控制其他应用时由真实应用请求自动化权限；访问受保护目录时检查该应用的文件权限。构建后本机运行不代表签名、公证或跨机器分发已完成。

依据：[Apple 脚本应用运行说明](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/RunaScript.html)与目标系统 `osacompile` 实测。

构建后进行 ad-hoc 签名与严格校验；它用于本机完整性检查。访问文稿等受保护目录可能等待用户授权，具体检查和交付记录见 [可靠交付](delivery.md)。
