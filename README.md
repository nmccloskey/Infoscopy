# PSAIR - Python Scaffolding for Analysis Itineraries in Research


![PyPI version](https://img.shields.io/pypi/v/psair)
![Python](https://img.shields.io/pypi/pyversions/psair)
![License](https://img.shields.io/pypi/l/psair)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://psair-dev.streamlit.app/)

**Status:** Alpha, active development  
**Current supported components:** documentation/manual tooling, plus alpha metadata and NLP utilities  
**Broader scope:** experimental infrastructure for ETL, EDA, NLP, and pipeline development

PSAIR is a backend utility package for research software repositories. Its long-term goal is to provide reusable scaffolding for documentation workflows, data handling, exploratory analysis, and pipeline-oriented tooling across projects such as DIAAD & ALASTR.

At present, **the documentation toolchain is the most stable component and is ready for general use**. PSAIR also includes early, usable metadata and NLP utilities for filename metadata extraction, file discovery, text preprocessing, and shared spaCy model loading. Other package areas are included as part of the package's evolving architecture, but they should currently be treated as **experimental, incomplete, and subject to substantial change**.

## What is ready now

The currently supported portion of PSAIR focuses on repository documentation workflows, including tools for:

- modular manual preparation
- outline generation
- character and formatting checks
- PDF-oriented manual export
- manual viewing utilities for Streamlit-style apps

These tools are intended to support repositories that maintain structured Markdown manuals and want lightweight support for viewing and export.

Also available in alpha form:

- metadata utilities for relative-path metadata field extraction and matching related files
- NLP utilities for text preprocessing and shared spaCy model/resource loading
- support for logging, provenance, and example I/O generation

## What is not ready yet

The broader `psair` namespace also contains modules related to:

- ETL
- exploratory data analysis
- pipeline scaffolding

These components are being actively developed and reorganized. They are not yet stable enough to treat as public APIs.

## Installation

For the currently supported documentation tooling:

```bash
pip install "psair[docs]"
```

If you are developing against the full experimental package layout:

```bash
pip install "psair[full]"
```

After installation, the documentation CLI is available as:

```bash
psair --help
```

If a terminal cannot find `psair`, confirm that the intended environment is active:

```bash
conda activate psair
python -m pip install -e ".[docs]"
psair --help
```

You can also run the command through Conda without changing the current shell:

```bash
conda run -n psair psair --help
```

The CLI currently focuses on manual/documentation workflows:

```bash
psair tree docs/manual
psair index docs/manual --show-files
psair search "topic" docs/manual
psair outline docs/manual --title "Instruction Manual" --version "0.0.3a1"
psair chars docs/manual --check-trailing --check-line-endings
psair pdf docs/manual --non-interactive --force
```

PDF compilation uses Pandoc and a LaTeX PDF engine such as XeLaTeX when using
the CLI PDF builder. Those executables must be installed separately and
available on `PATH`.

## Testing

This project uses [pytest](https://docs.pytest.org/) for its testing suite.  
All tests are located under the `tests/` directory, organized by module/function.

### Running Tests
To run the full suite:

```bash
pytest
```
Run with verbose output:
```bash
pytest -v
```
Run a specific test file:
```bash
pytest tests/test_manual/test_pdf.py
```

## Stability note

PSAIR is currently in alpha. Module structure, APIs, and dependency groupings may change significantly across early releases. Until the package reaches a more stable milestone, the documentation tooling should be treated as the primary supported interface; metadata and NLP utilities are available for alpha adopters but may still change.

## Intended use

PSAIR is primarily intended for developers and research programmers who want reusable infrastructure for analysis-oriented repositories. It is not yet a polished end-user application.

## Related projects

PSAIR serves as shared backend scaffolding for downstream repositories. Project-specific applications and domain workflows should be handled in those downstream tools rather than in PSAIR itself.
