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
| 庞门正道粗书体 | [PangMen.ttf](brush_title/PangMen.ttf) | [作者发布页](https://mp.weixin.qq.com/s/1ccpLCOrIn81JhV9ulwPIQ) · [来源记录](brush_title/provenance.json) | 作者授权全文尚未归档，许可待核实 |

## 衍生字体

以下字体仅包含有限字集；覆盖范围和字形来源见各自的 JSON 记录，使用前需确认所需字符是否齐全。

| 字体 | 本地文件 | 基础字体与处理 | 来源记录与许可 |
| --- | --- | --- | --- |
| ShingoukiFractureSC | [ShingoukiFractureSC.ttf](fracture/ShingoukiFractureSC.ttf) | [源界明朝](https://booth.pm/ja/items/1028548)字形，使用思源宋体补充简体字并添加裂纹效果 | [逐字来源与覆盖范围](fracture/ShingoukiFractureSC.json) · [源界明朝 OFL](fracture/OFL-Genkai.txt) · [思源宋体 OFL](fracture/OFL-SourceHanSerif.txt) |
| ShingoukiMeltSC | [ShingoukiMeltSC.ttf](melt/ShingoukiMeltSC.ttf) | 基于思源宋体的变形字形，仅含「烫」及空格 | [逐字来源与覆盖范围](melt/ShingoukiMeltSC.json) · [思源宋体 OFL](melt/OFL-SourceHanSerif.txt) |
| ShingoukiDiamondSC | [ShingoukiDiamondSC.ttf](diamond/ShingoukiDiamondSC.ttf) | 基于[风雅宋](https://github.com/maoken-fonts/fengyasong)的菱形装饰字形；视觉参考赤のアリス，未使用其字体轮廓 | [字形记录与覆盖范围](diamond/ShingoukiDiamondSC.json) · [风雅宋 OFL](diamond/OFL-FengYaSong.txt) |

银泽使用仓库内的[源界明朝](genkai/Genkaimincho.ttf)（[来源](genkai/provenance.json)、[OFL](genkai/OFL.txt)）；[GinzawaFractureSC](ginzawa-fracture/GinzawaFractureSC.ttf) 使用同一共享派生工具生成，[逐字来源](ginzawa-fracture/GinzawaFractureSC.json)与[配方](../production/ginzawa/research/fonts/recipe.toml)保留在仓库。简体缺字使用思源宋体重字加固定裂痕近似，并非确认原视频字体。

## 本机准备的字体

银泽推文修订使用 MiSans Regular 真实常规字面。字体从 [MiSans 官方下载页](https://hyperos.mi.com/font/zh/download/) 获取；使用前阅读随包许可，将静态 `MiSans-Regular.ttf` 放到本目录的 `local/` 下，再运行工程 README 的 `fonts-prepare` 命令。本机字体文件不随仓库分发。

完整本机依赖清单见 [local-fonts.toml](local-fonts.toml)，覆盖 MiSans Bold/Light/Regular、LXGW WenKai Regular、更纱等宽黑体 SC Bold、宋体 TTC、日文字体 W6 TTC。两个正式工程共用这些文件；信号灯研究的标注字体另用 MiSans Regular。将清单中的文件准备到 `fonts/local/`。宋体和日文 TTC 须从自己的合法安装准备，保留完整集合。

### 派生字体完整输入

风雅宋保存在 [MaoKenWangFengYaSong.ttf](fengyasong/MaoKenWangFengYaSong.ttf)，附 [OFL](fengyasong/OFL.txt) 与 [来源](fengyasong/provenance.json)。信号灯的菱形、破损和融化字库使用 `fonts/fengyasong/`、`fonts/genkai/`、`fonts/mincho/` 中的源字体。正式字库直接使用；需要修改字形时，按工程研究配方生成并检查后采纳。
