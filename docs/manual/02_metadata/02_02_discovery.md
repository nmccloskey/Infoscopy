# File Discovery

## Purpose

`psair.metadata.discovery.find_matching_files()` searches one or more
directories for files whose names match a base pattern, extension, and optional
metadata labels. It is a lightweight helper for locating files that correspond
to metadata extracted from another source.

For example, after extracting metadata fields from `AC001_Pre_story.cha`, a
downstream workflow might need to find a spreadsheet whose filename also
contains `AC`, `Pre`, and a known base label.

## Function Signature

```python
from psair.metadata.discovery import find_matching_files

find_matching_files(
    match_metadata_fields=None,
    directories=None,
    search_base="",
    search_ext=".xlsx",
    deduplicate=True,
)
```

The parameter name `match_metadata_fields` remains for compatibility with existing code.
Conceptually, it is a list of metadata labels to match.

## Matching Rules

The utility searches recursively with `Path.rglob()`. A file is included when
all of the following are true:

- the filename contains `search_base`
- the filename ends with `search_ext`
- every non-empty value in `match_metadata_fields` appears somewhere in the filename

Matching is case-sensitive because it uses ordinary Python substring checks.

Example:

```python
matches = find_matching_files(
    match_metadata_fields=["AC", "Pre"],
    directories=["data/forms", "data/exports"],
    search_base="scores",
    search_ext=".xlsx",
)
```

This searches both directories recursively for `.xlsx` files whose names
contain `scores`, `AC`, and `Pre`.

## Directories

`directories` can be:

- `None`, which searches the current working directory
- one path as a string or `Path`
- a list of strings and/or `Path` objects

Missing directories are skipped and logged as warnings. Search errors inside an
individual directory are caught and logged so another directory can still be
searched.

## Metadata Labels

`match_metadata_fields` is optional. When it is `None` or empty, the utility searches only
by `search_base` and `search_ext`.

Values are converted to strings and empty values are ignored:

```python
find_matching_files(match_metadata_fields=["AC", None, "", "Pre"])
```

is treated like:

```python
find_matching_files(match_metadata_fields=["AC", "Pre"])
```

## Deduplication

When `deduplicate=True`, duplicate filenames found in different directories are
collapsed to one result. Deduplication is based on `Path.name`, not the full
path.

The first matching path is retained, and later paths with the same filename are
logged as duplicates. This is useful when multiple export directories may
contain copies of the same named file.

Set `deduplicate=False` when each path should be preserved even if filenames
repeat:

```python
matches = find_matching_files(
    match_metadata_fields=["AC", "Pre"],
    directories=["batch_a", "batch_b"],
    search_base="scores",
    deduplicate=False,
)
```

## Return Value

The function always returns a list of `Path` objects. It returns an empty list
when no files match.

A single match is logged as a successful match. Multiple matches are logged as a
multi-match result, with paths emitted at debug level.

## Example With Metadata Extraction

```python
from psair.metadata.metadata_fields import MetadataManager
from psair.metadata.discovery import find_matching_files

config = {
    "metadata_fields": {
        "site": ["AC", "BU", "TU"],
        "test": ["Pre", "Post"],
    }
}

manager = MetadataManager(config)
labels = manager.match_metadata("AC001_Pre_story.cha", return_none=True)

matches = find_matching_files(
    match_metadata_fields=[labels["site"], labels["test"]],
    directories="data/metadata",
    search_base="scores",
    search_ext=".xlsx",
)
```

This looks for score spreadsheets in `data/metadata` whose filenames include
the same site and test labels extracted from the text file path.

## Practical Guidance

Use this utility when filenames carry enough structure to identify related
files without opening them. It is best suited to small and medium research data
directories where recursive filename search is cheap and transparent.

For large repositories, highly ambiguous filename conventions, or content-based
matching, use a more explicit index or manifest instead.
