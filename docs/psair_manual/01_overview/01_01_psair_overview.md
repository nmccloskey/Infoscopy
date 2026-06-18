# PSAIR Overview

## What PSAIR is

PSAIR, short for Python Scaffolding for Analysis Itineraries in Research, is a
backend utility package for research software repositories. It is intended to
provide reusable infrastructure for projects that need documentation workflows,
data handling, exploratory analysis, NLP utilities, and pipeline-oriented
scaffolding.

The package is currently in alpha. Its public surface is intentionally narrow:
the documentation and manual tooling is the most stable part of the package,
while the metadata and NLP modules now provide usable early utilities for
filename-derived metadata, file discovery, text preprocessing, and shared NLP
resource loading. ETL, EDA, and broader pipeline modules remain more
experimental.

PSAIR is used as shared scaffolding for downstream research systems such as
DIAAD, ALASTR, CLATR, and related repositories. Project-specific applications,
datasets, and domain workflows should live in those downstream projects rather
than in PSAIR itself.

## What is ready now

The currently supported portion of PSAIR is still centered on the documentation
toolchain. It supports repositories that maintain structured Markdown manuals
and want a lightweight way to inspect, validate, view, and export those manuals.

The ready documentation tools include:

- modular manual indexing
- generated manual trees
- documentation search
- outline generation
- character and formatting checks
- PDF-oriented manual export
- Streamlit manual viewing utilities

These tools are designed for filesystem-native manuals: each section is a
Markdown file, files are ordered with numeric prefixes, and generated artifacts
such as outlines and PDFs are derived from the source tree.

PSAIR also now includes alpha-ready metadata and NLP utilities. These are useful
for downstream projects that are already developing against PSAIR, but they
should be treated as evolving APIs rather than stable interfaces.

The metadata utilities include:

- configurable metadata field extraction from relative paths
- literal-value and regex-based metadata field definitions
- default filename-stem extraction when no metadata fields are configured
- recursive file discovery using metadata labels, a filename base, and extension
- optional duplicate filename handling across search directories

The NLP utilities include:

- text readers for `.txt`, `.docx`, `.cha`, `.csv`, and `.xlsx` inputs
- raw text scrubbing and cleaned text generation
- CHAT/CLAN-specific cleaned target and phonological text versions
- document-level and optional sentence-level preprocessing outputs
- semantic text based on spaCy lemmas for alphabetic, non-stopword tokens
- a singleton `NLPModel` helper for loading and reusing spaCy pipelines
- optional benepar and CMUdict loading when the relevant extras are installed

## What is still experimental

The broader `psair` namespace includes early modules for:

- ETL
- exploratory data analysis
- pipeline management

These modules are included to preserve the emerging package architecture, but
they should not yet be treated as stable public APIs. Their module paths,
dependencies, function signatures, and behavior may change across alpha
releases.

For this release line, downstream projects should depend only on the manual and
documentation tooling for stable workflows. The metadata and NLP modules can be
used by alpha adopters who are comfortable tracking changes.

## Installation

For the supported documentation tooling, install PSAIR with the `docs` extra:

```bash
pip install "psair[docs]"
```

For the Streamlit manual viewer and browser-oriented export helpers, install the
`view` extra:

```bash
pip install "psair[view]"
```

For local development against the full experimental package layout, install the
`full` extra:

```bash
pip install "psair[full]"
```

The base package can also be installed without extras:

```bash
pip install psair
```

The base install is intentionally small. It is appropriate when a downstream
project only needs the package namespace or dependency-light functionality.

## Command line entry point

After installation, PSAIR exposes the `psair` command:

```bash
psair --help
```

The CLI currently focuses on manual and documentation workflows:

```bash
psair tree docs/manual
psair index docs/manual --show-files
psair search "topic" docs/manual
psair outline docs/manual --title "Instruction Manual" --version "0.0.3a2"
psair chars docs/manual --check-trailing --check-line-endings
psair pdf docs/manual --non-interactive --force
```

PDF compilation uses Pandoc and a LaTeX PDF engine such as XeLaTeX. These are
external executables, not Python dependencies, and must be installed separately
and available on `PATH`.

## Manual workflow

A typical PSAIR documentation workflow is:

```text
Write modular Markdown files
Run character and formatting checks
Generate or refresh the manual outline
Build the PDF when a distributable manual is needed
Use the Streamlit viewer when interactive browsing is useful
```

For example:

```bash
psair chars docs/manual --check-trailing --check-line-endings
psair outline docs/manual --title "PSAIR Instruction Manual" --version "0.0.3a2"
psair pdf docs/manual --yaml docs/manual/manual_pdf.yaml --non-interactive --force
```

## Stability expectations

PSAIR is distributed as alpha software. Early releases are intended to make the
tooling installable, testable, and reusable while the design continues to
settle.

Users should expect:

- documentation tooling to be the supported interface
- metadata and NLP utilities to be usable but still alpha
- optional extras to change as the package is refined
- experimental modules to move or be reorganized
- dependency ranges to be adjusted between alpha releases
- release notes and manual updates to clarify what is safe to rely on

The package should be useful now for documentation work, but it is not yet a
polished end-user application or a fully stable framework.

## Intended audience

PSAIR is primarily intended for developers, research programmers, and project
maintainers who want reusable infrastructure for analysis-oriented repositories.
It is most useful in projects that need reproducible manuals, lightweight
documentation validation, and a shared place for early backend scaffolding.
