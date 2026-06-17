from __future__ import annotations

from pathlib import Path

import pytest

from psair.examples import (
    ManualCompositionError,
    ManualSource,
    build_composed_manual,
    build_composed_manual_index,
    split_front_matter,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def command_front_matter(
    *,
    object_id: str = "transcripts.tabularize",
    view: str = "example_io",
    title: str = "Transcript Tabularization Example",
    view_label: str = "Example I/O",
    view_order: int = 50,
) -> str:
    return f"""---
object_type: command
object_types:
  - command
object_id: {object_id}
command_id: {object_id}
canonical_command: transcripts tabularize
module_id: transcripts
title: {title}
view: {view}
view_label: {view_label}
view_order: {view_order}
slot: examples
source_manual: generated_example_io
generated: true
---

"""


def workflow_front_matter() -> str:
    return """---
object_type: workflow
object_types:
  - workflow
  - command
object_id: full_example_dataset
workflow_id: full_example_dataset
command_id: examples
canonical_command: examples
command_subtype: omnibus
typology: omnibus_command_workflow
title: Full Example Dataset
view: example_io
view_label: Example I/O
view_order: 50
source_manual: generated_example_io
generated: true
---

"""


def test_split_front_matter_parses_yaml_and_returns_body_only() -> None:
    metadata, body = split_front_matter(
        command_front_matter() + "# Transcript Tabularization Example\nBody\n"
    )

    assert metadata["object_type"] == "command"
    assert metadata["object_id"] == "transcripts.tabularize"
    assert metadata["view"] == "example_io"
    assert body == "# Transcript Tabularization Example\nBody\n"


def test_authored_root_only_preserves_physical_tree(tmp_path: Path) -> None:
    authored = tmp_path / "manual"
    write(authored / "01_intro.md", "# Intro\nBody.\n")
    write(authored / "section" / "02_topic.md", "# Topic\nDetails.\n")

    composed = build_composed_manual([authored])

    assert list(composed.flat) == ["01_intro.md", "section/02_topic.md"]
    assert composed.flat["01_intro.md"].title == "Intro"
    assert composed.flat["section/02_topic.md"].text == "# Topic\nDetails.\n"
    assert composed.diagnostics == ()


def test_composes_generated_example_io_as_virtual_command_sibling(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    quickstart = write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "01_quickstart.md",
        "# `transcripts tabularize` Quickstart\nRun it.\n",
    )
    write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "04_implementation_notes.md",
        "# `transcripts tabularize` Implementation Notes\nInternals.\n",
    )
    generated_doc = write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(
                generated,
                name="example_io",
                source_manual="generated_example_io",
                role="generated",
            ),
        ],
        infer_from_paths=True,
    )

    expected_rel = (
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md"
    )
    assert expected_rel in composed.flat
    assert composed.flat[expected_rel].abs_path == generated_doc.resolve()
    assert composed.flat[expected_rel].title == "Example I/O"
    assert composed.flat[expected_rel].text.startswith(
        "# Transcript Tabularization Example"
    )
    assert not composed.flat[expected_rel].text.startswith("---")
    assert composed.flat[
        "04_modules/01_transcripts/05_commands/01_tabularize/01_quickstart.md"
    ].abs_path == quickstart.resolve()
    assert not any("No authored anchor" in item for item in composed.diagnostics)


def test_build_composed_manual_index_returns_existing_tree_and_flat_shapes(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    write(authored / "01_intro.md", "# Intro\nBody.\n")

    tree, flat = build_composed_manual_index([ManualSource(str(authored))])

    assert "01_intro.md" in tree
    assert flat["01_intro.md"].title == "Intro"
    assert flat["01_intro.md"].text == "# Intro\nBody.\n"


def test_path_inference_is_opt_in(tmp_path: Path) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "01_quickstart.md",
        "# `transcripts tabularize` Quickstart\nRun it.\n",
    )
    write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=False,
    )

    assert (
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md"
        not in composed.flat
    )
    assert "transcripts/tabularize.md" in composed.flat
    assert any("No authored anchor" in item for item in composed.diagnostics)


