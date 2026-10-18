# 迁移与恢复指南

用于换机器、恢复本地资源或从工程包重建结果。制作过程中应持续满足的约束见 [可复现性要求](reproducibility.md)；单片具体构建与审阅命令仍以对应工程 README 为准。

下文资源盘点和验证记录基于 2026-10-18 的信号灯、银泽工程；其他工程及之后的变更须同时检查其 README 和配置。未跟踪文件、未提交修改和 Git 忽略的媒体不会自动随克隆迁移。

## 目标机器操作顺序

1. 复制当前仓库（包括尚未提交的必要修改），或检出包含这些修改的提交。可编辑 ZIP 只包含相应工程；它不是整个工作区的完整备份。
2. 按下文清单恢复原片、本机字体，以及需要保留的历史证据/确切成片。源代码、正式字体与人工结果来自 Git；凭据独立准备。
3. 安装 uv 与符合要求的 FFmpeg，运行 `uv sync --locked`。Git 检出按下文启用 `.githooks`。
4. 执行下列只读检查。缺文件、字体/原片哈希不匹配或缺必要编码功能均返回非零；不会改写配置或从缓存补资源。
5. 按工程 README 构建、准备字体、渲染并启动 Loupe。先核对字幕文件差异，再对代表画面和边界复核；需要交付时重新完成相应验收。

```sh
uv run --locked python tools/forge/forge.py --config production/shingouki/forge.toml check-inputs
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml check-inputs
```

仅准备字幕/字体输入时可加 `--no-media`，会明确跳过原片和视频工具检查。检查同时核对派生字体源输入与研究标注字体，但不验证任意研究候选、证据截图、旧成片是否最新、凭据或人工内容。正式字体文件由版本管理保留；未入库字体用 `fonts/local-fonts.toml` 校验。

## 迁移时带什么

2026-10-18 复查范围为 `shingouki`、`ginzawa` 的当前制作输入与公共工具；`shuueki` 是本轮开始前已有的未跟踪工程，本次保留不改，其资源准备见自己的 README。未跟踪文件不会随克隆迁移，须自行保留或确认纳入版本管理。

| 数据或资源 | Git / 工程包 | 迁移与恢复方式 |
| --- | --- | --- |
| `translation/work/`、`design/`、`description.md` | Git；当前打包配置收录 | 已确认的中文与演出源，不能用重新 ASR 或旧导出替代。 |
| `transcript/raw/`、`transcript/work/`、`patches/`、`session.toml` | Git；当前打包配置收录 | 保留原始转写、日文校对及阶段状态。会话中的旧阶段哈希不是当前设计的验收结论。 |
| `source.info.json`、工程配置、研究配方 | Git；当前打包配置收录 | 保存来源、路径和操作参数；原片哈希以会话 `input.media_sha256` 为准。 |
| `downloads/` | 忽略；不打包 | 优先备份现有原片。网络重下载只用于恢复候选，必须核对哈希与 PTS，见下文。原始下载元数据可能带临时 URL，不作为共享配置。 |
| `fonts/` 中正式字库、完整派生源字体与许可 | Git；包按工程引用收录 | 直接保留，普通渲染无需重建字库。信号灯派生配方已脱离候选目录。 |
| `fonts/local/` | 忽略；不打包 | 只需准备 `fonts/local-fonts.toml` 列出的 7 个实际使用文件，约 137 MiB；其余本机副本不参与当前流程。准备来源见清单。 |
| `frames/` 中的取证、逐事件合成图与最终成片采样 | 多数忽略；银泽包仅收录已声明的证据与最终采样 | 既是派生媒体，也是历史审阅的证据。若要保留原审阅记录对应的图片，迁移时一起备份；取帧配方能恢复采样，但未必恢复历史命名和联系表。不能仅因忽略规则而一概删除。 |
| `review/comparisons/` | 忽略；不纳入可编辑工程 ZIP | 局部左右对照视频及中点图。需要保留旧审阅效果时另行备份；用当前字幕重跑对照命令会覆盖同名样片，不能还原历史设计。选段配置随 `design/clips.toml` 保留。 |
| `audio/`、校对片段媒体 | 忽略；不打包 | 从同一原片重新提取即可继续取证；原 ASR 文字已保存。恢复旧会话的音频阶段可能影响下游状态，不作为成片重建步骤。 |
| `output/`、`deliverables/` | 字幕与部分文字/封面入库，视频/ZIP 忽略 | 当前源可以重建字幕与视频；要保留已验收文件的确切字节，另外备份原成片。各输出是否与当前工作稿一致，以工程 README 和对应核验记录为准。 |
| `.cache/loupe/`、工程 `.cache/` | 忽略；不打包 | 预览副本、抽帧、字体缓存和日志，可由当前输入重建。 |
| `.cache/migrations/` 等历史备份 | 忽略；不打包 | 是以前迁移留下的快照，本次没有证明其中全部内容都已归档；不将它们算作必需输入，也不自动清理。 |
| `.venv/`、工具下载缓存 | 忽略；不打包 | 重新 `uv sync --locked`，无需搬运旧虚拟环境。 |
| `.env`、服务授权、下载 cookies | 忽略；不打包 | 在目标机另行配置。已有字幕的 Forge 构建、渲染和 Loupe 不需要云服务凭据。 |

