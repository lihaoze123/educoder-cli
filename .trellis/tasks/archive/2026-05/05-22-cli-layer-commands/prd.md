# 完善 CLI 层功能

## Goal

完善 `educoder-cli` 的用户命令层，让现有 `EduCoderClient` 已具备的课堂、实验、任务详情、远端代码读取和单关提交能力可以通过稳定 CLI 使用。第一版保持无本地状态、无配置文件、无交互式选择，优先满足脚本化和手动终端使用。

## Requirements

- 保留现有顶层扁平命令结构和 `educoder courses` 行为。
- 新增顶层命令：
  - `educoder homeworks --course ...`
  - `educoder task --course ... --homework ...`
  - `educoder code --course ... --homework ... [--path ...] [--output ... --force]`
  - `educoder submit --course ... --homework ... --file ... [--no-wait --timeout ... --poll-interval ...]`
- 认证继续使用现有 `--zzud`、`--autologin`、`--session` 选项和 `EDUCODER_*` 环境变量。
- 课程选择支持课程 ID、课程 identifier、课程名称片段。
- 实验/作业选择支持 homework ID、名称片段。
- 课程或实验多匹配时不得静默选第一个；应报错并展示候选，要求用户提供更精确输入。
- `homeworks` 输出实验列表；默认 Rich 表格，支持 `--json`。
- `task` 输出当前关卡实用摘要；默认 Rich 文本/表格，支持 `--json`。
- `code` 默认把远端代码输出到 stdout；`--output/-o` 写入文件；目标文件已存在时默认拒绝覆盖，`--force` 才覆盖。
- `code` 默认使用当前任务详情中的 `challenge.clean_path`，也允许 `--path` 覆盖读取其他远端文件。
- `submit` 只从 `--file/-f` 读取本地代码；`--file -` 从 stdin 读取；不支持把大段代码直接作为命令行参数。
- `submit` 不开放远端代码路径覆盖，始终提交当前任务详情中的标准代码路径。
- `submit` 默认等待评测完成；支持 `--no-wait`、`--timeout`、`--poll-interval`。
- `submit --timeout` 必须传到底层轮询逻辑，不能只是 CLI 假选项。
- 新命令支持 `--json`，输出稳定的结构化摘要，不 dump 原始 Educoder API payload。
- 评测通过退出 `0`；评测失败或超时退出 `1`；成功触发 `--no-wait` 提交退出 `0`；缺认证保持退出 `2`。
- API/client 错误由 CLI 捕获后输出到 stderr，并退出 `1`。

## Acceptance Criteria

- [ ] `educoder homeworks --course <id|identifier|name>` 可展示实验列表。
- [ ] `educoder task --course ... --homework ...` 可展示当前关卡摘要。
- [ ] `educoder code --course ... --homework ...` 可把远端代码输出到 stdout。
- [ ] `educoder code --output file` 会写入文件，已存在时除非 `--force` 否则拒绝覆盖。
- [ ] `educoder submit --file file` 会读取本地文件并提交当前关卡。
- [ ] `educoder submit --file -` 会从 stdin 读取代码。
- [ ] `educoder submit --no-wait` 成功触发提交后退出 `0`。
- [ ] `educoder submit` 等待评测时，通过退出 `0`，失败/超时退出 `1`。
- [ ] 新命令的 `--json` 输出可由脚本消费。
- [ ] 多匹配课程/实验时输出候选并阻止继续执行。
- [ ] 缺认证、API 错误、上下文错误都有明确 exit code 和 stderr。
- [ ] 新行为有 focused pytest 覆盖，不访问真实 Educoder 网络。
- [ ] 本地质量命令通过：`uv run ruff format --check .`、`uv run ruff check .`、`uv run ty check`、`uv run pytest -q`。

## Definition of Done

- CLI 代码保持薄层：参数校验、调用 `EduCoderClient`、渲染输出。
- API URL、签名、请求体细节仍留在 `client.py`。
- 稳定响应摘要使用 dataclass 或显式转换逻辑，避免把原始 payload 作为用户输出。
- 认证 cookie、headers、提交代码内容、原始请求体不进入日志、错误消息或测试快照。
- README 更新新命令示例。

## Technical Approach

- 在 `cli.py` 增加复用的命令选项、JSON 输出 helper、错误渲染 helper 和任务选择流程 helper。
- 在 `client.py` 调整选择逻辑，避免 `select_course()` / `select_homework()` 静默选第一个模糊匹配；必要时增加候选异常或 helper。
- 在 `client.py` 为 `submit()` 增加 `timeout` 参数，并传给 `_poll_result()`。
- 在 `models.py` 仅在需要稳定输出摘要时补充轻量转换；不新增持久化存储。
- 在 `tests/` 增加 CLI 单元测试，使用 Typer `CliRunner` 和 fake client/monkeypatch，不访问真实网络。
- 在 `tests/test_client.py` 增加 timeout 传递或选择歧义行为的 focused 测试。

## Decision (ADR-lite)

**Context**: 项目已有同步 `EduCoderClient` 和一个小型 Typer/Rich CLI。CLI 层目前只暴露版本和课程列表，但底层已经有实验、任务详情、代码读取和单关提交流程。

**Decision**: 第一版只补齐无本地状态的显式参数命令，保持顶层扁平 CLI；不做登录、配置文件、缓存、交互式选择或 `submit-all`。

**Consequences**: 实现范围清晰，符合现有架构和安全边界；用户每次命令需要显式传入课程/实验和认证上下文。后续如果需要持久化配置或交互式选择，需要单独设计并更新 spec。

## Out of Scope

- 不新增 `submit-all` CLI 命令。
- 不实现登录流程。
- 不保存 cookie、本地配置、默认课程、默认实验或缓存。
- 不做交互式 fuzzy finder。
- 不支持多文件提交。
- 不开放 `submit --path`。
- 不接入 LLM 辅助解题。
- 不访问真实 Educoder 作为测试依赖。

## Technical Notes

- Relevant files:
  - `src/educoder_cli/cli.py`
  - `src/educoder_cli/client.py`
  - `src/educoder_cli/models.py`
  - `src/educoder_cli/errors.py`
  - `tests/`
  - `README.md`
- Relevant specs:
  - `.trellis/spec/backend/index.md`
  - `.trellis/spec/backend/directory-structure.md`
  - `.trellis/spec/backend/error-handling.md`
  - `.trellis/spec/backend/quality-guidelines.md`
  - `.trellis/spec/backend/logging-guidelines.md`
  - `.trellis/spec/backend/database-guidelines.md`
- Confirmed user decisions:
  - Use explicit arguments and environment variables; no local state.
  - Keep flat commands.
  - Add JSON mode.
  - Default `submit` waits for evaluation.
  - `code` may override path, `submit` may not.
  - Do not add `submit-all`.
