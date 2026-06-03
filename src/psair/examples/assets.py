from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Iterator


PathParts = Sequence[str]
SpecPath = str | PathParts


def asset_path(package: str, *parts: str) -> Traversable:
    """Return a package resource path built from package and path parts."""
    path = resources.files(package)
    for part in parts:
        path = path.joinpath(part)
    return path


def read_yaml_asset(package: str, *parts: str) -> dict[str, Any]:
    """Read a packaged YAML asset and require a mapping at the root."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read YAML example assets.") from exc

    with asset_path(package, *parts).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, Mapping):
        raise TypeError(f"YAML asset {'/'.join(parts)} must contain a mapping.")
    return dict(data)


def read_yaml_specs(
    package: str,
    specs: Mapping[str, SpecPath],
    *,
    root: PathParts = (),
) -> dict[str, dict[str, Any]]:
    """Read a named collection of YAML specs from package resources."""
    return {
        name: read_yaml_asset(package, *root, *_normalize_parts(path))
        for name, path in specs.items()
    }


def get_rendered_docs_path(
    package: str,
    *parts: str,
) -> Path:
    """Return a concrete Path for a packaged rendered-docs directory."""
    return Path(asset_path(package, *parts))


def iter_rendered_markdown_files(
    package: str,
    *parts: str,
) -> Iterator[Path]:
    """Yield rendered markdown files from a package resource directory."""
    docs_path = get_rendered_docs_path(package, *parts)
    if not docs_path.exists():
        return
    yield from sorted(docs_path.rglob("*.md"))


@dataclass(frozen=True)
class ExampleAssets:
    """Convenience wrapper around a package's example asset directories."""

    package: str
    spec_root: PathParts = ("assets", "spec")
    rendered_docs_root: PathParts = ("assets", "rendered_docs", "example_io")

    def path(self, *parts: str) -> Traversable:
        return asset_path(self.package, *parts)

    def read_yaml_mapping(self, *parts: str) -> dict[str, Any]:
        return read_yaml_asset(self.package, *parts)

    def read_specs(
        self,
        specs: Mapping[str, SpecPath],
        *,
        root: PathParts | None = None,
    ) -> dict[str, dict[str, Any]]:
        return read_yaml_specs(
            self.package,
            specs,
            root=self.spec_root if root is None else root,
        )

    def rendered_docs_path(self) -> Path:
        return get_rendered_docs_path(self.package, *self.rendered_docs_root)

    def iter_rendered_markdown_files(self) -> Iterator[Path]:
        return iter_rendered_markdown_files(self.package, *self.rendered_docs_root)

    def write_rendered_doc(self, *parts: str, text: str) -> Path:
        from psair.examples.docs import write_rendered_doc

        return write_rendered_doc(
            self.package,
            *self.rendered_docs_root,
            *parts,
            text=text,
        )


def _normalize_parts(path: SpecPath) -> tuple[str, ...]:
    if isinstance(path, str):
        return tuple(part for part in path.replace("\\", "/").split("/") if part)
    return tuple(path)
