from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import re
from typing import Dict, Literal, Optional, Union

import streamlit as st

from ..examples.manual import (
    DuplicatePolicy,
    ManualSource,
    UnmatchedPolicy,
    build_composed_manual,
)
from ..manual.index import (
    ManualFile,
    TreeNode,
    build_manual_index,
    numeric_sort_key,
    render_generated_tree_text,
    search_manual,
)
from ..manual.outline import ensure_manual_outline
from .manual_export import (
    build_manual_markdown_from_index,
    detect_manual_export_backends,
    export_manual_docx,
    export_manual_pdf,
)

OutlineMode = Literal["never", "if_missing", "always"]
ManualSourceInput = Union[ManualSource, Mapping[str, object], str, Path]
ManualSourceCacheSpec = tuple[str, str, str, str]
_SECTION_LABEL_RE = re.compile(r"^(?P<num>\d+(?:[_-]\d+)*)(?:[_-].*)?$")


@st.cache_data(show_spinner=False)
def build_manual_index_cached(manual_dir: str) -> tuple[TreeNode, Dict[str, ManualFile]]:
    return build_manual_index(manual_dir)


@st.cache_data(show_spinner=False)
def build_composed_manual_index_cached(
    source_specs: tuple[ManualSourceCacheSpec, ...],
    infer_from_paths: bool,
    unmatched_policy: UnmatchedPolicy,
    on_duplicate: DuplicatePolicy,
) -> tuple[TreeNode, Dict[str, ManualFile], tuple[str, ...]]:
    return _build_composed_manual_index_from_specs(
        source_specs,
        infer_from_paths=infer_from_paths,
        unmatched_policy=unmatched_policy,
        on_duplicate=on_duplicate,
    )


@st.cache_data(show_spinner=False)
def export_manual_pdf_cached(
    markdown_text: str,
    title: str,
    yaml_path: str,
    base_url: str,
    backend_key: str,
) -> tuple[bytes, str]:
    _ = backend_key
    return export_manual_pdf(
        markdown_text,
        title=title,
        yaml_path=yaml_path or None,
        base_url=base_url or None,
    )


@st.cache_data(show_spinner=False)
def export_manual_docx_cached(markdown_text: str, title: str) -> bytes:
    return export_manual_docx(markdown_text, title=title)


def _validate_outline_mode(mode: str) -> OutlineMode:
    allowed: set[str] = {"never", "if_missing", "always"}
    if mode not in allowed:
        raise ValueError(
            f"ensure_outline must be one of {sorted(allowed)}, got: {mode!r}"
        )
    return mode  # type: ignore[return-value]


def _format_section_label(mf: ManualFile | None, fallback_name: str) -> str:
    name = mf.rel_path.name if mf else fallback_name
    stem = Path(name).stem
    title = mf.title if mf else fallback_name

    match = _SECTION_LABEL_RE.match(stem)
    if not match:
        return title

    section_num = ".".join(
        str(int(part)) for part in re.split(r"[_-]", match.group("num"))
    )
    return f"{section_num}: {title}"


def _manual_ui_namespace(manual_rel_dir: Union[str, Path], ui_key: str | None = None) -> str:
    """
    Return a stable namespace for one manual viewer instance.
    """
    if ui_key:
        base = ui_key
    else:
        base = Path(manual_rel_dir).as_posix()

    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", base).strip("_").lower()
    return safe or "manual"


def _manual_state_keys(ns: str) -> dict[str, str]:
    """
    Return namespaced session-state keys for one manual viewer instance.
    """
    return {
        "selected": f"{ns}_selected",
        "expand_all": f"{ns}_expand_all",
        "search": f"{ns}_search",
    }


def _init_manual_state(state_keys: dict[str, str]) -> None:
    """
    Initialize namespaced manual state if missing.
    """
    if state_keys["selected"] not in st.session_state:
        st.session_state[state_keys["selected"]] = None
    if state_keys["expand_all"] not in st.session_state:
        st.session_state[state_keys["expand_all"]] = False
    if state_keys["search"] not in st.session_state:
        st.session_state[state_keys["search"]] = ""


def _toggle_selected(selected_key: str, rel_str: str) -> None:
    """
    Toggle the visible manual section for a specific manual viewer.
    """
    current = st.session_state.get(selected_key)
    st.session_state[selected_key] = None if current == rel_str else rel_str
    st.rerun()


