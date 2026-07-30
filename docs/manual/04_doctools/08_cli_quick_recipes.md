# Common CLI Workflows (Quick Start)

This section highlights **three practical workflows** for using the IRIDIC manual toolchain.
These examples show progressively more complete uses of the system.

After the examples, the section expands into **detailed task recipes**.

---

# Workflow 1 — Minimal

The simplest possible manual build.

```
iridic pdf manual
```

What happens:

1. The manual directory is scanned.
2. An outline is generated if needed.
3. character/content checks run.
4. the manual is compiled into a PDF.

This is the **fastest way to build a manual** when default settings are acceptable.

---

# Workflow 2 — Recommended (Typical Use)

A slightly more explicit and reproducible workflow.

```
iridic chars manual --check-trailing
iridic outline manual
iridic pdf manual --yaml manual/manual_pdf.yaml
```

What this does:

1. **Validate documentation formatting**
2. **Ensure the navigation outline exists**
3. **Compile the PDF using a Pandoc YAML configuration**

This is the **recommended IRIDIC workflow** because the YAML file ensures consistent document styling.

---

# Workflow 3 — Full Explicit Pipeline

A more verbose workflow that demonstrates every major module.

```
iridic tree manual
iridic search "installation"
iridic index manual

iridic chars manual --check-trailing --report-nonascii

iridic outline manual   --title "IRIDIC Instruction Manual"   --version 0.1.0

iridic pdf manual   --yaml manual/manual_pdf.yaml   --margin 1in   --toc-depth 3
```

This workflow:

1. explores the manual structure
2. searches documentation
3. validates documentation hygiene
4. regenerates the navigation outline
5. compiles the final PDF

This is helpful during **manual development and debugging**.

---

# Manual Pipeline Architecture

The IRIDIC manual system follows a modular pipeline.

```
Markdown manual files
        │
        ▼
manual_index  (indexing and search)
        │
        ▼
manual_outline (outline generation)
        │
        ▼
manual_chars   (documentation validation)
        │
        ▼
manual_pdf     (Pandoc compilation)
        │
        ▼
Compiled Manual PDF
```

Optional:

```
manual_viewer → interactive manual inside Streamlit applications
```

Each stage is **independent and composable**, which allows developers to run only the steps they need.

---

# Inspecting a Manual

## View the manual tree

```
iridic tree
```

Displays the generated directory tree of the manual.

Example:

```
IRIDIC/
├── 01_introduction.md
├── 02_installation.md
├── 03_workflow/
│   ├── 03_01_overview.md
│   └── 03_02_cli_commands.md
```

---

## Search the manual

```
iridic search "installation"
```

Searches titles and content across manual files.

Limit the number of results:

```
iridic search "database" --limit 10
```

---

## Inspect the indexed manual

```
iridic index
```

Shows summary statistics such as:

- number of indexed files
- number of top‑level sections

Show the list of indexed files:

```
iridic index --show-files
```

---

# Preparing a Manual

## Check documentation characters

```
iridic chars manual
```

Runs character and formatting validation across documentation files.

---

## Detect trailing whitespace

```
iridic chars manual --check-trailing
```

---

## Remove trailing whitespace

```
iridic chars manual --strip-trailing
```

---

## Detect Windows line endings

```
iridic chars manual --check-line-endings
```

---

## Normalize line endings

Convert to LF:

```
iridic chars manual --fix-line-endings lf
```

Convert to CRLF:

```
iridic chars manual --fix-line-endings crlf
```

---

## Detect non‑ASCII characters

```
iridic chars manual --report-nonascii
```

Treat non‑ASCII characters as errors:

```
iridic chars manual --fail-on-nonascii
```

---

# Generating Navigation

## Generate the manual outline

```
iridic outline manual
```

Creates:

```
manual/00_outline.md
```

---

## Specify manual title and version

```
iridic outline manual   --title "IRIDIC Instruction Manual"   --version 0.1.0
```

---

## Generate the outline only if missing

```
iridic outline manual --if-missing-only
```

---

# Building the Manual PDF

## Compile the manual

```
iridic pdf manual
```

---

## Compile using a YAML configuration

```
iridic pdf manual --yaml manual/manual_pdf.yaml
```

This is the **recommended workflow**.

---

## Specify output location

```
iridic pdf manual   --yaml manual/manual_pdf.yaml   --output dist/manual.pdf
```

---

## Adjust page margins

```
iridic pdf manual --margin 0.8in
```

---

## Disable the table of contents

```
iridic pdf manual --no-toc
```

---

## Change TOC depth

```
iridic pdf manual --toc-depth 2
```

---

## Include the outline in the PDF

```
iridic pdf manual --include-outline
```

---

## Pass additional arguments to Pandoc

```
iridic pdf manual   --yaml manual/manual_pdf.yaml   --extra-pandoc-arg "--citeproc"
```

---


# Controlling Preflight Checks

Skip outline generation:

```
iridic pdf manual --skip-outline
```

Force outline rebuild:

```
iridic pdf manual --rebuild-outline
```

Skip character validation:

```
iridic pdf manual --skip-chars
```

Run compilation non‑interactively:

```
iridic pdf manual --non-interactive
```

Proceed even if issues are detected:

```
iridic pdf manual --force
```

---

# Summary

The IRIDIC CLI supports workflows ranging from **single‑command builds** to **fully explicit manual pipelines**.

Most users will prefer:

```
iridic pdf manual
```

or the slightly more explicit:

```
iridic chars manual --check-trailing
iridic outline manual
iridic pdf manual --yaml manual/manual_pdf.yaml
```

For full command documentation, see the **CLI Command Reference** section.
