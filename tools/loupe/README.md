# Loupe

字幕与字体审阅工具，名称取自放大镜。播放器、字幕搜索、画面对照、自动同步、媒体探测和字体覆盖检查只在这里维护。工程提供 `production/<工程>/preview.toml`、素材和时间轴；公共代码不导入工程 Python 模块。

## 启动

在仓库根目录运行，需要 uv、FFmpeg 和 FFprobe。Python 和 fonttools 等依赖由仓库根目录的 uv 配置统一管理，准备方法见 [运行环境](../../docs/migration.md#python-运行环境)。

```sh
uv sync --locked
uv run --locked python tools/loupe/loupe.py --config production/shingouki/preview.toml --serve --port 8973
```

浏览器打开输出的本地地址。首次启动先生成完整快照，随后每 5 秒检查输入。`--validate` 只读验证；省略 `--serve` 只生成一次；`--watch` 持续同步但不提供网页。端口被占用时换一个端口，不自动终止其他服务。

首页直接携带当前快照、视频显示比例和首条字幕，避免等视频加载完成后才撑开页面。修改首页服务逻辑后需重启 Loupe 服务；单独修改前端资源只需刷新页面。

## 工程配置与输入适配

配置统一使用 TOML，入口配置必须位于工程根目录。所有配置文件中的路径（包括字体资源）均相对于该工程，不相对于配置所在的子目录。默认快照写入仓库 `.cache/loupe/<工程名>-<配置标识>/`，工程无需预览目录、启动脚本或独立环境。只有显式指定可选 `output` 时才写入该工程的指定子目录。媒体和字体可使用指向仓库共享目录的相对路径。本机字体放在被忽略的 `fonts/local/`。

最小配置参见 [最小配置](tests/fixtures/portable/preview.toml)，只有两份视频和一个 JSON 时间轴即可运行：

```json
[{"id":"caption-1","start":0,"end":2,"source_text":"Hello","text":"你好","style":{}}]
```

时间以秒表示，ID 唯一，开始时间不小于零，结束时间必须大于开始时间。允许空时间轴与重叠字幕。规范事件统一为 `id/start/end/source_text/text/style`，语言标签由 `[labels]` 提供。

`[timeline]` 支持声明式适配已有数据：

| 配置项 | 作用 |
| --- | --- |
| `file` | JSON 数组或 TOML/JSON 对象的相对路径 |
| `collection` | 对象中的事件数组键；数组文件不填 |
| `source_text` / `text` | 原文、译文字段名，默认同名 |
| `defaults` / `defaults_key` | 可选默认样式文件及对象键 |
| `overlays` | 可选相对 glob 列表，新增匹配文件自动纳入同步 |
| `overlay_collection` | 覆盖文件的事件数组键，默认 `events` |
| `supplemental_flag` | 补充字幕标识字段，默认 `supplemental` |
| `supplemental_source_text` / `supplemental_text` | 补充字幕的文本字段 |

覆盖配置使用 TOML 的 `[[events]]` 数组表（键名可用 `overlay_collection` 指定）。普通覆盖按 ID 合并，未知或重复 ID 明确报错；补充字幕提供自己的 ID、时间和文本。其他工程可以自行导出规范 JSON，再交给公共工具；无需在公共代码加入项目分支。现有 shingouki 适配仅使用配置，未执行字幕构建脚本。

可选 `fonts` 指向字体角色配置 TOML：

```toml
[body]
file = "fonts/body.ttf"
family = "Example"
weight = 400
```

TTC 可用 `face_index` 指定字面，否则根据家族和字重选择。只导出配置字面，检测对应角色的全部译文和页面输入的试样；字体读取失败、家族不符会报错，缺字显示方框。无字体配置时跳过字体功能。

混排 `text_runs` 与 Forge 共用 `tools/captions/` 的字符分段规则：每段按实际字体角色及字重检查缺字，长度不符或未知角色会报错。字体筛选和搜索包含段内角色。该共享模块随工具一起打包，不依赖任何 production 工程。

入口配置中的可选 `[content]` 表直接保存页面展示内容，不引用独立内容文件。支持 `description`、`focus_ids`、`[content.role_labels]`、`notes` 和 `[[content.links]]`（`label`、`url`）形式的外部链接。字体识别结论、重点 ID 和项目介绍属于工程内容。具体参数在画面卡片中展示；实际特效通过成片验收，通用工具不生成项目字体提案或重新烧录字幕。

页面标题直接使用入口配置的 `title`。各工程统一填写视频原始标题，与 `description.md` 中的标题一致，不添加工具名称、版本编号或「字幕与字体对照」等功能说明。标题下使用一张默认收起的「视频信息」卡片。入口配置可用 `[content.video]` 提供 `channel`、`channel_url`、`published`（日期字符串）、`url`、`thumbnail`（封面 HTTP(S) 地址）和 `description`（原视频简介），展开后集中展示。封面从声明的来源加载，需要网络；时长、分辨率及平均帧率由原片探测结果提供。未填写的资料项不显示。

## 输入与发布保证

- `[media].original` 和 `[media].rendered` 是播放、抽帧和自动同步的唯一来源，不扫描其他交付文件，不使用旧媒体缓存作为输入。
- FFprobe 读取时长、尺寸、像素比例、旋转和帧率。两路时长差默认允许 0.25 秒，可通过 `duration_tolerance` 调整；字幕超出片长或解码失败会阻止发布。这不能证明外部制作流程已结束，因此发布前还会重新检查输入是否变化。
- 两路按当前版平均帧率采样，缩略图分别保留显示比例。逐帧按钮和变帧率视频的采样均为近似定位。`thumbnail_width` 默认 960。
- VP8/VP9 视频换装为 WebM，H.264 换装为 MP4，其他视频转为 H.264。原片保留一条音轨并转换为浏览器支持的音频；当前版静音。
- 两路视频、全部抽帧及字体先写入临时目录，验证输入未变后发布不可变版本，再原子切换 `snapshot.json`。失败时保留旧快照并显示明确错误；恢复后自动重试。旧版本保留供已打开的页面使用，可在停止服务后清理该工程的 Loupe 缓存目录。
- 仅监听本机地址，支持视频 HTTP Range。只提供公共静态资源和生成快照，不提供工程目录、隐藏文件或目录列表。

## 验收

```sh
uv run --locked python -m unittest discover -s tools/loupe/tests -v
```

集成测试从工具内部的 fixtures 复制配置到临时工程，生成无音轨、不同帧率及画面比例的视频，验证同步、抽帧、时长检查、缺失来源、输入中途变化、失败保留、空时间轴、覆盖文件新增、字体缺字以及 Range 请求。测试使用临时目录，不改生产素材。
