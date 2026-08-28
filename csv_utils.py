from __future__ import annotations

import csv
from typing import Dict, Iterable, List, Sequence


def load_subject_hours(csv_path: str) -> Dict[str, int]:
    subjects: Dict[str, int] = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for line_number, row in enumerate(reader, start=1):
            if not row:
                continue
            if len(row) < 2:
                raise ValueError(f"{line_number}-qatorda format noto'g'ri. Kutilgan: Fan nomi,Soatlar soni")
            name = row[0].strip()
            if not name:
                raise ValueError(f"{line_number}-qatorda fan nomi bo'sh.")
            try:
                hours = int(str(row[1]).strip())
            except ValueError as exc:
                raise ValueError(f"{line_number}-qatorda soat soni butun son bo'lishi kerak.") from exc
            if hours <= 0:
                raise ValueError(f"{line_number}-qatorda soat soni 0 dan katta bo'lishi kerak.")
            subjects[name] = subjects.get(name, 0) + hours
    if not subjects:
        raise ValueError("CSV faylda fanlar topilmadi.")
    return subjects


def save_schedule_csv(output_path: str, days: Sequence[str], hour_major_rows: List[List[str]]) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Soat / Kun", *days])
        for idx, row in enumerate(hour_major_rows, start=1):
            writer.writerow([idx, *row])
