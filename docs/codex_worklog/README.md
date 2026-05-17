# Codex Worklog

用途：
- 记录 Codex 每次任务的执行结果。
- 让 ChatGPT 可以通过 GitHub 读取 LATEST.md，继续给出下一步指令。
- 避免人工复制粘贴终端输出。

规则：
1. 每次 Codex 完成任务后，必须更新 LATEST.md。
2. 每次 Codex 完成任务后，必须在 history/ 中新增一份时间戳日志。
3. LATEST.md 内容应与最新 history 文件一致，或者包含指向最新 history 文件的摘要。
4. 每次日志必须包含：
   - task_title
   - started_at
   - finished_at
   - git_commit_before
   - git_commit_after
   - commands_run
   - files_changed
   - outputs_generated
   - checks_performed
   - result_summary
   - remaining_issues
   - next_step_suggestion
   - safety_notes
