# 石川県の存在しない街『銀沢』へ行こう

原片：[YouTube](https://www.youtube.com/watch?v=hNc8Em2PKeQ)，してはる，2026-09-26 发布。整理日期：2026-10-18。

当前工程使用 `translation/work/`、`design/` 和 `deliverables/` 中的文件；修订直接更新当前文件，不另建版本目录、输入快照或带版本号的交付副本。

交付入口为 [1080p完整视频](deliverables/zh.performance.1080p.mp4)、[720p预览](deliverables/zh.preview.720p.mp4)、[软字幕MKV](deliverables/editable-tracks.mkv)，以及 [中文演出ASS](deliverables/zh.performance.ass)、[中文SRT](deliverables/zh.srt)、[日文校对ASS](deliverables/ja.review.ass) 和 [日文SRT](deliverables/ja.srt)。审阅页读取当前1080p成片。MKV未嵌入字体。

`review/comparisons/` 保存局部对照媒体；已有样片不会随工作稿同步，需要留存的历史样片另行备份。字体、画面文字范围与动画近似见 [内容与制作说明](description.md)。

## 原片与依据

- 本地原片：`../../downloads/石川県の存在しない街『銀沢』へ行こう [hNc8Em2PKeQ].mkv`。
- 1920×1080，30000/1001 fps，616.141 秒。
- 原作者明确提示九成内容是编造，故保留虚构设定和笑点。
- 内嵌字幕的字面内容与可见生命周期优先于语音自动分段；音频作为校对依据。
- 原片、提取音频、渲染视频、帧图和字体缓存不纳入 Git。

## 编辑与重建

[description.md](description.md) 保存术语与内容决策，[设计说明](design/SCHEMA.md) 说明演出参数；日文及中文的人工阶段通过 `rajio segments` 修改；不修改 `transcript/raw/`。

制作工具统一使用仓库的 [Forge](../../tools/forge/README.md)，审阅使用 [Loupe](../../tools/loupe/README.md)。工程只保留内容、配置、设计与取证数据。配置路径相对本工程，字体引用 `../../fonts/`；本机字体只从被忽略的 `../../fonts/local/` 读取。派生字体配方见 [字体研究说明](research/fonts/README.md)。

B 站投稿使用工程根目录的 [bilipack.toml](bilipack.toml)，导入时选择 `production/ginzawa/`。

以下命令从仓库根目录执行。

```sh
uv sync --locked
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml build
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml fonts-prepare
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml render preview
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml render full
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml render soft
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml compare-clips
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml compare-stills
```

上述 `compare-clips` 按 `design/clips.toml` 读取已构建的 ASS 和字体缓存，生成 `review/comparisons/` 中的对照视频；`compare-stills` 再提取中点图。只重做对照时，先执行 `build` 和 `fonts-prepare`，已有样片不会随工作稿自动更新，重跑会覆盖同名文件。

辅助取证命令也使用同一个环境：

```sh
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-frames --start 0 --end 36 --step 1 --label opening
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-boundary 1.5 --radius 0.3 --label opening-change
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-atlas --plan research/evidence/c-exact.toml --label c-exact-rebuilt
```

`source-frames` 标注请求取帧时间，`source-boundary` 和 `source-atlas` 标注实际解码 PTS。像素变化排序只提供候选，不自动确认字幕边界。取证参数与重建方法见 [原片取证说明](research/evidence/README.md)，历史帧索引保存到 `review/source-capture-indices.json`；事件直接引用的证据图片和最终成片采样保留在本地，其余图片可按参数重建，联系表版式可能与历史版本不同。

启动本地审阅页：

```sh
uv run --locked python tools/loupe/loupe.py --config production/ginzawa/preview.toml --serve --port 8974
```

打开命令输出的本地地址。Loupe 读取原片与当前 1080p 成片，包含全部 288 条时间轴事件。局部对照样片用于排版与动态检查。
