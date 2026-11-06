# img-convert

`img-convert` is a small command-line tool for converting raster images in bulk. It accepts files, directories, and quoted glob patterns, and writes each result beside its input unless an output directory is requested.

Supported input and output formats are JPEG (`.jpg`, `.jpeg`), PNG, WebP, BMP, TIFF (`.tif`, `.tiff`), GIF, and ICO. JPEG output uses the `.jpeg` extension; TIFF output uses `.tiff`.

## Install

This project requires Python 3.10 or newer and [uv](https://docs.astral.sh/uv/).

For a local clone on Ubuntu (or another system with `uv` installed), install the command globally with:

```bash
git clone https://github.com/<owner>/img-convert.git
cd img-convert
uv tool install .
```

After the repository is published, install directly from GitHub:

```bash
uv tool install git+https://github.com/<owner>/img-convert.git
```

Upgrade and uninstall it with:

```bash
uv tool upgrade img-convert
uv tool uninstall img-convert
```

## Usage

Invoke the converter directly:

```bash
img-convert INPUT... --to FORMAT
```

```bash
# One file: writes photo.jpeg beside photo.png
img-convert photo.png --to jpeg

# A directory (its immediate image files only)
img-convert photos --to webp --quality 90

# Quote globs so the tool can expand them consistently
img-convert "screenshots/*.png" --to jpg

# Search subdirectories too
img-convert photos --to tiff --recursive

# Preserve the input folder layout below converted/
img-convert photos --to webp --output-dir converted --recursive
```

Inputs may be individual image paths, directories, or quoted glob patterns. With `--recursive`, a simple quoted glob such as `"photos/*.png"` also searches subdirectories. Duplicate inputs are processed once.

`--quality` accepts 1 through 100 and applies to JPEG and WebP. An animated GIF is rejected instead of silently losing its extra frames.

### JPEG and transparency

JPEG has no alpha channel. To convert a transparent image to JPEG, choose the solid background explicitly:

```bash
img-convert logo.png --to jpeg --background '#ffffff'
```

Without `--background '#RRGGBB'`, that conversion is rejected so transparency is never discarded unexpectedly.

### Website favicons

`--to favicon` turns an image into the favicon set a website needs, written to a `<name>-favicon/` folder:

```bash
img-convert logo.png --to favicon                 # writes logo-favicon/
img-convert logo.png --to favicon -o public       # writes public/logo-favicon/
```

The folder holds `favicon.ico` (16, 32 and 48 px), `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`
(180 px), `android-chrome-192x192.png`, `android-chrome-512x512.png` and `site.webmanifest`. Copy them to the site
root and add the `<link>` tags the command prints to `<head>`; fill in `name` and `short_name` in the manifest.

Use a square image of at least 512 px for sharp results. A non-square image is centered on a transparent square.

### Existing files and replacing originals

Existing outputs are skipped by default. Use `--overwrite` only when replacing that output is intended:

```bash
img-convert photo.png --to webp --overwrite
```

`--replace` deletes an input only after its new output has saved successfully. It can be combined with `--overwrite`, but review the destination first:

```bash
img-convert originals --to webp --output-dir converted --replace --recursive
```

## Development

Run from a checkout without installing globally:

```bash
uv sync
uv run img-convert --help
uv run python -m img_convert --help
```

To contribute, make a focused change, refresh the lockfile with `uv lock`, and manually exercise the affected command before opening a pull request.