def _prepare_manual_root(
    *,
    repo_root: Union[str, Path],
    manual_rel_dir: Union[str, Path],
    ensure_outline: OutlineMode,
    outline_title: str,
    outline_version: str,
    outline_max_depth: int | None,
) -> Path | None:
    """
    Resolve manual root and ensure outline if requested.
    """
    repo_root = Path(repo_root).resolve()
    manual_root = (repo_root / manual_rel_dir).resolve()
    ensure_outline = _validate_outline_mode(ensure_outline)

    if not manual_root.exists():
        st.warning(f"Manual directory not found: {manual_root}")
        return None

    if ensure_outline != "never":
        try:
            ensure_manual_outline(
                manual_root,
                manual_title=outline_title,
                manual_version=outline_version,
                max_depth=outline_max_depth,
                if_missing_only=(ensure_outline == "if_missing"),
            )
        except Exception as exc:
            st.warning(f"Could not prepare manual outline: {exc}")

    return manual_root


def _normalize_manual_source_specs(
    *,
    repo_root: Union[str, Path],
    manual_sources: Sequence[ManualSourceInput],
) -> tuple[ManualSourceCacheSpec, ...]:
    """
    Convert public manual-source inputs to cache-safe absolute source specs.
    """
    repo_root = Path(repo_root).resolve()
    specs: list[ManualSourceCacheSpec] = []

    for source in manual_sources:
        root, name, source_manual, role = _manual_source_parts(source)
        root_path = Path(root)
        if not root_path.is_absolute():
            root_path = repo_root / root_path
        root_path = root_path.resolve()
        resolved_name = name or root_path.name or "manual"
        specs.append(
            (
                str(root_path),
                resolved_name,
                source_manual or "authored",
                role or "authored",
            )
        )

    return tuple(specs)


def _manual_source_parts(
    source: ManualSourceInput,
) -> tuple[Union[str, Path], str, str, str]:
    if isinstance(source, ManualSource):
        return source.root, source.name, source.source_manual, source.role

    if isinstance(source, Mapping):
        if "root" not in source:
            raise ValueError("Manual source mappings must include a 'root' value.")
        root = source["root"]
        if not isinstance(root, (str, Path)):
            raise TypeError("Manual source 'root' must be a path string or Path.")

        root_path = Path(root)
        name = _mapping_str(source, "name") or root_path.name or "manual"
        source_manual = _mapping_str(source, "source_manual") or "authored"
        role = _mapping_str(source, "role") or "authored"
        return root, name, source_manual, role

    path = Path(source)
    return path, path.name or "manual", "authored", "authored"


