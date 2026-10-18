# 银泽破损字幕字形

正式字库保存在共享的 `fonts/ginzawa-fracture/`，直接使用。需要修改字集或字形时，更新 `recipe.toml` 后从仓库根目录运行：

```sh
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml research-fracture
```

源界明朝已有的字形保留其原有剥落结构；不覆盖的简体字使用思源宋体 Heavy 加固定种子的裂纹。字体家族另命名为 `GinzawaFractureSC`，不声称已识别原作者字体。`derived/GinzawaFractureSC.json` 逐字记录来源；许可随资产保存。正式设计引用共享的 `fonts/ginzawa-fracture/` 副本，更新后需显式同步并重新检查，不自动替换正在交付的字体。

源字体已保存在共享字体目录。对照候选位于本地 `frames/fracture-proposal/`，最终采用与位置复修记录在各段审阅文件。
