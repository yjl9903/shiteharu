# Editable design contract

Font `file` paths in `fonts.toml` are relative to the production project directory (`production/shingouki/`). Shared font assets and licenses live in the repository-level `fonts/` directory, referenced as `../../fonts/...`.

All event files `events-*.toml` use TOML array-of-tables syntax (`[[events]]`). Main captions refer to a reviewed segment with `id`. Do not duplicate text for main captions: edit `translation/work/segments.toml` using rajio segments commands. New overlapping labels use `id`, `start`, `end`, `text_ja`, `text_zh`, `supplemental = true`.

Each event can set `font_role` (keys from fonts.toml, including round, mincho, marker, casual, brush_title, fracture, melt, diamond), `fontsize`, `x`, `y`, `align` (ASS 1–9), `color` / `outline_color` as RGB hex, `outline`, `shadow`, `bold`, `scale_x`, `scale_y`, `spacing`, `rotation`, `max_width`.

`line_advance` sets the distance between horizontal row anchors in full-resolution pixels. Rows share their width scale and move together; choose the advance and block position from actual visible ink gaps in the source Japanese rows. The source Japanese is burned in and is not moved.

Ordinary face-avoidance layouts use centered top placement, never a left-side column. `uv run --locked python ../../tools/forge/forge.py --config forge.toml calibrate-top` measures actual libass ink, including shadows, and gives explicitly top-centered events a 20px visible margin. Negative anchor coordinates can be valid because font ascenders include invisible space; judge the rendered ink rather than the anchor value. Preserve scene-specific corner labels, panels and vertical speech separately.

`line_breaks = [n1,n2,...]` provides manually chosen line lengths for horizontal performance layout only. Counts must sum to the reviewed Chinese character count after removing existing newlines; spaces count as characters. This changes no wording and does not alter SRT/rajio text. Use it for scene-specific arrangements near the original caption when preserving face visibility requires different wrapping. It cannot combine with vertical layout. Avoid automatically wrapping every caption by a fixed character count.

`effect`: none / fade / pop / slide / shake / pulse / typewriter / glow / distress. Parameters: `in_ms`, `out_ms`, `from_x`, `from_y`, `amplitude`, `period_ms`, `initial_scale`, `glow`, `char_ms`. Effects must be based on observed source behavior; do not apply animations just to embellish. Translation positions must not intersect source-caption bounding rectangles.

`source_style`, `timing_status` and `limitations` describe scene-specific design decisions. `source_boxes` and `face_boxes` retain reference layout bounds; rendering does not generate audit reports or evidence links.

The user permits Chinese to share an intentional face-covering effect when the original typography already does so. Judge the actual scene and emphasis, not a blanket geometric rule. Record `allow_face_overlap = true` and the scene-based reason in `limitations` for such exceptions. Ordinary unobstructed dialogue should still avoid newly covering faces; original Japanese text must remain visible in all cases.

For observed vertical speech, set `text_layout = "vertical"`. `x,y` anchor the top of the rightmost column. `column_chars` defaults to8; alternatively `vertical_columns` is an explicit list of character counts whose sum must match the text excluding newline. Columns advance right to left; `column_gap` (default1.25) and `row_gap` (default1.05) multiply fontsize. `vertical_rotate_punctuation` defaults to `…—～`. This changes glyph placement only; the editable Chinese wording remains in rajio. Fade/slide parameters apply to all characters together. Exact Japanese vertical glyph forms and balloons are approximated; report this limit.

Optional exact timing overrides `start`, `end` apply only in visual deliverables; prefer correcting active rajio data when possible. Final Japanese and Chinese plain tracks share these same corrected boundaries. Supplemental events may overlap normal dialogue, so ASS is the faithful editable delivery format.

ASS stores centiseconds. The builder floors source frame PTS to centiseconds rather than rounding up, so a cut at 402.235 starts at 402.23 and is visible on the 402.235 frame, without slipping to the following frame. SRT retains millisecond source timing. This is safe for the source's ~33 ms frame intervals.

Only a deliberately scrolling source caption may set `allow_offscreen = true`, with its reason in `limitations`. Set a large `max_width` for natural-width long scrolling text; otherwise the default width guard compresses it to fit.

For actual overlapping speech balloons, use exact `start`/`end` overrides and `allow_overlap = true`. Rajio's serialized dialogue may shorten them to maintain its work-file constraints, but final ASS/SRT should preserve the observed full visual lifetime. Explain overlap and cite boundary evidence. Audio-only lines should be labeled `timing_status = "audio-only"` and positioned separately.

`soft_shadow` adds a separate black layer beneath sharp foreground ink through `tools/forge/pipeline/subtitles/shadow_render.py`: `x`, `y` offsets, `spread` outline, `blur` radius in full-resolution pixels, and `alpha` two-digit ASS transparency. It follows the same time, wrapping and movement. Foreground shadow/blur stay zero. Recompute this scene-specific field when changing fontsize.
