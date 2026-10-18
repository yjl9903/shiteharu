# 开通收益报告

原题：みなさまに￥化をご報告。原作者：してはる。

原片：[YouTube](https://www.youtube.com/watch?v=CEyKoT2Ue8M)；发布日期：2026-05-10。素材整理日期：2026-10-18。

当前只完成原片资源准备，尚未开始转写、翻译或字幕设计。

## 素材

- 原片：[`みなさまに￥化をご報告 [CEyKoT2Ue8M].mkv`](<../../downloads/みなさまに￥化をご報告 [CEyKoT2Ue8M].mkv>)。
- 1920×1080，平均 29.972 fps，105.408 秒，41.71 MiB。
- yt-dlp 按 `bestvideo+bestaudio` 选择 `616+251`：VP9 视频、Opus 音频；所选视频流标记为 `Premium`。恢复时以流复制合并为 MKV。
- `downloads/` 同名 `.webp` 为封面，`.description` 为原文简介，`.info.json` 为 yt-dlp 下载元数据。这些下载文件不入库。
- [source.info.json](source.info.json) 保存标题、作者、原简介、来源和媒体参数。

## 重新下载

准备 uv、Node.js 和 FFmpeg（含 ffprobe），安装方式参考 [uv](https://docs.astral.sh/uv/getting-started/installation/)、[Node.js](https://nodejs.org/en/download)、[FFmpeg](https://ffmpeg.org/download.html)。uv 会获取命令中指定的 yt-dlp。

从仓库根目录执行：

```sh
UV_CACHE_DIR=.cache/uv UV_TOOL_DIR=.cache/uv-tools \
  uv tool run --from 'yt-dlp[default]==2026.8.19' yt-dlp \
  --ignore-config --js-runtimes node --no-playlist \
  -f '616+251' --merge-output-format mkv --concurrent-fragments 8 --abort-on-unavailable-fragments \
  --write-info-json --write-description --write-thumbnail \
  -o 'downloads/%(title)s [%(id)s].%(ext)s' \
  'https://www.youtube.com/watch?v=CEyKoT2Ue8M'
```

固定格式 ID 用于重新获取本次所选的视频、音频流；平台不再提供时命令会失败。若需重新评估平台当时的最高质量，可将 `-f '616+251'` 改为 `-f 'bestvideo+bestaudio'`，并检查视频参数和字幕时序。
