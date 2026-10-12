# 依赖、权限与恢复

构建/安装工具需要 macOS、Python 3.9+ 标准库。`python3 scripts/doctor.py --requires app|workflow|script` 检查系统构建依赖；业务脚本的依赖单独核对。产物运行无需 Python，除非任务本身使用它。

构建输出目录必须不存在；失败会清理本次新目录。交付保留可编辑 `source/`、包和 `build.json`。在交付目录执行记录的 `rebuild` 参数数组，替换 `<skill>` 和新输出目录；参数数组不要直接拼成 Shell 字符串。修改源码后重建，再核对任务结果。`build.json` 只记录配置和重建方式，不提供完整性证明。

应用资源装配后做 ad-hoc 签名并通过 `codesign --verify --deep --strict`。稳定 bundle ID 避免重建时更换应用身份；ad-hoc 签名变化仍可能触发 TCC 重新授权。未验证 Developer ID、公证、跨 Mac 分发。

权限属于最终宿主：应用任务检查 `.app`，文件夹操作检查 `FolderActionsDispatcher`；安装器通过 System Events 绑定时检查运行安装器的宿主。受保护目录可能等待用户处理权限弹窗；不要把终端执行成功当作应用已授权。

安装命令见[工作流说明](workflows.md)。`install.py` 返回 ID 和安装记录，保存在 `~/Library/Application Support/AutoAutomator/installations/`；`uninstall.py ID` 只处理对应安装，先解绑再删除。已有目标拒绝覆盖，被修改的安装副本拒绝删除。中断安装的文件仍与记录一致时可以重试卸载；清理失败会输出恢复 ID。最后一个文件夹安装移除后恢复原全局启用状态；其他绑定发生变化时保留当前状态并输出 warning。安装记录的文件摘要仅用于避免误删用户改动，与构建记录分开。

Shell 应用日志位于 `~/Library/Logs/AutoAutomator/<bundle-id>.log`；失败弹窗显示日志位置。工作流失败检查 Automator 日志或 CLI stderr。验证使用隔离数据，安装测试结束后卸载，核对原状态。

交付说明写明源码/包位置、启动方式、输入输出、依赖、必要权限、macOS 版本及实际测试结果。构建通过、CLI 执行通过与真实菜单/后台入口通过分别记录。
