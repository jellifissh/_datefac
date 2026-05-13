# _datefac

pdf transform excel

本项目用于将券商研报 PDF 转换为可追溯、可复核的结构化数据资产。

## 主要能力
- PDF -> Markdown 缓存
- 表格提取、清洗、分类
- 核心财务指标标准化输出
- 资产包批量回归报告

## 运行环境
- Windows
- Python 3
- Conda 环境：`factory_v4`

## 典型运行
```powershell
conda run -n factory_v4 python D:\_datefac\factory_core.py
```

## 回归报告
```powershell
conda run -n factory_v4 python D:\_datefac\tools\build_regression_report.py --output-dir D:\_datefac\output
```
