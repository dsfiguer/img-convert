# img-convert

CLI that bulk-converts raster images (JPEG, PNG, WebP, BMP, TIFF, GIF, ICO) with Pillow. Code: `src/img_convert/cli.py`
(Typer app, entry point `img-convert`). Usage and flags are in `README.md`.

- Setup / install: `uv tool install --force --editable .` (editable, so code changes apply to the global `img-convert`).
- Run without installing: `uv run img-convert <inputs> --to webp`.
- No tests, lint or CI yet. No deploy: it's a local tool.
- Git: default branch `master`, `origin` is `dsfiguer/img-convert` (public). Branch + PR for changes.
