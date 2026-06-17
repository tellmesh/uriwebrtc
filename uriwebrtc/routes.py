from __future__ import annotations

from importlib.resources import files

from urisysedge.manifest import register_manifest_file


def register(rt):
    register_manifest_file(rt, files(__package__).joinpath("manifest.yaml"))
