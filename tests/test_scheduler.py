import tempfile
import unittest
import zipfile
from pathlib import Path

from csv_utils import load_subject_hours
from scheduler import ScheduleGenerator


class SubjectLoaderRealDataTests(unittest.TestCase):
    def test_load_subject_hours_reads_school_timetable_csv(self):
        data = load_subject_hours("DARS_TAQSIMOT.csv")
        self.assertIn("Ingliz tili", data)
        self.assertIn("Matematika", data)
        self.assertGreater(data["Ingliz tili"], 0)
        self.assertGreater(data["Matematika"], 0)


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

    def test_load_subject_hours_accepts_excel_xlsx(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            xlsx_path = Path(tmp_dir) / "subjects.xlsx"
            with zipfile.ZipFile(xlsx_path, "w") as archive:
                archive.writestr(
                    "[Content_Types].xml",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
                      <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
                      <Default Extension=\"xml\" ContentType=\"application/xml\"/>
                      <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
                      <Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>
                      <Override PartName=\"/xl/sharedStrings.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml\"/>
                    </Types>
                    """,
                )
                archive.writestr(
                    "_rels/.rels",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
                      <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
                    </Relationships>
                    """,
                )
                archive.writestr(
                    "xl/workbook.xml",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
                      <sheets>
                        <sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/>
                      </sheets>
                    </workbook>
                    """,
                )
                archive.writestr(
                    "xl/_rels/workbook.xml.rels",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
                      <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>
                    </Relationships>
                    """,
                )
                archive.writestr(
                    "xl/sharedStrings.xml",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" count=\"4\" uniqueCount=\"4\">
                      <si><t>Matematika (Algebra)</t></si>
                      <si><t>4</t></si>
                      <si><t>Ingliz tili</t></si>
                      <si><t>3</t></si>
                    </sst>
                    """,
                )
                archive.writestr(
                    "xl/worksheets/sheet1.xml",
                    """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
                    <worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">
                      <sheetData>
                        <row r=\"1\">
                          <c r=\"A1\" t=\"s\"><v>0</v></c>
                          <c r=\"B1\" t=\"s\"><v>1</v></c>
                        </row>
                        <row r=\"2\">
                          <c r=\"A2\" t=\"s\"><v>2</v></c>
                          <c r=\"B2\" t=\"s\"><v>3</v></c>
                        </row>
                      </sheetData>
                    </worksheet>
                    """,
                )

            self.assertEqual(
                load_subject_hours(str(xlsx_path)),
                {
                    "Matematika (Algebra)": 4,
                    "Ingliz tili": 3,
                },
            )

    def test_load_subject_hours_accepts_wide_excel_schedule_rows(self):
        rows = [
            ["#", "O'qituvchi", "Fan\\Sinf", "Xona", "1A", "1B", "1", "2R", "2", "3", "3R", "4", "5", "6", "7", "8", "9", "10", "11"],
            ["1", "Abdurasulov Abduvohid", "Ona tili", "", "", "", "", "", "", "", "", "", "", "5", "", "5", "5", "5", "5"],
            ["2", "Boymurodova Feruza", "Ona tili", "", "", "", "2", "", "", "2", "", "5", "", "4.5", "", "", "", "", ""],
            ["3", "Yuldasheva Dilfuza", "Rus tili", "", "", "", "", "", "", "", "", "", "", "4", "3", "3", "3", "3", "3"],
        ]
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(suffix=".csv")
            with open(fd, "w", encoding="cp1251", newline="") as csv_file:
                import csv
                writer = csv.writer(csv_file)
                writer.writerows(rows)
            self.assertEqual(
                load_subject_hours(temp_path),
                {"Ona tili": 25, "Rus tili": 19},
            )
        finally:
            if temp_path:
                import os
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    unittest.main()
