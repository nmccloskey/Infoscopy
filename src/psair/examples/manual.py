from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
import re
from typing import Literal

from psair.manual.index import (
    ManualFile,
    TreeNode,
    extract_md_title,
    numeric_sort_key,
    read_text_safely,
)


MD_EXTS = {".md", ".markdown"}
DEFAULT_VIEW_ORDER = {
    "quickstart": 10,
    "usage_guide": 20,
    "research_context": 30,
    "implementation_notes": 40,
    "example_io": 50,
}
DEFAULT_VIEW_LABELS = {
    "quickstart": "Quickstart",
    "usage_guide": "Usage Guide",
    "research_context": "Research Context",
    "implementation_notes": "Implementation Notes",
    "example_io": "Example I/O",
}

DuplicatePolicy = Literal["error", "diagnostic"]
UnmatchedPolicy = Literal["source_path", "generated_root"]


class ManualCompositionError(RuntimeError):
    """Raised when manual views cannot be composed deterministically."""


@dataclass(frozen=True)
class ManualSource:
    """A physical manual-like source tree used for composition."""

    root: Path
    name: str = "manual"
    source_manual: str = "authored"
    role: str = "authored"


@dataclass(frozen=True)
class ManualView:
    """One discovered manual view, with source and virtual display metadata."""

    source: ManualSource
    source_rel_path: Path
    display_rel_path: Path
    abs_path: Path
    object_type: str | None
    object_types: tuple[str, ...]
    object_id: str | None
    view: str
    view_label: str
    view_order: int
    title: str
    source_manual: str
    generated: bool
    front_matter: dict[str, object]
    text: str


@dataclass(frozen=True)
class ComposedManual:
    """A composed manual index plus the views and diagnostics that produced it."""

    tree: TreeNode
    flat: dict[str, ManualFile]
    views: tuple[ManualView, ...]
    diagnostics: tuple[str, ...]


