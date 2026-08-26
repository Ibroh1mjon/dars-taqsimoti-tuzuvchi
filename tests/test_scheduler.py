import unittest

from scheduler import ScheduleGenerator


class ScheduleGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.subjects = {
            "Matematika (Algebra)": 4,
            "Matematika (Geometriya)": 4,
            "Ingliz tili": 3,
            "Fizika": 3,
            "Kimyo": 2,
            "Tarix": 2,
        }

    def _count_subject(self, schedule, subject):
        return sum(1 for day in schedule for slot in day if slot == subject)

    def _count_non_overlapping_pairs(self, schedule, subject):
        total_pairs = 0
        for day in schedule:
            idx = 0
            while idx < len(day) - 1:
                if day[idx] == subject and day[idx + 1] == subject:
                    total_pairs += 1
                    idx += 2
                else:
                    idx += 1
        return total_pairs

    def test_generate_preserves_hour_counts(self):
        generator = ScheduleGenerator(self.subjects)
        schedule = generator.generate(random_seed=42)

        self.assertEqual(len(schedule), 5)
        self.assertTrue(all(len(day) == 6 for day in schedule))
        for subject, expected_hours in self.subjects.items():
            self.assertEqual(self._count_subject(schedule, subject), expected_hours)

    def test_priority_subjects_have_required_double_blocks(self):
        generator = ScheduleGenerator(self.subjects)
        schedule = generator.generate(random_seed=7)

        for subject, hours in self.subjects.items():
            if generator.is_priority_subject(subject):
                required_pairs = hours // 2
                self.assertGreaterEqual(self._count_non_overlapping_pairs(schedule, subject), required_pairs)

    def test_regeneration_can_produce_different_layout(self):
        generator = ScheduleGenerator(self.subjects)
        first = generator.generate(random_seed=1)
        first_signature = generator.schedule_signature(first)
        second = generator.generate(exclude_signatures={first_signature}, random_seed=2)
        self.assertNotEqual(first_signature, generator.schedule_signature(second))


if __name__ == "__main__":
    unittest.main()
