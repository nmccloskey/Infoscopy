# PSAIR - Python Support for Aphasiology Itineraries in Research

![PyPI version](https://img.shields.io/pypi/v/psair)
![Python](https://img.shields.io/pypi/pyversions/psair)
![License](https://img.shields.io/pypi/l/psair)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://psair-dev.streamlit.app/)

**Status:** Usable alpha software; limited maintenance  
**Current scope:** Shared backend support for DIAAD and, indirectly, its lab-specific RASCAL wrapper  
**Development outlook:** No major feature expansion is currently planned, although bug reports and limited corrective updates may be considered at the maintainer's discretion

PSAIR provides backend utilities for aphasiology-oriented discourse-analysis software. DIAAD directly uses PSAIR for metadata handling, structured logging and provenance, lightweight NLP support, manual-viewing utilities, and example input/output generation. RASCAL does not import or run PSAIR directly; as a lab-specific wrapper around DIAAD workflows, it relies on PSAIR indirectly wherever its DIAAD calls use these shared components.

The package remains at an alpha version because some interfaces may still change, but its currently supported components are usable. PSAIR is intended primarily for developers and research programmers rather than as a standalone end-user application.

## Supported components

### Documentation and manual tooling

The documentation toolchain supports repositories that maintain structured Markdown manuals. Current functionality includes:

- modular manual preparation
- manual-tree indexing, browsing, and search
- outline generation
- character and formatting checks
- PDF-oriented manual export
- manual-viewing utilities for Streamlit-style applications

### Metadata and provenance

PSAIR also provides utilities for:

- extracting metadata fields from relative file paths
- discovering and matching related files
- recording configuration, input/output listings, and other run metadata
- generating structured logs and provenance records
- supporting reproducible example input/output generation

### Lightweight NLP support

Current NLP utilities include:

- text preprocessing helpers
- shared spaCy model and resource loading
- reusable support for NLP-backed DIAAD workflows

## Installation

For the documentation tooling:

```bash
pip install "psair[docs]"
```

To install the full set of optional dependencies currently exposed by the package:

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

The CLI currently focuses on manual and documentation workflows:

```bash
psair tree docs/manual
psair index docs/manual --show-files
psair search "topic" docs/manual
psair outline docs/manual --title "Instruction Manual" --version "0.0.3a2"
psair chars docs/manual --check-trailing --check-line-endings
psair pdf docs/manual --non-interactive --force
```

PDF compilation uses Pandoc and a LaTeX PDF engine such as XeLaTeX. These executables must be installed separately and available on `PATH`.

## Testing

This project uses [pytest](https://docs.pytest.org/) for its test suite. Tests are located under the `tests/` directory and organized by module or function.

Run the full suite:

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

## Stability and maintenance

PSAIR remains alpha software. Its present functionality is usable, but module structure, APIs, and optional dependency groupings may change if corrective maintenance requires it. No major new feature development or lab-directed support is planned.

Issue reports are welcome. Their submission does not imply a guaranteed response or resolution, but limited corrective updates may be made when they are useful for the public package or its maintained dependents.

Earlier plans contemplated broader ETL, exploratory data analysis, and general pipeline-development functionality within PSAIR. Those areas were not completed and are no longer part of this repository's planned scope. Any undeveloped scaffolding for them should be treated as historical and may be removed during repository cleanup.

## Project history and contributions

PSAIR was conceived, designed, and developed by Nicholas McCloskey as shared backend support for aphasiology-oriented discourse-analysis software. The project was originally named *Python Scaffolding for Analysis Itineraries in Research*. It was later renamed *Python Support for Aphasiology Itineraries in Research* to reflect its actual domain-specific scope.

McCloskey led the software architecture, implementation, documentation, testing, and release of PSAIR. Certain aspects of PSAIR's design and integrations were indirectly refined through domain, workflow, and usability feedback regarding DIAAD from members of the conversation treatment study at Temple and Boston Universities.

Initial development occurred in part during work supported by NIH grants R21 DC015859 and R01 DC018781. This funding statement describes the historical support context for PSAIR and does not imply that the funder or institution endorses the software or its documentation.

See [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) for a more detailed contribution record.

## Related projects

- [DIAAD](https://github.com/nmccloskey/DIAAD) directly uses PSAIR for shared metadata, logging and provenance, lightweight NLP, manual-viewing, and example input/output functionality.
- [RASCAL](https://github.com/nmccloskey/RASCAL) is a lab-specific wrapper around DIAAD. It does not directly import or invoke PSAIR, but relies on it indirectly through DIAAD workflows.

Future systems may address related infrastructure needs through independent implementations. Where relevant, PSAIR can be cited as a conceptual or technical precursor, but future systems should not be assumed to be continuations of this codebase.
