# 字体研究资料

本目录保存《信号機の墓場》的字体识别依据、逐事件提案、候选来源和有限字集派生字库资料。它是工程数据，不包含播放器、服务器、自动同步器或公共工具实现。Loupe 启动只需要 `preview.toml`、`design/`、时间轴和媒体，不读取本目录。

## 保留的数据

- `HANDOFF.txt`：历史识别结论、字形及阴影参数依据。记录的字幕数量是当时快照，不代表当前成片验收。
- `source-events.toml`、`source/`：重点字幕采样及原片裁切。
- `font-config.proposed.toml`、`event-font-patches.json`、`diamond-event-patches.json`、`shadow-event-patches.json`：待人工审阅的资源及事件参数提案。
- `baseline-events.toml`、`proposed-events.toml`、`proposed-full.ass`、`coverage.json`：历史提案及覆盖检查。
- `downloads*.json`、`candidate-inventory.json`、发布记录及作者页摘录：候选来源与校验信息。
- `derived/`：派生字库来源说明、许可及本地重建产物；正式使用的字库与许可在仓库顶层 `fonts/`。
- `candidates/`、研究图片、试排视频和字体副本均被 Git 忽略。没有素材时可重新下载或生成，不影响 Loupe 审阅正式成片。

资源清单中的文件路径以 `production/shingouki/` 为基准。例如 `source-events.toml` 的 `source_frame` 为 `research/fonts/source/…`。

## 研究配方与命令

`recipe.toml` 保存本片的事件 ID、字体选择、候选下载来源、派生字库命名和提案参数。算法统一在仓库 `tools/forge/pipeline/research/`；本目录只保存工程数据。从工程目录调用 Forge：

```sh
uv run --locked python ../../tools/forge/forge.py --config forge.toml research-capture
uv run --locked python ../../tools/forge/forge.py --config forge.toml research-fracture
uv run --locked python ../../tools/forge/forge.py --config forge.toml research-diamond
uv run --locked python ../../tools/forge/forge.py --config forge.toml research-propose
uv run --locked python ../../tools/forge/forge.py --config forge.toml research-sheets
```

这些命令会重新读取设计并更新研究产物。字体研究与 Loupe 共用仓库根目录的 uv 环境；依赖准备见 [运行环境](../../../../docs/reproducibility.md#python-运行环境)。

其他命令：`research-discover` 查询候选发布记录，`research-download` 与 `research-download-extra` 下载字体，`research-specimens` 生成字形试样，`research-reel` 和 `research-render` 生成提案视频。所有帮助都在加载实现前处理；运行研究命令不自动发布到 Loupe，也不自动合入设计。

合入已审阅提案仍使用 `../../tools/forge/forge.py --config forge.toml fonts-merge`，它会修改设计与共享字体，需要明确选择执行；普通预览或重建不会调用它。
