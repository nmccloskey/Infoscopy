from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from psair.core.logger import logger


# -------------------------
# MetadataField
# -------------------------


@dataclass(frozen=True)
class MetadataField:
    """
    A single path-parsing metadata field.

    The user-facing config key remains `tiers` for backward compatibility:

      tiers:
        site: [AC, BU, TU]
        test: [Pre, Post, Maint]
        study_id: "(AC|BU|TU)\\d+"

    Interpretation:
      - list[str] -> literal values metadata field
      - str       -> regex metadata field
    """

    name: str
    kind: str
    pattern: re.Pattern
    values: List[str]
    regex: Optional[str] = None

    def match(
        self,
        text: str,
        *,
        return_none: bool = False,
        return_name: bool = False,
        must_match: bool = False,
    ) -> Optional[str]:
        m = self.pattern.search(text)
        if m:
            return m.group(0)

        if must_match:
            logger.warning(f"No match for metadata field '{self.name}' in text: {text!r}")

        if return_none:
            return None
        return self.name if return_name else ""

    def match_path_parts(
        self,
        parts: List[str],
        *,
        return_none: bool = False,
        return_name: bool = False,
        must_match: bool = False,
        source: str = "",
    ) -> Optional[str]:
        """
        Match ordered relative path parts, preferring earlier folders over the
        filename. If multiple distinct values are found, the first path-ordered
        match wins and a warning is logged.
        """
        if self.kind == "default":
            parts = parts[-1:]

        matches: List[str] = []
        for part in parts:
            for match in self.pattern.finditer(part):
                value = match.group(0)
                if value:
                    matches.append(value)

        if matches:
            first = matches[0]
            distinct = list(dict.fromkeys(matches))
            if len(distinct) > 1:
                location = source or "/".join(parts)
                logger.warning(
                    f"Multiple distinct matches for metadata field '{self.name}' "
                    f"in relative path {location!r}: {distinct}. Using {first!r}."
                )
            return first

        if must_match:
            location = source or "/".join(parts)
            logger.warning(
                f"No match for metadata field '{self.name}' in relative path: {location!r}"
            )

        if return_none:
            return None
        return self.name if return_name else ""


# -------------------------
# MetadataManager
# -------------------------


