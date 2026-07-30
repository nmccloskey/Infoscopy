# `manual_pdf.yaml` Configuration

## Overview

The `manual_pdf.yaml` file is the recommended **Pandoc metadata configuration** for IRIDIC manual compilation.

Rather than hard-coding document presentation into the Python build logic, IRIDIC keeps most PDF formatting concerns in a dedicated YAML file. This separation keeps the system cleaner:

- **Markdown files** contain manual content
- **Python modules** orchestrate indexing, validation, and compilation
- **YAML configuration** controls document presentation and Pandoc metadata

This design makes manual builds more reproducible, easier to maintain, and easier to adapt across repositories.

---

# Purpose

The YAML file provides a centralized location for PDF-related settings such as:

- document title and subtitle
- author and version metadata
- page size and margins
- font size and line spacing
- title page behavior
- table of contents settings
- section numbering
- LaTeX header customizations
- hyperlink styling
- syntax highlighting style

In practice, this file serves as the **recommended styling and metadata control layer** for `manual_pdf`.

---

# Role Within the Manual Pipeline

The YAML file is consumed during PDF compilation, typically through the CLI command:

```bash
iridic pdf manual --yaml manual/manual_pdf.yaml
```

or through Python code passed to `build_manual_pdf()`.

At compile time, `manual_pdf.py` passes the YAML to Pandoc as a metadata file, allowing Pandoc to apply the requested formatting and layout decisions. fileciteturn5file0

This means the YAML file is not itself part of the manual text. It is a **build configuration artifact**.

---

# Recommended Placement

The recommended convention is to keep the file inside the manual directory:

```text
manual/
    00_outline.md
    01_introduction.md
    02_installation.md
    ...
    manual_pdf.yaml
```

This keeps the manual source, derived artifacts, and PDF configuration in one predictable location.

---

# Example Configuration

A representative IRIDIC configuration looks like this:

```yaml
title: "IRIDIC Instruction Manual"
subtitle: "Idiosyncratic Repository of Initialization & Development Itineraries for Codebases"
author: "Nick McCloskey"
date: "Version 0.1.0"

geometry: margin=3cm
fontsize: 11pt
linestretch: 1.15
papersize: letter

titlepage: true
titlepage-color: "FFFFFF"
titlepage-text-color: "000000"
titlepage-rule-height: 1

toc: true
toc-depth: 3
numbersections: true

header-includes:
  - \usepackage{etoolbox}
  - \apptocmd{\tableofcontents}{\clearpage}{}{}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyfoot[C]{\thepage}
  - \fancyhead[L]{IRIDIC Manual}
  - \fancyhead[R]{Version 0.1.0}
  - \usepackage{fvextra}
  - \fvset{breaklines=true,breakanywhere=true}

colorlinks: true
linkcolor: blue
urlcolor: blue

highlight-style: tango
```

This is the configuration currently associated with the IRIDIC manual build setup. fileciteturn5file0

---

# Field-by-Field Explanation

## Document metadata

```yaml
title: "IRIDIC Instruction Manual"
subtitle: "Idiosyncratic Repository of Initialization & Development Itineraries for Codebases"
author: "Nick McCloskey"
date: "Version 0.1.0"
```

These fields control the document metadata shown on the title page and in the compiled PDF.

### Notes

- `title` should be the formal name of the manual
- `subtitle` is useful for expanding acronyms or clarifying scope
- `author` can be an individual, lab, or organization
- `date` is often used as a **version label** rather than a literal date in software manuals

For IRIDIC, using the version string in the `date` field is perfectly reasonable because the manual functions as versioned documentation rather than a one-time publication.

---

## Page geometry and typography

```yaml
geometry: margin=3cm
fontsize: 11pt
linestretch: 1.15
papersize: letter
```

These fields control the basic physical layout of the PDF.

### `geometry`
Controls page margins through LaTeX geometry settings.

Example:

```yaml
geometry: margin=3cm
```

This can be overridden from the CLI using:

```bash
iridic pdf manual --margin 1in
```

For IRIDIC manuals, a narrower margin such as `1in` is often preferable to `3cm`, especially when the manual contains code blocks or wide headings.

### `fontsize`
Sets the main body font size.

Typical values:

- `10pt`
- `11pt`
- `12pt`

`11pt` is a good default for instruction manuals because it is readable without feeling oversized.

### `linestretch`
Controls line spacing.

A value like `1.15` gives slightly more breathing room than single spacing without looking too loose.

### `papersize`
Defines the page size, for example:

- `letter`
- `a4`

For your workflow on a U.S. Windows system, `letter` is the natural default.

---

## Title page settings

```yaml
titlepage: true
titlepage-color: "FFFFFF"
titlepage-text-color: "000000"
titlepage-rule-height: 1
```

These fields control whether a title page is created and how it looks.

### Notes

- `titlepage: true` enables a dedicated title page
- `titlepage-color` sets the page background color
- `titlepage-text-color` sets title-page text color
- `titlepage-rule-height` adjusts the decorative rule thickness

