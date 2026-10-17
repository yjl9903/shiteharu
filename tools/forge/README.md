# Forge

仓库共用的字幕制作工具：读取工程配置与人工确认的数据，构建 ASS/SRT、准备字体、渲染视频、生成对照与交付包。字体研究也使用同一套实现，具体字体、事件选择和提案决策由工程数据提供。

## 使用

先在仓库根目录执行 `uv sync --locked`；视频命令需要含 libass 的 FFmpeg 和 ffprobe。TOML 配置通过 tomlkit 写回以保留注释；所有 Python 依赖共用仓库根目录环境，见[运行环境](../../docs/reproducibility.md#python-运行环境)。

从仓库根目录执行：

```sh
uv run --locked python tools/forge/forge.py --config production/shingouki/forge.toml build
uv run --locked python tools/forge/forge.py --config production/shingouki/forge.toml render preview
uv run --locked python tools/forge/forge.py --config production/shingouki/forge.toml --help
```

`--config` 指向工程根目录的 TOML 配置。配置内的路径，包括研究配方里的路径，都相对该工程目录解析。启动命令可在任意目录执行，只需正确指定入口与配置位置。工程不需要 Python 文件、启动器或兼容入口。

## 配置与输入

[现有工程配置](../../production/shingouki/forge.toml)列出实际制作参数；[小型测试配置](tests/fixtures/portable/forge.toml)展示独立输入结构，不在 `production/` 添加样例工程。

| 配置 | 用途 |
| --- | --- |
| `title`、`canvas`、`duration` | ASS 标题、设计坐标系和允许的时间范围。坐标系属于设计输入，不随预览缩放改变；`duration` 使纯字幕构建不必读取视频。 |
| `timeline`、`collection`、`source_text`、`text` | 人工确认的 TOML/JSON 时间轴、集合名与双语字段。JSON 数组可省略 `collection`。 |
| `defaults`、`fonts`、`overlays` | 默认演出、字体角色及逐事件设计文件。事件文件使用 `[[events]]`，片段文件使用 `[[clips]]`；格式与[设计说明](../../production/shingouki/design/SCHEMA.md)一致；工程内容保存在各自文件中。 |
| `media_session` 或 `media` | 唯一原片来源：读取指定会话的 `input.media`，或直接指定视频。两者只配置一个。 |
| `ass_style`、`default_font`、`review`、`max_width` | ASS 基础样式、主轨默认字体角色、审阅轨排版和默认宽度限制。 |
| `output` 与 `*_ass`、`*_srt` | 输出目录及字幕文件名。 |
| `font_cache`、`shared_fonts` | 渲染字体缓存与已采纳字体的保存目录。 |
| `render` | preview/full/soft 输出文件、预览宽度、编码参数和软字幕语言标签。缩放保留视频比例，完成后用 ffprobe 校验时长。 |
| `clips`、`comparisons`、`comparison_width` | 对照片段列表、输出位置与单侧宽度。 |
| `calibration` | 顶部校准的可见边距与筛选位置。 |
| `research` | 可选研究配方 TOML。普通构建、渲染和 Loupe 不读取它。 |
| `package` | ZIP 位置与需要加入的工程资料列表。共享工具、环境锁文件、字幕输入和本工程配置引用的可分发字体由打包器加入；`include_evidence = true` 可额外收录事件引用的取证图片。 |

研究配方包含候选来源、字体映射、样例 ID、派生字体名称和许可，以及逐角色／逐事件提案规则。规则的 `set` 为固定值，`per_fontsize` 为按字号计算并保留两位小数的系数，`scale_x_cap` 为横向缩放上限。新增工程只需提供自己的配置、时间轴、设计和资源；需要研究时再提供配方。不要把单片 ID、字体选择或结论加入公共 Python。

## 命令与写入范围

| 命令 | 作用及输出 |
| --- | --- |
| `build [--output DIR]` | 生成主轨、审阅轨 ASS 与两份 SRT。输出目录可覆盖，用于回归比较。 |
| `fonts-prepare` | 校验并复制配置字体到缓存，移除缓存中不再配置的字体。 |
| `render [preview\|full\|soft]` | 构建字幕、准备字体、渲染所选视频；成功并通过时长校验后才替换目标。 |
| `compare-clips [FILTER]`、`compare-stills` | 按工程选定片段生成原片／译文对照视频和截图。 |
| `package` | 包含共享工具的可编辑工程 ZIP，保留仓库结构；排除本机字体、环境与缓存。视频按工程说明另行准备。 |
| `source-frames --start S [--end E --step N --label NAME]` | 采样原片并生成联系表；标签是请求时间，不是字幕边界认证。 |
| `source-boundary TIME [--radius R --crop x,y,w,h --label NAME]` | 提取时间附近的全部解码帧，标注真实 PTS，保存捕获参数。 |
| `review-stills [--start S --end E --label NAME --at TIME]` | 按每条事件中点或指定时间生成原片／译文对照；使用当前构建的 ASS。 |
| `audit [--output PATH]` | 检查所有事件字形、逐帧状态、设计描述、证据引用及机器路径，保存字体哈希。 |
| `audit-layout [--start S --end E --label NAME]` | 渲染透明背景墨迹，标记与源字框重叠、触边的候选；仍须人工查看。 |
| `calibrate-top` | **修改设计位置**，通过实际 libass 渲染测量顶部字形。结果仍需人工检查。 |
| `fonts-merge` | **修改设计与共享字体**，预检后合并已审阅的提案；不属于日常构建。 |
| `research-discover`、`research-download`、`research-download-extra` | 查询候选发布记录与下载工程指定资源。 |
| `research-capture`、`research-specimens`、`research-sheets` | 生成指定样例画面、字体试样与研究对照图。 |
| `research-diamond`、`research-fracture` | 根据指定轮廓、文字及许可生成有限字集派生字体。 |
| `research-propose` | 应用数据中的字体提案规则，检查覆盖并生成试排；不修改正式设计。 |
| `research-reel`、`research-render` | 输出研究提案的摘录或全片视频，不发布到 Loupe。 |

每条命令支持 `--help`。参数校验在加载实际实现之前完成，帮助和非法参数不会触发写入。下载后的 7z 等外部素材准备步骤按工程研究说明执行；缺少素材会明确失败，不自动换用系统字体。

`fonts-merge` 将新字体放到 `shared_fonts/<文件名去扩展名>-<内容哈希前16位>/`，已在共享目录内的资产保留原路径。任何已有文件（包括许可）的内容冲突都会在写入设计前报错，不覆盖另一工程正在引用的资产。提案中的 `old_` 角色仅用于研究对照，合入时还原为原角色；若原角色已被替换或提案过期则报错，须重新生成提案。

字体合入和打包携带同目录的同名字体说明文件，以及 `OFL*`、`LICENSE*`、`LICENCE*`、`COPYRIGHT*`、`README*` 和 `provenance` 文档（TXT/MD/JSON/TOML）。打包保留共享来源索引，但不再整包收录 `fonts/`；研究配方中 diamond/fracture 引用的共享源字体和许可也会加入。`fonts/local/` 始终排除。其他研究输入通过 `package.include` 明确声明或按工程说明重新准备。

混合字体使用 `text_runs = [{length = 3, font_role = "brush"}, ...]`，只指定连续字符数量和字体角色，不复制正文。数量之和必须等于译文长度，不能同时使用逐行布局、竖排或逐字动画。`typewriter` 可用 `reveal_ms` 为每个非换行字符提供递增的出现时刻；未指定时继续使用 `char_ms`。这些参数必须有原片依据。

审计字段 `source_boxes` 使用画布坐标的 `[left, top, right, bottom]` 矩形；`evidence` 为工程相对截图路径，`timing_status = "frame-confirmed"` 只适用于确实查看过相邻源帧的事件。技术审计不会自动做出这个判断，且联系表采样不能冒充完整动态观看。

## 实现与验证

`forge.py` 解析参数；`pipeline/paths.py` 载入显式工程上下文；`subtitles/`、`fonts/`、`delivery/`、`research/` 分别负责对应流程。文字分段与字体角色解析和 Loupe 共用 `tools/captions/`，复制工具时须一并保留。内部模块由 CLI 在配置完成后运行，不作为独立脚本或多工程常驻服务接口。

```sh
uv run --locked python -m unittest discover -s tools/forge/tests -v
```

测试使用临时工程与生成的测试字体，验证异地构建、错误输入、提案缩放、真实 FFmpeg 导出及打包后重建，不依赖现有成片或本机字体。缺少 FFmpeg 时视频集成测试会明确跳过；自动检查不代表字幕人工验收。

`source-atlas --plan research/evidence/c-exact.toml --label c-exact` 从工程相对路径读取 TOML 取证配方。配方包含 `windows = [{start=..., end=...}]`，或 `centers`、`offset`、`duration`；可设置 `crop=[x,y,width,height]`、`width`、`stride`、`columns`、`groups_per_sheet`。指定 `white_threshold` 时，按相邻白色像素掩码变化选出一个候选，`candidate_neighbors` 控制上下文帧数。输出记录真实 PTS 和全部配方；候选不是字幕边界判定，仍须人工查看。

连续擦出使用 `effect="wipe"`、`reveal_box=[left,top,right,bottom]` 与 `in_ms`；可选 `reveal_initial_width` 保留首帧已出现的笔画。它使用固定锚点的动画矩形裁切，适合源画连续露出半字的情况，和 `typewriter` 的整字显现不同。实际中间帧与末帧仍需对照核验。
