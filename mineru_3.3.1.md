# 347A MinerU 3.3.1 Side-by-Side Compatibility Benchmark 说明书

## 0. 任务定位

本任务用于 DateFac 项目的 MinerU 3.3.1 旁路兼容性验证。

当前 DateFac 主线正在做金融 PDF 表格结构化清洗、质量审计、sidecar demo-only recovery expansion。MinerU 3.3.1 只作为旁路实验和未来增强候选，不直接替换当前主链路。

本任务目标不是“立刻升级主线”，而是验证：

* MinerU 3.3.1 是否能稳定运行；
* pipeline / hybrid medium / hybrid high 三种模式输出结构有何差异；
* 新版输出是否兼容 DateFac 当前 JSON / Markdown / image evidence binding；
* 新版是否能改善 image_bound_count、json_md_context_bound_count、image_missing_count、ambiguous_image_candidate_count；
* 是否需要 347B Binding Adapter Fix。

## 1. 严格禁止事项

以下事项禁止执行：

* 不要修改 `D:\_datefac` 主项目代码；
* 不要修改 `D:\_datefac_worktrees\346b4r`；
* 不要写入或覆盖当前主链路输出目录；
* 不要重跑 345D / 346B / 346B4 / 346B5 系列输出；
* 不要覆盖旧 MinerU 输出；
* 不要删除旧 MinerU 环境；
* 不要 commit / push；
* 不要全量跑批；
* 不要让 MinerU 3.3.1 输出污染当前审计链路。

## 2. 当前已跑通的新环境信息

当前可用环境：

```text
conda env: mineru331_gpu
工作目录: E:\mineru_lab
隔离目录: E:\mineru331
模型缓存: E:\mineru331\hf_cache
下载目录: E:\mineru331\downloads
smoke 输入目录: E:\mineru331\smoke_input_fresh_20260615_215912
smoke 输出目录: E:\mineru331\smoke_output_fresh_hybrid_high_gpu_20260616
```

当前关键依赖版本：

```text
torch: 2.7.1+cu126
torchvision: 0.22.1+cu126
torchaudio: 2.7.1+cu126
CUDA_PATH: D:\anaconda\envs\mineru331_gpu\Library
```

验证命令：

```powershell
conda activate mineru331_gpu

python -c "import torch, torchvision; print(torch.__version__); print(torchvision.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"
```

期望输出：

```text
2.7.1+cu126
0.22.1+cu126
True
12.6
```

如果 `torch.cuda.is_available()` 不是 `True`，不要继续跑 hybrid high。

## 3. 每次启动前置命令

每次打开新的 PowerShell 后，先执行：

```powershell
conda activate mineru331_gpu

$env:HF_ENDPOINT="https://hf-mirror.com"
$env:HF_HOME="E:\mineru331\hf_cache"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
$env:HF_HUB_DOWNLOAD_TIMEOUT="300"
$env:HF_HUB_ETAG_TIMEOUT="120"

$env:CUDA_PATH="D:\anaconda\envs\mineru331_gpu\Library"
$env:PATH="$env:CUDA_PATH\bin;$env:PATH"

Test-Path "$env:CUDA_PATH\bin"

python -c "import torch, torchvision; print(torch.__version__); print(torchvision.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"

mineru --version
mineru --help
```

其中：

```powershell
Test-Path "$env:CUDA_PATH\bin"
```

应输出：

```text
True
```

否则 lmdeploy / turbomind 可能会报：

```text
Can not find $env:CUDA_PATH
```

或找不到 `bin` 目录。

## 4. 三种 MinerU 3.3.1 运行模式

### 4.1 pipeline：CPU / 稳定保底模式

用途：

* 验证安装是否可用；
* 不依赖 VLM high；
* 可作为低成本 baseline；
* 适合普通 OCR / 表格解析 smoke test。

