# 银泽 v2 完整导出

本版包含逐条用户修订，以及288事件的位置/字号专项复查后的编辑稿。旧版视频与交付包保留在 `../../`。

- `zh.performance.1080p.mp4`：本版1080p烧录视频。
- `zh.performance.ass`、`ja.review.ass`、`zh.srt`、`ja.srt`：同版编辑轨和纯文本轨。
- `inputs/`：本版制作输入快照，保留相对于原工程根目录的结构。
- `render-manifest.json`：输入与字体哈希、编码设置和版本信息。

重建时以 `production/ginzawa/` 为工程根目录：在副本工程中将 `inputs/` 的内容恢复至相同相对位置，按工程README准备原视频和字体，再读取 `forge.toml`，将输出目录设为 `deliverables/revisions/v2` 后执行Forge的full渲染。快照中的字体路径以原工程根目录解析，不应把 `inputs/` 当作独立工程。视频、字体与缓存不作为Git分发内容。

本版仅新增1080p完整视频及同版字幕轨，未重做720p、MKV、18段对照视频或ZIP；旧交付文件不能混称v2。技术核验与实际编码采样记录在 `../../../review/export-v2-qa.json`。
