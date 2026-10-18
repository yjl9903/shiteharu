# 石川県の存在しない街『銀沢』へ行こう

原片：[YouTube](https://www.youtube.com/watch?v=hNc8Em2PKeQ)，してはる，2026-09-26 发布。整理日期：2026-10-18。

本工程仍在制作中。修订直接更新 `translation/work/`、`design/` 和 `deliverables/` 中的当前文件，不另建版本目录、输入快照或带版本号的交付副本；核验记录随当前导出更新。

当前输出为 [1080p完整视频](deliverables/zh.performance.1080p.mp4)，以及 [中文演出ASS](deliverables/zh.performance.ass)、[中文SRT](deliverables/zh.srt)、[日文校对ASS](deliverables/ja.review.ass) 和 [日文SRT](deliverables/ja.srt)。本次导出已完成：616.141秒、1920×1080、约461 MiB；完整音视频解码通过，实看11处实际编码画面。核验见 [当前导出记录](review/current-export-qa.json)。审阅页使用当前成片；采样检查不等同连续人工观看全片。

本轮纳入 a002 句末问号、上置字幕顶部留白、a035缩小置顶、a055与c066字体修正，以及c067置顶。更早的位置字号专项覆盖288个事件，修改54条；依据见 [位置字号记录](review/composition-user-review.md) 和 [逐条修订记录](review/opening-user-revision.md)。

720p预览和软字幕MKV随当前字幕重新生成，覆盖 `deliverables/` 中的同名文件。`review/comparisons/` 中的历史局部对照片段仅作审阅证据，不代表当前成片；当前导出状态以上方核验记录为准。对照媒体不纳入 Git，需要留存的历史版本随本地制作资料另行备份。

字体采用逐条匹配的中文近似，原有日文保留；具体近似见 [差异记录](review/differences.md)。可编辑源以当前 `translation/work/` 与 `design/` 为准。MKV未嵌入字体。

## 原片与依据

- 本地原片：`../../downloads/石川県の存在しない街『銀沢』へ行こう [hNc8Em2PKeQ].mkv`。
- 1920×1080，30000/1001 fps，616.141 秒。
- 原作者明确提示九成内容是编造，故保留虚构设定和笑点。
- 内嵌字幕的字面内容与可见生命周期优先于语音自动分段；音频作为校对依据。
- 原片、提取音频、渲染视频、帧图和字体缓存不纳入 Git。

## 编辑与重建

`description.md` 保存术语与内容决策；日文及中文的人工阶段通过 `rajio segments` 修改；不修改 `transcript/raw/`。

制作工具统一使用仓库的 [Forge](../../tools/forge/README.md)，审阅使用 [Loupe](../../tools/loupe/README.md)。工程只保留内容、配置、设计与取证数据。配置路径相对本工程，字体引用 `../../fonts/`；本机字体只从被忽略的 `../../fonts/local/` 读取。

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

`source-frames` 标注请求取帧时间，`source-boundary` 和 `source-atlas` 标注实际解码 PTS。像素变化排序只提供候选，不自动确认字幕边界。旧取证参数已保存到 `research/evidence/`，历史帧索引保存到 `review/source-capture-indices.json`；事件直接引用的证据图片和最终成片采样保留在本地，其余图片可按参数重建，联系表版式可能与历史版本不同。

启动本地审阅页：

```sh
uv run --locked python tools/loupe/loupe.py --config production/ginzawa/preview.toml --serve --port 8974
```

打开命令输出的本地地址。Loupe 读取原片与当前 1080p 成片，包含全部 288 条时间轴事件。局部对照样片用于排版与动态检查，结论、疑点和检查范围保存在 `review/`。

## 完成检查

- [x] 原片完整下载及媒体参数核对
- [x] 转写服务授权、doctor 检查、原始音频转写
- [x] 全片日文主字幕按原画校对与起止帧确认
- [x] 全片简体中文翻译、三轮全文润色
- [x] 子代理逐段研究、匹配全部样式与特殊演出，两轮逐条实看
- [x] 中文字体缺字、排版、并发字幕、边界对照验证
- [x] 全片渲染、代表片段与截图对照、差异清单

技术审计覆盖 13 个字体角色、14 个实际字面，缺字、缺取证、未确认时序与机器专属路径均为零。288 个事件的 576 个时间边界均落在源 PTS 上；298 个布局采样的源字交集及未许可越界为零。19 个保守脸框候选已逐项人工复核排除，保留记录。中文通用检查的 19 条提示及日文的 49 条提示均按原画演出保留，详见 [内容审阅](review/content-review.md)。

共享 Forge 的历史测试记录包含实际编码、连续擦出与异地构建。
