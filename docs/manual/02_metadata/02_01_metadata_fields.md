# Metadata Fields

## Purpose

The metadata field system extracts structured labels from text file paths. It
is intended for research repositories where folder names or filenames encode
useful information such as site, group, assessment time, task, study identifier,
or corpus label.

The implementation lives in `psair.metadata.metadata_fields` and centers on two objects:

- `MetadataField`: one compiled path-matching rule
- `MetadataManager`: an ordered collection of metadata fields built from configuration

Metadata fields are deliberately simple. They search the relative path under
`input_dir`, checking folder names before the filename, and return the first
matching substring for each configured metadata field.

## Configuration Shape

`MetadataManager` expects a dictionary with a `metadata_fields` entry:

```yaml
metadata_fields:
  site: [AC, BU, TU]
  test: [Pre, Post, Maint]
  study_id: "(AC|BU|TU)\\d+"
```

Each metadata field value can be either:

- a list of strings, interpreted as literal allowed values
- a string, interpreted as a regular expression

The order of metadata fields follows the order in the configuration dictionary.
That order is preserved by `get_metadata_field_names()` and by the dictionaries
returned from `match_metadata()`.

## Literal Value Fields

A list of strings creates a literal-value metadata field:

```yaml
metadata_fields:
  site: [AC, BU, TU]
```

This metadata field searches for any of the listed values in the relative path.
Values are escaped before the regex is compiled, so characters such as `+`, `.`,
or `-` are treated literally rather than as regex syntax.

Example:

```python
from psair.metadata.metadata_fields import MetadataManager

manager = MetadataManager({"metadata_fields": {"site": ["AC", "BU", "TU"]}})
manager.match_metadata("AC001_Pre_story.cha")
```

Result:

```python
{"site": "AC"}
```

## Regex Fields

A string creates a regex metadata field:

```yaml
metadata_fields:
  study_id: "(AC|BU|TU)\\d+"
```

Regex metadata fields are useful when the metadata value has a pattern rather
than a fixed list of known values.

Example:

```python
manager = MetadataManager({"metadata_fields": {"study_id": r"(AC|BU|TU)\d+"}})
manager.match_metadata("AC001_Pre_story.cha")
```

Result:

```python
{"study_id": "AC001"}
```

## Path Matching

Use `match_metadata(path)` to extract all configured metadata fields from a
file path:

```python
config = {
    "input_dir": "data/input",
    "metadata_fields": {
        "site": ["AC", "BU", "TU"],
        "test": ["pretx", "posttx"],
        "study_id": r"(AC|BU|TU)\d+",
    }
}

manager = MetadataManager(config)
manager.match_metadata("data/input/pretx/AC001_story.cha")
```

Result:

```python
{
    "site": "AC",
    "test": "pretx",
    "study_id": "AC001",
}
```

When `input_dir` is configured and the provided path is absolute, matching is
based on the relative path below `input_dir`. For example, if `input_dir` is
`data/input`, the file `data/input/pretx/par1.cha` is searched as:

```text
pretx
par1.cha
```

Folder names are searched before the filename. This supports directory-based
metadata such as:

```text
pretx/par1.cha
posttx/par1.cha
```

If both folders and filenames contain distinct matches for the same metadata
field, the first match in relative path order is used and a warning is logged.
Repeated copies of the same value do not produce a warning.

## Missing Values

By default, an unmatched metadata field returns the metadata field name. This
keeps a placeholder in the result and makes missing matches visible in
downstream tables:

```python
manager.match_metadata("AC001_story.cha")
```

Result:

```python
{
    "site": "AC",
    "test": "test",
    "study_id": "AC001",
}
```

Set `return_none=True` when missing values should be represented as `None`:

```python
manager.match_metadata("AC001_story.cha", return_none=True)
```

Result:

```python
{
    "site": "AC",
    "test": None,
    "study_id": "AC001",
}
```

Set `must_match=True` when missing metadata fields should be logged as warnings:

```python
manager.match_metadata("AC001_story.cha", return_none=True, must_match=True)
```

## Default Field

If the config is missing, does not contain a valid `metadata_fields` dictionary, or the
`metadata_fields` dictionary is empty, `MetadataManager` creates one default metadata
field:

```python
{"file_name": "..."}
```

The default metadata field uses the regex `.*(?=\.cha)`, which extracts the
full filename stem before `.cha`.

For example:

```python
manager = MetadataManager({})
manager.match_metadata("AC001_Pre_story.cha")
```

Result:

```python
{"file_name": "AC001_Pre_story"}
```

## Name Transforms

`MetadataManager` accepts an optional `name_transform` callable. This can
normalize metadata field names as they are read from configuration:

```python
manager = MetadataManager(
    {"metadata_fields": {"Study ID": r"(AC|BU|TU)\d+"}},
    name_transform=lambda name: name.lower().replace(" ", "_"),
)
```

Resulting metadata field name:

```python
"study_id"
```

## Validation

Metadata field construction validates the config before matching:

- regex metadata fields must be non-empty valid regular expressions
- value metadata fields must be lists containing only strings
- empty value lists are allowed, but they log a warning and never match
- unsupported metadata field specifications raise `TypeError`

This validation happens when `MetadataManager` is constructed, so configuration
errors are found early.

## Compatibility

The old names `Tier`, `TierManager`, `get_tier_names()`, and `match_tiers()`
remain available as aliases for existing code. New code should use
`MetadataField`, `MetadataManager`, `get_metadata_field_names()`, and
`match_metadata()`.

## Practical Guidance

Use literal value metadata fields for controlled labels that should match
exactly, such as known sites or assessment names. Use regex metadata fields for
identifiers, dates, or compound labels whose valid values are easier to
describe with a pattern.

Keep labels distinct enough that accidental substring matches are unlikely.
For example, if one metadata field has values `["Pre", "Post"]`, filenames
such as `"Preview_AC001.cha"` may match `Pre` unless the metadata field is
expressed with a more specific regex.
