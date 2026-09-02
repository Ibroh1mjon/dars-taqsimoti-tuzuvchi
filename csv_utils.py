from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import xml.etree.ElementTree as ET


def _read_text_file(file_path: str) -> str:
    raw = Path(file_path).read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")

    for encoding in ("utf-8-sig", "cp1251", "cp1252", "latin-1", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_csv_rows(file_path: str) -> List[List[str]]:
    text = _read_text_file(file_path)
    sample = text[:4096]
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        pass

    rows: List[List[str]] = []
    reader = csv.reader(text.splitlines(), delimiter=delimiter)
    for row in reader:
        rows.append([cell.strip() for cell in row])
    return rows


def _read_xlsx_rows(file_path: str) -> List[List[str]]:
    rows: List[List[str]] = []
    with zipfile.ZipFile(file_path) as workbook:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in shared_root.findall("a:si", ns):
                texts = [node.text or "" for node in si.findall(".//a:t", ns)]
                shared_strings.append("".join(texts))

        sheet_path = None
        if "xl/workbook.xml" in workbook.namelist():
            workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
            ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
            for sheet in workbook_root.findall("a:sheets/a:sheet", ns):
                rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                if rel_id:
                    rels_path = "xl/_rels/workbook.xml.rels"
                    if rels_path in workbook.namelist():
                        rels_root = ET.fromstring(workbook.read(rels_path))
                        rel_ns = {"a": "http://schemas.openxmlformats.org/package/2006/relationships"}
                        for rel in rels_root.findall("a:Relationship", rel_ns):
                            if rel.attrib.get("Id") == rel_id:
                                target = rel.attrib.get("Target", "").lstrip("/")
                                sheet_path = target if target.startswith("xl/") else "xl/" + target
                                break
                    if sheet_path is None:
                        sheet_path = "xl/worksheets/sheet1.xml"
                    break

        sheet_path = sheet_path or next((name for name in workbook.namelist() if name.startswith("xl/worksheets/") and name.endswith(".xml")), None)
        if not sheet_path:
            return rows

        sheet_root = ET.fromstring(workbook.read(sheet_path))
        ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for row in sheet_root.findall(".//a:sheetData/a:row", ns):
            values: List[str] = []
            for cell in row.findall("a:c", ns):
                reference = cell.attrib.get("r", "")
                column_match = re.match(r"[A-Za-z]+", reference)
                if column_match:
                    column_letters = column_match.group().upper()
                    column_index = 0
                    for letter in column_letters:
                        column_index = column_index * 26 + ord(letter) - ord("A") + 1
                    while len(values) < column_index - 1:
                        values.append("")
                cell_type = cell.attrib.get("t")
                value = ""
                if cell_type == "inlineStr":
                    text_node = cell.find("a:is/a:t", ns)
                    if text_node is not None:
                        value = text_node.text or ""
                elif cell_type == "s":
                    v_text = cell.find("a:v", ns)
                    if v_text is not None and v_text.text is not None:
                        index = int(v_text.text)
                        if 0 <= index < len(shared_strings):
                            value = shared_strings[index]
                else:
                    v_text = cell.find("a:v", ns)
                    if v_text is not None:
                        value = v_text.text or ""
                values.append(value.strip())
            if values:
                rows.append(values)
    return rows


def load_class_subject_hours(file_path: str) -> Dict[str, Dict[str, int]]:
    """Load class lesson allocations from the wide XLSX timetable export."""
    if Path(file_path).suffix.lower() != ".xlsx":
        raise ValueError("Faqat XLSX fayllarni yuklash mumkin.")

    rows = _read_xlsx_rows(file_path)
    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if any("o'qituvchi" in cell.lower() or "teacher" in cell.lower() for cell in row)
            and any("fan" in cell.lower() or "subject" in cell.lower() for cell in row)
        ),
        None,
    )
    if header_index is None:
        raise ValueError("XLSX faylda O'qituvchi va Fan ustunlari topilmadi.")

    header = rows[header_index]
    teacher_index = next(
        index for index, cell in enumerate(header) if "o'qituvchi" in cell.lower() or "teacher" in cell.lower()
    )
    subject_index = next(
        index for index, cell in enumerate(header) if "fan" in cell.lower() or "subject" in cell.lower()
    )
    class_indexes = {
        cell.strip(): index
        for index, cell in enumerate(header)
        if index > subject_index + 1 and cell.strip() and cell.strip().lower() not in {"xona", "room"}
    }
    if not class_indexes:
        raise ValueError("XLSX faylda sinflar ustunlari topilmadi.")

    totals: Dict[str, Dict[str, float]] = {class_name: {} for class_name in class_indexes}
    for row in rows[header_index + 1 :]:
        if len(row) <= max(teacher_index, subject_index):
            continue
        teacher = row[teacher_index].strip()
        subject = row[subject_index].strip()
        if not teacher or not subject:
            continue
        for class_name, column_index in class_indexes.items():
            if column_index >= len(row):
                continue
            hours = _coerce_numeric_hours(row[column_index])
            if hours is not None and hours > 0:
                label = f"{subject}\n{teacher}"
                totals[class_name][label] = totals[class_name].get(label, 0.0) + hours

    result: Dict[str, Dict[str, int]] = {
        class_name: {
            label: int(round(hours))
            for label, hours in values.items()
            if int(round(hours)) > 0
        }
        for class_name, values in totals.items()
        if values
    }
    if not result:
        raise ValueError("XLSX faylda sinflar uchun darslar topilmadi.")
    return result


