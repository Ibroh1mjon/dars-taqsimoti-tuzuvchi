from __future__ import annotations

from typing import List, Sequence


def _pdf_escape(text: str) -> str:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    safe_bytes = safe.encode("latin-1", "replace")
    return safe_bytes.decode("latin-1")


def save_schedule_pdf(output_path: str, days: Sequence[str], hour_major_rows: List[List[str]]) -> None:
    header = " | ".join(days)
    lines = ["Haftalik dars jadvali", header]
    for hour_index, row in enumerate(hour_major_rows, start=1):
        lines.append(f"{hour_index}. {' | '.join(value or '-' for value in row)}")

    content_lines = []
    for line in lines:
        content_lines.append(f"({_pdf_escape(line)}) Tj")
        content_lines.append("T*")
    stream_text = "BT\n/F1 11 Tf\n50 790 Td\n14 TL\n" + "\n".join(content_lines) + "\nET"
    stream_data = stream_text.encode("latin-1", "replace")

    objects: List[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects.append(f"<< /Length {len(stream_data)} >>\nstream\n".encode("latin-1") + stream_data + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("latin-1")
    )

    with open(output_path, "wb") as pdf_file:
        pdf_file.write(pdf)
