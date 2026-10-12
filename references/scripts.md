# 最小脚本示例

```sh
/bin/zsh scripts/list_files.sh '/path/to/input' '/path/to/result.txt'
```

列出直属普通文件（含隐藏文件），每行一个名称；空目录生成空文件，已有输出拒绝覆盖。它是可读示例，换行文件名会占多行，业务任务自行选择输入输出格式。需要逐字节记录路径时参考 `record_paths.sh` 的 NUL 收据。

任务代码由 Agent 编写；非交互环境使用绝对工具路径，先验证脚本，再接入系统入口。
