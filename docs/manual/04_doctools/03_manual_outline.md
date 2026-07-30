
# manual_outline Module

## Overview

The `manual_outline` module generates a **structured outline document for IRIDIC manuals**.

Its primary responsibility is producing a derived Markdown artifact — typically named:

```
00_outline.md
```

This file provides two complementary views of the manual:

1. **Manual Map (Tree)** – a filesystem-style directory tree
2. **Outline (Links)** – a grouped clickable index of sections

The outline functions as both:

- a **navigation aid for manual readers**
- a **build artifact used by documentation workflows**

Unlike the `manual_index` module (which provides runtime indexing), `manual_outline` produces a **persistent manual navigation file** that can be included in repositories and compiled into PDF documentation.

---

# Data Model

## Entry

Each Markdown document in the manual is represented by an `Entry` object.

```
@dataclass(frozen=True)
class Entry:
    rel_path: Path
    title: Optional[str]
```

Fields:

| Field | Description |
|------|-------------|
| `rel_path` | File path relative to the manual root |
| `title` | Extracted Markdown heading (if available) |

This lightweight structure is sufficient for generating both tree and link-based outlines.

---

# Core Functions

## build_manual_outline

Creates and writes the manual outline file.

```
build_manual_outline(manual_dir)
```

### Purpose

Scans a manual directory, generates the outline Markdown, and writes it to disk.

### Default Output

```
manual/00_outline.md
```

### Parameters

| Parameter | Description |
|----------|-------------|
| `manual_dir` | Root directory containing manual files |
| `output_path` | Optional custom outline path |
| `manual_title` | Manual title for the outline header |
| `manual_version` | Version string included in metadata |
| `include_exts` | File extensions to include |
| `max_depth` | Optional maximum directory depth for the tree view |

### Behavior

The function:

1. Collects Markdown entries from the manual
2. Builds a hierarchical directory tree
3. Generates a Markdown outline
4. Writes the file to disk

Example header in the generated file:

```
# Instruction Manual

Version: 0.0.0
Generated: 2026-03-09
```

---

## ensure_manual_outline

Ensures that an outline exists.

```
ensure_manual_outline(manual_dir)
```

### Purpose

Creates an outline only when necessary.

### Behavior

If the outline file already exists:

```
00_outline.md
```

then the function returns without rewriting the file.

This avoids unnecessary rebuilds during workflows.

Optional behavior:

```
--rebuild-outline
```

forces regeneration.

---

## run_manual_outline

Convenience wrapper used by automation workflows.

```
run_manual_outline(manual_dir)
```

This simply forwards arguments to `ensure_manual_outline`.

---

# Supporting Utilities

## iter_markdown_entries

Collects Markdown entries under the manual directory.

Key behaviors:

- Recursively scans directories
- Skips hidden folders
- Skips `__pycache__`
- Extracts titles from Markdown files
- Applies numeric ordering

The result is a list of `Entry` objects representing the manual.

---

## extract_title

Extracts a document title from Markdown.

Supported heading styles:

### ATX headings

```
# Section Title
```

### Setext headings

```
Section Title
=============
```

If no title is found, the outline displays only the filename.

---

## numeric_key

Ensures logical ordering for numerically prefixed files such as:

```
01_intro.md
02_installation.md
03_workflow/
03_01_overview.md
```

Without numeric sorting, files like `10_appendix.md` would appear incorrectly before `2_setup.md`.

---

## build_tree

Constructs a nested dictionary representing the manual directory hierarchy.

Directories become nested dictionaries, while files remain `Entry` objects.

Example structure:

```
{
  "03_workflow": {
       "03_01_overview.md": Entry(...)
  }
}
```

---

## render_tree

Converts the nested tree structure into a formatted directory tree.

Example output:

```
├── 01_intro.md
├── 02_installation.md
└── 03_workflow/
    ├── 03_01_overview.md
    └── 03_02_examples.md
```

Optional behaviors include:

- limiting tree depth
- rendering Markdown links
- appending extracted titles

---

## render_grouped_outline

Produces a grouped list of manual files organized by directory.

Example:

```
### Manual root

- [01_intro.md — Introduction](01_intro.md)
- [02_installation.md — Installation](02_installation.md)

### 03_workflow/

- [03_01_overview.md — Overview](03_workflow/03_01_overview.md)
```

This format provides a clickable navigation index.

---

## render_outline_markdown

Generates the full Markdown content for the outline file.

Sections included:

1. Manual header and metadata
2. Tree representation of the manual
3. Grouped outline with links
4. Notes about maintaining the outline

Example sections:

```
## Manual Map (Tree)
## Outline (Links)
## Notes
```

---

# CLI Integration

The module is accessed through the IRIDIC CLI command:

```
iridic outline
```

Example usage:

```
iridic outline manual
```

Optional arguments:

```
iridic outline manual -o custom_outline.md
iridic outline manual --title "IRIDIC Manual"
iridic outline manual --version 0.2.0
iridic outline manual --max-depth 2
```

Internally the CLI invokes:

```
build_manual_outline()
```

or

```
ensure_manual_outline()
```

depending on the command flags.

This interface is defined in the CLI argument configuration system.

---

# Role Within IRIDIC

The `manual_outline` module produces a **derived manual artifact** used throughout the IRIDIC documentation ecosystem.

It supports:

| Workflow | Role |
|--------|------|
| Manual navigation | Provides an overview of all manual sections |
| Repository browsing | Allows quick navigation of documentation |
| PDF compilation | Optional inclusion in compiled manuals |
| Documentation maintenance | Ensures predictable ordering and visibility of sections |

The outline file also acts as a **quality check**, revealing missing numeric prefixes or misplaced documentation files.

---

# Design Principles

The module follows several design goals.

**Derived documentation artifacts**  
The outline is automatically generated rather than manually maintained.

**Filesystem-native manuals**  
Manuals remain simple Markdown directory structures.

**Stable ordering conventions**  
Numeric prefixes ensure deterministic ordering of sections.

**Readable navigation tools**  
The tree and grouped outline provide two complementary navigation views.

---

# Summary

`manual_outline` generates the canonical navigation file for IRIDIC manuals.

Core capabilities include:

- recursive Markdown discovery
- title extraction
- numeric-aware ordering
- directory tree rendering
- grouped link outlines
- automated outline file generation

This module ensures that IRIDIC manuals remain **organized, navigable, and reproducible as documentation grows**.
