import customtkinter as ctk
import sqlite3
from datetime import datetime
from tkinter import messagebox, ttk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CATEGORIES = ["أدوات مدرسية", "إعلام آلي", "أخرى"]


class MaktabaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("نظام إدارة المكتبة والخدمات")
        self.geometry("1150x720")
        self.minsize(1050, 650)

        self.create_database()
        self.setup_treeview_style()

        self.selected_product_id = None
        self.selected_customer_id = None
        self.cart = []  # each item: {product_id, name, qty, unit_price, buy_price}

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="right", fill="y")

        ctk.CTkLabel(self.sidebar, text="نظام المكتبة", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        self.nav_buttons = {}
        self.nav_buttons["home"] = ctk.CTkButton(self.sidebar, text="الرئيسية", command=self.show_home)
        self.nav_buttons["home"].pack(pady=10, padx=20, fill="x")

        self.nav_buttons["products"] = ctk.CTkButton(self.sidebar, text="المنتجات", command=self.show_products)
        self.nav_buttons["products"].pack(pady=10, padx=20, fill="x")

        self.nav_buttons["customers"] = ctk.CTkButton(self.sidebar, text="الزبائن والديون", command=self.show_customers)
        self.nav_buttons["customers"].pack(pady=10, padx=20, fill="x")

        self.nav_buttons["sales"] = ctk.CTkButton(self.sidebar, text="تسجيل بيع", command=self.show_sales)
        self.nav_buttons["sales"].pack(pady=10, padx=20, fill="x")

        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_home()

    # ---------------------------------------------------------------- #
    # إعداد عام
    # ---------------------------------------------------------------- #

    def setup_treeview_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=28,
            borderwidth=0,
            font=("Arial", 12),
        )
        style.configure("Treeview.Heading", background="#1f6aa5", foreground="white", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#144870")])

    def set_active_nav(self, key):
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color="#144870" if name == key else ["#3a7ebf", "#1f538d"])

    def create_database(self):
        self.conn = sqlite3.connect("maktaba.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER DEFAULT 0,
                buy_price REAL DEFAULT 0,
                sell_price REAL DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                debt REAL DEFAULT 0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                total REAL,
                payment_type TEXT,
                date TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        """)

        # جدول جديد: يربط كل عملية بيع بالمنتجات الفعلية التي بيعت
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                unit_price REAL,
                buy_price REAL,
                FOREIGN KEY(sale_id) REFERENCES sales(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

        self.conn.commit()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def on_close(self):
        self.conn.close()
        self.destroy()

    @staticmethod
    def parse_positive_int(value, field_name):
        try:
            n = int(value)
        except ValueError:
            raise ValueError(f"'{field_name}' يجب أن يكون رقمًا صحيحًا")
        if n < 0:
            raise ValueError(f"'{field_name}' لا يمكن أن يكون سالبًا")
        return n

    @staticmethod
    def parse_positive_float(value, field_name):
        try:
            n = float(value)
        except ValueError:
            raise ValueError(f"'{field_name}' يجب أن يكون رقمًا")
        if n < 0:
            raise ValueError(f"'{field_name}' لا يمكن أن يكون سالبًا")
        return n

    # ---------------------------------------------------------------- #
    # الرئيسية
    # ---------------------------------------------------------------- #

    def show_home(self):
        self.set_active_nav("home")
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="مرحباً بك في نظام إدارة المكتبة",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)

        self.cursor.execute("SELECT COUNT(*) FROM products")
        products_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM customers WHERE debt > 0")
        debtors_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT SUM(debt) FROM customers")
        total_debt = self.cursor.fetchone()[0] or 0

        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (f"{today}%",))
        today_sales = self.cursor.fetchone()[0] or 0

        self.cursor.execute("""
            SELECT SUM((unit_price - buy_price) * quantity)
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.date LIKE ?
        """, (f"{today}%",))
        today_profit = self.cursor.fetchone()[0] or 0

        stats_frame = ctk.CTkFrame(self.main_frame)
        stats_frame.pack(pady=20, padx=40, fill="x")

        stats = [
            ("عدد المنتجات", products_count),
            ("عدد الزبائن المدينين", debtors_count),
            ("إجمالي الديون", f"{total_debt:.2f} د.ج"),
            ("مبيعات اليوم", f"{today_sales:.2f} د.ج"),
            ("ربح اليوم", f"{today_profit:.2f} د.ج"),
        ]

        for label, value in stats:
            row = ctk.CTkFrame(stats_frame, fg_color="transparent")
            row.pack(fill="x", pady=6)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=16)).pack(side="right", padx=10)
            ctk.CTkLabel(row, text=str(value), font=ctk.CTkFont(size=16, weight="bold")).pack(side="right")

        low_stock_frame = ctk.CTkFrame(self.main_frame)
        low_stock_frame.pack(pady=10, padx=40, fill="both", expand=True)
        ctk.CTkLabel(low_stock_frame, text="منتجات كمياتها منخفضة (أقل من 5)",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))

        self.cursor.execute("SELECT name, quantity FROM products WHERE quantity < 5 ORDER BY quantity ASC")
        low_stock = self.cursor.fetchall()
        if not low_stock:
            ctk.CTkLabel(low_stock_frame, text="لا توجد منتجات منخفضة الكمية حاليًا").pack(pady=10)
        else:
            for name, qty in low_stock:
                ctk.CTkLabel(low_stock_frame, text=f"{name} — الكمية المتبقية: {qty}",
                             text_color="#e07b39").pack(pady=2)

    # ---------------------------------------------------------------- #
    # المنتجات
    # ---------------------------------------------------------------- #

    def show_products(self):
        self.set_active_nav("products")
        self.clear_main()
        self.selected_product_id = None

        ctk.CTkLabel(self.main_frame, text="إدارة المنتجات", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=15)

        form = ctk.CTkFrame(self.main_frame)
        form.pack(pady=10, padx=20, fill="x")

        self.p_name = ctk.CTkEntry(form, placeholder_text="اسم المنتج")
        self.p_name.pack(side="right", padx=5, pady=10)

        self.p_category = ctk.CTkOptionMenu(form, values=CATEGORIES)
        self.p_category.pack(side="right", padx=5, pady=10)

        self.p_qty = ctk.CTkEntry(form, placeholder_text="الكمية", width=80)
        self.p_qty.pack(side="right", padx=5, pady=10)

        self.p_buy = ctk.CTkEntry(form, placeholder_text="سعر الشراء", width=100)
        self.p_buy.pack(side="right", padx=5, pady=10)

        self.p_sell = ctk.CTkEntry(form, placeholder_text="سعر البيع", width=100)
        self.p_sell.pack(side="right", padx=5, pady=10)

        btns = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btns.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkButton(btns, text="إضافة منتج", command=self.add_product).pack(side="right", padx=5)
        ctk.CTkButton(btns, text="تحديث المنتج المحدد", command=self.update_product,
                      fg_color="#c98a1f").pack(side="right", padx=5)
        ctk.CTkButton(btns, text="حذف المنتج المحدد", command=self.delete_product,
                      fg_color="#b5432e").pack(side="right", padx=5)
        ctk.CTkButton(btns, text="تفريغ الحقول", command=self.clear_product_fields,
                      fg_color="gray40").pack(side="right", padx=5)

        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(padx=20, fill="x")
        ctk.CTkLabel(search_frame, text="بحث:").pack(side="right", padx=(0, 5))
        self.product_search = ctk.CTkEntry(search_frame, placeholder_text="ابحث عن منتج...")
        self.product_search.pack(side="right", padx=5, fill="x", expand=True)
        self.product_search.bind("<KeyRelease>", lambda e: self.refresh_products())

        columns = ("id", "name", "category", "quantity", "buy_price", "sell_price")
        self.products_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)
        headings = {"id": "ID", "name": "الاسم", "category": "الصنف", "quantity": "الكمية",
                    "buy_price": "سعر الشراء", "sell_price": "سعر البيع"}
        for col in columns:
            self.products_tree.heading(col, text=headings[col])
            self.products_tree.column(col, anchor="center", width=120)
        self.products_tree.pack(pady=10, padx=20, fill="both", expand=True)
        self.products_tree.bind("<<TreeviewSelect>>", self.on_select_product)

        self.refresh_products()

    def refresh_products(self):
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)

        term = self.product_search.get().strip()
        if term:
            self.cursor.execute(
                "SELECT id, name, category, quantity, buy_price, sell_price FROM products WHERE name LIKE ?",
                (f"%{term}%",),
            )
        else:
            self.cursor.execute("SELECT id, name, category, quantity, buy_price, sell_price FROM products")

        for row in self.cursor.fetchall():
            self.products_tree.insert("", "end", values=row)

    def on_select_product(self, event):
        selected = self.products_tree.selection()
        if not selected:
            return
        values = self.products_tree.item(selected[0], "values")
        self.selected_product_id = int(values[0])
        self.p_name.delete(0, "end")
        self.p_name.insert(0, values[1])
        self.p_category.set(values[2] if values[2] in CATEGORIES else CATEGORIES[-1])
        self.p_qty.delete(0, "end")
        self.p_qty.insert(0, values[3])
        self.p_buy.delete(0, "end")
        self.p_buy.insert(0, values[4])
        self.p_sell.delete(0, "end")
        self.p_sell.insert(0, values[5])

    def clear_product_fields(self):
        self.selected_product_id = None
        self.p_name.delete(0, "end")
        self.p_category.set(CATEGORIES[0])
        self.p_qty.delete(0, "end")
        self.p_buy.delete(0, "end")
        self.p_sell.delete(0, "end")
        self.products_tree.selection_remove(self.products_tree.selection())

    def read_product_form(self):
        name = self.p_name.get().strip()
        if not name:
            raise ValueError("أدخل اسم المنتج")
        category = self.p_category.get()
        qty = self.parse_positive_int(self.p_qty.get(), "الكمية")
        buy = self.parse_positive_float(self.p_buy.get(), "سعر الشراء")
        sell = self.parse_positive_float(self.p_sell.get(), "سعر البيع")
        return name, category, qty, buy, sell

    def add_product(self):
        try:
            name, category, qty, buy, sell = self.read_product_form()
        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
            return

        self.cursor.execute(
            "INSERT INTO products (name, category, quantity, buy_price, sell_price) VALUES (?, ?, ?, ?, ?)",
            (name, category, qty, buy, sell),
        )
        self.conn.commit()
        messagebox.showinfo("نجاح", "تم إضافة المنتج بنجاح")
        self.clear_product_fields()
        self.refresh_products()

    def update_product(self):
        if self.selected_product_id is None:
            messagebox.showerror("خطأ", "اختر منتجًا من القائمة أولاً")
            return
        try:
            name, category, qty, buy, sell = self.read_product_form()
        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
            return

        self.cursor.execute(
            "UPDATE products SET name=?, category=?, quantity=?, buy_price=?, sell_price=? WHERE id=?",
            (name, category, qty, buy, sell, self.selected_product_id),
        )
        self.conn.commit()
        messagebox.showinfo("نجاح", "تم تحديث المنتج")
        self.clear_product_fields()
        self.refresh_products()

    def delete_product(self):
        if self.selected_product_id is None:
            messagebox.showerror("خطأ", "اختر منتجًا من القائمة أولاً")
            return
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا المنتج؟"):
            return
        self.cursor.execute("DELETE FROM products WHERE id=?", (self.selected_product_id,))
        self.conn.commit()
        self.clear_product_fields()
        self.refresh_products()

    # ---------------------------------------------------------------- #
    # الزبائن والديون
    # ---------------------------------------------------------------- #

    def show_customers(self):
        self.set_active_nav("customers")
        self.clear_main()
        self.selected_customer_id = None

        ctk.CTkLabel(self.main_frame, text="الزبائن والديون", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=15)

        form = ctk.CTkFrame(self.main_frame)
        form.pack(pady=10, padx=20, fill="x")

        self.c_name = ctk.CTkEntry(form, placeholder_text="اسم الزبون")
        self.c_name.pack(side="right", padx=5, pady=10)

        self.c_phone = ctk.CTkEntry(form, placeholder_text="رقم الهاتف")
        self.c_phone.pack(side="right", padx=5, pady=10)

        btns = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btns.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkButton(btns, text="إضافة زبون", command=self.add_customer).pack(side="right", padx=5)
        ctk.CTkButton(btns, text="تحديث البيانات", command=self.update_customer,
                      fg_color="#c98a1f").pack(side="right", padx=5)
        ctk.CTkButton(btns, text="حذف الزبون", command=self.delete_customer,
                      fg_color="#b5432e").pack(side="right", padx=5)
        ctk.CTkButton(btns, text="تفريغ الحقول", command=self.clear_customer_fields,
                      fg_color="gray40").pack(side="right", padx=5)

        payment_frame = ctk.CTkFrame(self.main_frame)
        payment_frame.pack(pady=(0, 10), padx=20, fill="x")
        ctk.CTkLabel(payment_frame, text="تسديد دين (اختر زبونًا من الجدول ثم أدخل المبلغ):").pack(side="right", padx=5)
        self.payment_amount = ctk.CTkEntry(payment_frame, placeholder_text="المبلغ المدفوع", width=140)
        self.payment_amount.pack(side="right", padx=5)
        ctk.CTkButton(payment_frame, text="تسديد", command=self.pay_debt,
                      fg_color="green").pack(side="right", padx=5)

        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(padx=20, fill="x")
        ctk.CTkLabel(search_frame, text="بحث:").pack(side="right", padx=(0, 5))
        self.customer_search = ctk.CTkEntry(search_frame, placeholder_text="ابحث عن زبون...")
        self.customer_search.pack(side="right", padx=5, fill="x", expand=True)
        self.customer_search.bind("<KeyRelease>", lambda e: self.refresh_customers())

        columns = ("id", "name", "phone", "debt")
        self.customers_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)
        headings = {"id": "ID", "name": "الاسم", "phone": "الهاتف", "debt": "الدين"}
        for col in columns:
            self.customers_tree.heading(col, text=headings[col])
            self.customers_tree.column(col, anchor="center", width=140)
        self.customers_tree.pack(pady=10, padx=20, fill="both", expand=True)
        self.customers_tree.bind("<<TreeviewSelect>>", self.on_select_customer)

        self.refresh_customers()

    def refresh_customers(self):
        for row in self.customers_tree.get_children():
            self.customers_tree.delete(row)

        term = self.customer_search.get().strip()
        if term:
            self.cursor.execute(
                "SELECT id, name, phone, debt FROM customers WHERE name LIKE ? ORDER BY debt DESC",
                (f"%{term}%",),
            )
        else:
            self.cursor.execute("SELECT id, name, phone, debt FROM customers ORDER BY debt DESC")

        for row in self.cursor.fetchall():
            display = (row[0], row[1], row[2], f"{row[3]:.2f}")
            self.customers_tree.insert("", "end", values=display)

    def on_select_customer(self, event):
        selected = self.customers_tree.selection()
        if not selected:
            return
        values = self.customers_tree.item(selected[0], "values")
        self.selected_customer_id = int(values[0])
        self.c_name.delete(0, "end")
        self.c_name.insert(0, values[1])
        self.c_phone.delete(0, "end")
        self.c_phone.insert(0, values[2])

    def clear_customer_fields(self):
        self.selected_customer_id = None
        self.c_name.delete(0, "end")
        self.c_phone.delete(0, "end")
        self.payment_amount.delete(0, "end")
        self.customers_tree.selection_remove(self.customers_tree.selection())

    def add_customer(self):
        name = self.c_name.get().strip()
        phone = self.c_phone.get().strip()
        if not name:
            messagebox.showerror("خطأ", "أدخل اسم الزبون")
            return
        self.cursor.execute("INSERT INTO customers (name, phone, debt) VALUES (?, ?, 0)", (name, phone))
        self.conn.commit()
        messagebox.showinfo("نجاح", "تم إضافة الزبون")
        self.clear_customer_fields()
        self.refresh_customers()

    def update_customer(self):
        if self.selected_customer_id is None:
            messagebox.showerror("خطأ", "اختر زبونًا من القائمة أولاً")
            return
        name = self.c_name.get().strip()
        phone = self.c_phone.get().strip()
        if not name:
            messagebox.showerror("خطأ", "أدخل اسم الزبون")
            return
        self.cursor.execute("UPDATE customers SET name=?, phone=? WHERE id=?",
                             (name, phone, self.selected_customer_id))
        self.conn.commit()
        messagebox.showinfo("نجاح", "تم تحديث بيانات الزبون")
        self.clear_customer_fields()
        self.refresh_customers()

    def delete_customer(self):
        if self.selected_customer_id is None:
            messagebox.showerror("خطأ", "اختر زبونًا من القائمة أولاً")
            return
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الزبون؟"):
            return
        self.cursor.execute("DELETE FROM customers WHERE id=?", (self.selected_customer_id,))
        self.conn.commit()
        self.clear_customer_fields()
        self.refresh_customers()

    def pay_debt(self):
        if self.selected_customer_id is None:
            messagebox.showerror("خطأ", "اختر زبونًا من القائمة أولاً")
            return
        try:
            amount = self.parse_positive_float(self.payment_amount.get(), "المبلغ المدفوع")
        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
            return
        if amount == 0:
            messagebox.showerror("خطأ", "أدخل مبلغًا أكبر من صفر")
            return

        self.cursor.execute("SELECT debt FROM customers WHERE id=?", (self.selected_customer_id,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("خطأ", "الزبون غير موجود")
            return

        new_debt = max(0.0, row[0] - amount)
        self.cursor.execute("UPDATE customers SET debt=? WHERE id=?", (new_debt, self.selected_customer_id))
        self.conn.commit()
        messagebox.showinfo("نجاح", f"تم تسجيل التسديد. الدين المتبقي: {new_debt:.2f} د.ج")
        self.clear_customer_fields()
        self.refresh_customers()

    # ---------------------------------------------------------------- #
    # تسجيل بيع
    # ---------------------------------------------------------------- #

    def show_sales(self):
        self.set_active_nav("sales")
        self.clear_main()
        self.cart = []

        ctk.CTkLabel(self.main_frame, text="تسجيل عملية بيع", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=15)

        # اختيار منتج وإضافته للسلة
        add_frame = ctk.CTkFrame(self.main_frame)
        add_frame.pack(pady=10, padx=20, fill="x")

        self.cursor.execute("SELECT id, name, sell_price, quantity, buy_price FROM products ORDER BY name")
        self.available_products = self.cursor.fetchall()
        product_labels = [f"{p[1]} — {p[2]:.2f} د.ج (متوفر: {p[3]})" for p in self.available_products]

        if not product_labels:
            product_labels = ["لا توجد منتجات مسجلة"]

        self.sale_product_menu = ctk.CTkOptionMenu(add_frame, values=product_labels, width=320)
        self.sale_product_menu.pack(side="right", padx=5, pady=10)

        self.sale_qty = ctk.CTkEntry(add_frame, placeholder_text="الكمية", width=80)
        self.sale_qty.pack(side="right", padx=5, pady=10)

        ctk.CTkButton(add_frame, text="أضف للسلة", command=self.add_to_cart).pack(side="right", padx=10)

        # سلة المشتريات
        cart_columns = ("name", "qty", "unit_price", "subtotal")
        self.cart_tree = ttk.Treeview(self.main_frame, columns=cart_columns, show="headings", height=8)
        headings = {"name": "المنتج", "qty": "الكمية", "unit_price": "سعر الوحدة", "subtotal": "المجموع"}
        for col in cart_columns:
            self.cart_tree.heading(col, text=headings[col])
            self.cart_tree.column(col, anchor="center", width=140)
        self.cart_tree.pack(pady=10, padx=20, fill="both", expand=True)

        ctk.CTkButton(self.main_frame, text="إزالة العنصر المحدد من السلة", fg_color="#b5432e",
                      command=self.remove_from_cart).pack(pady=(0, 10))

        self.cart_total_label = ctk.CTkLabel(self.main_frame, text="الإجمالي: 0.00 د.ج",
                                              font=ctk.CTkFont(size=18, weight="bold"))
        self.cart_total_label.pack(pady=5)

        # بيانات الدفع
        checkout_frame = ctk.CTkFrame(self.main_frame)
        checkout_frame.pack(pady=10, padx=20, fill="x")

        self.cursor.execute("SELECT id, name FROM customers ORDER BY name")
        customers = self.cursor.fetchall()
        customer_labels = ["بدون زبون (نقدي فقط)"] + [f"{c[0]} - {c[1]}" for c in customers]
        self.sale_customer_menu = ctk.CTkOptionMenu(checkout_frame, values=customer_labels, width=220)
        self.sale_customer_menu.pack(side="right", padx=5, pady=10)

        self.payment_type = ctk.CTkOptionMenu(checkout_frame, values=["نقدي", "كريدي"])
        self.payment_type.pack(side="right", padx=5, pady=10)

        ctk.CTkButton(checkout_frame, text="إتمام عملية البيع", command=self.save_sale,
                      fg_color="green").pack(side="right", padx=10)

    def add_to_cart(self):
        if not self.available_products:
            messagebox.showerror("خطأ", "لا توجد منتجات لإضافتها")
            return
        try:
            qty = self.parse_positive_int(self.sale_qty.get(), "الكمية")
        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
            return
        if qty == 0:
            messagebox.showerror("خطأ", "أدخل كمية أكبر من صفر")
            return

        index = self.sale_product_menu.cget("values").index(self.sale_product_menu.get())
        product_id, name, sell_price, available_qty, buy_price = self.available_products[index]

        already_in_cart = sum(item["qty"] for item in self.cart if item["product_id"] == product_id)
        if already_in_cart + qty > available_qty:
            messagebox.showerror("خطأ", f"الكمية المتوفرة من '{name}' هي {available_qty} فقط")
            return

        self.cart.append({
            "product_id": product_id,
            "name": name,
            "qty": qty,
            "unit_price": sell_price,
            "buy_price": buy_price,
        })
        self.sale_qty.delete(0, "end")
        self.refresh_cart()

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showerror("خطأ", "اختر عنصرًا من السلة أولاً")
            return
        index = self.cart_tree.index(selected[0])
        del self.cart[index]
        self.refresh_cart()

    def refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        total = 0
        for item in self.cart:
            subtotal = item["qty"] * item["unit_price"]
            total += subtotal
            self.cart_tree.insert("", "end", values=(item["name"], item["qty"],
                                                       f"{item['unit_price']:.2f}", f"{subtotal:.2f}"))
        self.cart_total_label.configure(text=f"الإجمالي: {total:.2f} د.ج")

    def save_sale(self):
        if not self.cart:
            messagebox.showerror("خطأ", "السلة فارغة، أضف منتجًا واحدًا على الأقل")
            return

        pay_type = self.payment_type.get()
        customer_choice = self.sale_customer_menu.get()

        customer_id = None
        if customer_choice != "بدون زبون (نقدي فقط)":
            customer_id = int(customer_choice.split(" - ")[0])

        if pay_type == "كريدي" and customer_id is None:
            messagebox.showerror("خطأ", "البيع بالكريدي يتطلب اختيار زبون مسجل")
            return

        # تحقق أخير من توفر الكميات قبل الحفظ
        for item in self.cart:
            self.cursor.execute("SELECT quantity FROM products WHERE id=?", (item["product_id"],))
            row = self.cursor.fetchone()
            if not row or row[0] < item["qty"]:
                messagebox.showerror("خطأ", f"الكمية المتوفرة من '{item['name']}' لم تعد كافية")
                return

        total = sum(item["qty"] * item["unit_price"] for item in self.cart)
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        self.cursor.execute(
            "INSERT INTO sales (customer_id, total, payment_type, date) VALUES (?, ?, ?, ?)",
            (customer_id, total, pay_type, date),
        )
        sale_id = self.cursor.lastrowid

        for item in self.cart:
            self.cursor.execute(
                """INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, buy_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sale_id, item["product_id"], item["name"], item["qty"], item["unit_price"], item["buy_price"]),
            )
            self.cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (item["qty"], item["product_id"]),
            )

        if pay_type == "كريدي":
            self.cursor.execute("SELECT debt FROM customers WHERE id=?", (customer_id,))
            current_debt = self.cursor.fetchone()[0]
            self.cursor.execute("UPDATE customers SET debt=? WHERE id=?",
                                 (current_debt + total, customer_id))

        self.conn.commit()
        messagebox.showinfo("نجاح", f"تم تسجيل عملية البيع بنجاح. الإجمالي: {total:.2f} د.ج")
        self.show_sales()


if __name__ == "__main__":
    app = MaktabaApp()
    app.mainloop()
