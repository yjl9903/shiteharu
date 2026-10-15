# 工程脚本

统一入口为 `python3 scripts/run.py <命令>`，以下命令从工程目录执行。也可以从仓库根目录运行 `python3 production/shingouki/scripts/run.py <命令>`；所有素材路径和输出路径仍相对工程目录解析。

## 目录职责

```text
scripts/
├── run.py                  # 命令解析、参数校验和分派
├── requirements.txt        # 顶部字形校准的可选 Python 依赖
├── tests/                  # 跨工作目录和无副作用帮助测试
└── pipeline/
    ├── paths.py            # 工程定位、session 中的源视频解析
    ├── subtitles/          # ASS/SRT 生成、阴影渲染、顶部校准
    ├── fonts/              # 字体缓存、已审阅提案合并
    └── delivery/           # 视频导出、对照片段、工程打包
```

`pipeline` 是本工程内部 Python 包，不直接执行其中的 `.py` 文件。新增工具先按职责归类，再注册到 `run.py`；不要往顶层继续堆独立实现。只在有第二个工程的实际复用需求时再提取共享库。

## 命令与写入范围

| 命令 | 作用及输出 |
| --- | --- |
| `build [--output DIR]` | 读取人工字幕和设计，生成4份ASS/SRT；默认写deliverables，指定目录可用于回归比较 |
| `render [preview\|full\|soft]` | 先build、准备字体，再生成对应视频；默认preview |
| `compare-clips [FILTER]` | 按design/clips.json生成对照视频；可按名称筛选 |
| `compare-stills` | 从对照视频生成截图 |
| `package` | 生成工程ZIP，排除本机字体和缓存 |
| `fonts-prepare` | 复制配置字体到.cache/render-fonts，不改系统字体 |
| `fonts-merge` | **修改design及共享fonts**：合并已审阅的字体提案，不作为日常重建步骤 |
| `calibrate-top` | **修改design位置**：实际渲染测量顶部字形；仍需人工看图 |

每个命令均支持 `--help`；参数会先校验，再加载实际工具，帮助或错误参数不会触发导出和设计修改。字幕正文仍通过rajio手动编辑，脚本不负责自动翻译或改写。

## 依赖与运行

生成字幕与打包使用标准库；视频命令需要FFmpeg/ffprobe，shell步骤需要zsh。顶部校准工具通过工程`.venv/bin/python scripts/run.py ...`运行，依赖见requirements.txt。字体文件及本机字体准备见工程README。`render`的子步骤沿用启动入口所使用的Python解释器。

命令统一使用`run.py`，Python调用方直接导入`pipeline`模块，不保留旧入口或转发脚本。字体研究和预览服务留在`font-style-preview/`，直接使用正式字幕模块。

从工程目录运行 `python3 -m unittest discover -s scripts/tests -v` 检查入口。导出回归只写临时目录，不覆盖成片或交付字幕。测试需要工程的已审阅字幕与设计数据，不需要FFmpeg或本机字体。
