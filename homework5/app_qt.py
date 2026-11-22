"""Версия калькулятора стоимости занятий на Qt (PySide6)."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logic import HOUR_TYPE_LABELS, InputError, calculate_from_forms


class LessonCostWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Стоимость занятий")
        self.setMinimumSize(440, 420)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        title = QLabel("Рассчитайте стоимость занятий репетитора")
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        title.setFont(font)
        layout.addWidget(title)

        self.fields = {}
        form = QFormLayout()

        def add_entry(key, label, default=""):
            entry = QLineEdit()
            entry.setText(default)
            entry.returnPressed.connect(self.calculate)
            form.addRow(label, entry)
            self.fields[key] = entry
            return entry

        add_entry("rate", "Ставка за час, руб.", "1500")
        add_entry("hours", "Часов за одно занятие", "2")
        add_entry("lessons", "Количество занятий", "8")

        self.hour_type = QComboBox()
        # В словаре храним ключ academic/astronomic, а показываем подпись
        for key, text in HOUR_TYPE_LABELS.items():
            self.hour_type.addItem(text, key)
        form.addRow("Тип часа", self.hour_type)

        add_entry("discount", "Скидка, %", "10")
        add_entry("travel", "Выезд, руб.", "0")
        add_entry("paid", "Уже оплачено, руб.", "")

        layout.addLayout(form)

        button = QPushButton("Рассчитать")
        # В Qt действие кнопки подключается сигналом clicked к слоту
        button.clicked.connect(self.calculate)
        layout.addWidget(button)

        self.result = QLabel()
        self.result.setWordWrap(True)
        self.result.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.result, stretch=1)

        self.fields["rate"].setFocus()

    def calculate(self):
        try:
            result = calculate_from_forms(
                rate=self.fields["rate"].text(),
                hours=self.fields["hours"].text(),
                lessons=self.fields["lessons"].text(),
                discount=self.fields["discount"].text(),
                travel=self.fields["travel"].text(),
                paid=self.fields["paid"].text(),
                hour_type=self.hour_type.currentData(),
            )
        except InputError as exc:
            self.result.clear()
            QMessageBox.warning(self, "Ошибка ввода", str(exc))
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
                widget.setFocus()
                widget.selectAll()
            return

        self.result.setText(result.as_text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LessonCostWindow()
    window.show()
    sys.exit(app.exec())