def _mapping_str(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _prepare_manual_sources(
    *,
    repo_root: Union[str, Path],
    manual_sources: Sequence[ManualSourceInput],
    ensure_outline: OutlineMode,
    outline_title: str,
    outline_version: str,
    outline_max_depth: int | None,
) -> tuple[ManualSourceCacheSpec, ...] | None:
    """
    Resolve composed manual sources and ensure outlines for authored roots.
    """
    ensure_outline = _validate_outline_mode(ensure_outline)
    specs = _normalize_manual_source_specs(
        repo_root=repo_root,
        manual_sources=manual_sources,
    )
    prepared: list[ManualSourceCacheSpec] = []

    for root_str, name, source_manual, role in specs:
        root = Path(root_str)
        if not root.exists():
            st.warning(f"Manual source directory not found: {root}")
            continue

        if ensure_outline != "never" and not _manual_source_is_generated(
            source_manual=source_manual,
            role=role,
        ):
            try:
                ensure_manual_outline(
                    root,
                    manual_title=outline_title,
                    manual_version=outline_version,
                    max_depth=outline_max_depth,
                    if_missing_only=(ensure_outline == "if_missing"),
                )
            except Exception as exc:
                st.warning(f"Could not prepare manual outline for {root}: {exc}")

        prepared.append((root_str, name, source_manual, role))

    if not prepared:
        st.warning("No manual source directories found.")
        return None

    return tuple(prepared)


def _manual_source_is_generated(*, source_manual: str, role: str) -> bool:
    return (
        role.strip().lower() == "generated"
        or source_manual.strip().lower().startswith("generated")
    )


def _build_composed_manual_index_from_specs(
    source_specs: tuple[ManualSourceCacheSpec, ...],
    *,
    infer_from_paths: bool,
    unmatched_policy: UnmatchedPolicy,
    on_duplicate: DuplicatePolicy,
) -> tuple[TreeNode, Dict[str, ManualFile], tuple[str, ...]]:
    sources = [
        ManualSource(
            root=Path(root),
            name=name,
            source_manual=source_manual,
            role=role,
        )
        for root, name, source_manual, role in source_specs
    ]
    composed = build_composed_manual(
        sources,
        infer_from_paths=infer_from_paths,
        unmatched_policy=unmatched_policy,
        on_duplicate=on_duplicate,
    )
    return composed.tree, composed.flat, composed.diagnostics


def _render_manual_controls(
    *,
    ns: str,
    state_keys: dict[str, str],
) -> None:
    """
    Render the top-row manual controls.
    """
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        st.session_state[state_keys["expand_all"]] = st.toggle(
            "Expand all",
            value=st.session_state[state_keys["expand_all"]],
            key=f"{ns}_toggle_expand_all",
        )

    with c2:
        if st.button("Hide section", key=f"{ns}_hide_section"):
            st.session_state[state_keys["selected"]] = None
            st.rerun()

    with c3:
        st.session_state[state_keys["search"]] = st.text_input(
            "Search",
            value=st.session_state[state_keys["search"]],
            placeholder="Search titles + content...",
            key=f"{ns}_search_input",
        )


def _render_manual_downloads(
    *,
    ns: str,
    repo_root: Path,
    manual_root: Path,
    flat: Dict[str, ManualFile],
    pdf_yaml_rel_path: Union[str, Path, None],
    fallback_title: str,
    enable_pdf_export: bool = False,
    enable_docx_export: bool = True,
) -> None:
    """Render manual export controls for available, enabled formats only."""
    backends = detect_manual_export_backends(check_pdf=enable_pdf_export)

    pdf_available = enable_pdf_export and (
        backends["pandoc_pdf"] or backends["weasyprint_pdf"]
    )
    docx_available = enable_docx_export and backends["docx"]
    if not pdf_available and not docx_available:
        unavailable_reasons = []
        if enable_docx_export and not backends["docx"]:
            unavailable_reasons.append("DOCX export requires python-docx.")
        if enable_pdf_export and not (
            backends["pandoc_pdf"] or backends["weasyprint_pdf"]
        ):
            unavailable_reasons.append(
                "PDF export requires Pandoc or the markdown/weasyprint packages."
            )
        if unavailable_reasons:
            st.caption(f"Manual export unavailable: {' '.join(unavailable_reasons)}")
        return

    yaml_path = _resolve_pdf_yaml_path(repo_root, manual_root, pdf_yaml_rel_path)
    title = _manual_export_title(manual_root, yaml_path, fallback_title)
    markdown_text, _section_meta = build_manual_markdown_from_index(flat)

    renderers = []
    if pdf_available:
        renderers.append(
            lambda: _render_pdf_download_button(
                ns=ns,
                manual_root=manual_root,
                markdown_text=markdown_text,
                title=title,
                yaml_path=yaml_path,
                backends=backends,
            )
        )
    if docx_available:
        renderers.append(
            lambda: _render_docx_download_button(
                ns=ns,
                manual_root=manual_root,
                markdown_text=markdown_text,
                title=title,
            )
        )

    columns = st.columns(len(renderers)) if len(renderers) > 1 else [st.container()]
    for column, render in zip(columns, renderers):
        with column:
            render()


def _render_pdf_download_button(
    *,
    ns: str,
    manual_root: Path,
    markdown_text: str,
    title: str,
    yaml_path: Path | None,
    backends: dict[str, bool],
) -> None:
    try:
        with st.spinner("Preparing PDF export..."):
            pdf_bytes, backend = export_manual_pdf_cached(
                markdown_text,
                title,
                str(yaml_path) if yaml_path else "",
                str(manual_root),
                _backend_cache_key(backends),
            )
    except Exception as exc:
        st.warning(f"PDF export failed: {exc}")
        return

    st.download_button(
        "Download manual (PDF)",
        data=pdf_bytes,
        file_name=_manual_export_filename(manual_root, ".pdf"),
        mime="application/pdf",
        key=f"{ns}_download_pdf",
    )
    st.caption(f"PDF export backend: {backend}")


def _render_docx_download_button(
    *,
    ns: str,
    manual_root: Path,
    markdown_text: str,
    title: str,
) -> None:
    try:
        with st.spinner("Preparing DOCX export..."):
            docx_bytes = export_manual_docx_cached(markdown_text, title)
    except Exception as exc:
        st.warning(f"DOCX export failed: {exc}")
        return

    st.download_button(
        "Download manual (DOCX)",
        data=docx_bytes,
        file_name=_manual_export_filename(manual_root, ".docx"),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        key=f"{ns}_download_docx",
    )


def _resolve_pdf_yaml_path(
    repo_root: Path,
    manual_root: Path,
    pdf_yaml_rel_path: Union[str, Path, None],
) -> Path | None:
    if pdf_yaml_rel_path is not None:
        candidate = Path(pdf_yaml_rel_path)
        candidates = [candidate] if candidate.is_absolute() else [
            repo_root / candidate,
            manual_root / candidate,
        ]
        return next((path.resolve() for path in candidates if path.exists()), None)

    candidates = [
        manual_root / "manual_pdf.yaml",
        manual_root / f"{manual_root.name}_pdf.yaml",
    ]
    return next((path.resolve() for path in candidates if path.exists()), None)


def _manual_export_title(
    manual_root: Path,
    yaml_path: Path | None,
    fallback_title: str,
) -> str:
    yaml_title = _read_yaml_title(yaml_path)
    if yaml_title:
        return yaml_title
    if fallback_title and fallback_title != "Instruction Manual":
        return fallback_title
    return manual_root.name.replace("_", " ").title()


def _read_yaml_title(yaml_path: Path | None) -> str | None:
    if yaml_path is None:
        return None
    try:
        import yaml

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict) and isinstance(data.get("title"), str):
        return data["title"].strip() or None
    return None


