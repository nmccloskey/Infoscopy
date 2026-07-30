# Optional Extras and Build Splits

## Why PSAIR uses extras

PSAIR keeps its base installation deliberately small. The package includes
several areas of functionality, but not every user needs the same dependency
stack. Optional extras let users install only the dependencies needed for a
particular workflow.

This matters because the supported documentation tooling, Streamlit viewing, and NLP utilities have different dependency profiles. For example, a project that only wants the manual CLI should not have to install spaCy or Streamlit.

Install extras with standard `pip` syntax:

```bash
pip install "psair[docs]"
```

For editable development installs, use:

```bash
python -m pip install -e ".[docs]"
```

Multiple extras can be combined:

```bash
python -m pip install -e ".[docs,view,dev]"
```

## Base install

```bash
pip install psair
```

The base install has no required third-party dependencies. It installs the
`psair` package and the CLI entry points, but workflows that require optional
libraries will need the appropriate extra.

Use the base install when a project needs only dependency-light package
functionality or when another environment layer manages dependencies directly.

## Documentation extra

```bash
pip install "psair[docs]"
```

The `docs` extra is the recommended install target for the currently supported
PSAIR documentation toolchain. It includes dependencies used for manual export,
document handling, YAML configuration, and PDF support.

Use `docs` for:

- `psair tree`
- `psair index`
- `psair search`
- `psair outline`
- `psair chars`
- `psair pdf`
- Markdown manual workflows
- Pandoc-oriented PDF builds

Pandoc and a LaTeX PDF engine such as XeLaTeX are still external system tools.
They are not installed by `pip install "psair[docs]"`.

## Viewer extra

```bash
pip install "psair[view]"
```

The `view` extra supports the Streamlit manual viewer and browser-oriented
manual export helpers. It is useful for projects that want to embed PSAIR manual
browsing inside a Streamlit app.

Use `view` for:

- interactive manual browsing
- Streamlit-hosted documentation panels
- lightweight manual export from the viewer
- deployments such as Streamlit Community Cloud

The repository-level `requirements.txt` installs `.[view]` so the hosted viewer
can keep the base package dependency-free while still installing the packages
needed by the app.

## NLP extra

```bash
pip install "psair[nlp]"
```

The `nlp` extra installs spaCy, which is the core dependency for PSAIR's shared
NLP model loader. Use this extra when code needs `NLPModel`, tokenization,
lemmatization, stopword filtering, or other spaCy pipeline behavior.

spaCy language models are not bundled inside the Python package. By default,
`NLPModel` can attempt to download a requested spaCy model when it is missing.
For controlled environments, install the model ahead of time or call
`get_nlp(..., auto_download_model=False)` so missing models fail explicitly.

## Web extra

```bash
pip install "psair[web]"
```

The `web` extra installs Streamlit and Markdown rendering dependencies for
web-facing PSAIR components. It overlaps with `view`, but is kept as a separate
build split for broader web-facing work as the package evolves.

Use `view` when the goal is the manual viewer specifically. Use `web` when
working on broader web application pieces.

## Development extra

```bash
python -m pip install -e ".[dev]"
```

The `dev` extra installs test tooling for contributors. At present, this means
`pytest`.

For documentation development, contributors will usually want:

```bash
python -m pip install -e ".[docs,view,dev]"
```

## Full extra

```bash
pip install "psair[full]"
```

The `full` extra installs the union of the main optional dependency groups. It
is intended for contributors who are developing across the package, not for
minimal downstream use.

Use `full` when:

- testing several package areas in one environment
- developing against experimental modules
- preparing broad integration checks
- investigating dependency interactions before a release

Avoid `full` for lightweight deployments unless the deployment truly needs the
whole experimental stack.

## Recommended install targets

For most users of the current alpha release:

```bash
pip install "psair[docs]"
```

For the manual viewer:

```bash
pip install "psair[view]"
```

For contributors working on documentation and tests:

```bash
python -m pip install -e ".[docs,view,dev]"
```

For broad experimental development:

```bash
python -m pip install -e ".[full,dev]"
```
