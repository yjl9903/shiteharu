#!/bin/zsh
set -eu
root=${0:A:h:h:h:h}
cd "$root"
mode=${1:-preview}
"${PYTHON:-python3}" scripts/run.py build
"${PYTHON:-python3}" scripts/run.py fonts-prepare
media=$("${PYTHON:-python3}" -c 'import sys; sys.path.insert(0, "scripts"); from pipeline.paths import source_media; print(source_media())')
mkdir -p .cache/logs
export XDG_CACHE_HOME="$root/.cache/fontconfig"
mkdir -p "$XDG_CACHE_HOME"
case "$mode" in
  preview)
    ffmpeg -y -hide_banner -i "$media" -vf 'ass=deliverables/zh.performance.ass:fontsdir=.cache/render-fonts,scale=1280:720' -c:v libx264 -preset fast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart deliverables/zh.preview.720p.rendering.mp4 2>.cache/logs/render-preview.log
    mv deliverables/zh.preview.720p.rendering.mp4 deliverables/zh.preview.720p.mp4 ;;
  full)
    ffmpeg -y -hide_banner -i "$media" -vf 'ass=deliverables/zh.performance.ass:fontsdir=.cache/render-fonts' -c:v libx264 -preset fast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart deliverables/zh.performance.1080p.rendering.mp4 2>.cache/logs/render-full.log
    mv deliverables/zh.performance.1080p.rendering.mp4 deliverables/zh.performance.1080p.mp4 ;;
  soft)
    ffmpeg -y -hide_banner -i "$media" -i deliverables/zh.performance.ass -i deliverables/ja.review.ass -map 0:v -map 0:a -map 1:0 -map 2:0 -c copy -metadata:s:s:0 language=zho -metadata:s:s:0 title='中文演出字幕' -metadata:s:s:1 language=jpn -metadata:s:s:1 title='日文校对（原片已有日文）' -disposition:s:0 default -disposition:s:1 0 deliverables/editable-tracks.rendering.mkv 2>.cache/logs/mux.log
    mv deliverables/editable-tracks.rendering.mkv deliverables/editable-tracks.mkv ;;
  *) print -u2 'usage: python3 scripts/run.py render preview|full|soft';exit 2;;
esac
