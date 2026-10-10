# Automator 工作流与系统入口

构建工具需要 macOS、Python 3.9+ 标准库及系统“运行 Shell 脚本”动作。产物使用系统 Shell 与 Automator，无需 Python。当前实现单个 Shell 动作，任务源码嵌入 `document.wflow`，可移走原源码或安装后执行。保留 `source/task.sh` 与 `build.json` 供修改及重建。

## 普通工作流

```sh
python3 scripts/build_workflow.py --script scripts/list_files.sh \
  --arg='/path/to/输入 目录' --arg='/path/to/结果.txt' \
  --name '文件清单' --output '/path/to/new-delivery'
```

用 Automator 打开 `.workflow`，点击“运行”，核对输出和动作日志。可用 `/usr/bin/automator '/path/to/文件清单.workflow'` 做回归，但仍需 GUI 入口验收。

## 快速操作

```sh
python3 scripts/build_workflow.py --script scripts/record_paths.sh --type quick-action \
  --arg='/path/to/receipts' --name '记录所选路径' --output '/path/to/new-delivery'
```

工作流声明 Finder 上下文、文件或文件夹输入及服务菜单项。输入传递方式是“作为自变量”：固定 `--arg` 在前，每个所选路径单独追加到任务参数。输出不替换 Finder 输入。

安装并刷新服务缓存：

```sh
python3 scripts/install.py '/path/to/new-delivery/记录所选路径.workflow'
python3 scripts/uninstall.py '<install 返回的 id>'
```

目标为 `~/Library/Services/`，已存在则拒绝。安装返回 ID、位置和安装记录，卸载只处理该 ID 对应的副本。在 Finder 选中文件，通过“访达 → 服务 → 记录所选路径”调用，核对收据。菜单未出现时检查服务启用状态和上下文。快捷键在系统设置 → 键盘 → 键盘快捷键 → 服务中手动配置；未实现跨版本偏好设置写入。

### 文本快速操作

```sh
python3 scripts/build_workflow.py --script text.sh --type quick-action \
  --input text --app any --output-replaces-selection \
  --name '转换所选文本' --output '/path/to/new-delivery'
```

文本从 stdin 传入，stdout 作为服务结果；省略 `--output-replaces-selection` 时不替换原文（任务可自行写剪贴板）。`--input files|text|none` 默认 files；`--app finder|any|<bundle-id>` 默认文件用 Finder，文本/无输入用任意应用。替换选项仅用于文本快速操作；文件夹操作只接收文件。文本服务的 `NSSendTypes` / `NSReturnTypes` 使用 `public.utf8-plain-text`，并与工作流的输入输出类型一致。

在 TextEdit 和一个非 Apple 应用中选中含中文、换行、引号的文本，通过服务菜单分别核对替换与非替换。服务是否支持所选控件由宿主应用决定。

## 文件夹操作

```sh
python3 scripts/build_workflow.py --script scripts/record_paths.sh --type folder-action \
  --arg='/path/to/receipts' --name '记录新增路径' --output '/path/to/new-delivery'
```

```sh
python3 scripts/install.py '/path/to/new-delivery/记录新增路径.workflow' --folder '/path/to/watched'
python3 scripts/uninstall.py '<install 返回的 id>'
```

安装器复制到 `~/Library/Workflows/Applications/Folder Actions/`，通过 System Events 绑定并启用，记录原状态。已有目标拒绝覆盖，已有停用脚本的目标目录拒绝自动激活。卸载先解绑再删除，只处理本工具安装的项目；最后一项文件夹安装移除后恢复原全局启用状态。如果期间其他绑定发生变化，保留当前全局状态并输出 warning。

在新建隔离目录验证：输出收据目录置于监控目录之外；记录原启用状态及绑定；绑定后新增样例文件，等待后台触发并核对路径。结束后移除测试绑定及安装副本，恢复原启用状态。正式交付保留用户要求的绑定，并说明实际执行宿主 `FolderActionsDispatcher` 的权限。

任务设计需考虑未复制完成的文件、批次、重复触发和并发。路径记录示例只记录路径，不读取文件内容；不承诺内容就绪。实际处理任务应有有界等待和幂等策略，不把无限重试或递归触发用于修复。

## 示例契约与兼容范围

`record_paths.sh` 参数为收据目录与至少一个现存输入路径，每次调用用 `mktemp` 创建独立文件，内容是 NUL 分隔的输入路径。可用 Python `path.read_bytes().split(b'\0')[:-1]` 读取；不要按行解析，换行本身是合法文件名。

普通工作流结构通过本机 Automator 原生保存样本核对；服务声明通过本机现有服务元数据核对，未复制其任务代码。生成的三种类型在 macOS 26.6.2、Automator 2.10 实测。元数据为系统实现细节，不承诺跨版本兼容；换系统版本后重新验证编辑器识别、参数传递和真实触发。

背景依据：[Apple 的 Automator 脚本说明](https://support.apple.com/guide/automator/use-scripts-aut4bb6b2b4f/mac)。生成器使用目标系统动作版本，不硬编码开发机版本号。
