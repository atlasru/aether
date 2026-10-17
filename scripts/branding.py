"""Render original repository-native Aether geometry and reuse upstream resource mappings.

Pillow is already a Helium build requirement. SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations
from pathlib import Path
import shutil

from common import ROOT


def icon(size, *, mono=False):
    from PIL import Image, ImageDraw
    scale = 4
    image = Image.new("RGBA", (256 * scale, 256 * scale))
    draw = ImageDraw.Draw(image)
    def points(values):
        return [(round(x * scale), round(y * scale)) for x, y in values]
    if not mono:
        draw.rounded_rectangle((0, 0, 256 * scale - 1, 256 * scale - 1),
                               radius=58 * scale, fill="#252733")
    draw.polygon(points([(53, 187), (115, 57), (128, 49), (141, 57),
                         (203, 187), (169, 187), (128, 96), (87, 187)]),
                 fill="#f3f3fa" if not mono else "#777a84")
    draw.polygon(points([(88, 157), (156, 139), (168, 165), (74, 189)]),
                 fill="#a89be9" if not mono else "#777a84")
    return image.resize((size, size), Image.Resampling.LANCZOS)


def install(source: Path, platform_root: Path, write):
    from PIL import Image
    manifests = [platform_root / "helium-chromium/resources/helium_resources.txt"]
    if (platform_root / "resources/platform_resources.txt").exists():
        manifests.append(platform_root / "resources/platform_resources.txt")
    for manifest in manifests:
        for line in manifest.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            original, target = line.split()
            if not (original.startswith("branding/") or original.startswith("generated/")):
                continue
            dst = source / target
            if dst.suffix == ".svg":
                write(dst, (ROOT / "assets/aether.svg").read_bytes())
            elif dst.suffix == ".icon":
                write(dst, (ROOT / "assets/aether.icon").read_bytes())
            elif dst.suffix in (".png", ".ico"):
                import io
                if dst.suffix == ".ico":
                    image = icon(256)
                    buf = io.BytesIO()
                    image.save(buf, format="ICO", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
                else:
                    if dst.exists():
                        with Image.open(dst) as previous:
                            size = previous.width
                    else:
                        size = int(original.split("/")[-1].split("x")[0])
                    image = icon(size, mono="mono" in original)
                    buf = io.BytesIO()
                    image.save(buf, format="PNG")
                write(dst, buf.getvalue())


def rebrand_strings(source: Path, platform_root: Path, write):
    """Reuse Helium's GRIT fingerprint migration, without editing upstream tools."""
    import sys
    import re
    sys.path.insert(0, str(platform_root / "helium-chromium/utils"))
    import name_substitution as names
    import name_substitution_utils as util
    names.IGNORE_DIRS = [*names.IGNORE_DIRS, ".aether-backup", ".git"]
    util.add_grit_to_path(source)
    util.REPLACEMENT_REGEXES = [(re.compile(r"\bHelium\b"), "Aether"),
                               (re.compile(r"\bhelium://"), "aether://")]
    replacements = {}
    for path in names.get_substitutable_files(source, ["grd", "grdp"]):
        original = path.read_text(encoding="utf-8")
        text = original.replace("&#36;", "!!dollar-sign-literal!!")
        updated, mapping = util.replace_grit_tree(text)
        if mapping:
            replacements.update(mapping)
            write(path, updated.replace("!!dollar-sign-literal!!", "&#36;").encode("utf-8"))
    for path in names.get_substitutable_files(source, ["xtb"]):
        text = path.read_text(encoding="utf-8").replace("&#36;", "!!dollar-sign-literal!!")
        updated = util.replace_xtb_tree(text, replacements)
        if updated:
            write(path, updated.replace("!!dollar-sign-literal!!", "&#36;").encode("utf-8"))
