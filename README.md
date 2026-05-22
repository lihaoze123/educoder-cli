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

列出课程需要提供浏览器 Cookie 中的认证信息：

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
