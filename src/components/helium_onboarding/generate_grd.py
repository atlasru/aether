#!/usr/bin/env python3
"""Emit a small, deterministic GRIT manifest. SPDX-License-Identifier: GPL-3.0-only"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def generate(output: Path):
    root = ET.Element("grit", {"latest_public_release": "0", "current_release": "1",
                              "base_dir": str(Path(__file__).resolve().parent)})
    outputs = ET.SubElement(root, "outputs")
    for name, kind in [("grit/helium_onboarding_generated.h", "rc_header"),
                       ("grit/helium_onboarding_generated_map.cc", "resource_file_map_source"),
                       ("grit/helium_onboarding_generated_map.h", "resource_map_header"),
                       ("helium_onboarding_generated.pak", "data_package")]:
        ET.SubElement(outputs, "output", {"filename": name, "type": kind})
    includes = ET.SubElement(ET.SubElement(root, "release", {"seq": "1"}), "includes")
    for name, filename in [("INDEX_HTML", "index.html"), ("STYLE", "setup.css"),
                           ("SCRIPT", "setup.js"), ("STATE", "state.mjs"),
                           ("LOGO", "aether.svg")]:
        ET.SubElement(includes, "include", {"name": "IDR_HELIUM_ONBOARDING_" + name,
                       "file": filename, "type": "BINDATA", "resource_path": filename})
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    output.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


if __name__ == "__main__":
    generate(Path(sys.argv[1]))