def test_generated_only_views_can_be_grouped_under_generated_root(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "example_io"
    generated_doc = write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [ManualSource(generated, name="example_io", role="generated")],
        unmatched_policy="generated_root",
    )

    rel = "generated/example_io/transcripts/tabularize.md"
    assert rel in composed.flat
    assert composed.flat[rel].abs_path == generated_doc.resolve()


def test_workflow_collection_object_is_retained_without_command_special_case(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "example_io"
    overview = write(
        generated / "01_overview.md",
        workflow_front_matter() + "# Full Example Dataset\nOverview.\n",
    )

    composed = build_composed_manual(
        [ManualSource(generated, name="example_io", role="generated")],
        unmatched_policy="generated_root",
    )

    rel = "generated/example_io/01_overview.md"
    assert rel in composed.flat
    assert composed.flat[rel].abs_path == overview.resolve()
    assert composed.flat[rel].title == "Example I/O"
    workflow_views = [
        view for view in composed.views if view.object_id == "full_example_dataset"
    ]
    assert len(workflow_views) == 1
    assert workflow_views[0].object_type == "workflow"
    assert workflow_views[0].object_types == ("workflow", "command")
    assert "No authored anchor for workflow:full_example_dataset" in composed.diagnostics[0]


def test_view_order_controls_virtual_generated_sibling_order(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    write(
        authored
        / "04_modules"
        / "01_transcripts"
        / "05_commands"
        / "01_tabularize"
        / "01_quickstart.md",
        "# `transcripts tabularize` Quickstart\nRun it.\n",
    )
    write(
        generated / "transcripts" / "tabularize.md",
        command_front_matter()
        + "# Transcript Tabularization Example\nGenerated preview.\n",
    )
    write(
        generated / "transcripts" / "tabularize_appendix.md",
        command_front_matter(
            view="appendix",
            title="Transcript Tabularization Appendix",
            view_label="Appendix",
            view_order=60,
        )
        + "# Transcript Tabularization Appendix\nExtra detail.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=True,
    )

    command_paths = [
        path
        for path in composed.flat
        if path.startswith(
            "04_modules/01_transcripts/05_commands/01_tabularize/"
        )
    ]
    assert command_paths == [
        "04_modules/01_transcripts/05_commands/01_tabularize/01_quickstart.md",
        "04_modules/01_transcripts/05_commands/01_tabularize/05_example_io.md",
        "04_modules/01_transcripts/05_commands/01_tabularize/06_appendix.md",
    ]
    assert composed.flat[command_paths[-1]].title == "Appendix"


def test_path_module_aliases_anchor_generated_command_views(
    tmp_path: Path,
) -> None:
    authored = tmp_path / "manual"
    generated = tmp_path / "example_io"
    write(
        authored
        / "04_modules"
        / "03_complete_utterances"
        / "05_commands"
        / "01_files"
        / "01_quickstart.md",
        "# `cus files` Quickstart\nRun it.\n",
    )
    generated_doc = write(
        generated / "cus" / "files.md",
        command_front_matter(object_id="cus.files")
        + "# CU Files Example\nGenerated preview.\n",
    )

    composed = build_composed_manual(
        [
            ManualSource(authored, name="authored", role="authored"),
            ManualSource(generated, name="example_io", role="generated"),
        ],
        infer_from_paths=True,
        path_module_aliases={"complete_utterances": "cus"},
        unmatched_policy="generated_root",
    )

    rel = (
        "04_modules/03_complete_utterances/05_commands/"
        "01_files/05_example_io.md"
    )
    assert rel in composed.flat
    assert composed.flat[rel].abs_path == generated_doc.resolve()
    assert not any(path.startswith("generated/") for path in composed.flat)
    assert composed.diagnostics == ()


def test_duplicate_object_view_pairs_raise_deterministic_error(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "example_io"
    write(
        generated / "one.md",
        command_front_matter(object_id="demo.run")
        + "# First Example\nGenerated preview.\n",
    )
    write(
        generated / "nested" / "two.md",
        command_front_matter(object_id="demo.run")
        + "# Second Example\nGenerated preview.\n",
    )

    with pytest.raises(ManualCompositionError, match="Duplicate manual view"):
        build_composed_manual(
            [ManualSource(generated, name="example_io", role="generated")]
        )
