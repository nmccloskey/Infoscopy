# NLP Model

## Purpose

`psair.nlp.NLPmodel.NLPModel` is a singleton manager for NLP resources. It keeps
spaCy imports optional, loads spaCy language models on demand, reuses loaded
pipelines, and provides small helpers for optional resources such as benepar and
CMUdict.

The class is intended to give PSAIR modules one shared place to request NLP
resources without repeatedly loading large models.

## Singleton behavior

Every call to `NLPModel()` returns the same instance:

```python
from psair.nlp.NLPmodel import NLPModel

a = NLPModel()
b = NLPModel()
assert a is b
```

The singleton stores:

- `_nlp_models`: loaded spaCy pipelines keyed by model name
- `_cmu_dict`: a cached CMUdict dictionary once loaded
- `_spacy`: the imported spaCy module once imported

This reduces repeated import and model-loading work in preprocessing,
visualization, and downstream analysis code.

## Optional imports

The base PSAIR install does not require spaCy, benepar, or NLTK. `NLPModel`
imports these packages only when a method needs them.

If an optional package is missing, the class raises an `ImportError` with a
message pointing the user toward the appropriate PSAIR extra.

Common install targets are:

```bash
pip install "psair[nlp]"
pip install "psair[nlp-full]"
```

## Loading a spaCy pipeline

Use `get_nlp()` or `load_nlp()` to load a spaCy model:

```python
from psair.nlp.NLPmodel import NLPModel

nlp = NLPModel().get_nlp("en_core_web_sm")
doc = nlp("The patient described the picture clearly.")
```

Defaults:

```python
get_nlp(
    model_name="en_core_web_sm",
    require_benepar=False,
    auto_download_model=True,
)
```

When `auto_download_model=True`, PSAIR checks whether the spaCy model can be
loaded. If not, it runs:

```bash
python -m spacy download <model_name>
```

Then it loads and caches the model with `spacy.load(model_name)`.

In environments where runtime downloads are not allowed, disable automatic
downloads:

```python
nlp = NLPModel().get_nlp(
    "en_core_web_sm",
    auto_download_model=False,
)
```

With this setting, a missing model fails through spaCy instead of attempting a
download.

## Reusing loaded models

Models are cached by name:

```python
manager = NLPModel()
nlp_small = manager.get_nlp("en_core_web_sm")
nlp_small_again = manager.get_nlp("en_core_web_sm")
```

The second call returns the already-loaded pipeline. A different model name gets
its own cache entry.

## Tokenizer access

Use `get_tokenizer()` when only tokenization is needed:

```python
tokenizer = NLPModel().get_tokenizer("en_core_web_sm")
tokens = tokenizer("Short text for tokenization.")
```

This still loads the underlying spaCy model if it is not already cached.

## Benepar support

Set `require_benepar=True` to ensure that the benepar component is available in
the spaCy pipeline:

```python
nlp = NLPModel().get_nlp(
    "en_core_web_sm",
    require_benepar=True,
)
```

The method:

1. Imports `benepar`.
2. Attempts to download `benepar_en3`.
3. Adds the `benepar` pipe with `{"model": "benepar_en3"}` if it is not already
   present.

Install benepar support with:

```bash
pip install "psair[nlp,nlp-parse]"
```

or:

```bash
pip install "psair[nlp-full]"
```

If benepar is installed but cannot be added to the pipeline, PSAIR raises a
`RuntimeError`.

## CMUdict support

Use `get_cmu_dict()` to load the NLTK CMU Pronouncing Dictionary:

```python
cmu = NLPModel().get_cmu_dict()
pronunciations = cmu.get("research")
```

The method imports NLTK and then imports `nltk.corpus.cmudict`. If the corpus is
missing, PSAIR attempts:

```python
nltk.download("cmudict")
```

The dictionary is cached after the first successful load.

Install this support with:

```bash
pip install "psair[nlp-phon]"
```

or:

```bash
pip install "psair[nlp-full]"
```

## Practical guidance

Use `NLPModel` instead of calling `spacy.load()` directly inside PSAIR modules.
That keeps model loading centralized, avoids repeated pipeline construction,
and preserves the optional-dependency boundary.

For reproducible production runs, install spaCy models, benepar models, and NLTK
corpora before running PSAIR. Automatic downloads are convenient for local
development, but explicit provisioning is easier to audit.