For IRIDIC, the current configuration keeps the title page minimal and clean. fileciteturn5file0

---

## Table of contents and section numbering

```yaml
toc: true
toc-depth: 3
numbersections: true
```

These settings determine whether Pandoc generates a table of contents and whether sections are numbered.

### `toc`
Enables an automatically generated table of contents.

### `toc-depth`
Controls how many heading levels appear in the table of contents.

A depth of `3` is usually a good compromise for manuals:
- major sections appear
- subsections appear
- the TOC does not become too crowded

### `numbersections`
Tells Pandoc to number section headings in the compiled PDF.

This can coexist with the IRIDIC build logic that strips numeric filename prefixes from headings before compilation. In other words:

- filenames preserve deterministic ordering
- compiled headings can still receive clean automatic numbering

That combination is one of the cleaner design choices in this manual system.

---

## Header customizations

```yaml
header-includes:
  - \usepackage{etoolbox}
  - \apptocmd{\tableofcontents}{\clearpage}{}{}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyfoot[C]{\thepage}
  - \fancyhead[L]{IRIDIC Manual}
  - \fancyhead[R]{Version 0.1.0}
  - \usepackage{fvextra}
  - \fvset{breaklines=true,breakanywhere=true}
```

This block injects raw LaTeX into the Pandoc build.

It is the most powerful section of the YAML file, and also the one that should be edited most cautiously.

### `etoolbox` + `pptocmd`
This appends a page break after the table of contents:

```latex
pptocmd{	ableofcontents}{\clearpage}{}{}
```

That is useful because it ensures the TOC does not run directly into the first manual section.

### `fancyhdr`
This package customizes page headers and footers.

Current behavior:

- centered footer page number
- left header: `IRIDIC Manual`
- right header: `Version 0.1.0`

This is a strong choice for versioned technical manuals because it keeps the document identity visible on every page.

### `fvextra`
This improves code block rendering.

Current setting:

```latex
vset{breaklines=true,breakanywhere=true}
```

This is especially useful for manuals containing:
- command-line examples
- long file paths
- YAML snippets
- Python code

Without it, long code lines can overflow the page.

---

## Link styling

```yaml
colorlinks: true
linkcolor: blue
urlcolor: blue
```

These fields control hyperlink appearance in the compiled PDF.

### Notes

- `colorlinks: true` renders links as colored text instead of boxes
- `linkcolor` affects internal links such as TOC links
- `urlcolor` affects external URLs

Blue is a conventional and readable default.

---

## Syntax highlighting

```yaml
highlight-style: tango
```

This controls Pandoc’s syntax highlighting theme for code blocks.

`Tango` is a solid default because it is readable and unobtrusive.

If a repository later develops a stronger visual identity, this field can be changed without altering the manual content itself.

---

# Relationship to CLI Overrides

One important design feature is that CLI arguments can override parts of the YAML configuration.

For example, even if the YAML says:

```yaml
geometry: margin=3cm
toc: true
toc-depth: 3
```

the CLI may still modify these behaviors with options such as:

```bash
iridic pdf manual --margin 1in --no-toc --toc-depth 2
```

This gives you a useful split:

- **YAML** defines the recommended baseline
- **CLI flags** provide situational overrides

That arrangement is particularly good for IRIDIC, where you may want stable defaults but still experiment with margin widths or TOC inclusion during development.

---

# Recommended Best Practices

## Keep the YAML under version control

The YAML file should generally be committed alongside the manual so that document styling remains reproducible across machines and versions.

## Treat the YAML as the styling SSOT

Most Pandoc presentation settings should live here rather than being scattered across Python defaults or ad hoc CLI flags.

## Use CLI overrides sparingly

Overrides are useful, but the YAML should represent the preferred manual build configuration.

## Prefer readable PDF defaults

For technical manuals, prioritize:
- modest margins
- clear title pages
- page headers with version information
- reliable code wrapping
- sensible TOC depth

## Edit `header-includes` cautiously

This field is powerful but can introduce LaTeX-specific build fragility if it becomes too elaborate.

---

# Recommended IRIDIC Direction

For the IRIDIC manual specifically, a slightly updated baseline would likely be:

- keep the YAML-based configuration model
- reduce the effective margin from `3cm` toward `1in`
- keep the TOC enabled by default
- keep code-line wrapping enabled
- keep header/footer version labeling
- use the YAML as the primary place for Pandoc styling decisions

That aligns well with the broader IRIDIC philosophy of making workflows explicit, modular, and reproducible.

---

# Summary

`manual_pdf.yaml` is the recommended configuration file for IRIDIC manual PDF builds.

It provides a centralized, version-controlled place to define:

- metadata
- layout
- typography
- TOC behavior
- LaTeX customizations
- link appearance
- code highlighting

Used well, it keeps the manual pipeline cleaner by separating **content**, **orchestration**, and **presentation**. fileciteturn5file0
