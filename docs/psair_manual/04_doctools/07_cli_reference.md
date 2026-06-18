
# IRIDIC CLI Command Reference

## Overview

The IRIDIC command-line interface provides utilities for exploring, validating, and compiling modular instruction manuals.

The CLI entry point is:

```
iridic
```

Commands are organized around the major documentation modules.

| Command | Module | Purpose |
|-------|-------|--------|
| `tree` | manual_index | Print the generated manual tree |
| `search` | manual_index | Search manual content |
| `index` | manual_index | Summarize indexed manual files |
| `outline` | manual_outline | Generate or refresh the manual outline |
| `chars` | manual_chars | Validate documentation characters and formatting |
| `pdf` | manual_pdf | Compile the manual into a PDF |

Each command is implemented as a subparser under the main CLI program. fileciteturn6file0

---

# General Command Structure

Most commands follow the structure:

```
iridic <command> [manual_dir] [options]
```

Example:

```
iridic tree manual
iridic search "installation"
iridic pdf manual --yaml manual/manual_pdf.yaml
```

If the manual directory is not specified, the default directory is:

```
manual/
```

---

# manual_index Commands

These commands explore and query the manual structure.

---

## `iridic tree`

Print the generated manual directory tree.

### Usage

```
iridic tree [manual_dir]
```

### Arguments

| Argument | Description |
|--------|-------------|
| `manual_dir` | Path to the manual directory (default: `docs/manual`) |

### Example

```
iridic tree manual
```

### Output

Displays a generated tree representation of the manual directory.

---

## `iridic search`

Search manual titles and content.

### Usage

```
iridic search <query> [manual_dir]
```

### Arguments

| Argument | Description |
|--------|-------------|
| `query` | Search string |
| `manual_dir` | Manual directory (default: `docs/manual`) |

### Options

| Option | Description | Default |
|------|-------------|--------|
| `--limit` | Maximum results returned | 25 |

### Example

```
iridic search "installation"
```

---

## `iridic index`

Summarize the indexed manual.

### Usage

```
iridic index [manual_dir]
```

### Arguments

| Argument | Description |
|--------|-------------|
| `manual_dir` | Manual directory (default: `docs/manual`) |

### Options

| Option | Description |
|------|-------------|
| `--show-files` | Print indexed relative file paths |

### Example

```
iridic index manual --show-files
```

---

# manual_outline Commands

---

## `iridic outline`

Generate or update the manual outline file.

### Usage

```
iridic outline [manual_dir] [options]
```

### Options

| Option | Description | Default |
|------|-------------|--------|
| `-o`, `--output` | Output outline path | `docs/manual` |
| `--title` | Manual title | "Instruction Manual" |
| `--version` | Manual version | "0.0.0" |
| `--exts` | File extensions to include | `.md,.markdown` |
| `--max-depth` | Maximum directory depth rendered | None |
| `--if-missing-only` | Build outline only if it does not exist | False |

### Example

```
iridic outline manual --title "IRIDIC Manual" --version 0.1.0
```

This generates:

```
manual/00_outline.md
```

---

# manual_chars Commands

---

## `iridic chars`

Validate documentation files for character and formatting issues.

### Usage

```
iridic chars [root] [options]
```

### Arguments

| Argument | Description |
|--------|-------------|
| `root` | Root directory to scan (default: `docs/manual`) |

### File selection

| Option | Description | Default |
|------|-------------|--------|
| `--exts` | File extensions to include | `.md,.markdown,.txt,.yaml,.yml,.toml,.json,.py` |

### Character checks

| Option | Description |
|------|-------------|
| `--report-nonascii` | Report non-ASCII characters |
| `--fail-on-nonascii` | Treat non-ASCII characters as errors |
| `--max-nonascii` | Maximum unique non-ASCII characters listed per line |

### Formatting checks