命令：

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_pipeline_20260616 -b pipeline
```

特点：

* 环境成本最低；
* 适合保底；
* 对图表理解和复杂语义绑定不如 hybrid high；
* 可以作为 347A benchmark 的基础对照组。

### 4.2 hybrid medium：未来普通 PDF 新默认候选

用途：

* 普通 PDF；
* 大多数日常批量解析；
* 速度优先；
* 未来可以考虑作为“普通 extraction 候选”。

命令：

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_hybrid_medium_20260616 -b hybrid-engine --effort medium
```

特点：

* 官方默认 effort；
* 速度比 high 更适合日常；
* 但 medium 会自动关闭 image/chart analysis；
* 不能直接等价替换旧主线；
* 必须先验证 JSON schema、Markdown 顺序、image path、table caption、chart block 是否兼容 DateFac 当前 evidence binding。

### 4.3 hybrid high：复杂金融研报 / 图表 / image binding 恢复模式

用途：

* 复杂金融 PDF；
* 表格图片；
* 图表；
* 旧版 image binding 失败样本；
* image_missing_count 高的样本；
* 死信队列恢复；
* 高价值 PDF 精修。

命令：

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 -o E:\mineru331\smoke_output_fresh_hybrid_high_gpu_20260616 -b hybrid-engine --effort high
```

成功日志应包含：

```text
Using lmdeploy-engine as the inference engine for VLM
Lmdeploy device is: cuda
lmdeploy backend is: turbomind
Hybrid processing window
```

特点：

* 精度和图表理解更强；
* 支持 image/chart analysis；
* 环境成本高；
* 首次运行会下载额外模型；
* 跑批成本高，不适合直接全量默认启用；
* 更适合作为 sidecar recovery / high precision rerun。

## 5. 推荐长期启动方式：常驻 mineru-api

不建议 DateFac 主流程每次都临时启动 MinerU。更推荐把 MinerU 3.3.1 当作一个旁路解析服务。

### 5.1 启动 MinerU API 服务

单独开一个 PowerShell：

```powershell
conda activate mineru331_gpu

$env:HF_ENDPOINT="https://hf-mirror.com"
$env:HF_HOME="E:\mineru331\hf_cache"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
$env:HF_HUB_DOWNLOAD_TIMEOUT="300"
$env:HF_HUB_ETAG_TIMEOUT="120"

$env:CUDA_PATH="D:\anaconda\envs\mineru331_gpu\Library"
$env:PATH="$env:CUDA_PATH\bin;$env:PATH"

mineru-api --host 127.0.0.1 --port 18080 --enable-vlm-preload true
```

浏览器访问：

```text
http://127.0.0.1:18080/docs
```

用于确认 API 服务已启动。

### 5.2 通过常驻 API 执行解析

另开一个 PowerShell：

```powershell
conda activate mineru331_gpu

mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 `
-o E:\mineru331\smoke_output_api_hybrid_high_20260616 `
--api-url http://127.0.0.1:18080 `
-b hybrid-engine `
--effort high
```

medium 模式：

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 `
-o E:\mineru331\smoke_output_api_hybrid_medium_20260616 `
--api-url http://127.0.0.1:18080 `
-b hybrid-engine `
--effort medium
```

pipeline 模式：

```powershell
mineru -p E:\mineru331\smoke_input_fresh_20260615_215912 `
-o E:\mineru331\smoke_output_api_pipeline_20260616 `
--api-url http://127.0.0.1:18080 `
-b pipeline
```

## 6. 输出目录规范

smoke test 阶段继续使用：

```text
E:\mineru331\
```

建议目录：

```text
E:\mineru331\
  smoke_input_fresh_20260615_215912\
  smoke_output_fresh_pipeline_20260616\
  smoke_output_fresh_hybrid_medium_20260616\
  smoke_output_fresh_hybrid_high_gpu_20260616\
  hf_cache\
  downloads\
