# Educoder API Client

一个封装头歌 / Educoder API 的现代 Python CLI 客户端工具，支持获取课堂列表、获取实验列表、手动提交代码，以及后续扩展 LLM 辅助解题。

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

LLM 辅助解题命令会在后续功能中接入。