class MetadataManager:
    """
    Parse metadata field definitions from config into MetadataField objects and
    provide:
      - ordered metadata matching
      - metadata field name access in config order

    Metadata is extracted from relative paths under `input_dir`, scanning folder
    names before the filename. The config key is still `tiers` so existing user
    configuration files keep working.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        *,
        name_transform: Optional[Callable[[str], str]] = None,
    ):
        self._name_transform = name_transform or (lambda s: s)
        self.input_dir = self._extract_input_dir(config)

        self.metadata_fields: Dict[str, MetadataField] = {}
        self.tiers = self.metadata_fields
        self.order: List[str] = []

        self._init_from_config(config)

    # ---- init ----

    def _init_from_config(self, config: Any) -> None:
        config_dict = self._extract_config_dict(config)
        raw_fields = config_dict.get("tiers", None)

        if not isinstance(raw_fields, dict) or not raw_fields:
            logger.warning(
                "Metadata field config missing/invalid - defaulting to single "
                "'file_name' field matching full filename stem before '.cha'."
            )
            self.metadata_fields = self._default_metadata_fields()
            self.tiers = self.metadata_fields
            self.order = list(self.metadata_fields.keys())
            return

        self.metadata_fields = self._read_metadata_fields(raw_fields)
        self.tiers = self.metadata_fields
        self.order = list(self.metadata_fields.keys())

        logger.info(
            f"Initialized MetadataManager with {len(self.metadata_fields)} metadata fields."
        )
        logger.info(f"Metadata field order: {self.order}")

    def _extract_config_dict(self, config: Any) -> Dict[str, Any]:
        if isinstance(config, dict):
            return config
        maybe_config = getattr(config, "config", None)
        return maybe_config if isinstance(maybe_config, dict) else {}

    def _extract_input_dir(self, config: Any) -> Optional[Path]:
        input_dir = None
        if isinstance(config, dict):
            input_dir = config.get("input_dir")
        else:
            input_dir = getattr(config, "input_dir", None)
            if input_dir is None:
                maybe_config = getattr(config, "config", None)
                if isinstance(maybe_config, dict):
                    input_dir = maybe_config.get("input_dir")

        if not input_dir:
            return None

        return Path(input_dir).expanduser().resolve()

    def _default_metadata_fields(self) -> Dict[str, MetadataField]:
        name = "file_name"
        regex = r".*(?=\.cha)"
        pat = re.compile(regex)
        field = MetadataField(
            name=name,
            kind="default",
            pattern=pat,
            values=[],
            regex=regex,
        )
        logger.info(f"Created default metadata field '{name}' with regex={regex!r}")
        return {name: field}

    def _read_metadata_fields(self, raw_fields: Dict[str, Any]) -> Dict[str, MetadataField]:
        fields: Dict[str, MetadataField] = {}

        for raw_name, spec in raw_fields.items():
            name = self._name_transform(raw_name)

            if isinstance(spec, str):
                field = self._build_regex_field(name=name, regex=spec)
            elif isinstance(spec, list):
                field = self._build_values_field(name=name, values=spec)
            else:
                raise TypeError(
                    f"Metadata field '{raw_name}' must be either a regex string or "
                    f"a list[str] of literal values. Got: {type(spec).__name__}"
                )

            fields[name] = field

        if not fields:
            logger.warning(
                "No metadata fields constructed (unexpected) - defaulting to "
                "'file_name' field."
            )
            return self._default_metadata_fields()

        return fields

    def _build_regex_field(self, *, name: str, regex: str) -> MetadataField:
        if not regex.strip():
            raise ValueError(f"Metadata field '{name}': regex string must be non-empty.")

        try:
            pat = re.compile(regex)
        except re.error as e:
            raise ValueError(
                f"Metadata field '{name}': invalid regex {regex!r}: {e}"
            ) from e

        logger.info(f"Created metadata field '{name}' from regex={regex!r}")
        return MetadataField(
            name=name,
            kind="regex",
            pattern=pat,
            values=[],
            regex=regex,
        )

    def _build_values_field(self, *, name: str, values: List[Any]) -> MetadataField:
        if not all(isinstance(v, str) for v in values):
            raise ValueError(f"Metadata field '{name}': values field must be a list[str].")

        if not values:
            logger.warning(
                f"Metadata field '{name}' has empty values list - it will never match anything."
            )
            search_str = r"(?!x)x"
            pat = re.compile(search_str)
        else:
            escaped = [re.escape(v) for v in values]
            search_str = "(?:" + "|".join(escaped) + ")"
            pat = re.compile(search_str)

        logger.info(
            f"Created metadata field '{name}' from {len(values)} literal values; "
            f"regex={search_str!r}"
        )
        return MetadataField(
            name=name,
            kind="values",
            pattern=pat,
            values=list(values),
            regex=None,
        )

    # ---- public API ----

    def get_metadata_field_names(self) -> List[str]:
        return list(self.order)

    def match_metadata(
        self,
        path: str | Path,
        *,
        return_none: bool = False,
        return_name: bool = False,
        must_match: bool = False,
    ) -> Dict[str, Optional[str]]:
        parts = self._get_relative_parts(path)
        source = self._format_source(path, parts)
        return {
            field_name: self.metadata_fields[field_name].match_path_parts(
                parts,
                return_none=return_none,
                return_name=return_name,
                must_match=must_match,
                source=source,
            )
            for field_name in self.order
        }

    def _get_relative_parts(self, path: str | Path) -> List[str]:
        path_obj = Path(path)
        relative_path = path_obj

        if self.input_dir is not None:
            try:
                relative_path = path_obj.resolve().relative_to(self.input_dir)
            except ValueError:
                if path_obj.is_absolute():
                    relative_path = Path(path_obj.name)

        parts = [part for part in relative_path.parts if part not in ("", ".")]
        return parts or [path_obj.name]

    def _format_source(self, path: str | Path, parts: List[str]) -> str:
        if self.input_dir is None:
            return str(path)
        return str(Path(*parts)) if parts else str(path)

    # ---- backward-compatible aliases ----

    def get_tier_names(self) -> List[str]:
        return self.get_metadata_field_names()

    def match_tiers(
        self,
        text: str | Path,
        *,
        return_none: bool = False,
        return_name: bool = False,
        must_match: bool = False,
    ) -> Dict[str, Optional[str]]:
        return self.match_metadata(
            text,
            return_none=return_none,
            return_name=return_name,
            must_match=must_match,
        )

    def make_metadata_field(self, name: str) -> MetadataField:
        return MetadataField(
            name=self._name_transform(name),
            kind="spreadsheet",
            pattern=re.compile(r"(?!x)x"),
            values=[],
            regex=None,
        )

    def make_tier(self, name: str) -> MetadataField:
        return self.make_metadata_field(name)

    def get_partition_tiers(self) -> List[str]:
        return self.get_metadata_field_names()


Tier = MetadataField
TierManager = MetadataManager
