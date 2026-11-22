"""
Домашняя работа № 6.
Графическое приложение «Магазин»: покупатели и заказы.
Поддерживаются две СУБД — локальная SQLite и промышленная PostgreSQL.
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


# Файл локальной базы создаётся рядом со скриптом
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db")


def format_db_error(exc):
    """Переводит типичные ошибки ограничений SQL на понятный язык."""
    text = str(exc).lower()
    pgcode = getattr(exc, "pgcode", None)

    if pgcode == "23505" or "unique" in text:
        return "Такой email уже есть в базе (нарушение UNIQUE)."
    if pgcode == "23514" or "check constraint" in text or "check" in text:
        return "Количество должно быть больше 0 (нарушение CHECK)."
    if pgcode == "23502" or "not null" in text:
        return "Заполните все обязательные поля (нарушение NOT NULL)."
    if pgcode == "23503" or "foreign key" in text:
        return (
            "Нельзя выполнить операцию: нарушена связь между таблицами "
            "(FOREIGN KEY). Сначала удалите связанные заказы."
        )
    return f"Ошибка базы данных: {exc}"


class Database:
    """Общий интерфейс работы с SQLite и PostgreSQL."""

    def __init__(self):
        self.backend = None
        self.conn = None
        self.placeholder = "?"

    def is_connected(self):
        return self.conn is not None

    def _sql(self, text):
        """Подставляет плейсхолдер: ? для SQLite и %s для PostgreSQL."""
        if self.placeholder != "?":
            return text.replace("?", self.placeholder)
        return text

    def connect_sqlite(self, path=SQLITE_PATH):
        """Подключение к локальной базе SQLite."""
        self.close()
        self.conn = sqlite3.connect(path)
        # В SQLite внешние ключи по умолчанию выключены
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.backend = "sqlite"
        self.placeholder = "?"
        self.create_tables()

    def connect_postgres(self, host, port, dbname, user, password):
        """Подключение к PostgreSQL. psycopg2 импортируется только здесь."""
        import psycopg2  # ленивый импорт: без него можно работать с SQLite

        self.close()
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password or "",
        )
        self.backend = "postgres"
        self.placeholder = "%s"
        self.create_tables()

    def create_tables(self):
        """Создаёт таблицы, если их ещё нет. Схема одна и та же для обеих СУБД."""
        if self.backend == "postgres":
            id_type = "SERIAL PRIMARY KEY"
        else:
            id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"

        cur = self.conn.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS customers (
                id {id_type},
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
            """
        )
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS orders (
                id {id_type},
                customer_id INTEGER NOT NULL,
                product TEXT NOT NULL,
                quan INTEGER NOT NULL CHECK (quan > 0),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """
        )
        self.conn.commit()

    def execute(self, sql, params=(), fetch=None, commit=False):
        """Цикл работы с БД: cursor() -> execute() -> (fetch) -> commit/rollback."""
        cur = self.conn.cursor()
        try:
            cur.execute(self._sql(sql), params)
            result = None
            if fetch == "all":
                result = cur.fetchall()
            elif fetch == "one":
                result = cur.fetchone()
            if commit:
                self.conn.commit()
            return result
        except Exception:
            self.conn.rollback()
            raise

    def add_customer(self, name, email):
        self.execute(
            "INSERT INTO customers (name, email) VALUES (?, ?)",
            (name, email),
            commit=True,
        )

    def add_order(self, customer_id, product, quan):
        self.execute(
            "INSERT INTO orders (customer_id, product, quan) VALUES (?, ?, ?)",
            (customer_id, product, quan),
            commit=True,
        )

    def get_customers(self, search=""):
        if search:
            pattern = f"%{search}%"
            return self.execute(
                """
                SELECT id, name, email
                FROM customers
                WHERE name LIKE ? OR email LIKE ?
                ORDER BY id
                """,
                (pattern, pattern),
                fetch="all",
            )
        return self.execute(
            "SELECT id, name, email FROM customers ORDER BY id",
            fetch="all",
        )

    def get_orders(self, search=""):
        # JOIN нужен, чтобы показать имя покупателя рядом с заказом
        if search:
            pattern = f"%{search}%"
            return self.execute(
                """
                SELECT o.id, c.name, o.product, o.quan
                FROM orders AS o
                JOIN customers AS c ON c.id = o.customer_id
                WHERE c.name LIKE ? OR c.email LIKE ?
                ORDER BY o.id
                """,
                (pattern, pattern),
                fetch="all",
            )
        return self.execute(
            """
            SELECT o.id, c.name, o.product, o.quan
            FROM orders AS o
            JOIN customers AS c ON c.id = o.customer_id
            ORDER BY o.id
            """,
            fetch="all",
        )

    def delete_customer(self, customer_id):
        self.execute(
            "DELETE FROM customers WHERE id = ?",
            (customer_id,),
            commit=True,
        )

    def delete_order(self, order_id):
        self.execute(
            "DELETE FROM orders WHERE id = ?",
            (order_id,),
            commit=True,
        )

    def close(self):
        """Закрывает соединение с базой."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            self.backend = None


class ShopApp:
    """Окно магазина: выбор СУБД, добавление записей, таблицы и поиск."""

    def __init__(self, root):
        self.root = root
        self.root.title("Магазин: покупатели и заказы")
        self.root.geometry("920x680")
        self.root.minsize(800, 600)

        self.db = Database()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # --- Выбор СУБД и подключение ---
        conn_frame = ttk.LabelFrame(self.root, text="Подключение к базе данных")
        conn_frame.pack(fill="x", padx=10, pady=8)

        self.backend_var = tk.StringVar(value="sqlite")
        radio_row = ttk.Frame(conn_frame)
        radio_row.pack(fill="x", **pad)
        ttk.Label(radio_row, text="СУБД:").pack(side="left")
        ttk.Radiobutton(
            radio_row,
            text="SQLite (локальная)",
            variable=self.backend_var,
            value="sqlite",
            command=self._toggle_pg_fields,
        ).pack(side="left", padx=8)
        ttk.Radiobutton(
            radio_row,
            text="PostgreSQL (промышленная)",
            variable=self.backend_var,
            value="postgres",
            command=self._toggle_pg_fields,
        ).pack(side="left", padx=8)

        pg_row = ttk.Frame(conn_frame)
        pg_row.pack(fill="x", **pad)

        self.pg_entries = {}
        fields = [
            ("host", "Хост", "localhost"),
            ("port", "Порт", "5432"),
            ("dbname", "База", "postgres"),
            ("user", "Пользователь", "postgres"),
            ("password", "Пароль", ""),
        ]
        for key, label, default in fields:
            ttk.Label(pg_row, text=label + ":").pack(side="left")
            show = "*" if key == "password" else ""
            entry = ttk.Entry(pg_row, width=14, show=show)
            entry.insert(0, default)
            entry.pack(side="left", padx=(2, 8))
            self.pg_entries[key] = entry

        ttk.Button(pg_row, text="Подключиться", command=self.connect).pack(
            side="left", padx=4
        )

        self.status_var = tk.StringVar(value="Нет подключения")
        ttk.Label(conn_frame, textvariable=self.status_var).pack(anchor="w", **pad)

        # --- Добавление покупателя ---
        cust_frame = ttk.LabelFrame(self.root, text="Добавить покупателя")
        cust_frame.pack(fill="x", padx=10, pady=4)
        row = ttk.Frame(cust_frame)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Имя:").pack(side="left")
        self.name_entry = ttk.Entry(row, width=24)
        self.name_entry.pack(side="left", padx=(2, 10))
        ttk.Label(row, text="Email:").pack(side="left")
        self.email_entry = ttk.Entry(row, width=28)
        self.email_entry.pack(side="left", padx=(2, 10))
        ttk.Button(row, text="Добавить покупателя", command=self.add_customer).pack(
            side="left"
        )

        # --- Добавление заказа ---
        order_frame = ttk.LabelFrame(self.root, text="Добавить заказ")
        order_frame.pack(fill="x", padx=10, pady=4)
        row = ttk.Frame(order_frame)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Покупатель:").pack(side="left")
        self.customer_combo = ttk.Combobox(row, width=28, state="readonly")
        self.customer_combo.pack(side="left", padx=(2, 10))
        ttk.Label(row, text="Товар:").pack(side="left")
        self.product_entry = ttk.Entry(row, width=20)
        self.product_entry.pack(side="left", padx=(2, 10))
        ttk.Label(row, text="Количество:").pack(side="left")
        self.quan_entry = ttk.Entry(row, width=8)
        self.quan_entry.pack(side="left", padx=(2, 10))
        ttk.Button(row, text="Добавить заказ", command=self.add_order).pack(side="left")

        # --- Поиск ---
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(search_frame, text="Поиск по покупателю:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, width=32)
        self.search_entry.pack(side="left", padx=6)
        ttk.Button(search_frame, text="Найти", command=self.refresh_tables).pack(
            side="left", padx=2
        )
        ttk.Button(search_frame, text="Сбросить", command=self.clear_search).pack(
            side="left", padx=2
        )
        ttk.Button(
            search_frame, text="Удалить выбранную запись", command=self.delete_selected
        ).pack(side="right")

        # --- Таблицы на вкладках ---
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=8)
        self.notebook = notebook

        customers_tab = ttk.Frame(notebook)
        orders_tab = ttk.Frame(notebook)
        notebook.add(customers_tab, text="Покупатели")
        notebook.add(orders_tab, text="Заказы")

        self.customers_tree = self._make_tree(
            customers_tab,
            columns=("id", "name", "email"),
            headings=("ID", "Имя", "Email"),
            widths=(60, 280, 360),
        )
        self.orders_tree = self._make_tree(
            orders_tab,
            columns=("id", "customer", "product", "quan"),
            headings=("ID", "Покупатель", "Товар", "Количество"),
            widths=(60, 260, 280, 120),
        )

        self._toggle_pg_fields()

    def _make_tree(self, parent, columns, headings, widths):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for col, heading, width in zip(columns, headings, widths):
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _toggle_pg_fields(self):
        state = "normal" if self.backend_var.get() == "postgres" else "disabled"
        for entry in self.pg_entries.values():
            entry.configure(state=state)

    def _need_connection(self):
        if not self.db.is_connected():
            messagebox.showwarning("Нет подключения", "Сначала подключитесь к базе данных.")
            return False
        return True

    def connect(self):
        try:
            if self.backend_var.get() == "sqlite":
                self.db.connect_sqlite()
                self.status_var.set(f"Подключено к SQLite: {SQLITE_PATH}")
            else:
                params = {key: entry.get().strip() for key, entry in self.pg_entries.items()}
                # пароль можно оставить пустым, его не обрезаем по краям
                params["password"] = self.pg_entries["password"].get()
                if not params["host"] or not params["port"] or not params["dbname"] or not params["user"]:
                    messagebox.showwarning(
                        "Подключение",
                        "Заполните поля хоста, порта, базы и пользователя.",
                    )
                    return
                self.db.connect_postgres(
                    host=params["host"],
                    port=params["port"],
                    dbname=params["dbname"],
                    user=params["user"],
                    password=params["password"],
                )
                self.status_var.set(
                    f"Подключено к PostgreSQL: {params['user']}@{params['host']}:"
                    f"{params['port']}/{params['dbname']}"
                )
            self.refresh_tables()
        except ImportError:
            messagebox.showerror(
                "PostgreSQL",
                "Не установлен пакет psycopg2.\n"
                "Установите его командой:\npip install -r requirements.txt",
            )
        except Exception as exc:
            self.status_var.set("Нет подключения")
            messagebox.showerror("Ошибка подключения", str(exc))

    def refresh_tables(self):
        if not self.db.is_connected():
            return
        search = self.search_entry.get().strip()
        try:
            for tree in (self.customers_tree, self.orders_tree):
                for item in tree.get_children():
                    tree.delete(item)

            for row in self.db.get_customers(search):
                self.customers_tree.insert("", "end", values=row)

            for row in self.db.get_orders(search):
                self.orders_tree.insert("", "end", values=row)

            # Обновляем список покупателей в форме заказа
            customers = self.db.get_customers()
            labels = [f"{row[0]}: {row[1]} ({row[2]})" for row in customers]
            self.customer_combo["values"] = labels
            self._customer_ids = [row[0] for row in customers]
            if labels and self.customer_combo.current() == -1:
                self.customer_combo.current(0)
            if not labels:
                self.customer_combo.set("")
        except Exception as exc:
            messagebox.showerror("Ошибка чтения", format_db_error(exc))

    def clear_search(self):
        self.search_entry.delete(0, "end")
        self.refresh_tables()

    def add_customer(self):
        if not self._need_connection():
            return
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        if not name or not email:
            messagebox.showwarning(
                "Проверка ввода",
                "Имя и email обязательны (ограничение NOT NULL).",
            )
            return
        try:
            self.db.add_customer(name, email)
            self.name_entry.delete(0, "end")
            self.email_entry.delete(0, "end")
            self.refresh_tables()
        except Exception as exc:
            messagebox.showerror("Не удалось добавить покупателя", format_db_error(exc))

    def add_order(self):
        if not self._need_connection():
            return
        if not self.customer_combo.get() or not getattr(self, "_customer_ids", None):
            messagebox.showwarning("Проверка ввода", "Сначала добавьте и выберите покупателя.")
            return
        product = self.product_entry.get().strip()
        quan_text = self.quan_entry.get().strip()
        if not product or not quan_text:
            messagebox.showwarning(
                "Проверка ввода",
                "Товар и количество обязательны (ограничение NOT NULL).",
            )
            return
        try:
            quan = int(quan_text)
        except ValueError:
            messagebox.showwarning("Проверка ввода", "Количество должно быть целым числом.")
            return
        # Даже если число неположительное, отправляем его в БД,
        # чтобы сработало ограничение CHECK (quan > 0)
        try:
            index = self.customer_combo.current()
            customer_id = self._customer_ids[index]
            self.db.add_order(customer_id, product, quan)
            self.product_entry.delete(0, "end")
            self.quan_entry.delete(0, "end")
            self.refresh_tables()
        except Exception as exc:
            messagebox.showerror("Не удалось добавить заказ", format_db_error(exc))

    def delete_selected(self):
        if not self._need_connection():
            return
        tab = self.notebook.index(self.notebook.select())
        if tab == 0:
            tree = self.customers_tree
            kind = "customer"
        else:
            tree = self.orders_tree
            kind = "order"

        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите запись в текущей вкладке.")
            return
        item_id = tree.item(selected[0], "values")[0]
        try:
            if kind == "customer":
                self.db.delete_customer(item_id)
            else:
                self.db.delete_order(item_id)
            self.refresh_tables()
        except Exception as exc:
            messagebox.showerror("Не удалось удалить запись", format_db_error(exc))

    def on_close(self):
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    ShopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
