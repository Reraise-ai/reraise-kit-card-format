import io
import os
import unittest
from contextlib import redirect_stdout

import cardformat as cf
from cardformat.__main__ import main

HERE = os.path.join(os.path.dirname(__file__), "cards")


def card(name):
    return os.path.join(HERE, name)


def text(name, mode="r"):
    with open(card(name), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f:
        return f.read()


class ValidCards(unittest.TestCase):
    def test_topic(self):
        r = cf.read_card(card("valid-topic.md"))
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["notes"], [])
        self.assertIn("three months", r["body"])

    def test_decision(self):
        self.assertEqual(cf.read_card(card("valid-decision.md"))["errors"], [])

    def test_dump_roundtrip(self):
        fields, body = cf.parse(text("valid-decision.md"))
        self.assertEqual(cf.parse(cf.dump(fields, body)), (fields, body))

    def test_crlf(self):
        crlf = text("valid-topic.md").replace("\n", "\r\n")
        self.assertEqual(cf.check(crlf)["errors"], [])


class InvalidCards(unittest.TestCase):
    def test_decision_without_quote(self):
        errs = " | ".join(cf.read_card(card("invalid-decision-no-quote.md"))["errors"])
        self.assertIn("decided_quote", errs)
        self.assertIn("decided_ref", errs)

    def test_bad_fields(self):
        errs = " | ".join(cf.read_card(card("invalid-fields.md"))["errors"])
        for word in ("created_by", "date", "release", "source", "level"):
            self.assertIn(word, errs)

    def test_proposal_rules(self):
        base = {"format": 2, "id": "B-2026-10-05-1", "type": "proposal", "title": "t", "created_by": "agent:a",
                "date": "2026-10-05", "language": "en", "release": "private", "question": "q?"}
        self.assertTrue(cf.validate(base))  # proposed_by missing
        ok = dict(base, proposed_by="agent:a")
        self.assertEqual(cf.validate(ok), [])
        self.assertTrue(cf.validate(dict(ok, decided_by="human")))  # decided_by without quote and ref
        self.assertEqual(cf.validate(dict(ok, decided_by="human", decided_quote="Yes, A.", decided_ref="chat:s@t")), [])
        self.assertTrue(cf.validate(dict(ok, number=3)))

    def test_no_front_matter(self):
        with self.assertRaises(cf.CardError):
            cf.check("# just text\n")


class LegacyNames(unittest.TestCase):
    def test_german_fields_read_as_canonical(self):
        r = cf.read_card(card("legacy-german.md"))
        self.assertEqual(r["errors"], [])
        f = r["fields"]
        self.assertEqual((f["created_by"], f["source"], f["layer"], f["training"]),
                         ("human", "C:/archiv/rechnung.pdf", "evidenced", False))
        self.assertNotIn("urheber", f)
        self.assertEqual({lvl for lvl, _ in r["notes"]}, {"info"})

    def test_file_is_never_rewritten(self):
        before = text("legacy-german.md", "rb")
        cf.read_card(card("legacy-german.md"))
        self.assertEqual(text("legacy-german.md", "rb"), before)

    def test_author_from_decision_loop(self):
        f, notes = cf.normalize({"author": "human"})
        self.assertEqual(f, {"created_by": "human"})

    def test_strict_rejects_legacy_on_write(self):
        fields, _ = cf.parse(text("legacy-german.md"))
        errs = " | ".join(cf.validate(fields, strict=True))
        self.assertIn("'urheber'", errs)
        self.assertIn("'quelle'", errs)

    def test_old_format_only_read(self):
        r = cf.read_card(card("old-format.md"))
        self.assertFalse(r["v2"])
        self.assertEqual(r["errors"], [])
        self.assertNotIn("layer", r["fields"])
        texts = " | ".join(t for _, t in r["notes"])
        self.assertIn("private stance", texts)
        self.assertIn("author unclear", texts)


class Conflict(unittest.TestCase):
    def test_canonical_wins_and_is_reported(self):
        r = cf.read_card(card("conflict.md"))
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["fields"]["created_by"], "agent:keeper")
        self.assertEqual([lvl for lvl, _ in r["notes"]], ["warn"])
        self.assertIn("conflict", r["notes"][0][1])

    def test_same_value_is_no_conflict(self):
        f, notes = cf.normalize({"created_by": "human", "urheber": "mensch"})
        self.assertEqual((f, notes), ({"created_by": "human"}, []))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = main(list(args))
        return rc, out.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(card("valid-topic.md"), card("conflict.md"))[0], 0)
        rc, out = self.run_cli(card("valid-topic.md"), card("invalid-fields.md"))
        self.assertEqual(rc, 1)
        self.assertIn("ERROR", out)
        self.assertEqual(self.run_cli("--strict", card("legacy-german.md"))[0], 1)
        self.assertEqual(self.run_cli()[0], 2)


if __name__ == "__main__":
    unittest.main()
