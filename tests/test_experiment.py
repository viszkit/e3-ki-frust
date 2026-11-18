from __future__ import annotations

import unittest

from experiment import CONDITIONS, RIDDLES, aid_is_available, is_correct


class ExperimentTests(unittest.TestCase):
    def test_study_material_has_eight_unique_riddles(self) -> None:
        self.assertEqual(len(RIDDLES), 8)
        self.assertEqual([riddle.number for riddle in RIDDLES], list(range(1, 9)))
        for riddle in RIDDLES:
            self.assertEqual(len(riddle.hints), 3)
            self.assertEqual(len(riddle.entities), 4)
            self.assertEqual(len(riddle.targets), 4)
            self.assertEqual(len(riddle.solution), 4)
            self.assertEqual({entity for entity, _ in riddle.solution}, set(riddle.entities))
            self.assertEqual({target for _, target in riddle.solution}, set(riddle.targets))
            self.assertEqual(len(riddle.options), 4)
            self.assertIn(riddle.correct_option, range(len(riddle.options)))

    def test_aid_only_exists_for_first_block(self) -> None:
        for condition in CONDITIONS:
            self.assertFalse(aid_is_available(condition, 5))
        self.assertFalse(aid_is_available("keine_hilfe", 1))
        self.assertTrue(aid_is_available("statische_hilfe", 4))
        self.assertTrue(aid_is_available("ki_chat", 1))

    def test_correctness_uses_selected_option(self) -> None:
        riddle = RIDDLES[0]
        self.assertTrue(is_correct(riddle, riddle.correct_option))
        self.assertFalse(is_correct(riddle, (riddle.correct_option + 1) % len(riddle.options)))


if __name__ == "__main__":
    unittest.main()
