
# manual_index Module

## Overview

The `manual_index` module provides the **core indexing and search infrastructure** for IRIDIC manuals.  
It scans a manual directory, builds a structured representation of its contents, and enables:

- hierarchical manual navigation
- searchable manual content
- generation of clean directory trees for documentation or CLI viewing

Within the IRIDIC ecosystem, this module functions as the **foundation layer** for manual inspection tools.  
Higher-level utilities (CLI commands, Streamlit manual viewers, PDF compilers, etc.) rely on the index it builds.

The module operates on Markdown manuals organized as a directory tree and extracts both **file metadata and content** for downstream operations.

---

# Data Model

## ManualFile

The central data structure representing a manual file.

```
@dataclass(frozen=True)
class ManualFile:
    rel_path: Path
    abs_path: Path
    title: str
    text: str
```

Fields:

| Field | Description |
|------|-------------|
| `rel_path` | File path relative to the manual root |
| `abs_path` | Absolute filesystem path |
| `title` | Extracted Markdown title (first `#` heading) |
| `text` | Full file text content |

This structure allows the manual system to simultaneously support:

- filesystem operations
- search functionality
- display interfaces

---

# Core Functions

## build_manual_index

Builds a structured representation of the manual.

```
build_manual_index(manual_dir)
```

### Purpose

Scans the manual directory recursively and constructs:

1. A **hierarchical tree representation**
2. A **flat index of files**

### Returns

```
(tree, flat)
```

| Object | Description |
|------|-------------|
| `tree` | Nested dictionary representing the manual directory structure |
| `flat` | Dictionary mapping relative file paths to `ManualFile` objects |

### Behavior

- Recursively scans for Markdown files (`*.md`)
- Automatically extracts titles from Markdown headings
- Ignores the file `00_outline.md`
- Sorts files numerically using prefix conventions (e.g., `01_intro.md`, `02_setup.md`)

Example:

```
manual/
    01_intro.md
    02_installation.md
    03_workflow/
        03_01_overview.md
```

Produces a structured tree used by the CLI viewer and manual UI tools.

---

## render_generated_tree_text

Renders a manual directory tree as formatted text.

```
render_generated_tree_text(tree)
```

### Purpose

Converts the hierarchical manual tree into a human‑readable CLI display.

Example output:

```
Manual Map (Tree)
├── 01_intro.md
├── 02_installation.md
└── 03_workflow/
    ├── 03_01_overview.md
    └── 03_02_examples.md
```

### Usage

Primarily used by the CLI command:

```
iridic tree
```

This command prints a clean tree view of the manual.

---

## search_manual

Searches manual titles and content.

```
search_manual(flat, query, limit=25)
```

### Parameters

| Parameter | Description |
|----------|-------------|
| `flat` | Flat manual index from `build_manual_index` |
| `query` | Search string |
| `limit` | Maximum results returned |

### Search Behavior

The search algorithm:

1. Normalizes the query to lowercase
2. Scores matches based on:
   - title matches (higher weight)
   - text occurrences
3. Returns ranked results

Scoring rules:

- Title match → +5 points
- Each text occurrence → +1 point (capped)

Example output:

```
  7  03_workflow/03_02_examples.md  --  Example Workflows
  5  01_intro.md  --  Introduction
```

---

# Supporting Utilities

## numeric_sort_key

Handles numeric file prefixes such as:

```
01_intro.md
02_installation.md
10_appendix.md
```

Ensures files are sorted logically rather than alphabetically.

Without this logic:

```
1_intro.md
10_appendix.md
2_setup.md
```

With numeric sorting:

```
1_intro.md
2_setup.md
10_appendix.md
```

---

## extract_md_title

Extracts the first Markdown heading:

```
# Section Title
```

If no heading is found, the filename is used as a fallback.

---

## read_text_safely

Reads Markdown text using UTF‑8 encoding.

If decoding fails, it replaces invalid characters rather than crashing.

---

# CLI Integration

The module powers several IRIDIC CLI commands.

The CLI layer calls these functions through `cli.py`.

### Manual Tree

```
iridic tree
```

Displays the generated manual structure.

Example:

```
iridic tree manual
```

Internally this executes:

```
tree, flat = build_manual_index(manual_dir)
print(render_generated_tree_text(tree))
```

---

### Manual Search

```
iridic search <query>
```

Searches titles and manual content.

Example:

```
iridic search reliability
```

Internally:

```
_, flat = build_manual_index(manual_dir)
search_manual(flat, query)
```

---

### Manual Index Summary

```
iridic index
```

Displays basic indexing statistics.

Example output:

```
manual_dir: /repo/manual
files_indexed: 28
top_level_nodes: 7
```

Optional flag:

```
iridic index --show-files
```

Prints the full list of indexed files.

---

# Role Within IRIDIC

The `manual_index` module serves as the **documentation discovery engine** for the IRIDIC system.

It enables:

- CLI navigation of manuals
- interactive manual viewers
- document search
- automated manual compilation pipelines

Other modules build on top of this functionality:

| Module | Role |
|------|------|
| `manual_outline` | Generates manual outlines |
| `manual_pdf` | Compiles manuals into PDFs |
| `manual_chars` | Validates documentation formatting |
| `manual_viewer` | Interactive manual browser (Streamlit) |

The indexing system ensures these tools operate on a **consistent representation of manual content**.

---

# Design Principles

The module is intentionally designed to be:

**Filesystem‑native**  
Manuals remain simple Markdown directories.

**Non‑destructive**  
Indexing never modifies files.

**Lightweight**  
No database or cache required.

**Reusable**  
The index can support CLI tools, web apps, and build pipelines.

---

# Summary

`manual_index` provides the infrastructure required for navigating and searching IRIDIC manuals.

Core capabilities:

- recursive Markdown discovery
- structured manual indexing
- title extraction
- CLI tree rendering
- ranked manual search

These features enable IRIDIC manuals to function as **structured, navigable documentation systems rather than static file collections**.
