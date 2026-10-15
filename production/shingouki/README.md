# 『信号機の墓場』へ行こう 字幕制作工程

原始视频位于 `../../downloads/『信号機の墓場』へ行こう [l_jfyIEddfw].mkv`，不修改原文件。所有时间使用原视频的时间轴；画面烧录字幕优先于自动转写。

## 交付文件

- `deliverables/zh.preview.720p.mp4`：全片中文演出预览，仅叠加中文。
- `deliverables/zh.performance.1080p.mp4`：1080p 中文演出版。
- `deliverables/zh.performance.ass`：可编辑中文演出字幕。
- `deliverables/ja.review.ass`：独立日文审阅轨；不要同时烧入中文预览。
- `deliverables/ja.srt` / `zh.srt`：同时间轴的纯文本字幕，含并发旁注；需完整演出及并发显示时使用 ASS。
- `deliverables/comparisons/`：左边原片、右边中文演出的代表段落。

## 修改位置

| 内容 | 可编辑源 |
| --- | --- |
| 主字幕中日文、常规时间轴 | `translation/work/segments.toml`，使用 `rajio segments edit/apply --stage translation` |
| 字体名称和文件路径 | `design/fonts.json`（相对路径以本工程目录为基准，共享字体位于 `../../fonts/`） |
| 默认字号、位置、描边 | `design/defaults.json` |
| 单条字幕字体、位置、动画、并发视觉时间 | `design/events-*.json` |
| 没有念出的画面旁注及其翻译 | `design/events-*.json` 中 `supplemental: true` 事件 |
| 对照片段选择 | `design/clips.json` |
| 演出生成逻辑 | `scripts/pipeline/subtitles/build.py` |

不要编辑 `transcript/raw/`。它是原始 ASR 参考，不是最终字幕。`output/` 是 rajio 的标准导出；最终演出及并发视觉时间以 `deliverables/` 为准。`design/SCHEMA.md` 解释各参数。

原视频字幕有刻意省略、提炼或改写旁白的情况，主轨以原画文字为准。并发气泡、旁注允许在最终 ASS 中重叠；它们不受 rajio 单线时间轴限制。`timing_status` 区分逐帧确认、采样和仅语音内容。

## 脚本组织

工程命令统一通过 `python3 scripts/run.py <命令>` 调用，`--help` 查看完整列表。内部按字幕、字体和交付分组，目录职责与写入范围见 [脚本说明](scripts/README.md)。

## 重建

本机使用 rajio 0.2.1、Python 3.14.2、FFmpeg 7.1.1（含 libass）、zsh。共享字体及许可统一保存在仓库顶层 `fonts/`，来源见 [字体来源](../../fonts/SOURCES.md)。字体必须在本机可用；`scripts/run.py fonts-prepare` 根据配置复制到本地渲染缓存，不需要改动系统字体。渲染字体缓存和运行日志位于 `.cache/`，不纳入交付。

从本目录运行：

```sh
python3 scripts/run.py build
python3 scripts/run.py fonts-prepare
python3 scripts/run.py render preview
python3 scripts/run.py render full
python3 scripts/run.py render soft
python3 scripts/run.py compare-clips
python3 scripts/run.py compare-stills
python3 scripts/run.py package
```

配置、报告和预览元数据中的文件路径统一相对本工程目录解析；`clips/*/clip.toml` 的 `source_media` 也遵循 rajio 的工程目录基准。Python 脚本以 `__file__` 定位工程，避免依赖启动命令时的工作目录。

未随仓库分发的本机字体放在仓库顶层 `fonts/local/`（已被 Git 和交付打包脚本排除）。按 `design/fonts.json` 准备 MiSans-Bold.ttf、LXGWWenKai-Regular.ttf、SarasaMonoSC-Bold.ttf、Songti.ttc 和ヒラギノ角ゴシック W6.ttc。从自己的合法字体安装中复制同名文件即可；保留实际字体文件，不使用指向本机绝对路径的软链接。字体预览会读取该目录内同字体家族的其他字重。配置中只填写 `../../fonts/local/文件名`，不填写用户目录或系统安装位置。

`soft` 无损复制原始音视频并附加可开关的中文、日文 ASS；默认仅开启中文。播放器需要支持 libass 或 ASS 样式并能找到配置字体。烧录预览不依赖播放端字体。

若修改 rajio 工作文件，要同步标准导出：

```sh
rajio check . --stage translation --language zh
rajio check . --stage translation --language ja
rajio . --reset export --commit --continue=until-manual
```

原画连续切换、夸张长句、短促反应与标点可能刻意不符合 rajio 的阅读规则。只为经人工核对的具体字幕保留对应 `skip_checks` 及原因，不要批量消除警告，也不要用格式规范改坏原片节奏。

## 时间与打包

ASS 使用百分之一秒，生成器向下量化原片帧时间，SRT 保留毫秒时机。动画时长、字号、位置和文字均可独立修改后重建。

`deliverables/editable-project.zip` 只收录字幕文字、设计、共享字体及许可和重建脚本。检查页、CSV/JSON 检查索引和审计报告已删除，构建不再生成这些文件。必要的运行缓存写入 `.cache/`；本机字体和视频不装入工程包。

解压时保留仓库目录结构，并按上述说明准备源视频和本机字体。字体对比页直接读取字幕配置用于导航，不依赖交付目录中的检查索引。
