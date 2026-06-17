
# manual_viewer Module

## Overview

The `manual_viewer` module provides an **interactive Streamlit interface for browsing IRIDIC manuals**.

Unlike the other manual modules, which operate as CLI utilities or build tools, this module renders manuals as a **dynamic web interface** embedded within Streamlit applications.

The viewer allows users to:

- browse manual sections through a hierarchical folder UI
- search manual content and titles
- expand and collapse manual directories
- display documentation inline within the application
- download the displayed manual as PDF or DOCX when optional export backends are available
- compose authored manual roots with generated Example I/O roots into one
  navigable tree

This functionality makes it possible to integrate **fully navigable instruction manuals directly into Streamlit-based tools**.

## Download Backends

Manual downloads are optional runtime features. Pandoc is detected from `PATH`
and remains an external system dependency rather than a Python package
dependency; local CLI users install Pandoc separately, while hosted Streamlit
deployments can provide it through root-level `packages.txt`. If Pandoc is
absent or PDF compilation fails, the app falls back to WeasyPrint when the
Python webapp dependencies are installed. DOCX export uses `python-docx` and
can remain available even when no PDF backend succeeds.

---

# Data Model

The module primarily relies on data structures provided by the `manual_index` module.

Key structures used include:

| Structure | Purpose |
|----------|---------|
| `ManualFile` | Represents a manual document |
| `TreeNode` | Nested dictionary representing manual hierarchy |

These structures are generated using:

```
build_manual_index()
```

and cached within the viewer for performance.

---

# Composed Manual Sources

`render_manual_ui()` can still read a single physical manual root through
`manual_rel_dir`. It can also compose multiple source roots through the
`manual_sources` argument.

Each source can be a path, a `ManualSource`, or a mapping with:

| Field | Purpose |
|----------|-------------|
| `root` | Source directory, absolute or relative to `repo_root` |
| `name` | Stable source name used in diagnostics and unmatched generated paths |
| `source_manual` | Source label such as `authored` or `generated_example_io` |
| `role` | Source role such as `authored` or `generated` |

Example:

```python
render_manual_ui(
    repo_root=repo_root,
    manual_sources=[
        {"root": "docs/manual", "name": "manual", "role": "authored"},
        {
            "root": package_root / "examples/assets/rendered_docs/example_io",
            "name": "example_io",
            "source_manual": "generated_example_io",
            "role": "generated",
        },
    ],
    compose_infer_from_paths=True,
)
```

Generated views are matched to authored views by manual metadata such as
`object_type`, `object_id`, and `view`. When an authored command folder can be
identified, generated `example_io` content appears as a virtual sibling such as
`05_example_io.md` without being copied into the authored manual tree.
See Manual Composition (`docs/doctools_manual/09_manual_composition.md`) for
the full source, front matter, ordering, export, and limitation contract.

---

# Core Functions

## render_manual_ui

Primary entry point for the manual viewer.

```
render_manual_ui(repo_root)
```

### Purpose

Renders a complete interactive manual viewer within a Streamlit application.

### Parameters

| Parameter | Description |
|----------|-------------|
| `repo_root` | Repository root containing the manual directory |
| `manual_rel_dir` | Manual directory relative to the repo root |
| `expander_label` | Label for the manual viewer toggle |
| `ensure_outline` | Outline generation policy |
| `outline_title` | Title used if an outline is generated |
| `outline_version` | Version string used if outline is generated |
| `outline_max_depth` | Maximum depth for generated outline trees |
| `manual_sources` | Optional multi-root source list for composed manuals |
| `compose_infer_from_paths` | Enables transitional path inference for authored command views |
| `compose_unmatched_policy` | Controls placement of generated views without authored anchors |

### Outline Modes

The `ensure_outline` parameter controls whether the manual outline is generated.

| Mode | Behavior |
|-----|----------|
| `"never"` | Do not generate an outline |
| `"if_missing"` | Generate outline only if absent |
| `"always"` | Rebuild outline on each render |

This mechanism ensures that the viewer always has a valid navigation index when needed.

---

## build_manual_index_cached

Cached wrapper around the indexing system.

```
build_manual_index_cached(manual_dir)
```

The function uses:

```
@st.cache_data
```

to avoid recomputing the manual index on every page refresh.

This significantly improves performance for large manuals.

---

# Supporting Utilities

## _toggle_selected

Handles selection state for manual sections.

Behavior:

- first click → open section
- second click → close section

The function updates `st.session_state` and triggers a rerun of the Streamlit script.

---

## _validate_outline_mode

Validates the configuration for outline generation.

Accepted values:

```
never
if_missing
always
```

Invalid modes raise a descriptive error.

---

## _render_folder_accordion

Recursive helper used to render the folder hierarchy.

The function:

1. traverses the manual tree
2. creates nested Streamlit expanders
3. attaches click handlers to each manual file

This produces the interactive folder-style navigation interface.

---

# UI Components

The viewer renders several interactive elements.

### Manual expander

The entire manual interface is wrapped in a collapsible container:

```
📘 Show / Hide Instruction Manual
```

---

### Manual tree preview

Displays a textual directory tree:

```
Manual Map (Tree)
```

This representation mirrors the CLI output of the indexing module.

---

### Expand-all toggle

Users can expand all manual directories simultaneously.

```
Expand all
```

---

### Search interface

Manual titles and content can be searched interactively.

Search results appear as clickable manual entries.

---

### Manual section navigation

Manual files appear as buttons.

Example label:

```
📄 03_02_transcript_tables.md — Transcript Tables
```

When selected, the document content is rendered below the navigation interface.

---

# CLI Integration

Unlike other manual modules, `manual_viewer` **does not expose a CLI command**.

Instead it is designed for integration inside Streamlit applications.

Example usage:

```
from iridic.manual_viewer import render_manual_ui

render_manual_ui(repo_root=".")
```

This approach allows developers to embed manuals directly into project dashboards.

---

# Role Within IRIDIC

The `manual_viewer` module serves as the **interactive documentation interface** of the IRIDIC ecosystem.

While other modules support:

| Module | Role |
|------|------|
| `manual_index` | runtime indexing and search |
| `manual_outline` | outline file generation |
| `manual_chars` | documentation validation |
| `manual_pdf` | compiled manual creation |

`manual_viewer` provides **interactive manual browsing within applications**.

This enables IRIDIC-powered tools to ship with built-in instruction manuals.

---

# Design Principles

The viewer module follows several design goals.

**Embedded documentation**  
Manuals can be accessed directly within applications.

**Performance-aware indexing**  
Manual indexes are cached using Streamlit caching.

**Intuitive navigation**  
Hierarchical folders mirror the repository structure.

**Minimal configuration**  
Most projects can enable the viewer with a single function call.

---

# Summary

`manual_viewer` provides an interactive interface for exploring IRIDIC manuals inside Streamlit applications.

Core capabilities include:

- hierarchical manual navigation
- content search
- interactive document display
- integrated manual outline generation

This module completes the IRIDIC documentation ecosystem by making manuals **accessible within application interfaces rather than only through CLI tools or static documents**.