```

进入正式 347A benchmark 后，才允许使用：

```text
D:\_datefac\output\mineru_331_compatibility_benchmark_347a\
```

建议结构：

```text
D:\_datefac\output\mineru_331_compatibility_benchmark_347a\
  input_manifest\
  old_mineru_reference\
  mineru331_pipeline\
  mineru331_hybrid_medium\
  mineru331_hybrid_high\
  comparison_reports\
  evidence_binding_audit\
```

禁止写入：

```text
D:\_datefac\output\345D*
D:\_datefac\output\346B*
D:\_datefac\output\346B4*
D:\_datefac\output\346B5*
```

## 7. 输出文件固定证据

每次跑完后生成 manifest 和 sha256：

```powershell
$out = "E:\mineru331\smoke_output_fresh_hybrid_high_gpu_20260616"

$manifestOut = "${out}_manifest.txt"
$hashOut = "${out}_sha256.txt"

Get-ChildItem $out -Recurse -File |
Sort-Object FullName |
Select-Object FullName, Length, LastWriteTime |
Out-File $manifestOut -Encoding utf8

Get-ChildItem $out -Recurse -File |
Sort-Object FullName |
Get-FileHash -Algorithm SHA256 |
Out-File $hashOut -Encoding utf8
```

统计文件类型：

```powershell
Get-ChildItem $out -Recurse -File |
Group-Object Extension |
Select-Object Name, Count
```

统计输出体积：

```powershell
(Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
```

## 8. DateFac 对接原则

MinerU 3.3.1 不直接替换 DateFac 主线 parser。

正确对接方式：

```text
DateFac 主线
  ↓
旧 MinerU / 当前 pipeline 继续处理常规样本
  ↓
识别低置信 / image_missing / ambiguous / complex table 样本
  ↓
旁路调用 MinerU 3.3.1 hybrid medium 或 hybrid high
  ↓
生成独立输出 artifact
  ↓
347B Binding Adapter 标准化
  ↓
进入 DateFac evidence binding / audit
```

新版 MinerU 定位：

```text
sidecar high-precision recovery engine
```

不是：

```text
current parser direct replacement
```

## 9. DateFac 统一中间层建议

建议把 MinerU 输出标准化为：

```text
MinerUArtifactSet
```

字段：

```text
pdf_id
source_pdf_sha256
mineru_version
backend
effort
runtime_seconds
output_root
md_path
content_list_json_path
content_list_v2_json_path
middle_json_path
model_json_path
images_dir
layout_pdf_path
span_pdf_path
table_count
chart_count
image_count
page_count
```

每个 block 标准化为：

```text
block_id
page_idx
type
sub_type
bbox
text
html
img_path
caption
footnote
source_json_file
source_md_anchor
image_exists
image_sha256
```

## 10. Adapter 必须处理的兼容差异

### 10.1 输出目录差异

旧版可能是：

```text
auto
```

新版 hybrid high 可能是：

```text
hybrid_auto
```

Adapter 必须同时支持：

```text
auto
hybrid_auto
```

### 10.2 图片路径不能依赖 hash

新旧版本图片路径都类似：

```text
images/<hash>.jpg
```

但 hash 不稳定，不能做跨版本精确匹配。

推荐绑定键：

```text
page_idx + bbox + type + caption + image_exists + image_sha256
```

不要依赖：

```text
old_img_hash == new_img_hash
```

### 10.3 caption 位置变化

旧版 caption 可能作为 table 前面的 text/title block。

新版更可能直接进入：

```text
table_caption
chart_caption
```

Adapter 优先级：

```text
1. block.table_caption / block.chart_caption
2. 邻近上方 text/title block
3. 邻近下方 footnote/source block
4. page-level context
```

### 10.4 chart block 变化

新版可能输出：

```text
type: chart
content: markdown table / approximate chart data
chart_caption
img_path
```

DateFac 不能把 chart 近似数据当成高精度财务指标，但可以作为：

```text
chart evidence
visual context
market performance context
```

### 10.5 dirty row 处理

新版可能把旧版粘连值拆成空 key 行，例如：

```html
<tr><td></td><td>1</td></tr>
```

清洗规则：

```text
如果 key 为空且 value 是孤立页码/噪声，则丢弃
如果 key 为空但 value 是长文本/注释，则保留为 footnote candidate
```

## 11. 347A Benchmark 指标

至少统计：

```text
pdf_count
page_count
runtime_seconds
success_pdf_count
failed_pdf_count
json_output_count
md_output_count
table_image_count
page_image_count
table_crop_count
chart_count
table_count
image_count
output_size_mb
json_schema_changed
md_placeholder_changed
image_path_pattern_changed
datefac_binding_reusable
image_bound_count_old
image_bound_count_new
json_md_context_bound_count_old
json_md_context_bound_count_new
image_missing_count_old
image_missing_count_new
ambiguous_image_candidate_count_old
ambiguous_image_candidate_count_new
adapter_fix_required
recommended_decision
```

## 12. 推荐决策规则

### 12.1 保持旧版主链路

使用决策：

```text
KEEP_OLD_MINERU_FOR_CURRENT_CHAIN
```

条件：

```text
新版只提升速度；
新版破坏 DateFac image/json binding；
新版输出目录/schema 变化大；
新版 image_missing_count 没下降；
新版 ambiguous_image_candidate_count 上升；
新版运行成本过高。
```

### 12.2 未来新数据采用 3.3.1

使用决策：

```text
ADOPT_MINERU_331_FOR_FUTURE_EXTRACTION
```

条件：

```text
新版输出结构稳定；
DateFac binding 可复用；
image_bound_count 明显提升；
json_md_context_bound_count 明显提升；
image_missing_count 下降；
无需明显 adapter fix。
```

### 12.3 适配后采用 3.3.1

推荐当前决策：

```text
ADOPT_MINERU_331_AFTER_BINDING_ADAPTER_FIX
```

条件：

```text
新版质量更强；
caption/chart/reading order/image evidence 更好；
但目录结构、caption 字段、chart block、图片 hash、schema 有差异；
需要先做 347B Binding Adapter Fix。
```

## 13. medium 能不能直接当旧主线替代？

不能直接替代。

更准确结论：

```text
medium 可以作为未来普通 PDF 的新默认候选；
不能直接作为当前旧 MinerU / marker 主链路的无缝替代。
```

原因：

```text
1. medium 会自动关闭 image/chart analysis；
2. DateFac 当前痛点包含 image binding 和 chart/table evidence；
3. medium 的输出目录、caption、chart block、content_list_v2 可能与旧版不同；
4. 旧版主链路已经有历史审计输出，不能回头污染；
5. 必须先跑 347A side-by-side benchmark；
6. 必须先做 347B Binding Adapter Fix；
7. 通过后，medium 才能作为未来 ordinary extraction candidate。
```

推荐模式分工：

```text
pipeline:
  CPU / 稳定保底 / smoke test / baseline

hybrid medium:
  普通 PDF / 日常批量 / 速度优先 / 未来默认候选

hybrid high:
  复杂金融研报 / 图表 / 表格图片 / image_missing 恢复 / 高价值样本
```

## 14. 最终建议

当前不替换 DateFac 主线。

推荐路线：

```text
347A:
  做 side-by-side benchmark

347B:
  做 Binding Adapter Fix

347C:
  做 Selective Recovery Routing
```

长期策略：

```text
旧主线:
  继续负责当前已审计链路和历史输出

MinerU 3.3.1 medium:
  未来普通新数据候选

MinerU 3.3.1 high:
  高精度旁路恢复引擎

pipeline:
  CPU 保底与回归验证
```

当前推荐决策：

```text
ADOPT_MINERU_331_AFTER_BINDING_ADAPTER_FIX
```

不要把 3.3.1 输出直接塞进 345D 到 346B5Q 的历史链路。新版只影响未来 extraction，不覆盖已有审计证据链。
