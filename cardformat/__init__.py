"""Card format v2: parse, read rule for legacy field names, validation against card-v2.schema.json."""
import datetime
import json
import os
import re

import jsonschema

__version__ = "0.1.0"

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "card-v2.schema.json")
with open(SCHEMA_PATH, encoding="utf-8") as _f:
    SCHEMA = json.load(_f)
_VALIDATOR = jsonschema.Draft7Validator(SCHEMA)

# canonical field -> legacy spellings that are read as that field (SPEC.md, "Read rule")
LEGACY = {
    "created_by": ("urheber", "author"),
    "source": ("quelle",),
    "layer": ("ebene",),
    "originSystem": ("herkunft_system",),
    "worlds": ("welten",),
    "edges": ("kanten",),
}
LEGACY_KEYS = {k for v in LEGACY.values() for k in v}
VALUE_MAP = {
    "created_by": {"mensch": "human"},
    "layer": {"belegt": "evidenced", "gesagt": "said", "erfahrung": "experience", "geglaubt": None},
    "training": {"ja": True, "nein": False},
}
UNCLEAR_AUTHOR = "agent:unbenannt"

_FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


class CardError(ValueError):
    pass


def parse(text):
    """-> (fields, body). One `key: value` per line, values as JSON; non-JSON values are kept as plain text."""
    m = _FRONT.match(text)
    if not m:
        raise CardError("no front matter (file must start with a '---' line)")
    fields = {}
    for line in m.group(1).split("\n"):  # only \n: splitlines() would also break at U+2028 inside a value
        line = line.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, raw = line.partition(":")
        if not sep or not key.strip():
            raise CardError("front matter line is not 'key: value': %r" % line[:80])
        raw = raw.strip()
        if key.strip() in fields:
            raise CardError("field %r appears twice in the header" % key.strip())
        try:
            fields[key.strip()] = json.loads(raw)
        except ValueError:
            fields[key.strip()] = raw  # shortcut: no YAML parser; legacy plain values stay text
    return fields, text[m.end():]


_LINE_BREAKS = {"\u0085": "\\u0085", "\u2028": "\\u2028", "\u2029": "\\u2029"}


def _value(v):
    out = json.dumps(v, ensure_ascii=False)
    for ch, esc in _LINE_BREAKS.items():
        out = out.replace(ch, esc)
    return out


def dump(fields, body=""):
    """Header values as JSON on one line each; characters other tools treat as line breaks are escaped."""
    bad = [k for k in fields if not isinstance(k, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k)]
    if bad:
        raise CardError("invalid field names: %s" % ", ".join(map(repr, bad)))
    head = "".join("%s: %s\n" % (k, _value(v)) for k, v in fields.items())
    text = "---\n" + head + "---\n" + body
    if parse(text)[0] != fields:
        raise CardError("header does not read back as written")
    return text


def _translate(field, value):
    table = VALUE_MAP.get(field, {})
    return table.get(value, value) if isinstance(value, str) or value is None else value


def normalize(fields):
    """Read rule. -> (canonical fields, notes). notes = [(level, text)], level 'info' or 'warn'. Input is not changed."""
    out = {k: v for k, v in fields.items() if k not in LEGACY_KEYS}
    notes = []
    if "training" in out:
        out["training"] = _translate("training", out["training"])
    for canon, olds in LEGACY.items():
        for old in olds:
            if old not in fields:
                continue
            val = _translate(canon, fields[old])
            if val is None:
                notes.append(("info", "%s=%r is a private stance, not a layer; not taken over" % (old, fields[old])))
                continue
            if canon not in out:
                out[canon] = val
                notes.append(("info", "legacy field %r read as %r" % (old, canon)))
            elif out[canon] != val:
                notes.append(("warn", "conflict: %s=%r but %s=%r; %r applies" % (canon, out[canon], old, fields[old], canon)))
    if "layer" in out and out["layer"] in VALUE_MAP["layer"]:
        val = VALUE_MAP["layer"][out["layer"]]
        if val is None:
            notes.append(("info", "layer=%r is a private stance, not taken over" % out.pop("layer")))
        else:
            out["layer"] = val
    if out.get("created_by") == UNCLEAR_AUTHOR:
        notes.append(("warn", "author unclear (created_by=%r)" % UNCLEAR_AUTHOR))
    return out, notes


def validate(fields, strict=False):
    """Errors of canonical fields against the schema. strict=True (for writing) also rejects legacy field names."""
    errors = []
    for k in ("date", "review_date"):
        v = fields.get(k)
        if isinstance(v, str) and re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", v):
            try:
                datetime.date.fromisoformat(v)
            except ValueError:
                errors.append("%s: %r is not a calendar date" % (k, v))
    for e in sorted(_VALIDATOR.iter_errors(fields), key=lambda e: list(e.path)):
        where = ".".join(str(p) for p in e.path)
        errors.append(("%s: %s" % (where, e.message)) if where else e.message)
    if strict:
        errors += ["legacy field %r must not be written; use %r" % (k, c)
                   for c, olds in LEGACY.items() for k in olds if k in fields]
    return errors


def check(text):
    """Read a card as a component would: parse, apply the read rule, validate v2 cards. -> dict."""
    fields, body = parse(text)
    canon, notes = normalize(fields)
    if canon.get("format") != 2:
        notes.append(("info", "not a v2 card (format=%r): read with the read rule only, not validated" % canon.get("format")))
        return {"fields": canon, "body": body, "errors": [], "notes": notes, "v2": False}
    return {"fields": canon, "body": body, "errors": validate(canon), "notes": notes, "v2": True}


def read_card(path):
    with open(path, encoding="utf-8") as f:
        return check(f.read())
