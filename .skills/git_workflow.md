# Skill: Git 工作流

## 每轮标准流程
1. 开始先看 `git status`。  
2. 完成修改后先 `py_compile`。  
3. 验证通过后输出 `git diff --stat`。  
4. 使用简洁英文 `commit message`。  
5. 推送到 `origin/main`。  
6. 推送后执行 `git log --oneline --decorate -5`。

## 提交边界
- 不要提交 `output` 大文件、`debug_reports`、临时缓存。
- 不要把本轮无关文件一起提交。
- 仅提交本轮需求涉及文件，保证可审计。

## 风险操作规范
- 不要 `reset` / `rebase`，除非用户明确要求。
- 遇到提交拦截（自动审查/权限）：
  - 先说明拦截原因
  - 等用户确认后重试
- 遇到 `index.lock` 或权限问题：
  - 先检查是否有 git 进程
  - 不要盲删锁文件

## 输出要求
- 提交后回报：
  - commit id
  - push 结果
  - 最新 5 条 log
- 若未完成 push，必须明确阻塞原因和当前仓库状态。
