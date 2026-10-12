# 开发约定

- 新分支使用 `feat/`，每个 Issue 一个提交，保留用户已有改动。
- 用目标 Mac 的系统动作 bundle 读取版本和默认参数。
- 新能力验证正常输入及实际失败场景；CLI、GUI 和系统入口证据分别记录。
- 回归：`python3 -m unittest discover -s tests -v`。
- 验证目录隔离；系统安装测试结束后用安装 ID 卸载并核对原状态。
- Skill 安装包仅需 `SKILL.md`、`agents/`、`scripts/`、`references/`。
- 历史计划与类型调研在 [docs/development-history.md](docs/development-history.md)，验证证据在 [docs/verification.md](docs/verification.md)。历史文档保留当时状态，当前行为以代码和使用说明为准。