def _manual_export_filename(manual_root: Path, suffix: str) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", manual_root.name).strip("_")
    return f"{safe_name or 'manual'}{suffix}"


def _backend_cache_key(backends: dict[str, bool]) -> str:
    return ",".join(
        f"{name}={int(enabled)}" for name, enabled in sorted(backends.items())
    )


def _render_manual_search(
    *,
    ns: str,
    flat,
    state_keys: dict[str, str],
) -> None:
    """
    Render search results for a manual viewer.
    """
    q = st.session_state[state_keys["search"]].strip()
    if not q:
        return

    with st.expander("Search results", expanded=True):
        results = search_manual(flat, q, limit=25)
        if not results:
            st.caption("No matches.")
            return

        for rel_str, _score in results:
            mf = flat[rel_str]
            label = _format_section_label(mf, mf.rel_path.name)
            if st.button(label, key=f"{ns}_search_result_{rel_str}"):
                _toggle_selected(state_keys["selected"], rel_str)


def _render_manual_sections(
    *,
    ns: str,
    tree,
    flat,
    state_keys: dict[str, str],
) -> None:
    """
    Render the manual section browser.
    """
    st.markdown("### Manual Sections")
    st.caption("Tip: Click a file once to show it below. Click it again to hide it.")

    expand_all = st.session_state[state_keys["expand_all"]]
    selected = st.session_state[state_keys["selected"]]

    root_keys = sorted(tree.keys(), key=numeric_sort_key)
    for name in root_keys:
        node = tree[name]

        if isinstance(node, dict):
            with st.expander(
                f"Folder: {name}",
                expanded=expand_all,
            ):
                _render_folder_accordion(
                    node=node,
                    rel_prefix=Path(name),
                    flat=flat,
                    expand_all=expand_all,
                    selected_key=state_keys["selected"],
                    key_prefix=f"{ns}_folder",
                )
            continue

        rel_str = Path(name).as_posix()
        mf = flat.get(rel_str)
        label = _format_section_label(mf, name)

        if selected == rel_str:
            label = f"> {label}"

        if st.button(label, key=f"{ns}_root_open_{rel_str}"):
            _toggle_selected(state_keys["selected"], rel_str)


def _render_manual_content(*, flat, state_keys: dict[str, str], header_label: str = "Manual") -> None:
    """
    Render the selected manual section content below the menu.
    """
    rel_selected: Optional[str] = st.session_state[state_keys["selected"]]
    if not rel_selected:
        st.info("Select from the above menu to view instructions.")
        return

    if rel_selected not in flat:
        st.warning(f"Selected file not found: {rel_selected}")
        return

    mf = flat[rel_selected]
    crumbs = [header_label] + list(mf.rel_path.parts)
    st.caption(" / ".join(crumbs))
    st.markdown(mf.text)


