from __future__ import annotations

from pathlib import Path

import pytest

from psair.metadata.metadata_fields import MetadataManager, TierManager


def test_default_metadata_field_matches_cha_filename_stem() -> None:
    manager = MetadataManager({})

    assert manager.get_metadata_field_names() == ["file_name"]
    assert manager.match_metadata("sample_001.cha") == {"file_name": "sample_001"}
    assert manager.match_metadata("sample_001.txt") == {"file_name": ""}
    assert manager.match_metadata("sample_001.txt", return_name=True) == {
        "file_name": "file_name"
    }


def test_values_and_regex_metadata_fields_match_in_config_order() -> None:
    manager = MetadataManager(
        {
            "tiers": {
                "site": ["AC", "BU"],
                "visit": r"(Pre|Post)\d?",
            }
        }
    )

    assert manager.get_metadata_field_names() == ["site", "visit"]
    assert manager.match_metadata("study_AC_Pre2.xlsx") == {
        "site": "AC",
        "visit": "Pre2",
    }


def test_metadata_match_can_return_none_for_missing_values() -> None:
    manager = MetadataManager({"tiers": {"site": ["AC"]}})

    assert manager.match_metadata("study_BU.xlsx") == {"site": ""}
    assert manager.match_metadata("study_BU.xlsx", return_none=True) == {"site": None}
    assert manager.match_metadata("study_BU.xlsx", return_name=True) == {"site": "site"}


def test_name_transform_is_applied_to_metadata_field_names() -> None:
    manager = MetadataManager(
        {"tiers": {"Study Site": ["AC"]}},
        name_transform=lambda value: value.lower().replace(" ", "_"),
    )

    assert manager.get_metadata_field_names() == ["study_site"]
    assert manager.match_metadata("AC_001.cha") == {"study_site": "AC"}


def test_empty_values_metadata_field_never_matches() -> None:
    manager = MetadataManager({"tiers": {"site": []}})

    assert manager.match_metadata("AC_001.cha", return_none=True) == {"site": None}


def test_invalid_metadata_field_specs_raise_clear_errors() -> None:
    with pytest.raises(TypeError, match="must be either"):
        MetadataManager({"tiers": {"bad": {"nested": "value"}}})

    with pytest.raises(ValueError, match="list\\[str\\]"):
        MetadataManager({"tiers": {"bad": ["AC", 12]}})

    with pytest.raises(ValueError, match="non-empty"):
        MetadataManager({"tiers": {"bad": "   "}})

    with pytest.raises(ValueError, match="invalid regex"):
        MetadataManager({"tiers": {"bad": "("}})


def test_metadata_matches_parent_directory_before_filename(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    file_path = input_dir / "pretx" / "par1.cha"

    manager = MetadataManager(
        {
            "input_dir": str(input_dir),
            "tiers": {
                "visit": ["pretx", "posttx"],
                "participant": r"par\d+",
            },
        }
    )

    assert manager.match_metadata(file_path) == {
        "visit": "pretx",
        "participant": "par1",
    }


def test_metadata_warns_on_multiple_distinct_matches_and_prefers_path_order(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    input_dir = tmp_path / "input"
    file_path = input_dir / "pretx" / "par1_posttx.cha"
    manager = MetadataManager(
        {
            "input_dir": str(input_dir),
            "tiers": {"visit": ["pretx", "posttx"]},
        }
    )

    result = manager.match_metadata(file_path)

    assert result == {"visit": "pretx"}
    assert "Multiple distinct matches for metadata field 'visit'" in caplog.text


def test_legacy_tier_manager_alias_still_works() -> None:
    manager = TierManager({"tiers": {"site": ["AC"]}})

    assert manager.get_tier_names() == ["site"]
    assert manager.match_tiers("AC_001.cha") == {"site": "AC"}
