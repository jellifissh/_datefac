# AI Handoff

用途：
- ChatGPT 在这里写给 Codex 的详细任务说明。
- 用户只需要让 Codex 读取 `docs/ai_handoff/NEXT_CODEX_TASK.md` 并执行。
- 避免在聊天窗口中反复复制超长提示词。

规则：
1. `NEXT_CODEX_TASK.md` 始终保存下一步 Codex 任务。
2. 任务完成后，Codex 必须更新 `docs/codex_worklog/LATEST.md`。
3. 任务完成后，Codex 必须在 `docs/codex_worklog/history/` 新增历史日志。
4. ChatGPT 在聊天中只给用户简略版说明，详细版写入本目录。
5. 不要在本目录提交 PDF 原文、完整 Excel 产物或敏感数据。
