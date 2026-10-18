# 石川県の存在しない街『銀沢』へ行こう

原片：[YouTube](https://www.youtube.com/watch?v=hNc8Em2PKeQ)，してはる，2026-09-26 发布。整理日期：2026-10-18。

本工程仍在制作中，不使用发布版本编号。字幕、设计和当前成片持续按审阅意见更新。

当前输出为 [1080p完整视频](deliverables/zh.performance.1080p.mp4)，以及 [中文演出ASS](deliverables/zh.performance.ass)、[中文SRT](deliverables/zh.srt)、[日文校对ASS](deliverables/ja.review.ass) 和 [日文SRT](deliverables/ja.srt)。本次导出已完成：616.141秒、1920×1080、约461 MiB；完整音视频解码通过，实看11处实际编码画面。核验见 [当前导出记录](review/current-export-qa.json)。审阅页使用当前成片；采样检查不等同连续人工观看全片。

本轮纳入 a002 句末问号、上置字幕顶部留白、a035缩小置顶、a055与c066字体修正，以及c067置顶。更早的位置字号专项覆盖288个事件，修改54条；依据见 [位置字号记录](review/composition-user-review.md) 和 [逐条修订记录](review/opening-user-revision.md)。

`deliverables/` 中的720p预览、软字幕MKV、ZIP和对照片段是较早的制作产物，本次不更新，不能代表当前字幕设计。旧审阅记录中的版本称呼仅为当时制作记录，不代表对外发布。

字体采用逐条匹配的中文近似，原有日文保留；具体近似见 [差异记录](review/differences.md)。可编辑源以当前 `translation/work/` 与 `design/` 为准。MKV未嵌入字体；工程包不含原视频、本机字体或凭据。

## 原片与依据

- 本地原片：`../../downloads/石川県の存在しない街『銀沢』へ行こう [hNc8Em2PKeQ].mkv`。
- 1920×1080，30000/1001 fps，616.141 秒；SHA-256 见 `session.toml`。
- 原作者明确提示九成内容是编造，故保留虚构设定和笑点。
- 内嵌字幕的字面内容与可见生命周期优先于语音自动分段；音频作为校对依据。
- 原片、提取音频、渲染视频、帧图和字体缓存不纳入 Git。

## 编辑与重建

`description.md` 保存术语与内容决策；日文及中文的人工阶段通过 `rajio segments` 修改；不修改 `transcript/raw/`。

制作工具统一使用仓库的 [Forge](../../tools/forge/README.md)，审阅使用 [Loupe](../../tools/loupe/README.md)。工程只保留内容、配置、设计与取证数据。配置路径相对本工程，字体引用 `../../fonts/`；本机字体只从被忽略的 `../../fonts/local/` 读取。

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
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml package
```

辅助取证命令也使用同一个环境：

```sh
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-frames --start 0 --end 36 --step 1 --label opening
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-boundary 1.5 --radius 0.3 --label opening-change
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml source-atlas --plan research/evidence/c-exact.toml --label c-exact-rebuilt
```

`source-frames` 标注请求取帧时间，`source-boundary` 和 `source-atlas` 标注实际解码 PTS。像素变化排序只提供候选，不自动确认字幕边界。旧取证参数已保存到 `research/evidence/`，历史帧索引保存到 `review/source-capture-indices.json`；工程包收录事件直接引用的证据图片和最终成片采样，其余图片可按参数重建，联系表版式可能与历史版本不同。

启动本地审阅页：

```sh
uv run --locked python tools/loupe/loupe.py --config production/ginzawa/preview.toml --serve --port 8974
```

打开命令输出的本地地址。预览明确使用原片与最终 1080p 成片，包含全部 288 条时间轴事件。

## 完成检查

- [x] 原片完整下载及媒体参数核对
- [x] 转写服务授权、doctor 检查、原始音频转写
- [x] 全片日文主字幕按原画校对与起止帧确认
- [x] 全片简体中文翻译、三轮全文润色
- [x] 子代理逐段研究、匹配全部样式与特殊演出，两轮逐条实看
- [x] 中文字体缺字、排版、并发字幕、边界对照验证
- [x] 全片渲染、代表片段与截图对照、差异清单、可编辑打包

技术审计覆盖 13 个字体角色、14 个实际字面，缺字、缺取证、未确认时序与机器专属路径均为零。288 个事件的 576 个时间边界均落在源 PTS 上；298 个布局采样的源字交集及未许可越界为零。19 个保守脸框候选已逐项人工复核排除，保留记录。中文通用检查的 19 条提示及日文的 49 条提示均按原画演出保留，详见 [内容审阅](review/content-review.md)。

共享 Forge 的 8 项测试通过，包括实际编码、连续擦出、异地构建与工程包重建。当前工程包的解压重建结果见 `review/package-verification.json`。


## B 站投稿包（Bilipack）

独立投稿目录：`deliverables/bilipack/`。在 [B 站投稿页](https://member.bilibili.com/platform/upload/video/frame) 的「上传 Bilipack 目录」中选择此目录。它只包含 `bilipack.toml`、`deliverables/zh.performance.1080p.mp4` 和 `deliverables/cover.jpg`；无需上传整个制作工程。

投稿配置编辑入口为本工程根目录的 [bilipack.toml](bilipack.toml)。包内保留相同相对目录结构，配置可原样复制。当前标题为「【熟肉】去石川县并不存在的城市『银泽』吧 してはる」，沿用上一期的「动画」分区，声明为转载，关闭自制禁止转载声明。简介包含原简介中文翻译、原视频与制作信息、逐字保留的日文简介。原作者提示九成内容为虚构，中文保留该提示。已烧录中文字幕，不额外导入 SRT；未设置定时、合集、活动和互动开关。

[source.info.json](source.info.json) 保存下载时元数据中的标题、作者、发布日期、链接、原始简介与封面 URL，不包含本机路径。原简介中的 LINE 链接原样保留截断文本；中文部分采用仓库首页记录的完整贴图链接。封面使用原视频的 1280×720 JPEG，4:3 裁剪靠右以保留「銀沢」标题。封面 SHA-256：`305d821666903c8e8df99be757ef5abd74794600d93acdb230cbe35aa4958a2d`。

从仓库根目录重新准备封面并组包（先按上文生成当前 1080p 成片；更新配置或成片后需重新复制）：

```sh
curl -fL https://i.ytimg.com/vi/hNc8Em2PKeQ/maxresdefault.jpg -o production/ginzawa/deliverables/cover.jpg
mkdir -p production/ginzawa/deliverables/bilipack/deliverables
cp production/ginzawa/bilipack.toml production/ginzawa/deliverables/bilipack/bilipack.toml
cp production/ginzawa/deliverables/zh.performance.1080p.mp4 production/ginzawa/deliverables/bilipack/deliverables/
cp production/ginzawa/deliverables/cover.jpg production/ginzawa/deliverables/bilipack/deliverables/
```

配置依据为 2026-10-18 读取的 [Bilipack README](https://github.com/yjl9903/bilipack/blob/main/README.md) 与 [schema.ts](https://github.com/yjl9903/bilipack/blob/main/packages/bilipack/src/config/schema.ts)。本次打包检查见 [bilipack-validation.json](review/bilipack-validation.json)，包括上游 schema 校验、包内文件校验及完整音视频解码；这些检查不替代全片人工观看或 B 站页面实际导入验收。提交前请在页面检查分区、封面裁剪及投稿信息。
