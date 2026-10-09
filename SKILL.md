---
name: autoautomator
description: 在 macOS 上根据任务需求生成、构建和验证自动化脚本、AppleScript 应用及 Automator 工作流。适用于要求可运行脚本、双击应用、快速操作或文件夹操作的任务。
---

# AutoAutomator

把用户的任务交付为可维护源码和可运行产物。先确定输入输出、触发方式、保存位置及副作用；只询问影响实现的缺失信息。遵循用户指定类型，没有指定时按入口选择：终端执行用脚本，双击用应用，Automator 编排用工作流，Finder 选中文件用快速操作，目录新增文件用文件夹操作。

## 实施与验证

1. 检查目标 macOS、系统工具和任务依赖；构建前读取 [references/delivery.md](references/delivery.md)，可用 `scripts/doctor.py` 检查所选类型依赖。用系统绝对路径；不要假定终端 PATH、Homebrew 或 Python 已存在。辅助构建工具的依赖与产物运行依赖分别说明。
2. 在独立输出目录保留源码、配置与构建命令。参数以数据传递，Shell 参数逐个引用，避免把路径或输入拼入可执行代码。已有产物默认拒绝覆盖。
3. 先用临时样例验证任务脚本，检查结果、退出状态及副作用，再封装实际需要的类型。删除、移动、覆盖真实数据及系统集成遵循本次授权范围。
4. 构建后可用 `scripts/verify_delivery.py` 检查交付目录完整性，再按真实入口验收：脚本执行；应用从 Finder 双击；工作流在 Automator 运行；快速操作从菜单调用；文件夹操作由新增文件触发。构建或命令行运行不能代替尚未测过的入口。
5. 交付源码、产物、构建方式、启动方式、输入输出、依赖、权限和验证记录。记录系统版本、样例及结果，明确未验证行为。权限失败检查实际宿主，不关闭系统安全机制。

从最小的低副作用任务开始。文件清单示例见 [references/scripts.md](references/scripts.md)，可直接执行随 Skill 安装的 `scripts/list_files.sh`。任务不必套用示例逻辑，按用户需求编写可编辑源文件。

## 能力边界

已有脚本示例和 AppleScript 应用构建工具。应用任务读取 [references/applications.md](references/applications.md)，通过 `scripts/build_app.py` 构建。普通工作流、快速操作与文件夹操作读取 [references/workflows.md](references/workflows.md)，通过 `scripts/build_workflow.py` 构建。系统集成在用户要求范围内安装及绑定，验证完成后恢复测试状态。打印插件、日历提醒、图像捕捉插件、听写命令需要单独确认目标系统的注册方式和真实入口，不能仅凭扩展名宣布支持。签名、公证、跨 Mac 分发和长期后台运行按需求处理。
