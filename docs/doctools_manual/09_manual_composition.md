# Manual Composition

## Overview

PSAIR can compose authored manual pages and generated manual-like pages into one
navigation tree without moving either set of files.

This is useful when a downstream project keeps prose documentation under a
manual root such as `docs/manual/`, but also generates reproducible Example I/O
pages under an asset root such as
`src/project/examples/assets/rendered_docs/example_io/`.

The composition layer is intentionally metadata-driven:

- authored pages remain in the authored manual tree;
- generated pages remain in the generated asset tree;
- the viewer and export helpers build a virtual tree at runtime;
- front matter is used for matching, ordering, and display labels;
- Markdown body text is rendered without showing YAML front matter.

Views are optional. A command can have `quickstart`, `usage_guide`, and
`implementation_notes` without having `research_context`. A generated
`example_io` view can still be threaded after the authored views that exist.

---

## Source Roots

Each physical source tree is represented by `ManualSource`:

```python
from pathlib import Path

from psair.examples import ManualSource

sources = [
    ManualSource(
        root=Path("docs/manual"),
        name="manual",
        source_manual="authored",
        role="authored",
    ),
    ManualSource(
        root=Path("src/project/examples/assets/rendered_docs/example_io"),
        name="example_io",
        source_manual="generated_example_io",
        role="generated",
    ),
]
```

Downstream webapps can also pass source mappings to `render_manual_ui()`.
Relative roots are resolved against the `repo_root` argument in the viewer.

---

## Front Matter Contract

Composable pages use YAML front matter at the top of each Markdown file.
The composer strips the front matter before the page is displayed or exported.

Command-oriented pages should declare:

```yaml
---
object_type: command
object_types:
  - command
object_id: transcripts.tabularize
command_id: transcripts.tabularize
module_id: transcripts
view: example_io
view_label: Example I/O
view_order: 50
source_manual: generated_example_io
generated: true
---
```

Required matching fields:

| Field | Purpose |
|---|---|
| `object_type` | Primary object kind, such as `command` or `workflow` |
| `object_id` | Stable object identifier shared by related views |
| `view` | Stable view identifier, such as `quickstart` or `example_io` |

Recommended display fields:

| Field | Purpose |
|---|---|
| `object_types` | Optional secondary object kinds for project-specific use |
| `view_label` | Human label shown in the tree |
| `view_order` | Numeric ordering within the object view set |
| `title` | Optional document title override |
| `source_manual` | Source label for diagnostics, such as `authored` |
| `generated` | Boolean hint that the page came from generated assets |

Project-specific fields such as `command_id`, `module_id`,
`canonical_command`, `workflow_id`, or `slot` can be included for downstream
renderers and tests. PSAIR does not require those fields for generic
composition.

---

## View Vocabulary

PSAIR provides default labels and order values for the common manual view
vocabulary:

| View | Label | Order | Virtual filename |
|---|---|---:|---|
| `quickstart` | Quickstart | 10 | `01_quickstart.md` |
| `usage_guide` | Usage Guide | 20 | `02_usage_guide.md` |
| `research_context` | Research Context | 30 | `03_research_context.md` |
| `implementation_notes` | Implementation Notes | 40 | `04_implementation_notes.md` |
| `example_io` | Example I/O | 50 | `05_example_io.md` |

Downstream projects can use other views by providing explicit `view_label` and
`view_order` values. The composer does not require every object to have every
view.

---

## Virtual Paths

When authored and generated views share the same `object_type` and `object_id`,
generated views are placed beside the authored views for display.

For example, this generated source file:

```text
src/project/examples/assets/rendered_docs/example_io/transcripts/tabularize.md
```

can appear virtually as:

```text
docs/manual/04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md
```

The physical file stays under the generated asset root. The virtual path exists
only inside the composed index returned by `build_composed_manual()` and the
viewer/export helpers.

If a generated view has no authored anchor, `unmatched_policy` controls where it
appears:

| Policy | Behavior |
|---|---|
| `source_path` | Keep the generated file's source-relative path |
| `generated_root` | Place it under `generated/<source-name>/...` |

Diagnostics are recorded when generated views cannot be anchored or when
duplicate views are discovered. Duplicate views raise
`ManualCompositionError` by default.

---

## Viewer Integration

`render_manual_ui()` accepts composed manual sources:

```python
from psair.webapp.manual_viewer import render_manual_ui

render_manual_ui(
    repo_root=repo_root,
    manual_rel_dir="docs/manual",
    manual_sources=[
        {
            "root": repo_root / "docs/manual",
            "name": "manual",
            "source_manual": "authored",
            "role": "authored",
        },
        {
            "root": package_root / "examples/assets/rendered_docs/example_io",
            "name": "example_io",
            "source_manual": "generated_example_io",
            "role": "generated",
        },
    ],
    compose_infer_from_paths=True,
    compose_unmatched_policy="generated_root",
)
```

`compose_infer_from_paths=True` is a transitional aid for DIAAD-shaped authored
command folders. Explicit front matter is preferred for new projects because it
keeps matching independent of folder naming conventions.

When an authored module folder uses a descriptive name but generated pages use a
short command module ID, pass `compose_path_module_aliases`:

```python
render_manual_ui(
    repo_root=repo_root,
    manual_sources=sources,
    compose_infer_from_paths=True,
    compose_path_module_aliases={
        "complete_utterances": "cus",
        "word_counting": "words",
    },
)
```

Aliases only affect inferred metadata. Explicit front matter on a Markdown file
still wins.

The viewer prepares outlines only for authored roots. Generated asset roots are
read as inputs and should be regenerated by their owning renderer, not edited by
the viewer.

---

## Export Behavior

Webapp PDF and DOCX downloads use the same composed `flat` index that powers
the interactive tree. If a generated `example_io` page appears virtually after
authored command views in the webapp, it is exported in that same order.

For direct export-oriented workflows, use
`build_composed_manual_markdown()`:

```python
from psair.webapp.manual_export import build_composed_manual_markdown

markdown_text, section_meta = build_composed_manual_markdown(
    sources,
    infer_from_paths=True,
    path_module_aliases={"complete_utterances": "cus"},
    unmatched_policy="generated_root",
)
```

The returned Markdown has front matter stripped, optional page breaks inserted,
and section metadata keyed by virtual paths. The CLI `psair pdf` command still
compiles a single physical manual root; composed exports are currently exposed
through the webapp/export helpers.

---

## Limitations

Relative media and links need care. A generated page may be displayed at a
virtual path that differs from its physical file path, and composed exports may
assemble sections from multiple roots. Prefer self-contained Markdown tables,
code blocks, absolute links, or project-specific media handling until a
downstream app has explicit rewriting rules.

Generated pages that cannot be matched still remain available, but their
placement depends on `unmatched_policy`. Use diagnostics and focused tests to
confirm the final tree for important downstream manuals.

Composition keeps storage separate. Do not copy generated pages into the
authored manual tree, and do not paste generated preview tables into authored
manual pages. Update the generator, renderer, specs, or tests, then regenerate
the generated asset root.

---

## Summary

Manual composition lets downstream projects keep authored documentation and
generated Example I/O assets in separate source trees while presenting one
manual for browsing and export.

Core capabilities include:

- metadata-based grouping by object identity;
- optional view sets with deterministic ordering;
- virtual paths for generated sibling views;
- one Streamlit navigation tree;
- export ordering that matches the viewer;
- diagnostics for unmatched or duplicate generated content.
