# 银泽破损字幕字形

`recipe.toml` 记录有限字集和源文件，使用共享 Forge 的 `research-fracture` 重建，不在工程内保留脚本。

```sh
uv run --locked python tools/forge/forge.py --config production/ginzawa/forge.toml research-fracture
```

源界明朝已有的字形保留其原有剥落结构；不覆盖的简体字使用思源宋体 Heavy 加固定种子的裂纹。字体家族另命名为 `GinzawaFractureSC`，不声称已识别原作者字体。`derived/GinzawaFractureSC.json` 逐字记录来源；许可随资产保存。正式设计引用共享的 `fonts/ginzawa-fracture/` 副本，更新后需显式同步并重新检查，不自动替换正在交付的字体。

完整源字体已保存到共享字体目录，工程不依赖其他生产工程的候选缓存。字体时间戳继承输入资产，连续重建字节一致，见 `../../review/fracture-rebuild.json`。对照候选位于本地 `frames/fracture-proposal/`，最终采用与位置复修记录在各段审阅文件。
