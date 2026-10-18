# 字体来源

本目录收录字体文件、来源记录和许可文本。

## 原始字体

| 字体 | 本地文件 | 来源 | 许可 |
| --- | --- | --- | --- |
| 马善政楷书（Ma Shan Zheng Regular） | [MaShanZheng-Regular.ttf](mashanzheng/MaShanZheng-Regular.ttf) | [Google Fonts](https://github.com/google/fonts/tree/main/ofl/mashanzheng) · [上游项目](https://github.com/googlefonts/mashanzheng) | [SIL OFL 1.1](mashanzheng/OFL.txt) |
| 资源圆体（Resource Han Rounded CN Heavy） | [ResourceHanRoundedCN-Heavy.ttf](round/ResourceHanRoundedCN-Heavy.ttf) | [CyanoHao/Resource-Han-Rounded](https://github.com/CyanoHao/Resource-Han-Rounded) | [SIL OFL 1.1](round/OFL-License.txt) |
| 思源宋体（Source Han Serif SC Heavy） | [SourceHanSerifSC-Heavy.otf](mincho/SourceHanSerifSC-Heavy.otf) | [adobe-fonts/source-han-serif](https://github.com/adobe-fonts/source-han-serif) | [SIL OFL 1.1](mincho/LICENSE.txt) |
| 龙珠体（LongZhuTi Regular） | [LongZhuTi-Regular.ttf](marker/LongZhuTi-Regular.ttf) | [maoken-fonts/LongZhuTi](https://github.com/maoken-fonts/LongZhuTi) | [SIL OFL 1.1](marker/OFL.txt) |
| 悠哉体（Yozai Regular） | [Yozai-Regular.ttf](casual/Yozai-Regular.ttf) | [lxgw/yozai-font](https://github.com/lxgw/yozai-font) | [SIL OFL 1.1](casual/OFL.txt) |
| 庞门正道粗书体 | [PangMen.ttf](brush_title/PangMen.ttf) | [作者发布页](https://mp.weixin.qq.com/s/1ccpLCOrIn81JhV9ulwPIQ) · [下载来源与校验值](brush_title/provenance.json) | 作者授权全文尚未归档，许可待核实 |

## 衍生字体

以下字体仅包含有限字集；覆盖范围和字形来源见各自的 JSON 记录，使用前需确认所需字符是否齐全。

| 字体 | 本地文件 | 基础字体与处理 | 来源记录与许可 |
| --- | --- | --- | --- |
| ShingoukiFractureSC | [ShingoukiFractureSC.ttf](fracture/ShingoukiFractureSC.ttf) | [源界明朝](https://booth.pm/ja/items/1028548)字形，使用思源宋体补充简体字并添加裂纹效果 | [逐字来源与覆盖范围](fracture/ShingoukiFractureSC.json) · [源界明朝 OFL](fracture/OFL-Genkai.txt) · [思源宋体 OFL](fracture/OFL-SourceHanSerif.txt) |
| ShingoukiMeltSC | [ShingoukiMeltSC.ttf](melt/ShingoukiMeltSC.ttf) | 基于思源宋体的变形字形，仅含「烫」及空格 | [逐字来源与覆盖范围](melt/ShingoukiMeltSC.json) · [思源宋体 OFL](melt/OFL-SourceHanSerif.txt) |
| ShingoukiDiamondSC | [ShingoukiDiamondSC.ttf](diamond/ShingoukiDiamondSC.ttf) | 基于[风雅宋](https://github.com/maoken-fonts/fengyasong)的菱形装饰字形；视觉参考赤のアリス，未使用其字体轮廓 | [字形记录与覆盖范围](diamond/ShingoukiDiamondSC.json) · [风雅宋 OFL](diamond/OFL-FengYaSong.txt) |

银泽新增可复现来源：[源界明朝完整源资产](genkai/Genkaimincho.ttf)（[来源与校验](genkai/provenance.json)、[OFL](genkai/OFL.txt)）；[GinzawaFractureSC](ginzawa-fracture/GinzawaFractureSC.ttf) 使用同一共享派生工具生成，[逐字来源](ginzawa-fracture/GinzawaFractureSC.json)与[配方](../production/ginzawa/research/fonts/recipe.toml)保留在仓库。简体缺字使用思源宋体重字加固定裂痕近似，并非确认原视频字体。

## 本机准备的字体

银泽推文修订使用 MiSans Regular 真实常规字面。字体从 [MiSans 官方下载页](https://hyperos.mi.com/font/zh/download/) 获取；使用前阅读随包许可，将静态 `MiSans-Regular.ttf` 放到本目录的 `local/` 下，再运行工程 README 的 `fonts-prepare` 命令。本机字体文件不纳入 Git 或交付包。

本次使用版本为 4.003，PostScript 名为 `MiSans-Regular`，SHA-256 为 `6aa32ded55e110a95be10080e0c322f2382681cd581c5cbb24f4fd4ce96fbb08`。重建时应核对该版本与校验值；若官方包已更新，应重新检查排版，不把不同版本当作相同输入。


完整本机依赖清单见 [local-fonts.toml](local-fonts.toml)，覆盖 MiSans Bold/Light/Regular、LXGW WenKai Regular、更纱等宽黑体 SC Bold、宋体 TTC、日文字体 W6 TTC。两个正式工程共用这些文件；信号灯研究的标注字体另用 MiSans Regular。将清单中的文件准备到 `fonts/local/`，运行工程的 `check-inputs` 核对 SHA-256。宋体和日文 TTC 须从自己的合法安装准备，保留完整集合；其他平台未必可取得同一版本，缺少时明确停下，不能用同名字体替代已确认的排版。

### 派生字体完整输入

风雅宋完整源资产已保存在 [MaoKenWangFengYaSong.ttf](fengyasong/MaoKenWangFengYaSong.ttf)，附 [OFL](fengyasong/OFL.txt) 与 [来源、版本、SHA-256](fengyasong/provenance.json)。它是本次从现存研究输入保存的原文件；原下载修订号未记录，不声称等于上游最新版。信号灯的菱形、破损和融化字库现在只引用 `fonts/fengyasong/`、`fonts/genkai/`、`fonts/mincho/`，无需候选缓存。现有正式派生字库不改动；重建产物在工程研究目录中，需检查后显式采纳。
