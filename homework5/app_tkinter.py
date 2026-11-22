"""Версия калькулятора стоимости занятий на Tkinter."""

import tkinter as tk
from tkinter import messagebox, ttk

from logic import HOUR_TYPE_LABELS, InputError, calculate_from_forms


class LessonCostApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Стоимость занятий")
        self.minsize(440, 420)

        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Рассчитайте стоимость занятий репетитора",
            font=("", 11, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.fields = {}
        row = 1

        def add_entry(key, label, default=""):
            nonlocal row
            ttk.Label(container, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=3
            )
            entry = ttk.Entry(container)
            if default:
                entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            entry.bind("<Return>", self.calculate)
            self.fields[key] = entry
            row += 1
            return entry

        add_entry("rate", "Ставка за час, руб.", "1500")
        add_entry("hours", "Часов за одно занятие", "2")
        add_entry("lessons", "Количество занятий", "8")

        ttk.Label(container, text="Тип часа").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=3
        )
        self.hour_type = ttk.Combobox(
            container,
            state="readonly",
            values=list(HOUR_TYPE_LABELS.values()),
        )
        self.hour_type.set(HOUR_TYPE_LABELS["academic"])
        self.hour_type.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        add_entry("discount", "Скидка, %", "10")
        add_entry("travel", "Выезд, руб.", "0")
        add_entry("paid", "Уже оплачено, руб.", "")

        ttk.Button(container, text="Рассчитать", command=self.calculate).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 8)
        )
        row += 1

        self.result = ttk.Label(container, justify="left", wraplength=420)
        self.result.grid(row=row, column=0, columnspan=2, sticky="nw")

        self.fields["rate"].focus_set()

    def _hour_type_key(self):
        label = self.hour_type.get()
        for key, text in HOUR_TYPE_LABELS.items():
            if text == label:
                return key
        return "academic"

    def calculate(self, event=None):
        try:
            result = calculate_from_forms(
                rate=self.fields["rate"].get(),
                hours=self.fields["hours"].get(),
                lessons=self.fields["lessons"].get(),
                discount=self.fields["discount"].get(),
                travel=self.fields["travel"].get(),
                paid=self.fields["paid"].get(),
                hour_type=self._hour_type_key(),
            )
        except InputError as exc:
            self.result.configure(text="")
            messagebox.showwarning("Ошибка ввода", str(exc), parent=self)
            # Возвращаем курсор в поле, которое нужно исправить
            widget = self.fields.get(
                {
                    "Ставка за час": "rate",
                    "Часов за одно занятие": "hours",
                    "Количество занятий": "lessons",
                    "Скидка": "discount",
                    "Выезд": "travel",
                    "Уже оплачено": "paid",
                }.get(exc.field)
            )
            if widget is not None:
                widget.focus_set()
                widget.selection_range(0, tk.END)
            return

        self.result.configure(text=result.as_text())


if __name__ == "__main__":
    LessonCostApp().mainloop()
