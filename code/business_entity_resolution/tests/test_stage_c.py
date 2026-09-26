import unittest

from business_entity_resolution.stage_c import assemble_candidates, cheap_blocking_keys, classify_truth_link, enforce_candidate_caps, family_rescue_queries, select_queries


class StageCSelectionTests(unittest.TestCase):
    def test_selection_covers_required_strata_and_prefers_miss(self):
        metadata = {}
        truth = {}
        candidates = {}
        index = 0
        for country in ("India", "US"):
            for singleton in (True, False):
                for _ in range(3):
                    entity_id = f"S1-{index}"
                    metadata[entity_id] = {"country": country, "singleton": singleton, "partition": "holdout"}
                    truth[entity_id] = set() if singleton else {f"S2-{index}"}
                    candidates[entity_id] = set(truth[entity_id])
                    index += 1
        truth["S1-3"] = {"S2-missed"}
        candidates["S1-3"] = set()
        chosen = select_queries(metadata, truth, candidates, 20260925, 10)
        self.assertEqual(len(chosen), 10)
        self.assertIn("S1-3", chosen)
        self.assertEqual({(metadata[item]["country"], metadata[item]["singleton"]) for item in chosen}, {("India", True), ("India", False), ("US", True), ("US", False)})
        keys = cheap_blocking_keys("Northwind Trading Ltd", "17 Merchant Avenue")
        self.assertIn("at:merchant", keys)
        self.assertFalse(any(key.startswith("sh") for key in keys))

    def test_only_cross_family_evidence_rescues(self):
        consumers = {("US", "nt:northwind"): {"S1-q"}, ("US", "at:merchant"): {"S1-q"}}
        self.assertEqual(set(family_rescue_queries("US", {"nt:northwind", "at:merchant"}, consumers)), {"S1-q"})
        name_only = {("US", "nt:northwind"): {"S1-q"}, ("US", "np:nort"): {"S1-q"}, ("US", "ne:northwind"): {"S1-q"}}
        self.assertEqual(family_rescue_queries("US", {key for _, key in name_only}, name_only), {})
        address_only = {("US", "at:merchant"): {"S1-q"}, ("US", "ap:merc"): {"S1-q"}}
        self.assertEqual(family_rescue_queries("US", {key for _, key in address_only}, address_only), {})
        counts = {lookup: 501 for lookup in consumers}
        candidates, skipped = assemble_candidates({"S1-q": {}}, consumers, counts, {lookup: [] for lookup in consumers}, {"S1-q": {"S2-hit"}}, 500)
        self.assertEqual(candidates["S1-q"], {"S2-hit"})
        self.assertEqual(skipped, 2)

    def test_candidate_caps_name_the_query(self):
        with self.assertRaisesRegex(RuntimeError, "query=S1-q"):
            enforce_candidate_caps({"S1-q": {"a", "b"}}, {"S1-q": {"a", "b"}}, 10, 1)

    def test_truth_diagnostic_classifications(self):
        capped = classify_truth_link({"nt:name"}, {"nt:name": 501}, 500, 0, False)
        simhash = classify_truth_link(set(), {}, 500, 2, False)
        self.assertEqual(capped["classification"], "all_cheap_keys_capped")
        self.assertEqual(simhash["classification"], "simhash_only")


if __name__ == "__main__":
    unittest.main()
