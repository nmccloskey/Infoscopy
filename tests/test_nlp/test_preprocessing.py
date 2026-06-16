from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture()
def preprocessing_module(monkeypatch: pytest.MonkeyPatch):
    fake_pandas = types.ModuleType("pandas")
    fake_pandas.read_csv = lambda path: None
    fake_pandas.read_excel = lambda path: None
    fake_docx2txt = types.ModuleType("docx2txt")
    fake_docx2txt.process = lambda path: "DOCX text"
    fake_output_manager_module = types.ModuleType("psair.etl.OutputManager")
    fake_output_manager_module.OutputManager = type(
        "OutputManager",
        (),
        {"config": {}, "__init__": lambda self: None},
    )

    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)
    monkeypatch.setitem(sys.modules, "docx2txt", fake_docx2txt)
    monkeypatch.setitem(sys.modules, "psair.etl.OutputManager", fake_output_manager_module)
    sys.modules.pop("psair.nlp.preprocessing", None)
    module = importlib.import_module("psair.nlp.preprocessing")
    yield module
    sys.modules.pop("psair.nlp.preprocessing", None)


class FakeToken:
    def __init__(self, lemma: str, *, is_alpha: bool = True, is_stop: bool = False) -> None:
        self.lemma_ = lemma
        self.is_alpha = is_alpha
        self.is_stop = is_stop


class FakeSent:
    def __init__(self, text: str, tokens: list[FakeToken]) -> None:
        self.text = text
        self._tokens = tokens

    def __iter__(self):
        return iter(self._tokens)


class FakeDoc:
    def __init__(self, text: str, sents: list[FakeSent]) -> None:
        self.text = text
        self.sents = sents
        self._tokens = [token for sent in sents for token in sent]

    def __iter__(self):
        return iter(self._tokens)


def test_process_sents_builds_sentence_data_and_text(preprocessing_module) -> None:
    doc = FakeDoc(
        "Cats run. Dogs nap.",
        [
            FakeSent("Cats run.", [FakeToken("cat"), FakeToken("run")]),
            FakeSent("Dogs nap.", [FakeToken("dog"), FakeToken("nap", is_stop=True)]),
        ],
    )
    sample = {"doc_id": 7, "doc_label": "sample.txt", "site": "AC", "text": doc.text}

    sent_data, sent_text, cleaned_doc, semantic_doc, cleaned_phon_doc = (
        preprocessing_module.process_sents(doc, sample)
    )

    assert sent_data == [
        {"doc_id": 7, "sent_id": 1, "doc_label": "sample.txt", "site": "AC"},
        {"doc_id": 7, "sent_id": 2, "doc_label": "sample.txt", "site": "AC"},
    ]
    assert sent_text[0]["raw"] == "Cats run."
    assert sent_text[0]["semantic"] == "cat run"
    assert cleaned_doc == "Cats run. Dogs nap."
    assert semantic_doc == "cat run dog"
    assert cleaned_phon_doc == ""


def test_process_sents_adds_phonological_text_for_cha(preprocessing_module) -> None:
    doc = FakeDoc(
        "birbday [: birthday].",
        [FakeSent("birbday [: birthday].", [FakeToken("birthday")])],
    )

    sent_data, sent_text, cleaned_doc, _semantic_doc, cleaned_phon_doc = (
        preprocessing_module.process_sents(
            doc,
            {"doc_id": 1, "doc_label": "sample.cha", "text": doc.text},
            is_cha=True,
        )
    )

    assert sent_data == [{"doc_id": 1, "sent_id": 1, "doc_label": "sample.cha"}]
    assert sent_text[0]["cleaned"] == "birthday."
    assert sent_text[0]["cleaned_phon"] == "birbday."
    assert cleaned_doc == "birthday."
    assert cleaned_phon_doc == "birbday."


def test_process_sample_data_sentence_level(preprocessing_module, monkeypatch: pytest.MonkeyPatch) -> None:
    doc = FakeDoc(
        "Cats run.",
        [FakeSent("Cats run.", [FakeToken("cat"), FakeToken("run")])],
    )

    class FakeNLPModel:
        def get_nlp(self):
            return lambda text: doc

    class FakeSection:
        def init_results_dict(self):
            return {
                "sample_data_doc": {},
                "sample_text_doc": {},
                "sample_data_sent": [],
                "sample_text_sent": [],
            }

    pm = types.SimpleNamespace(
        sentence_level=True,
        sections={"preprocessing": FakeSection()},
    )
    monkeypatch.setattr(preprocessing_module, "NLPModel", FakeNLPModel)

    results = preprocessing_module.process_sample_data(
        pm,
        {"doc_id": 3, "doc_label": "sample.txt", "text": "Cats run.", "site": "AC"},
    )

    assert results["sample_data_doc"] == {
        "doc_id": 3,
        "doc_label": "sample.txt",
        "site": "AC",
    }
    assert results["sample_text_doc"]["cleaned"] == "Cats run."
    assert results["sample_text_sent"][0]["semantic"] == "cat run"


def test_process_sample_data_returns_empty_dict_for_invalid_text(preprocessing_module) -> None:
    pm = types.SimpleNamespace(sections={}, sentence_level=False)

    assert preprocessing_module.process_sample_data(
        pm,
        {"doc_id": 1, "doc_label": "bad.txt", "text": None},
    ) == {}


