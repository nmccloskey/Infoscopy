# PSAIR Overview

## What PSAIR is

PSAIR, short for Python Support for Aphasiology Itineraries in Research, is a
backend utility package for discourse analysis software repositories. It is intended to provide reusable infrastructure for projects that need documentation support, file name metadata parsing, some lightweight NLP utilities, and example input/output file generation.

The package is currently in alpha. Its public surface is intentionally narrow:
the custom logging, manual tooling, metadata, NLP, and example I/O utilities are used by DIAAD and by extension its lab-specific wrapper RASCAL.

Project-specific applications, datasets, and domain workflows live in those downstream projects rather than in PSAIR itself.

## PSAIR Utilities

The documentation toolchain supports repositories that maintain structured Markdown manuals and want a lightweight way to inspect, validate, view, and export those manuals.

These include:

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

PSAIR also includes lightweight metadata and NLP utilities useful
for downstream projects that are already developing against PSAIR.

The metadata utilities include:

- configurable metadata field extraction from relative paths
- literal-value and regex-based metadata field definitions
- default filename-stem extraction when no metadata fields are configured
- recursive file discovery using metadata labels, a filename base, and extension
- optional duplicate filename handling across search directories

The NLP utilities include:

- a singleton `NLPModel` helper for loading and reusing spaCy pipelines
- optional benepar and CMUdict loading when the relevant extras are installed

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

## Intended audience

PSAIR is primarily intended for developers, research programmers, and project
maintainers who want reusable infrastructure for analysis-oriented repositories.
It is most useful in discourse analysis projects that need reproducible manuals, lightweight documentation validation, and a shared place for early backend scaffolding.
