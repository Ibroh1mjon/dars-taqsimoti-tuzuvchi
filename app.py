from __future__ import annotations

import tkinter as tk
import hashlib
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set

from csv_utils import load_class_subject_hours
from scheduler import DAYS, ScheduleConfig, ScheduleGenerator, generate_class_schedules


class ScheduleApp(tk.Tk):
    TEACHER_COLORS = (
        "#fff2cc", "#e2f0d9", "#d9eaf7", "#fce4d6", "#e4dfec",
        "#dDEBF7", "#f4cccc", "#d9ead3", "#ead1dc", "#cfe2f3",
        "#fff4e6", "#e8f5e9",
    )

    def __init__(self) -> None:
        super().__init__()
        self.title("Dars jadvali yaratuvchi")
        self.geometry("980x520")

        self.class_subjects: Dict[str, Dict[str, int]] = {}
        self.current_schedule: Optional[Dict[str, List[List[Optional[str]]]]] = None
        self.generated_signatures: Set[str] = set()
        self.schedule_days = DAYS

        self._build_ui()

    def _build_ui(self) -> None:
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="XLSX yuklash", command=self.load_xlsx).pack(side="left", padx=4)
        self.generate_btn = ttk.Button(button_frame, text="Jadval yaratish", command=self.generate_schedule, state="disabled")
        self.generate_btn.pack(side="left", padx=4)
        self.regenerate_btn = ttk.Button(
            button_frame, text="Qaytadan yaratish", command=lambda: self.generate_schedule(regenerate=True), state="disabled"
        )
        self.regenerate_btn.pack(side="left", padx=4)

        self.file_label = ttk.Label(self, text="Fayl tanlanmagan")
        self.file_label.pack(anchor="w", padx=10)

        table_container = ttk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.table_canvas = tk.Canvas(table_container, highlightthickness=0, background="#d9e2f3")
        self.table_canvas.grid(row=0, column=0, sticky="nsew")
        vertical_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.table_canvas.yview)
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.table_canvas.xview)
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        self.table_canvas.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
        table_container.rowconfigure(0, weight=1)
        table_container.columnconfigure(0, weight=1)
        self.table_frame = ttk.Frame(self.table_canvas)
        self.table_canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.table_frame.bind(
            "<Configure>",
            lambda _event: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all")),
        )

        self.status_label = ttk.Label(self, text="XLSX faylni yuklang va jadval yarating.")
        self.status_label.pack(anchor="w", padx=10, pady=(0, 10))

    def load_xlsx(self) -> None:
        file_path = filedialog.askopenfilename(
            title="XLSX faylni tanlang",
            filetypes=[("Excel files", "*.xlsx")],
        )
        if not file_path:
            return
        try:
            self.class_subjects = load_class_subject_hours(file_path)
        except Exception as exc:
            messagebox.showerror("Xatolik", str(exc))
            return

        self.file_label.config(text=f"Yuklangan fayl: {file_path}")
        self.status_label.config(text="XLSX yuklandi. Endi jadval yaratishingiz mumkin.")
        self.generate_btn.config(state="normal")
        self.regenerate_btn.config(state="disabled")
        self.generated_signatures.clear()
        self.current_schedule = None
        self._clear_table()

    def generate_schedule(self, regenerate: bool = False) -> None:
        if not self.class_subjects:
            messagebox.showinfo("Ma'lumot kerak", "Avval XLSX faylni yuklang.")
            return
        excludes = self.generated_signatures if regenerate else set()
        try:
            self.schedule_days = DAYS
            schedules = generate_class_schedules(
                self.class_subjects,
                config=ScheduleConfig(days=self.schedule_days),
                exclude_signatures=excludes,
            )
        except Exception as exc:
            messagebox.showwarning("Jadval yaratilmadi", str(exc))
            return

        self.current_schedule = schedules
        signature = "|".join(
            f"{class_name}:{ScheduleGenerator.schedule_signature(schedule)}"
            for class_name, schedule in sorted(schedules.items())
        )
        self.generated_signatures.add(signature)
        self._render_schedule(schedules)
        self.regenerate_btn.config(state="normal")
        self.status_label.config(text="Jadval tayyor. Yoqmasa 'Qaytadan yaratish' tugmasini bosing.")

    def _render_schedule(self, schedules: Dict[str, List[List[Optional[str]]]]) -> None:
        self._clear_table()
        column_width = 190
        header = tk.Frame(self.table_frame, background="#4472c4", bd=1, relief="solid")
        header.grid(row=0, column=0, columnspan=len(schedules) + 1, sticky="ew")
        tk.Label(
            header, text="Kun", width=12, height=2, anchor="center",
            background="#4472c4", foreground="white", font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="nsew")
        for column_index, class_name in enumerate(schedules, start=1):
            tk.Label(
                header, text=f"Sinf {class_name}", width=column_width // 10, height=2,
                anchor="center", background="#4472c4", foreground="white",
                font=("TkDefaultFont", 10, "bold"), bd=1, relief="solid",
            ).grid(row=0, column=column_index, sticky="nsew")
        header.grid_columnconfigure(0, weight=0)
        for column_index in range(1, len(schedules) + 1):
            header.grid_columnconfigure(column_index, minsize=column_width, weight=1)

        for day_index, day in enumerate(self.schedule_days):
            row_background = "#f2f6fc" if day_index % 2 == 0 else "#e7eef8"
            tk.Label(
                self.table_frame, text=day, width=12, height=8, anchor="center",
                background="#d9e2f3", font=("TkDefaultFont", 10, "bold"),
                bd=1, relief="solid",
            ).grid(row=day_index + 1, column=0, sticky="nsew")
            for column_index, schedule in enumerate(schedules.values(), start=1):
                cell = tk.Text(
                    self.table_frame, width=column_width // 10, height=8, wrap="word",
                    state="disabled", relief="solid", borderwidth=1, padx=7, pady=5,
                    background=row_background, foreground="#1f1f1f",
                    font=("TkDefaultFont", 9), spacing1=1,
                )
                cell.grid(row=day_index + 1, column=column_index, sticky="nsew")
                cell.tag_configure("teacher", font=("TkDefaultFont", 8), foreground="#666666")
                for period, value in enumerate(schedule[day_index], start=1):
                    if value:
                        subject, teacher = value.split("\n", 1)
                        teacher_tag = f"teacher_{hashlib.md5(teacher.encode('utf-8')).hexdigest()}"
                        cell.tag_configure(
                            teacher_tag,
                            background=self._teacher_color(teacher),
                        )
                        cell.configure(state="normal")
                        cell.insert("end", f"{period}. {subject}\n", teacher_tag)
                        cell.insert("end", f"   {teacher}\n", (teacher_tag, "teacher"))
                        cell.configure(state="disabled")
            self.table_frame.grid_rowconfigure(day_index + 1, minsize=135)

    @classmethod
    def _teacher_color(cls, teacher: str) -> str:
        color_index = int(hashlib.md5(teacher.encode("utf-8")).hexdigest()[:8], 16)
        return cls.TEACHER_COLORS[color_index % len(cls.TEACHER_COLORS)]

    def _clear_table(self) -> None:
        for child in self.table_frame.winfo_children():
            child.destroy()


def main() -> None:
    app = ScheduleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