def test_read_text_and_docx_files_scrub_content(preprocessing_module, tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Alpha\n\nBeta", encoding="utf-8")
    docx_path = tmp_path / "sample.docx"

    preprocessing_module.dx.process = lambda path: "Gamma\r\nDelta"

    assert preprocessing_module.read_text_file(str(text_path)) == "Alpha<p>Beta"
    assert preprocessing_module.read_docx_file(str(docx_path)) == "Gamma<p>Delta"


def test_read_chat_file_uses_output_manager_exclusions(
    preprocessing_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeOutputManager:
        config = {"exclude_speakers": ["INV", "MOT"]}

    def fake_get_text_from_cha(path: str, exclude_speakers: list[str]) -> str:
        captured["path"] = path
        captured["exclude_speakers"] = exclude_speakers
        return "child text"

    monkeypatch.setattr(preprocessing_module, "_get_output_manager", FakeOutputManager)
    monkeypatch.setattr(preprocessing_module, "get_text_from_cha", fake_get_text_from_cha)

    assert preprocessing_module.read_chat_file("sample.cha") == "child text"
    assert captured == {
        "path": "sample.cha",
        "exclude_speakers": ["INV", "MOT"],
    }


def test_prep_samples_handles_unsupported_and_text_files(
    preprocessing_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeMetadataManager:
        def match_metadata(self, file_path: str | Path) -> dict[str, str]:
            assert file_path == text_path
            return {"site": "AC"}

    om = types.SimpleNamespace(mm=FakeMetadataManager())
    text_path = tmp_path / "sample_AC.txt"
    monkeypatch.setattr(preprocessing_module, "read_text_file", lambda path: "Text body")

    assert preprocessing_module.prep_samples("sample.pdf", text_path, 1, om) == []
    assert preprocessing_module.prep_samples("sample_AC.txt", text_path, 4, om) == [
        {
            "doc_id": 4,
            "doc_label": "sample_AC.txt",
            "text": "Text body",
            "site": "AC",
        }
    ]


class FakeVector:
    def __init__(self, values: list[object]) -> None:
        self.values = list(values)

    def astype(self, type_: type) -> "FakeVector":
        return FakeVector([type_(value) for value in self.values])

    def __add__(self, other: object) -> "FakeVector":
        if isinstance(other, FakeVector):
            return FakeVector([str(a) + str(b) for a, b in zip(self.values, other.values)])
        return FakeVector([str(value) + str(other) for value in self.values])

    def __radd__(self, other: object) -> "FakeVector":
        return FakeVector([str(other) + str(value) for value in self.values])

    def __iter__(self):
        return iter(self.values)


class FakeColumnFrame:
    def __init__(self, rows: list[dict[str, object]], columns: list[str]) -> None:
        self.rows = rows
        self.columns = columns

    def astype(self, type_: type) -> "FakeColumnFrame":
        return self

    def agg(self, func, axis: int) -> FakeVector:
        assert axis == 1
        return FakeVector([
            func([str(row[column]) for column in self.columns])
            for row in self.rows
        ])


class FakeIndex(FakeVector):
    pass


class FakeDataFrame:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.columns = list(rows[0]) if rows else []
        self.index = FakeIndex(list(range(len(rows))))

    @property
    def empty(self) -> bool:
        return not self.rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, key):
        if isinstance(key, list):
            return FakeColumnFrame(self.rows, key)
        return FakeVector([row[key] for row in self.rows])

    def insert(self, loc: int, name: str, values) -> None:
        values_list = list(values)
        for row, value in zip(self.rows, values_list):
            row[name] = value
        self.columns.insert(loc, name)

    def dropna(self, subset: list[str]) -> "FakeDataFrame":
        self.rows = [
            row for row in self.rows
            if all(row.get(column) is not None for column in subset)
        ]
        return self

    def to_dict(self, orient: str) -> list[dict[str, object]]:
        assert orient == "records"
        return [dict(row) for row in self.rows]


def test_read_spreadsheet_builds_samples_and_registers_metadata_fields(
    preprocessing_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    df = FakeDataFrame(
        [
            {"text": "Alpha", "site": "AC", "visit": "Pre"},
            {"text": None, "site": "BU", "visit": "Post"},
        ]
    )
    monkeypatch.setattr(preprocessing_module.pd, "read_csv", lambda path: df)

    class FakeMetadataField:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeMetadataManager:
        def __init__(self) -> None:
            self.metadata_fields: dict[str, FakeMetadataField] = {}
            self.metadata_fields = self.metadata_fields

        def make_metadata_field(self, name: str) -> FakeMetadataField:
            return FakeMetadataField(name)

    om = types.SimpleNamespace(mm=FakeMetadataManager())

    samples = preprocessing_module.read_spreadsheet(
        tmp_path / "samples.csv",
        "samples.csv",
        10,
        om,
    )

    assert samples == [
        {
            "text": "Alpha",
            "site": "AC",
            "visit": "Pre",
            "doc_label": "samples.csv|AC|Pre|0",
            "doc_id": 10,
        }
    ]
    assert set(om.mm.metadata_fields) == {"site", "visit"}
