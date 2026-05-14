# Skill: 回归验证流程

## 通用验证（按需执行）
- 编译修改过的文件：`python -m py_compile ...`
- 必要时主流程回归：  
  `D:\anaconda\envs\factory_v4\python.exe D:\_datefac\factory_core.py`
- 必要时批量回归报告：  
  `D:\anaconda\envs\factory_v4\python.exe D:\_datefac\tools\build_regression_report.py`
- 必要时运行诊断工具：  
  - `tools/check_asset_consistency.py`
  - `tools/compare_raw_vs_structured.py`

## 05 相关改动后的强制检查
- 样本范围：至少三个一致性 OK 资产包。
- 输出字段：
  - 抽取明细行数
  - 非空指标数
  - 命中指标
  - 未命中指标
  - 误抽检查（同比/增速/扣非/少数股东损益）
  - `header_repaired` 数量
  - `source_table_index` 分布

## 路径/产物相关改动后的强制检查
- 是否出现 `OSError [Errno 22]`。
- 是否生成乱码文件名或非法路径。
- 是否生成 `14_invalid_output_paths_report.xlsx`。
- 是否误删历史产物（严格禁止）。

## 分层归因顺序
1. 先看一致性（12）
2. 再看抽取层（02A/10）
3. 再看后处理（02/11）
4. 最后看标准化（05/13）

## 汇报模板建议
- 改动范围（改了什么、没改什么）
- 执行命令
- 样本结果表
- 分层结论（extraction / postprocess / financial_standardizer）
- 风险与下一步建议