2026-10-18 本地体积参考：仓库 `.cache/` 约 40 GiB，其中 Loupe 约 35 GiB、历史迁移快照约 5 GiB；`fonts/local/` 约 501 MiB；信号灯候选字体约 500 MiB。这是盘点快照，不是清理指令。本次未删除任何本地素材或备份。

## Python 运行环境

仓库内的工程脚本、字体研究、Loupe 和维护检查共用根目录的 `pyproject.toml`、`uv.lock` 与 `.python-version`，由 uv 创建根目录 `.venv/`。依赖覆盖 Pillow 图像处理、NumPy 测量、fonttools 字体读写、skia-pathops 字形运算和 tomlkit 配置读写。不再维护工程或工具各自的 requirements 文件和独立环境。

先按 [uv 官方说明](https://docs.astral.sh/uv/getting-started/installation/) 安装 uv，然后在仓库根目录执行：

```sh
uv sync --locked
uv run --locked python tools/forge/forge.py --help
```

uv 会按 `.python-version` 选择 Python；本机缺少该版本时会下载。`uv sync --locked` 按锁文件安装依赖，清单与锁文件不一致时直接报错。无需激活虚拟环境或手动运行 pip。FFmpeg（含 libass）、ffprobe，以及各工程列出的素材和字体仍需单独准备。

在 `production/<工程>/` 或 `tools/loupe/` 内执行 `uv run --locked python ...` 时，uv 向上找到仓库配置，共用根目录环境。从仓库外启动时，使用 `uv run --locked --project <仓库位置> python <脚本位置>`。Forge 的构建与渲染准备步骤在同一 Python 进程内执行；工具中的 Python 子进程沿用 `sys.executable`。

若运行环境不允许写入用户级 uv 缓存，可从仓库根目录执行 `UV_CACHE_DIR=.cache/uv uv sync --locked`，后续 `uv run` 同样设置此变量。它只改变缓存位置，不改变锁定依赖。

## 启用路径检查

在 Git 检出根目录执行：

```sh
git config core.hooksPath .githooks
```

该设置不随克隆复制。已有其他 hooks 时先整合，避免覆盖其用途；ZIP 解压目录没有 Git 元数据时无需启用。

## 工具与阶段依赖

| 操作 | 必需输入与环境 | 不需要的输入 |
| --- | --- | --- |
| Forge `build` | 锁定的 Python 环境、时间轴、设计、字体配置 | 原片、字体文件本体、FFmpeg、ASR 服务 |
| `fonts-prepare`、字体/排版检查 | 配置中的字体文件；TTC 必须保留完整字面集合 | 系统安装字体、历史字体缓存 |
| `render`、对照、原片取帧 | 同一原片、字幕输入、字体、FFmpeg/ffprobe | ASR 服务、候选字体目录 |
| Loupe | `preview.toml` 指定的原片和成片、时间轴、字体、FFmpeg/ffprobe | 字体研究提案、旧 Loupe 缓存 |
| `research-fracture` / `research-diamond` | 配方、字集/时间轴、仓库完整源字库及许可、锁定的 Python 环境 | 网络下载和候选目录；不自动替换正式字库 |
| 其他字体研究 | `research/fonts/README.md` 与配方声明的候选、发布记录和下载工具 | 不属于日常成片复现；上游资源可能变更或下架 |
| `package` | 字幕输出、声明的工程资料、共享工具/字体；银泽还需要引用的证据图片 | 原片、本机字体、虚拟环境和缓存不纳入包 |

Python 包由 `uv.lock` 管理；FFmpeg 按 [官方入口](https://ffmpeg.org/download.html)单独准备，须包含 `ass` 滤镜（libass）、`libx264` 与 AAC 编码器。rajio 按现有工程说明使用。

## 原片恢复

首选从备份恢复 `session.toml` 指定的 MKV，并校验 SHA-256。当前两片的已保存原片均已与会话哈希核对一致。

- 银泽：原下载元数据记录 `399+251`、yt-dlp 2026.03.17；时长 616.141 秒。
- 信号灯：未保留原下载格式选择记录，不能声称重新选择流一定获得原输入；时长 601.709 秒。原片备份是字节级恢复的可靠来源。

需要重新下载时，先写入独立目录，避免覆盖工作原片。以下从仓库根目录执行，准备 Node.js 与 FFmpeg：

```sh
uv tool run --from 'yt-dlp[default]==2026.3.17' yt-dlp \
  --ignore-config --js-runtimes node --no-playlist \
  -f '399+251' --merge-output-format mkv --abort-on-unavailable-fragments \
  --write-info-json --write-description \
  -o 'downloads/reacquired/石川県の存在しない街『銀沢』へ行こう [%(id)s].%(ext)s' \
  'https://www.youtube.com/watch?v=hNc8Em2PKeQ'

uv tool run --from 'yt-dlp[default]==2026.3.17' yt-dlp \
  --ignore-config --js-runtimes node --no-playlist \
  -f 'bestvideo[height=1080]+bestaudio' --merge-output-format mkv --abort-on-unavailable-fragments \
  --write-info-json --write-description \
  -o 'downloads/reacquired/『信号機の墓場』へ行こう [%(id)s].%(ext)s' \
  'https://www.youtube.com/watch?v=l_jfyIEddfw'
```

这是候选恢复命令，本轮未重新下载全片验证。固定格式不可用、平台策略变化或旧下载器不再工作时应明确处理失败，不能静默换流。即使格式相同，平台重编码和 MKV 封装也可能改变哈希。先用 `shasum -a 256` 与会话记录比对；不一致时保留原记录，核查流参数及字幕对应的真实 PTS，再决定是否接纳新素材，不能直接改哈希让检查通过。

## 验证记录（2026-10-18）

- `check-inputs`：信号灯 29 个、银泽 26 个去重输入文件通过检查；包括原片及本机字体 SHA-256、派生源输入和 FFmpeg/ffprobe 功能。
- 从当前受版本管理的文件及本轮新增文件复制到带空格的新目录，未带原片、本机字体、虚拟环境或任何缓存，使用当前锁定的 Python 解释器运行 Forge：两片各 4 份 ASS/SRT 均与当前交付文件逐字节一致。
- 在该目录连续两次重建 4 个派生字体，结果逐字节一致；`glyf`、`cmap`、`hmtx`、`name` 表与已采用字体一致。只修正菱形生成器的时间戳确定性，没有替换正式字库。
- 显式补入银泽设计引用的 844 张历史证据图及最终成片采样后，分别生成临时工程包（信号灯 129 文件、银泽 1106 文件）；解压后字幕和派生字体重建成功。包中有新增来源/转写/字体准备资料，没有本机字体或缓存。原工作区的旧 ZIP 未覆盖。
- Forge 的 12 项测试通过，包含真实 FFmpeg 编码、打包重建、缺失/变更/外部资源拒绝及派生字体时间戳；当前文本路径检查和 TOML 解析通过。

这次验证覆盖异地路径与无缓存输入，不等于已在另一操作系统安装同一环境；未重下原片、未重渲染两部全片，也未做新的人工字幕/全片验收。庞门正道粗书体授权全文仍待归档（沿用字体来源中的既有标注）；本轮未改变字体选择或交付声明。
