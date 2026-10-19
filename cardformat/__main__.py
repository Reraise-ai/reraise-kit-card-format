"""python -m cardformat [--strict] CARD.md ...  -> one line per finding; exit 1 if any card has errors."""
import sys

from . import CardError, normalize, parse, read_card, validate


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in args
    paths = [a for a in args if a != "--strict"]
    if not paths:
        print(__doc__.strip())
        return 2
    bad = 0
    for p in paths:
        try:
            if strict:
                with open(p, encoding="utf-8") as f:
                    fields, _ = parse(f.read())
                errors, notes = validate(fields, strict=True), []
            else:
                r = read_card(p)
                errors, notes = r["errors"], r["notes"]
        except (OSError, UnicodeDecodeError, CardError) as e:
            errors, notes = [str(e)], []
        for level, text in notes:
            print("%s %s: %s" % (level.upper(), p, text))
        for e in errors:
            print("ERROR %s: %s" % (p, e))
        if errors:
            bad += 1
        else:
            print("OK %s" % p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