def split_front_matter(text: str) -> tuple[dict[str, object], str]:
    """
    Split YAML front matter from Markdown text.

    Only an opening delimiter on the first line and a later delimiter line are
    treated as front matter. The returned body excludes one blank line after the
    closing delimiter so renderers start at the actual Markdown content.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return {}, text

    metadata_text = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])
    if body.startswith("\r\n"):
        body = body[2:]
    elif body.startswith("\n"):
        body = body[1:]

    return _load_front_matter(metadata_text), body


def discover_manual_views(
    sources: Sequence[ManualSource | str | Path],
    *,
    include_exts: set[str] | None = None,
    include_outline: bool = False,
    outline_name: str = "00_outline.md",
    infer_from_paths: bool = False,
    path_module_aliases: Mapping[str, str] | None = None,
) -> list[ManualView]:
    """Discover Markdown views from one or more source roots."""
    normalized_sources = [_normalize_source(source) for source in sources]
    views: list[ManualView] = []

    for source in normalized_sources:
        source_root = source.root.resolve()
        if not source_root.exists():
            continue

        for path in _iter_markdown_files(
            source_root,
            include_exts=include_exts,
            include_outline=include_outline,
            outline_name=outline_name,
        ):
            rel_path = path.relative_to(source_root)
            raw_text = read_text_safely(path)
            front_matter, body = split_front_matter(raw_text)
            inferred = (
                _infer_diaad_command_metadata(
                    rel_path,
                    module_aliases=path_module_aliases,
                )
                if infer_from_paths
                else {}
            )
            metadata: dict[str, object] = {**inferred, **front_matter}

            views.append(
                _build_manual_view(
                    source=replace(source, root=source_root),
                    source_rel_path=rel_path,
                    abs_path=path.resolve(),
                    front_matter=front_matter,
                    metadata=metadata,
                    text=body,
                )
            )

    return views


def compose_manual_views(
    views: Sequence[ManualView],
    *,
    unmatched_policy: UnmatchedPolicy = "source_path",
    on_duplicate: DuplicatePolicy = "error",
) -> ComposedManual:
    """
    Compose discovered views into the ManualFile tree used by PSAIR viewers.

    Generated views are placed beside authored views when they share
    ``object_type`` and ``object_id``. Views that cannot be matched are retained
    according to ``unmatched_policy``.
    """
    _validate_unmatched_policy(unmatched_policy)
    _validate_duplicate_policy(on_duplicate)

    diagnostics: list[str] = []
    composed_views: list[ManualView] = []

    grouped = _group_composable_views(views)
    grouped_ids = {id(view) for group in grouped.values() for view in group}

    for group_key in sorted(grouped, key=lambda key: (key[0], key[1])):
        group = grouped[group_key]
        duplicate_messages = _duplicate_view_messages(group)
        if duplicate_messages and on_duplicate == "error":
            raise ManualCompositionError("; ".join(duplicate_messages))
        diagnostics.extend(duplicate_messages)

        anchor_parent = _anchor_parent_for_group(group)
        if anchor_parent is None:
            diagnostics.append(
                "No authored anchor for "
                f"{group_key[0]}:{group_key[1]}; preserving generated view paths."
            )

        for view in sorted(group, key=_view_sort_key):
            display_rel_path = _display_path_for_view(
                view,
                anchor_parent=anchor_parent,
                unmatched_policy=unmatched_policy,
            )
            composed_views.append(replace(view, display_rel_path=display_rel_path))

    for view in views:
        if id(view) in grouped_ids:
            continue
        if view.generated:
            diagnostics.append(
                f"Generated view lacks object identity: {view.abs_path}"
            )
        composed_views.append(view)

    composed_views.sort(key=lambda view: _manual_path_sort_key(view.display_rel_path))
    tree, flat = _build_tree_and_flat(composed_views)
    return ComposedManual(
        tree=tree,
        flat=flat,
        views=tuple(composed_views),
        diagnostics=tuple(diagnostics),
    )


def build_composed_manual(
    sources: Sequence[ManualSource | str | Path],
    *,
    include_exts: set[str] | None = None,
    include_outline: bool = False,
    outline_name: str = "00_outline.md",
    infer_from_paths: bool = False,
    path_module_aliases: Mapping[str, str] | None = None,
    unmatched_policy: UnmatchedPolicy = "source_path",
    on_duplicate: DuplicatePolicy = "error",
) -> ComposedManual:
    """Discover and compose manual views from source roots."""
    views = discover_manual_views(
        sources,
        include_exts=include_exts,
        include_outline=include_outline,
        outline_name=outline_name,
        infer_from_paths=infer_from_paths,
        path_module_aliases=path_module_aliases,
    )
    return compose_manual_views(
        views,
        unmatched_policy=unmatched_policy,
        on_duplicate=on_duplicate,
    )


def build_composed_manual_index(
    sources: Sequence[ManualSource | str | Path],
    **kwargs: object,
) -> tuple[TreeNode, dict[str, ManualFile]]:
    """Build the composed manual tree and flat mapping for existing consumers."""
    composed = build_composed_manual(sources, **kwargs)
    return composed.tree, composed.flat


def _load_front_matter(metadata_text: str) -> dict[str, object]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PyYAML is required to parse Markdown front matter."
        ) from exc

    loaded = yaml.safe_load(metadata_text) or {}
    if not isinstance(loaded, Mapping):
        raise TypeError("Markdown front matter must contain a YAML mapping.")
    return dict(loaded)


def _normalize_source(source: ManualSource | str | Path) -> ManualSource:
    if isinstance(source, ManualSource):
        return replace(source, root=Path(source.root))
    path = Path(source)
    return ManualSource(root=path, name=path.name or "manual")


def _normalize_exts(exts: set[str] | None) -> set[str]:
    if not exts:
        return set(MD_EXTS)
    normalized = {ext.strip().lower() for ext in exts if ext and ext.strip()}
    return {ext if ext.startswith(".") else f".{ext}" for ext in normalized}


def _iter_markdown_files(
    root: Path,
    *,
    include_exts: set[str] | None,
    include_outline: bool,
    outline_name: str,
) -> list[Path]:
    include_exts = _normalize_exts(include_exts)
    paths: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if "__pycache__" in rel.parts:
            continue
        if path.suffix.lower() not in include_exts:
            continue
        if not include_outline and path.name == outline_name:
            continue

        paths.append(path)

    paths.sort(key=lambda path: _manual_path_sort_key(path.relative_to(root)))
    return paths


def _build_manual_view(
    *,
    source: ManualSource,
    source_rel_path: Path,
    abs_path: Path,
    front_matter: dict[str, object],
    metadata: dict[str, object],
    text: str,
) -> ManualView:
    view = _metadata_str(metadata, "view") or _view_from_path(source_rel_path)
    view_label = _metadata_str(metadata, "view_label") or _view_label(view)
    view_order = _metadata_int(
        metadata,
        "view_order",
        DEFAULT_VIEW_ORDER.get(view, 100),
    )
    object_type = _metadata_str(metadata, "object_type")
    object_id = _metadata_str(metadata, "object_id")
    object_types = _metadata_str_tuple(metadata.get("object_types"))
    if not object_types and object_type:
        object_types = (object_type,)

    title = _metadata_str(metadata, "title") or extract_md_title(
        text,
        fallback=source_rel_path.name,
    )
    source_manual = _metadata_str(metadata, "source_manual") or source.source_manual
    generated = _metadata_bool(metadata, "generated")
    if generated is None:
        generated = _source_is_generated(source)

    return ManualView(
        source=source,
        source_rel_path=source_rel_path,
        display_rel_path=source_rel_path,
        abs_path=abs_path,
        object_type=object_type,
        object_types=object_types,
        object_id=object_id,
        view=view,
        view_label=view_label,
        view_order=view_order,
        title=title,
        source_manual=source_manual,
        generated=generated,
        front_matter=front_matter,
        text=text,
    )


def _group_composable_views(
    views: Sequence[ManualView],
) -> dict[tuple[str, str], list[ManualView]]:
    grouped: dict[tuple[str, str], list[ManualView]] = {}
    for view in views:
        if view.object_type is None or view.object_id is None:
            continue
        grouped.setdefault((view.object_type, view.object_id), []).append(view)
    return grouped


def _duplicate_view_messages(views: Sequence[ManualView]) -> list[str]:
    by_view: dict[str, list[ManualView]] = {}
    for view in views:
        by_view.setdefault(view.view, []).append(view)

    messages: list[str] = []
    for view_name, duplicates in sorted(by_view.items()):
        if len(duplicates) < 2:
            continue
        object_type = duplicates[0].object_type or "unknown"
        object_id = duplicates[0].object_id or "unknown"
        sources = ", ".join(str(view.abs_path) for view in duplicates)
        messages.append(
            f"Duplicate manual view {object_type}:{object_id}:{view_name}: {sources}"
        )
    return messages


def _anchor_parent_for_group(views: Sequence[ManualView]) -> Path | None:
    authored = [view for view in views if not view.generated]
    if not authored:
        return None

    authored.sort(key=_view_sort_key)
    parent_counts: dict[Path, int] = {}
    for view in authored:
        parent_counts[view.source_rel_path.parent] = (
            parent_counts.get(view.source_rel_path.parent, 0) + 1
        )

    return max(
        parent_counts,
        key=lambda parent: (parent_counts[parent], _manual_path_sort_key(parent)),
    )


def _display_path_for_view(
    view: ManualView,
    *,
    anchor_parent: Path | None,
    unmatched_policy: UnmatchedPolicy,
) -> Path:
    if view.generated and anchor_parent is not None:
        return anchor_parent / _view_filename(view)

    if view.generated and anchor_parent is None and unmatched_policy == "generated_root":
        return Path("generated") / view.source.name / view.source_rel_path

    return view.source_rel_path


def _build_tree_and_flat(
    views: Sequence[ManualView],
) -> tuple[TreeNode, dict[str, ManualFile]]:
    tree: TreeNode = {}
    flat: dict[str, ManualFile] = {}

    for view in views:
        rel_str = view.display_rel_path.as_posix()
        if rel_str in flat:
            raise ManualCompositionError(f"Duplicate composed manual path: {rel_str}")

        title = view.view_label if view.object_type and view.object_id else view.title
        manual_file = ManualFile(
            rel_path=view.display_rel_path,
            abs_path=view.abs_path,
            title=title,
            text=view.text,
        )
        flat[rel_str] = manual_file

        cursor = tree
        parts = list(view.display_rel_path.parts)
        for part in parts[:-1]:
            child = cursor.get(part)
            if not isinstance(child, dict):
                child = {}
                cursor[part] = child
            cursor = child
        cursor[parts[-1]] = manual_file

    return tree, flat


def _infer_diaad_command_metadata(
    rel_path: Path,
    *,
    module_aliases: Mapping[str, str] | None = None,
) -> dict[str, object]:
    parts = list(rel_path.parts)
    if len(parts) < 5:
        return {}

    normalized = [_strip_numeric_prefix(Path(part).stem) for part in parts]
    try:
        commands_index = normalized.index("commands")
    except ValueError:
        return {}

    if commands_index < 1 or commands_index + 2 >= len(parts):
        return {}

    module_id = _strip_numeric_prefix(parts[commands_index - 1])
    module_id = _normalize_module_aliases(module_aliases).get(module_id, module_id)
    action_id = _strip_numeric_prefix(parts[commands_index + 1])
    view = _view_from_path(rel_path)
    if not module_id or not action_id or not view:
        return {}

    command_id = f"{module_id}.{action_id}"
    return {
        "object_type": "command",
        "object_types": ["command"],
        "object_id": command_id,
        "command_id": command_id,
        "module_id": module_id,
        "view": view,
        "view_label": _view_label(view),
        "view_order": DEFAULT_VIEW_ORDER.get(view, 100),
        "source_manual": "authored",
        "generated": False,
    }


def _normalize_module_aliases(
    aliases: Mapping[str, str] | None,
) -> dict[str, str]:
    if aliases is None:
        return {}
    normalized: dict[str, str] = {}
    for key, value in aliases.items():
        key_norm = _strip_numeric_prefix(str(key))
        value_norm = str(value).strip().lower()
        if key_norm and value_norm:
            normalized[key_norm] = value_norm
    return normalized


def _view_from_path(rel_path: Path) -> str:
    return _strip_numeric_prefix(rel_path.stem)


def _strip_numeric_prefix(value: str) -> str:
    stripped = Path(value).stem
    stripped = re.sub(r"^\d+(?:[_-]\d+)*[_-]?", "", stripped)
    return stripped.strip("_-").lower()


def _view_label(view: str) -> str:
    return DEFAULT_VIEW_LABELS.get(view, view.replace("_", " ").title())


def _view_filename(view: ManualView) -> str:
    prefix = view.view_order // 10 if view.view_order % 10 == 0 else view.view_order
    return f"{prefix:02d}_{view.view}.md"


def _metadata_str(metadata: Mapping[str, object], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _metadata_int(metadata: Mapping[str, object], key: str, default: int) -> int:
    value = metadata.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _metadata_bool(metadata: Mapping[str, object], key: str) -> bool | None:
    value = metadata.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return None


def _metadata_str_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        )
    return ()


def _source_is_generated(source: ManualSource) -> bool:
    return (
        source.role.strip().lower() == "generated"
        or source.source_manual.strip().lower().startswith("generated")
    )


def _view_sort_key(view: ManualView) -> tuple[int, list[tuple[int, str]]]:
    return view.view_order, _manual_path_sort_key(view.source_rel_path)


def _manual_path_sort_key(path: Path) -> list[tuple[int, str]]:
    return [numeric_sort_key(part) for part in path.parts]


def _validate_unmatched_policy(policy: str) -> None:
    if policy not in {"source_path", "generated_root"}:
        raise ValueError(
            "unmatched_policy must be one of ['generated_root', 'source_path'], "
            f"got: {policy!r}"
        )


def _validate_duplicate_policy(policy: str) -> None:
    if policy not in {"diagnostic", "error"}:
        raise ValueError(
            "on_duplicate must be one of ['diagnostic', 'error'], "
            f"got: {policy!r}"
        )