def render_manual_ui(
    *,
    repo_root: Union[str, Path],
    manual_rel_dir: Union[str, Path] = "manual",
    manual_sources: Sequence[ManualSourceInput] | None = None,
    expander_label: str = "Show / Hide Instruction Manual",
    ensure_outline: OutlineMode = "if_missing",
    outline_title: str = "Instruction Manual",
    outline_version: str = "0.0.0",
    outline_max_depth: int | None = None,
    ui_key: str | None = None,
    pdf_yaml_rel_path: Union[str, Path, None] = None,
    enable_pdf_export: bool = False,
    enable_docx_export: bool = True,
    compose_infer_from_paths: bool = False,
    compose_unmatched_policy: UnmatchedPolicy = "source_path",
    compose_on_duplicate: DuplicatePolicy = "error",
) -> None:
    """
    Render a namespaced Streamlit manual viewer.

    This version supports multiple manual viewers on the same page by
    namespacing widget keys and session-state fields. Set manual_sources to
    compose authored and generated manual roots into one tree. pdf_yaml_rel_path
    may point to a Pandoc metadata YAML file relative to repo_root or the
    primary manual root. PDF export is opt-in so downstream web apps can stay
    lightweight.
    """
    ns = _manual_ui_namespace(manual_rel_dir, ui_key=ui_key)
    state_keys = _manual_state_keys(ns)
    _init_manual_state(state_keys)

    if manual_sources is None:
        manual_root = _prepare_manual_root(
            repo_root=repo_root,
            manual_rel_dir=manual_rel_dir,
            ensure_outline=ensure_outline,
            outline_title=outline_title,
            outline_version=outline_version,
            outline_max_depth=outline_max_depth,
        )
        if manual_root is None:
            return

        tree, flat = build_manual_index_cached(str(manual_root))
        diagnostics: tuple[str, ...] = ()
    else:
        source_specs = _prepare_manual_sources(
            repo_root=repo_root,
            manual_sources=manual_sources,
            ensure_outline=ensure_outline,
            outline_title=outline_title,
            outline_version=outline_version,
            outline_max_depth=outline_max_depth,
        )
        if source_specs is None:
            return

        manual_root = Path(source_specs[0][0])
        tree, flat, diagnostics = build_composed_manual_index_cached(
            source_specs,
            compose_infer_from_paths,
            compose_unmatched_policy,
            compose_on_duplicate,
        )

    if not flat:
        st.warning(f"No markdown files found under: {manual_root}")
        return

    with st.expander(expander_label, expanded=False):
        _render_manual_controls(ns=ns, state_keys=state_keys)
        _render_manual_downloads(
            ns=ns,
            repo_root=Path(repo_root).resolve(),
            manual_root=manual_root,
            flat=flat,
            pdf_yaml_rel_path=pdf_yaml_rel_path,
            fallback_title=outline_title,
            enable_pdf_export=enable_pdf_export,
            enable_docx_export=enable_docx_export,
        )

        with st.expander("Manual Map (Tree)", expanded=False):
            st.code(render_generated_tree_text(tree, show_titles=True), language="text")

        if diagnostics:
            with st.expander("Manual Composition Notes", expanded=False):
                for diagnostic in diagnostics:
                    st.caption(diagnostic)

        _render_manual_search(ns=ns, flat=flat, state_keys=state_keys)
        _render_manual_sections(ns=ns, tree=tree, flat=flat, state_keys=state_keys)

    _render_manual_content(flat=flat, state_keys=state_keys, header_label="Manual")


def _render_folder_accordion(
    *,
    node,
    rel_prefix: Path,
    flat,
    expand_all: bool,
    selected_key: str,
    key_prefix: str,
) -> None:
    """
    Render nested manual folders/files with namespaced widget keys.
    """
    child_keys = sorted(node.keys(), key=numeric_sort_key)

    for name in child_keys:
        child = node[name]
        rel_path = rel_prefix / name

        if isinstance(child, dict):
            with st.expander(
                f"Folder: {name}",
                expanded=expand_all,
            ):
                _render_folder_accordion(
                    node=child,
                    rel_prefix=rel_path,
                    flat=flat,
                    expand_all=expand_all,
                    selected_key=selected_key,
                    key_prefix=f"{key_prefix}_{name}",
                )
            continue

        rel_str = rel_path.as_posix()
        mf = flat.get(rel_str)
        label = _format_section_label(mf, name)

        if st.session_state.get(selected_key) == rel_str:
            label = f"> {label}"

        if st.button(label, key=f"{key_prefix}_open_{rel_str}"):
            _toggle_selected(selected_key, rel_str)
