# reraise-kit-card-format

The common card format (version 2) for knowledge and decisions, with a small checker.

A card is a Markdown file with a short header of fields. This repository contains:

- [`SPEC.md`](SPEC.md): what a card looks like, which fields are required, and how older field names are read.
- [`cardformat/card-v2.schema.json`](cardformat/card-v2.schema.json): the same rules as JSON Schema.
- `cardformat`: a Python package and command that check cards.

## Install

Needs Python 3.9 or newer.

```
pip install .
```

## Use

Check one or more cards:

```
cardformat path/to/card.md other-card.md
```

Each card gets one line: `OK`, `ERROR` (breaks a rule), `WARN` (for example two different authors on one card)
or `INFO` (for example an older field name was read). The exit code is 1 if any card has an error.

`cardformat --strict card.md` checks a card before it is written: older field names are then errors.

From Python:

```python
import cardformat
result = cardformat.read_card("card.md")   # fields (canonical names), body, errors, notes
errors = cardformat.validate(fields, strict=True)
text = cardformat.dump(fields, body)
```

Reading never changes a file.

## Tests

```
python -m unittest discover -s tests
```

## License

Apache-2.0, see [LICENSE](LICENSE).
