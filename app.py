from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set

from csv_utils import load_subject_hours, save_schedule_csv
from pdf_utils import save_schedule_pdf
from scheduler import DAYS, ScheduleGenerator


class ScheduleApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Dars jadvali yaratuvchi")
        self.geometry("980x520")

        self.subjects: Dict[str, int] = {}
        self.current_schedule: Optional[List[List[Optional[str]]]] = None
        self.generated_signatures: Set[str] = set()
        self.generator: Optional[ScheduleGenerator] = None

        self._build_ui()

    def _build_ui(self) -> None:
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="CSV yuklash", command=self.load_csv).pack(side="left", padx=4)
        self.generate_btn = ttk.Button(button_frame, text="Jadval yaratish", command=self.generate_schedule, state="disabled")
        self.generate_btn.pack(side="left", padx=4)
        self.regenerate_btn = ttk.Button(
            button_frame, text="Qaytadan yaratish", command=lambda: self.generate_schedule(regenerate=True), state="disabled"
        )
        self.regenerate_btn.pack(side="left", padx=4)
        self.export_csv_btn = ttk.Button(button_frame, text="CSV yuklab olish", command=self.export_csv, state="disabled")
        self.export_csv_btn.pack(side="left", padx=4)
        self.export_pdf_btn = ttk.Button(button_frame, text="PDF yuklab olish", command=self.export_pdf, state="disabled")
        self.export_pdf_btn.pack(side="left", padx=4)

        self.file_label = ttk.Label(self, text="Fayl tanlanmagan")
        self.file_label.pack(anchor="w", padx=10)

        columns = ("soat", *DAYS)
        self.table = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self._configure_table_columns(DAYS)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self.status_label = ttk.Label(self, text="CSV faylni yuklang va jadval yarating.")
        self.status_label.pack(anchor="w", padx=10, pady=(0, 10))

    def _configure_table_columns(self, days: Sequence[str]) -> None:
        self.table.configure(columns=("soat", *days))
        self.table.heading("soat", text="Soat")
        self.table.column("soat", width=70, anchor="center")
        for day in days:
            self.table.heading(day, text=day)
            self.table.column(day, width=170, anchor="center")

    def load_csv(self) -> None:
        file_path = filedialog.askopenfilename(
            title="CSV/Excel faylni tanlang",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            self.subjects = load_subject_hours(file_path)
            self.generator = ScheduleGenerator(self.subjects)
            self._configure_table_columns(self.generator.config.days)
        except Exception as exc:
            messagebox.showerror("Xatolik", str(exc))
            return

        self.file_label.config(text=f"Yuklangan fayl: {file_path}")
        self.status_label.config(text="CSV yuklandi. Endi jadval yaratishingiz mumkin.")
        self.generate_btn.config(state="normal")
        self.regenerate_btn.config(state="disabled")
        self.export_csv_btn.config(state="disabled")
        self.export_pdf_btn.config(state="disabled")
        self.generated_signatures.clear()
        self.current_schedule = None
        self._clear_table()

    def generate_schedule(self, regenerate: bool = False) -> None:
        if not self.generator:
            messagebox.showinfo("Ma'lumot kerak", "Avval CSV faylni yuklang.")
            return
        excludes = self.generated_signatures if regenerate else set()
        try:
            schedule = self.generator.generate(exclude_signatures=excludes)
        except Exception as exc:
            messagebox.showwarning("Jadval yaratilmadi", str(exc))
            return

        self.current_schedule = schedule
        signature = self.generator.schedule_signature(schedule)
        self.generated_signatures.add(signature)
        self._render_schedule(schedule)
        self.regenerate_btn.config(state="normal")
        self.export_csv_btn.config(state="normal")
        self.export_pdf_btn.config(state="normal")
        self.status_label.config(text="Jadval tayyor. Yoqmasa 'Qaytadan yaratish' tugmasini bosing.")

    def _render_schedule(self, schedule: List[List[Optional[str]]]) -> None:
        self._clear_table()
        assert self.generator is not None
        hour_rows = self.generator.to_hour_major(schedule)
        for hour_idx, row in enumerate(hour_rows, start=1):
            self.table.insert("", "end", values=(hour_idx, *row))

    def _clear_table(self) -> None:
        for item in self.table.get_children():
            self.table.delete(item)

    def export_csv(self) -> None:
        if not self.current_schedule or not self.generator:
            messagebox.showinfo("Ma'lumot yo'q", "Avval jadval yarating.")
            return
        output_path = filedialog.asksaveasfilename(
            title="CSV saqlash",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not output_path:
            return
        hour_rows = self.generator.to_hour_major(self.current_schedule)
        save_schedule_csv(output_path, self.generator.config.days, hour_rows)
        self.status_label.config(text=f"CSV saqlandi: {output_path}")

    def export_pdf(self) -> None:
        if not self.current_schedule or not self.generator:
            messagebox.showinfo("Ma'lumot yo'q", "Avval jadval yarating.")
            return
        output_path = filedialog.asksaveasfilename(
            title="PDF saqlash",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not output_path:
            return
        hour_rows = self.generator.to_hour_major(self.current_schedule)
        save_schedule_pdf(output_path, self.generator.config.days, hour_rows)
        self.status_label.config(text=f"PDF saqlandi: {output_path}")


def main() -> None:
    app = ScheduleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
