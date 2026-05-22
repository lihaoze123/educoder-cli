# Educoder API Client

一个封装头歌 / Educoder API 的现代 Python CLI 客户端工具，支持获取课堂列表、获取实验列表、手动提交代码，以及后续扩展 LLM 辅助解题。

## 安装

可以直接通过 `uv tool install` 从 GitHub 安装：

```bash
uv tool install git+https://github.com/lihaoze123/educoder-cli
```

安装后先登录一次，后续 CLI 和 Agent 辅助流程会复用保存的登录态：

```bash
educoder login --login <手机号/用户名/邮箱>
educoder status
```

## 开发环境

本项目使用 `uv` 管理环境和依赖，使用 `ruff` 统一 lint/format，使用 `ty` 做类型检查。

```bash
uv sync --all-extras --dev
```

## CLI

CLI 层使用 Typer + Rich：Typer 负责命令和参数解析，Rich 负责表格与终端输出。

```bash
uv run educoder --help
uv run educoder version
```

用账号密码登录。密码会安全提示输入，登录成功后会保存登录态供后续命令使用：

```bash
uv run educoder login --login <手机号/用户名/邮箱>
```

检查当前保存的认证信息是否可用：

```bash
uv run educoder status
```

登录后可直接列出课程：

```bash
uv run educoder courses
```

也可以通过环境变量提供或覆盖认证信息：

```bash
EDUCODER_ZZUD=... \
EDUCODER_AUTOLOGIN=... \
EDUCODER_SESSION=... \
uv run educoder courses
```

也可以通过命令选项传入：

```bash
uv run educoder courses \
  --zzud ... \
  --autologin ... \
  --session ...
```

列出课堂中的实验：

```bash
uv run educoder homeworks --course py
uv run educoder homeworks --course py --json
```

查看当前实验关卡详情：

```bash
uv run educoder task --course py --homework 123
uv run educoder task --course py --homework "实验一" --json
```

读取远端代码，默认输出到 stdout；也可以写入本地文件：

```bash
uv run educoder code --course py --homework 123
uv run educoder code --course py --homework 123 --output main.py
uv run educoder code --course py --homework 123 --output main.py --force
```

提交本地代码。默认等待评测完成；评测失败或超时会以非零退出码结束：

```bash
uv run educoder submit --course py --homework 123 --file main.py
cat main.py | uv run educoder submit --course py --homework 123 --file -
uv run educoder submit --course py --homework 123 --file main.py --no-wait
uv run educoder submit --course py --homework 123 --file main.py --timeout 60
```

## Agent 辅助写题

本仓库提供了一个项目内 Skill：`skills/educoder-cli`。安装后，可以让支持 Skills 的 Agent 工具按真实 `educoder-cli` 路径读取题面、下载远端代码、编辑本地答案，并在你确认目标后提交评测。

在本仓库根目录安装 Skill：

```bash
npx skills@latest add lihaoze123/educoder-cli --skill educoder-cli --agent codex --copy -y
```

如果你使用的不是 Codex，把 `--agent codex` 换成对应 Agent 名称；也可以省略 `--agent` 按 `skills` 工具提示选择。

安装后，在 Agent 里这样发起：

```text
Use $educoder-cli to solve my EduCoder homework.
```

Skill 会要求先用 `educoder login` 建立登录态，不会要求你在对话里粘贴密码、Cookie、`zzud`、`autologin` 或 `_educoder_session`。提交会远端保存代码并触发评测，Agent 应只在课程和作业目标明确后执行。

## 本地检查

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
```

自动格式化：

```bash
uv run ruff format .
```

## LLM 依赖

`litellm` 不属于基础 CLI 必需依赖，已作为可选 extra 保留：

```bash
uv sync --extra llm --dev
```

LLM 辅助解题命令会在后续功能中接入；当前推荐通过上面的项目 Skill 调用 Agent 辅助完成作业。