| Option | Description |
|------|-------------|
| `--check-trailing` | Detect trailing whitespace |
| `--strip-trailing` | Strip trailing whitespace |
| `--check-line-endings` | Detect CRLF line endings |
| `--fix-line-endings` | Normalize line endings (`lf` or `crlf`) |

### Output control

| Option | Description |
|------|-------------|
| `--summary-only` | Print summary only |
| `--no-line-context` | Hide offending line text |
| `--warnings-as-errors` | Treat warnings as errors |

### Example

```
iridic chars manual --report-nonascii --check-trailing
```

---

# manual_pdf Commands

---

## `iridic pdf`

Compile the manual into a PDF using Pandoc.

### Usage

```
iridic pdf [manual_dir] [options]
```

### Compile options

| Option | Description | Default |
|------|-------------|--------|
| `-y`, `--yaml` | Pandoc metadata YAML file | `[manual dir]/manual_pdf.yaml` |
| `-o`, `--output` | Output PDF path | `docs` |
| `--pandoc` | Pandoc executable | pandoc |
| `--pdf-engine` | Pandoc PDF engine | xelatex |
| `--exts` | File extensions included | `.md,.markdown` |

### Layout options

| Option | Description | Default |
|------|-------------|--------|
| `--margin` | Page margin (Pandoc geometry) | `1in` |
| `--no-pagebreaks` | Disable section page breaks | False |
| `--keep-heading-numbers` | Keep numeric prefixes in headings | False |
| `--no-toc` | Disable automatic TOC | False |
| `--toc-depth` | Table-of-contents depth | 3 |

### Content inclusion

| Option | Description |
|------|-------------|
| `--include-outline` | Include `00_outline.md` |
| `--outline-name` | Outline filename |

### Build artifacts

| Option | Description |
|------|-------------|
| `--file-dividers` | Insert HTML comments marking file boundaries |
| `--keep-temp-md` | Keep assembled markdown file |
| `--temp-md-path` | Explicit path for temporary markdown |

### Pandoc passthrough

| Option | Description |
|------|-------------|
| `--extra-pandoc-arg` | Pass additional arguments to Pandoc |

Example:

```
iridic pdf manual --yaml manual/manual_pdf.yaml
```

---

# PDF Preflight Options

The `pdf` command includes optional validation steps before compilation.

### Outline generation

| Option | Description |
|------|-------------|
| `--skip-outline` | Skip outline generation |
| `--rebuild-outline` | Force outline rebuild |
| `--outline-title` | Title used if outline is generated |
| `--outline-version` | Version string for outline |
| `--outline-max-depth` | Maximum depth of outline tree |

### Character validation

| Option | Description |
|------|-------------|
| `--skip-chars` | Skip character validation |
| `--include-hidden` | Include hidden files |
| `--report-nonascii` | Report non-ASCII characters |
| `--fail-on-nonascii` | Treat non-ASCII characters as errors |
| `--check-trailing` | Check trailing whitespace |
| `--strip-trailing` | Strip trailing whitespace |
| `--check-line-endings` | Detect CRLF line endings |
| `--fix-line-endings` | Normalize line endings |

### Safety controls

| Option | Description |
|------|-------------|
| `--non-interactive` | Abort instead of prompting |
| `--force` | Proceed even if issues are found |

Example:

```
iridic pdf manual --yaml manual/manual_pdf.yaml --force
```

---

# Example Workflows

### Inspect a manual

```
iridic tree
iridic search "installation"
iridic index
```

### Prepare a manual

```
iridic chars manual --check-trailing
iridic outline manual
```

### Compile the PDF

```
iridic pdf manual --yaml manual/manual_pdf.yaml
```

---

# Summary

The IRIDIC CLI provides a compact set of commands for working with modular manuals.

Capabilities include:

- exploring manual structure
- searching documentation
- validating formatting
- generating navigation outlines
- compiling publishable PDF manuals

These commands expose the functionality of the underlying IRIDIC documentation modules through a consistent command-line interface. fileciteturn6file1
