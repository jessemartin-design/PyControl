import unittest

from mir.parser import infer_verb, parse_line, resolve_value


class ParseLineTests(unittest.TestCase):
    def test_exact_goto(self):
        parsed = parse_line("GoToPosition Station2")
        self.assertEqual(parsed.verb, "GoToPosition")
        self.assertEqual(parsed.kind, "exact")
        self.assertEqual(parsed.argument, "Station2")
        self.assertFalse(parsed.needs_correction)

    def test_exact_run(self):
        parsed = parse_line("RunMission Charge")
        self.assertEqual(parsed.verb, "RunMission")
        self.assertEqual(parsed.kind, "exact")
        self.assertEqual(parsed.argument, "Charge")

    def test_quoted_name_with_space(self):
        parsed = parse_line('GoToPosition "Charging Station"')
        self.assertEqual(parsed.argument, "Charging Station")

    def test_unquoted_multiword_argument(self):
        parsed = parse_line("RunMission Station 2")
        self.assertEqual(parsed.argument, "Station 2")

    def test_goto_typo_offers_correction(self):
        parsed = parse_line("GoTo Station2")
        self.assertEqual(parsed.verb, "GoToPosition")
        self.assertTrue(parsed.needs_correction)
        self.assertEqual(parsed.argument, "Station2")
        self.assertEqual(parsed.catalog, "positions")

    def test_run_typo_offers_correction(self):
        parsed = parse_line("Run Charge")
        self.assertEqual(parsed.verb, "RunMission")
        self.assertTrue(parsed.needs_correction)
        self.assertEqual(parsed.argument, "Charge")
        self.assertEqual(parsed.catalog, "missions")

    def test_go_to_phrase(self):
        parsed = parse_line("go to Station2")
        self.assertEqual(parsed.verb, "GoToPosition")
        self.assertTrue(parsed.needs_correction)
        self.assertEqual(parsed.argument, "Station2")

    def test_list_positions_phrase(self):
        parsed = parse_line("list positions")
        self.assertEqual(parsed.verb, "ListPositions")
        self.assertIsNone(parsed.argument)

    def test_unknown_command(self):
        parsed = parse_line("dance")
        self.assertIsNone(parsed.verb)
        self.assertEqual(parsed.kind, "none")

    def test_list_alone_is_ambiguous(self):
        parsed = parse_line("list")
        self.assertIsNone(parsed.verb)
        self.assertIn("ListPositions", parsed.alternatives)
        self.assertIn("ListMissions", parsed.alternatives)


class InferVerbTests(unittest.TestCase):
    def test_prefix_gotopos(self):
        verb, kind, _, _ = infer_verb("GoToPos")
        self.assertEqual(verb, "GoToPosition")
        self.assertIn(kind, {"prefix", "alias", "fuzzy"})

    def test_status_alias(self):
        verb, kind, _, _ = infer_verb("stat")
        self.assertEqual(verb, "Status")
        self.assertNotEqual(kind, "none")


class ResolveValueTests(unittest.TestCase):
    names = ["Station1", "Station2", "Charge", "Home"]

    def test_exact_case_insensitive(self):
        match, suggestions = resolve_value("station2", self.names)
        self.assertEqual(match, "Station2")
        self.assertEqual(suggestions, [])

    def test_unique_prefix(self):
        match, _ = resolve_value("Ho", self.names)
        self.assertEqual(match, "Home")

    def test_typo_suggestions_only_from_given_catalog(self):
        match, suggestions = resolve_value("Staton2", self.names)
        self.assertIsNone(match)
        self.assertIn("Station2", suggestions)
        self.assertNotIn("Charge", suggestions)  # much farther than Station*


if __name__ == "__main__":
    unittest.main()
