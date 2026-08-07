"""Command-line implementation for img-convert."""

from __future__ import annotations

import glob
import re
from pathlib import Path

import typer
from PIL import Image, UnidentifiedImageError

app = typer.Typer(add_completion=False, help="Convert raster images in bulk.")

IMAGE_EXTENSIONS = {".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
FORMAT_ALIASES = {"jpg": "jpeg", "tif": "tiff"}
PILLOW_FORMATS = {
    "bmp": "BMP",
    "gif": "GIF",
    "ico": "ICO",
    "jpeg": "JPEG",
    "png": "PNG",
    "tiff": "TIFF",
    "webp": "WEBP",
}
BACKGROUND_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def resolve_inputs(inputs: list[str], recursive: bool = False) -> list[tuple[Path, Path]]:
    """Expand paths, directories, and quoted glob patterns without duplicates."""
    results: list[tuple[Path, Path]] = []
    seen: set[Path] = set()

    def add(path: Path, relative: Path) -> None:
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            return
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            results.append((path, relative))

    for raw_input in inputs:
        path = Path(raw_input)
        if path.is_dir():
            iterator = path.rglob("*") if recursive else path.iterdir()
            for candidate in sorted(iterator):
                add(candidate, candidate.relative_to(path))
            continue

        if glob.has_magic(raw_input):
            search = raw_input
            if recursive and "**" not in raw_input:
                pattern_path = Path(raw_input)
                search = str(pattern_path.parent / "**" / pattern_path.name)

            base_parts: list[str] = []
            for part in Path(raw_input).parts:
                if glob.has_magic(part):
                    break
                base_parts.append(part)
            base = Path(*base_parts) if base_parts else Path(".")

            for match in sorted(glob.glob(search, recursive=True)):
                candidate = Path(match)
                try:
                    relative = candidate.relative_to(base)
                except ValueError:
                    relative = Path(candidate.name)
                add(candidate, relative)
            continue

        if path.is_file():
            add(path, Path(path.name))
        else:
            typer.echo(f"Warning: skipping '{raw_input}' (not found)", err=True)

    return results


def normalized_format(value: str) -> str:
    target = FORMAT_ALIASES.get(value.lower(), value.lower())
    if target not in PILLOW_FORMATS:
        supported = ", ".join(("jpg/jpeg", "png", "webp", "bmp", "tif/tiff", "gif", "ico"))
        raise typer.BadParameter(f"unsupported format '{value}'. Supported: {supported}")
    return target


def parse_background(value: str | None) -> tuple[int, int, int] | None:
    if value is None:
        return None
    if not BACKGROUND_PATTERN.fullmatch(value):
        raise typer.BadParameter("must be a hex color in the form #RRGGBB")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def has_transparency(image: Image.Image) -> bool:
    rgba = image.convert("RGBA")
    return rgba.getchannel("A").getextrema()[0] < 255


def flattened_for_jpeg(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    result = Image.new("RGB", rgba.size, background)
    result.paste(rgba, mask=rgba.getchannel("A"))
    return result


@app.command()
def convert(
    inputs: list[str] = typer.Argument(..., metavar="INPUT...", help="Image files, directories, or quoted glob patterns."),
    to: str = typer.Option(..., "--to", "-t", help="Target format (for example: png or jpeg)."),
    output_dir: Path | None = typer.Option(None, "--output-dir", "-o", help="Mirror input paths under this directory."),
    quality: int = typer.Option(85, "--quality", "-q", min=1, max=100, help="Quality for JPEG and WebP (1-100)."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite an existing output file."),
    replace: bool = typer.Option(False, "--replace", "-r", help="Delete an original only after its output saves."),
    recursive: bool = typer.Option(False, "--recursive", "-R", help="Recurse through directory and glob inputs."),
    background: str | None = typer.Option(None, "--background", help="JPEG background color, as #RRGGBB."),
) -> None:
    """Convert INPUT files directly; no subcommand is required."""
    target = normalized_format(to)
    background_color = parse_background(background)
    files = resolve_inputs(inputs, recursive=recursive)
    if not files:
        typer.echo("Error: no supported image files found.", err=True)
        raise typer.Exit(1)

    converted = skipped = failed = 0
    for source, relative in files:
        destination = (
            output_dir / relative.with_suffix(f".{target}")
            if output_dir is not None
            else source.with_suffix(f".{target}")
        )

        if destination.exists() and not overwrite:
            typer.echo(f"Skipped: {source} -> {destination} (already exists; use --overwrite)")
            skipped += 1
            continue

        try:
            with Image.open(source) as opened:
                opened.load()
                if opened.format == "GIF" and getattr(opened, "n_frames", 1) > 1:
                    raise ValueError("animated GIFs are not supported")

                image = opened.copy()
                if target == "jpeg":
                    if has_transparency(image):
                        if background_color is None:
                            raise ValueError("transparent images need --background '#RRGGBB' for JPEG output")
                        image = flattened_for_jpeg(image, background_color)
                    elif image.mode != "RGB":
                        image = image.convert("RGB")

                destination.parent.mkdir(parents=True, exist_ok=True)
                save_options: dict[str, int] = {}
                if target in {"jpeg", "webp"}:
                    save_options["quality"] = quality
                image.save(destination, format=PILLOW_FORMATS[target], **save_options)

            deleted = ""
            if replace and destination.resolve() != source.resolve():
                source.unlink()
                deleted = " (original deleted)"
            typer.echo(f"Converted: {source} -> {destination}{deleted}")
            converted += 1
        except (OSError, UnidentifiedImageError, ValueError) as error:
            typer.echo(f"Error: {source}: {error}", err=True)
            failed += 1

    typer.echo(f"Finished: {converted} converted, {skipped} skipped, {failed} failed.")
    if failed:
        raise typer.Exit(1)
