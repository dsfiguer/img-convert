"""Run with: uv run python tests/test_favicon.py (also works under pytest)."""

import json
import tempfile
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from img_convert.cli import FAVICON_PNGS, app


def test_favicon_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "logo.png"
        Image.new("RGBA", (600, 300), (200, 30, 30, 255)).save(source)  # non-square on purpose

        result = CliRunner().invoke(app, [str(source), "--to", "favicon"])
        assert result.exit_code == 0, result.output
        assert '<link rel="manifest" href="/site.webmanifest">' in result.output

        folder = Path(tmp) / "logo-favicon"
        for name, size in FAVICON_PNGS.items():
            with Image.open(folder / name) as png:
                assert png.size == (size, size), name
                assert png.getpixel((0, 0))[3] == 0, f"{name}: padding should be transparent"
        with Image.open(folder / "favicon.ico") as ico:
            assert ico.info["sizes"] == {(16, 16), (32, 32), (48, 48)}
        manifest = json.loads((folder / "site.webmanifest").read_text())
        assert [icon["sizes"] for icon in manifest["icons"]] == ["192x192", "512x512"]

        again = CliRunner().invoke(app, [str(source), "--to", "favicon"])
        assert "Skipped" in again.output


if __name__ == "__main__":
    test_favicon_set()
    print("ok")
