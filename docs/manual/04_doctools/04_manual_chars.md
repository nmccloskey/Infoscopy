
# manual_chars Module

## Overview

The `manual_chars` module provides **character and content hygiene validation for IRIDIC documentation**.

It scans documentation directories for formatting issues that can interfere with:

- documentation readability
- repository consistency
- PDF compilation
- cross-platform text compatibility

The module detects and optionally fixes common issues such as:

- trailing whitespace
- inconsistent line endings (CRLF vs LF)
- non‑ASCII characters
- hidden formatting artifacts

Unlike other IRIDIC modules that generate or compile manual artifacts, `manual_chars` acts as a **preflight validation tool** that helps maintain documentation quality before downstream operations such as PDF compilation.

---

# Data Model

## Finding

Represents a single detected formatting issue.

```
@dataclass(frozen=True)
class Finding:
    path: Path
    line_no: int
    kind: str
    message: str
    line: str = ""
```

Fields:

| Field | Description |
|------|-------------|
| `path` | File containing the issue |
| `line_no` | Line number of the finding |
| `kind` | Type of issue detected |
| `message` | Human-readable description |
| `line` | Offending line text (optional) |

Findings are classified as either **warnings** or **errors** depending on configuration.

---

## CharScanResult

Aggregates results from a documentation scan.

```
@dataclass
class CharScanResult:
    root: Path
    scanned_files: list[Path]
    fixed_files: list[Path]
    warnings: list[Finding]
    errors: list[Finding]
```

Additional properties:

| Property | Description |
|--------|-------------|
| `ok` | True if no errors were found |
| `total_findings` | Total number of warnings and errors |

Utility methods provide formatted output for CLI reporting.

---

# Core Functions

## check_manual_chars

Primary scanning function.

```
check_manual_chars(root)
```

### Purpose

Scans documentation files and optionally applies safe automatic fixes.

### Parameters

| Parameter | Description |
|----------|-------------|
| `root` | Directory to scan |
| `exts` | File extensions to include |
| `include_hidden` | Include hidden files |
| `report_nonascii` | Warn about non‑ASCII characters |
| `fail_on_nonascii` | Treat non‑ASCII as errors |
| `check_trailing` | Detect trailing whitespace |
| `strip_trailing` | Remove trailing whitespace |
| `check_line_endings` | Detect CRLF line endings |
| `fix_line_endings` | Normalize line endings |
| `warnings_as_errors` | Promote warnings to errors |

### Behavior

The function:

1. Collects target files
2. Optionally applies safe formatting fixes
3. Scans each file for issues
4. Aggregates results into a `CharScanResult` object

Example summary:

```
Root: manual
Files scanned: 42
Files modified: 3
Warnings: 6
Errors: 0
```

---

## run_manual_chars

CLI wrapper around the scanning engine.

```
run_manual_chars(root)
```

This function:

1. Executes `check_manual_chars`
2. Prints formatted findings
3. Returns a process exit code

Return values:

| Code | Meaning |
|----|-------|
| `0` | Scan successful |
| `1` | Errors detected |

---

# Supporting Utilities

## iter_target_files

Collects text-like files within the root directory.

Default extensions include:

```
.md
.markdown
.txt
.yaml
.yml
.toml
.json
.py
```

The function also:

- skips hidden directories
- ignores `__pycache__`
- sorts results deterministically

---

## scan_file

Scans an individual file for formatting issues.

Checks may include:

- non‑ASCII characters
- trailing whitespace
- CRLF line endings

The function returns two lists:

```
(warnings, errors)
```

depending on the configured policy.

---

## apply_fixes

Applies safe automatic corrections.

Supported fixes include:

### Trailing whitespace removal

```
strip_trailing=True
```

### Line ending normalization

```
fix_line_endings="lf"
fix_line_endings="crlf"
```

The function modifies files **only when necessary** and reports which files were updated.

---

## format_finding

Formats scan findings for CLI output.

Example:

```
[trailing_whitespace] manual/intro.md:12 - Trailing whitespace detected.
    This line contains extra spaces
```

The offending line may optionally be suppressed for concise reporting.

---

# CLI Integration

The module is exposed through the IRIDIC CLI command:

```
iridic chars
```

Example usage:

```
iridic chars manual
```

Optional flags include:

```
--check-trailing
--strip-trailing
--report-nonascii
--fail-on-nonascii
--check-line-endings
--fix-line-endings lf
--warnings-as-errors
```

These options allow the tool to operate either as:

- a **passive diagnostic scanner**, or
- an **automatic documentation formatter**.

The CLI interface integrates with the argument configuration system used across IRIDIC tools. fileciteturn2file0

---

# Role Within IRIDIC

The `manual_chars` module serves as the **documentation hygiene layer** of the IRIDIC manual toolchain.

Typical workflow position:

```
manual editing
        ↓
manual_chars validation
        ↓
manual_outline generation
        ↓
manual_pdf compilation
```

By enforcing clean formatting and encoding conventions, the module prevents issues such as:

- Pandoc rendering errors
- inconsistent repository formatting
- cross-platform newline problems

---

# Design Principles

The module emphasizes several design goals.

**Safe automated fixes**  
Only non-destructive formatting corrections are applied automatically.

**Transparent reporting**  
All detected issues are reported in structured findings.

**Configurable strictness**  
Warnings can be escalated to errors when needed.

**Language-agnostic scanning**  
The tool works on Markdown and other text-based formats used in documentation repositories.

---

# Summary

`manual_chars` ensures that IRIDIC documentation remains clean, consistent, and safe for downstream tooling.

Core capabilities include:

- documentation scanning
- whitespace validation
- encoding checks
- newline normalization
- optional automatic formatting fixes

Together these features help maintain a **high-quality documentation environment** across IRIDIC repositories.