def _coerce_numeric_hours(value: str) -> float | None:
    text = value.strip().replace(" ", "").replace(",", ".")
    if not text:
        return None
    if text.lower() in {"nan", "inf", "-inf"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _record_subject_hours(subjects: Dict[str, float], name: str, hours: float) -> None:
    normalized_name = name.strip()
    if not normalized_name:
        return
    if hours <= 0:
        return
    subjects[normalized_name] = subjects.get(normalized_name, 0.0) + hours


def load_subject_hours(csv_path: str) -> Dict[str, int]:
    path = Path(csv_path)
    if path.suffix.lower() == ".xlsx":
        rows = _read_xlsx_rows(str(path))
    else:
        rows = _read_csv_rows(str(path))

    subject_totals: Dict[str, float] = {}
    for line_number, row in enumerate(rows, start=1):
        if not row or not any(cell for cell in row):
            continue

        cells = [cell.strip() for cell in row]
        if not cells:
            continue

        first = cells[0].lower()
        if first.startswith("#") or "o'qituvchi" in first or "teacher" in first:
            continue

        # Real dataset shape: teacher timetable export with subject in column 3 and numeric lesson counts in later columns.
        if len(cells) >= 4 and cells[2] and not cells[0].lower().startswith("fan") and not cells[0].lower().startswith("subject"):
            subject_name = cells[2]
            numeric_total = 0.0
            seen_numeric = False
            for value in cells[3:]:
                numeric_value = _coerce_numeric_hours(value)
                if numeric_value is not None:
                    numeric_total += numeric_value
                    seen_numeric = True
            if seen_numeric:
                _record_subject_hours(subject_totals, subject_name, numeric_total)
                continue

        if len(cells) < 2:
            raise ValueError(f"{line_number}-qatorda format noto'g'ri. Kutilgan: Fan nomi,Soatlar soni")

        if cells[0].lower().startswith("fan") and "soat" in cells[0].lower() or "fan" in cells[0].lower() and "soat" in cells[1].lower():
            continue

        name = cells[0].strip()
        if not name:
            raise ValueError(f"{line_number}-qatorda fan nomi bo'sh.")

        hours_value = _coerce_numeric_hours(cells[1])
        if hours_value is None:
            raise ValueError(f"{line_number}-qatorda soat soni butun son bo'lishi kerak.")
        hours = int(round(hours_value))
        if hours <= 0:
            raise ValueError(f"{line_number}-qatorda soat soni 0 dan katta bo'lishi kerak.")
        subject_totals[name] = subject_totals.get(name, 0.0) + hours

    if not subject_totals:
        raise ValueError("CSV/Excel faylda fanlar topilmadi. Kutilgan format: Fan nomi, Soatlar soni")

    return {name: int(round(total)) for name, total in subject_totals.items()}


def save_schedule_csv(output_path: str, days: Sequence[str], hour_major_rows: List[List[str]]) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Soat / Kun", *days])
        for idx, row in enumerate(hour_major_rows, start=1):
            writer.writerow([idx, *row])
