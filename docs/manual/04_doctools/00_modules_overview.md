
# Manual Modules Overview

## Purpose

The IRIDIC **manual modules** provide a small, modular toolkit for managing, validating, and distributing project documentation written as structured Markdown manuals.

Rather than maintaining large monolithic documents, IRIDIC manuals are designed as **filesystem‑native documentation trees**. Each manual section is an individual Markdown file organized in a predictable directory structure.

The manual modules provide tools that allow these modular documents to function as a **coherent documentation system** that supports:

- interactive browsing inside applications
- command‑line exploration and search
- automated validation of documentation hygiene
- deterministic outline generation
- compilation of full manuals into distributable PDFs

Together, these modules transform a simple directory of Markdown files into a **reproducible documentation pipeline**.

---

# Manual Architecture

IRIDIC manuals follow a **source–artifact separation** pattern: the manual's Markdown
source lives in `docs/manual/`, while compiled artifacts (such as PDFs) live in
`docs/`. This keeps source files clean and prevents generated outputs from mixing
with author-maintained content.

A typical structure looks like:

```
docs/
├── manual/
│   ├── 00_outline.md
│   ├── 01_introduction.md
│   ├── 02_installation.md
│   ├── 03_workflow/
│   │   ├── 03_01_overview.md
│   │   └── 03_02_transcript_tables.md
│   └── manual_pdf.yaml
├── lineage.md
└── iridic_manual.pdf   # generated (gitignored)
```

## Design Principles

### Modular documentation
Each section is written as an independent Markdown file.  
This allows sections to be edited, reordered, or expanded without modifying a
monolithic document.

### Deterministic ordering
Numeric prefixes (`01_`, `02_`, `03_01_`, etc.) define the manual’s logical order.
This makes the structure explicit and keeps rendering deterministic regardless of
filesystem ordering.

### Filesystem transparency
The manual is readable and navigable directly from the repository.  
Anyone browsing the repo can follow the manual structure without needing the
compiled PDF.

### Derived artifacts
Certain files are generated automatically rather than authored manually.

Typical derived artifacts include:

- `00_outline.md` – an auto-generated structural outline of the manual.
- `docs/<repo>_manual.pdf` – the compiled manual produced via Pandoc.

Generated artifacts should **not normally be committed to the repository**.

### Local configuration
Pandoc build settings live alongside the manual source in:

```
docs/manual/manual_pdf.yaml
```

This YAML file defines document metadata and Pandoc configuration such as:

- title and subtitle
- page geometry
- fonts and LaTeX settings
- table of contents configuration

Placing the config in the manual directory ensures that build settings travel with
the manual itself.

## Recommended `.gitignore` Entries

Compiled manuals and temporary build artifacts should usually be ignored.  
Typical entries include:

```
# Generated manuals
docs/*_manual.pdf
docs/manual.pdf

# Optional build directories
docs/build/
```

This keeps the repository focused on **source documentation**, while allowing local
PDF builds for distribution or review.

---

# Manual Module Ecosystem

The IRIDIC manual system is composed of several modules that operate at different stages of the documentation lifecycle.

| Module | Role |
|------|------|
| `manual_index` | Index manual files and enable search |
| `manual_outline` | Generate navigation outlines |
| `manual_chars` | Validate documentation formatting |
| `manual_pdf` | Compile manuals into PDFs |
| `manual_viewer` | Render manuals interactively in Streamlit |

These modules can be used independently or combined into automated workflows.

---

# Typical Documentation Workflow

The modules are usually used in the following order:

```
Write manual sections (Markdown)
        ↓
manual_chars validation
        ↓
manual_outline generation
        ↓
manual_pdf compilation
        ↓
manual_viewer browsing (optional)
```

### 1. Write manual sections

Documentation is written as Markdown files organized within a `manual/` directory.

### 2. Validate documentation

```
iridic chars manual
```

This stage detects issues such as:

- trailing whitespace
- inconsistent line endings
- non‑ASCII characters

Optional automatic fixes may be applied.

### 3. Generate outline

```
iridic outline manual
```

This generates the file:

```
00_outline.md
```

which contains a navigable overview of the manual.

### 4. Compile PDF

```
iridic pdf manual
```

This produces a single compiled manual suitable for distribution.

### 5. Interactive viewing (optional)

The Streamlit viewer can render the manual directly inside applications.

---

# CLI Interface

The IRIDIC manual toolkit exposes several commands:

```
iridic tree
iridic search
iridic index
iridic outline
iridic chars
iridic pdf
```

These commands allow users to explore, validate, and compile manuals entirely from the command line.

---

# Streamlit Integration

The manual viewer module enables manuals to be embedded directly inside Streamlit tools.

Example usage:

```
from iridic.manual_viewer import render_manual_ui

render_manual_ui(repo_root=".")
```

This creates an interactive documentation browser with:

- folder navigation
- search functionality
- inline document rendering

This feature allows IRIDIC tools to ship with **built‑in interactive documentation**.

---

# Recommended Manual Configuration (YAML)

When compiling manuals into PDFs, IRIDIC strongly recommends maintaining a **Pandoc metadata YAML file** alongside the manual.

Example:

```
manual_pdf.yaml
```

This configuration file controls aspects such as:

- title and author metadata
- page geometry
- fonts
- line spacing
- syntax highlighting
- PDF layout settings

Using a YAML configuration provides several advantages:

**Separation of concerns**  
Manual styling is separated from manual content.

**Reproducible builds**  
Manual formatting remains consistent across environments.

**Override flexibility**  
CLI arguments can override YAML settings when needed.

---

# Documentation Philosophy

The IRIDIC manual system is designed around several principles.

### Filesystem‑native documentation

Documentation should remain simple Markdown files that can be edited with standard tools.

### Derived navigation artifacts

Navigation files such as outlines should be generated automatically rather than maintained manually.

### Reproducible documentation builds

Compiled manuals should be deterministic and reproducible.

### Embedded documentation

Applications should be able to ship with integrated manuals.

---

# Summary

The IRIDIC manual modules provide a lightweight system for managing modular documentation.

Key capabilities include:

- indexing manual files
- searching documentation
- generating outlines
- validating documentation formatting
- compiling manuals into PDFs
- embedding manuals inside applications

Together these modules enable IRIDIC projects to maintain **clean, navigable, and reproducible instruction manuals while preserving a simple Markdown‑based documentation workflow**.
