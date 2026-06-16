# Web UI Layout Contract

This contract freezes the compact desktop workbench used by the Web UI. It is
intended to keep future UI work from fixing one layout issue by reintroducing
left-column clutter, hidden controls, or extra internal scrollbars.

## Desktop Target

- Primary verification viewport: 1366x768 at 100% browser zoom.
- The first screen must preserve the existing compact three-column workbench:
  left task controls/provider-specific statistics, middle API/progress controls,
  and right run logs.
- The page may scroll naturally below the workbench to reach field editing.
- Field editing intentionally stays below the first workbench and is not part of
  the first-screen control set.

## First-Screen Workbench

At the desktop target, the first screen must show:

- Header/title and language switch.
- Task Settings.
- PDF directory and output path.
- LLM provider, PDF mode, max characters, timeout, bad-data threshold, recursive
  mode, fallback mode, and copy-failed-PDF option.
- Start, Pause, Resume, and Stop buttons.
- API/model configuration.
- Statistics.
- Progress area.
- Run Logs.

Statistics are provider-specific in the first screen:

- In Cloud mode, Statistics must appear directly below Task Settings in the left
  column, while the middle column shows API config followed by Progress.
- In Local Ollama mode, Statistics must appear in the middle column above
  Progress, while the left column contains Task Settings only.
- The UI must use one Statistics section and move it between left/middle mount
  points. Do not duplicate Statistics DOM nodes or backend-bound IDs.

Do not hide these controls, move them below the field editor, or depend on
scrolling inside the left or middle column to reach them.

## Scrolling Rules

- No internal scrollbar in the left Task Settings column.
- No internal scrollbar in the middle API/Progress or API/Statistics/Progress
  column.
- The only intended internal scroll region in the workbench is `pre#logs`.
- Whole-page scrolling is allowed for content below the first workbench.

## Compact Label Rules

- Chinese and English labels must remain compact enough for the desktop target.
- Chinese task labels should use short forms such as `模型来源`, `解析方式`,
  `上传字数`, `超时秒`, `坏行阈值`, `Ollama 地址`, `含子目录`,
  `失败换模型`, and `复制失败 PDF`.
- Warning copy for failed PDF copying must remain visible, short, and clear.
- Copying failed source PDFs must not be enabled by default.

## Manual Visual Checklist

Before merging UI layout changes, check Chrome or Edge at 1366x768 and 100%
zoom:

- The three-column workbench remains intact.
- Header/title/language switch is visible.
- Task Settings and all core task controls are visible.
- Start/Pause/Resume/Stop are visually stable in a compact row.
- Cloud mode shows Statistics under Task Settings and Progress under API config.
- Local Ollama mode shows Statistics above Progress in the middle column.
- Stat cards show number and label on the same row.
- `可疑/坏行 0 / 0` is not clipped.
- Run Logs are visible and `pre#logs` is the only internal scroll area.
- The left and middle columns do not show internal scrollbars.
- Field editing starts below the first workbench.
