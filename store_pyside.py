# store_pyside.py
import sys
import os
import sqlite3
import jdatetime
from PySide6 import QtCore, QtGui, QtWidgets

# ========================= Determine base directory (for PyInstaller) =========================
# When the app is bundled with PyInstaller, files are located inside sys._MEIPASS
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the database (works correctly even when bundled)
DB_PATH = os.path.join(BASE_DIR, "products.db")


# ========================= Persian number helper =========================
def persian_to_english_number(text: str) -> str:
    """Convert Persian digits in text to English digits."""
    if text is None:
        return ""
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    trans_table = str.maketrans(persian_digits, english_digits)
    return text.translate(trans_table)


# ========================= Store (Database + Logic) =========================
class Store:
    def __init__(self, db_path="products.db"):
        self.db_path = db_path
        self.products = []
        self.total_sales = 0
        self.init_db()
        self.load_products_from_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize the database and create tables if not exist."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS products 
               (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL, number INTEGER)"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS sales 
               (id INTEGER PRIMARY KEY, product_name TEXT, number INTEGER, total_price REAL, date TEXT)"""
        )
        conn.commit()
        conn.close()

    def load_products_from_db(self):
        """Load all products from the database."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products")
        self.products = cur.fetchall()
        conn.close()

    def add_product(self, name, price, number):
        """Add a new product."""
        name = name.strip()
        if not name:
            return False, "Product name cannot be empty."

        for product in self.products:
            if product[1] == name:
                return False, "A product with this name already exists."

        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO products (name, price, number) VALUES (?, ?, ?)",
                (name, price, number),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            return False, "Database error: " + str(e)
        conn.close()
        self.load_products_from_db()
        return True, "Product added successfully."

    def edit_product(self, product_id, new_name, new_price, new_number):
        """Edit product details."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE products SET name=?, price=?, number=? WHERE id=?",
            (new_name, new_price, new_number, product_id),
        )
        conn.commit()
        conn.close()
        self.load_products_from_db()
        return True

    def sell_product(self, name, number):
        """Sell a product and record it in sales history."""
        self.load_products_from_db()
        for product in self.products:
            if product[1] == name:
                if product[3] < number:
                    return False, "Not enough quantity in stock."

                total_price = number * product[2]
                self.total_sales += total_price
                new_number = product[3] - number
                self.update_product_number(product[0], new_number)

                today_jalali = jdatetime.date.today().strftime("%Y-%m-%d")
                conn = self._connect()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO sales (product_name, number, total_price, date) VALUES (?, ?, ?, ?)",
                    (name, number, total_price, today_jalali),
                )
                conn.commit()
                conn.close()
                self.load_products_from_db()
                return True, f"Total price: {int(total_price)} Toman"
        return False, "Product not found."

    def update_product_number(self, product_id, new_number):
        """Update product quantity."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("UPDATE products SET number=? WHERE id=?", (new_number, product_id))
        conn.commit()
        conn.close()
        self.load_products_from_db()

    def remove_product(self, product_id):
        """Remove a product from the database."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
        self.load_products_from_db()

    def search_product(self, name):
        """Search for a product by name (case-insensitive)."""
        result = []
        for product in self.products:
            if name.strip().lower() in product[1].lower():
                result.append(product)
        return result

    def sales_report(self, start_date=None, end_date=None):
        """Return total sales between two given dates."""
        conn = self._connect()
        cur = conn.cursor()
        if start_date and end_date:
            cur.execute(
                "SELECT SUM(total_price) FROM sales WHERE date BETWEEN ? AND ?",
                (start_date, end_date),
            )
        else:
            cur.execute("SELECT SUM(total_price) FROM sales")
        total = cur.fetchone()[0]
        conn.close()
        return int(total) if total else 0

    def clear_sales_history(self):
        """Delete all sales records."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM sales")
        conn.commit()
        conn.close()

    def total_inventory_value(self):
        """Calculate the total value of inventory."""
        total_value = 0
        for product in self.products:
            total_value += product[2] * product[3]
        return int(total_value)


# ========================= Qt Main Window =========================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.setWindowTitle("Product Sales Management")
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)
        self._setup_ui()
        self.refresh_table()

    # ----------------------------------------------------------------------
    # UI SETUP
    # ----------------------------------------------------------------------
    def _setup_ui(self):
        """Setup the layout and widgets."""
        central = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # ---------- Left panel: vertical buttons ----------
        left_panel = QtWidgets.QFrame()
        left_panel.setFixedWidth(260)
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_panel.setLayout(left_layout)

        # Header box
        header = QtWidgets.QLabel("AR7MS")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setFixedHeight(80)
        header.setStyleSheet("font-size:18pt; font-weight:bold; color:white;")
        header_frame = QtWidgets.QFrame()
        header_frame.setStyleSheet(
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #002f4b, stop:1 #1f8a70); border-radius:10px;"
        )
        hf_layout = QtWidgets.QVBoxLayout()
        hf_layout.addWidget(header)
        header_frame.setLayout(hf_layout)
        left_layout.addWidget(header_frame)

        # Helper to create styled buttons
        def make_btn(text, color_from, color_to):
            btn = QtWidgets.QPushButton(text)
            btn.setFixedHeight(48)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    color: white;
                    font-size: 13pt;
                    border-radius: 10px;
                    padding: 6px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color_from}, stop:1 {color_to});
                }}
                QPushButton:hover {{ transform: scale(1.01); }}
                """
            )
            return btn

        # Buttons
        self.btn_show_all = make_btn("Show All Products", "#00a8ff", "#0072ff")
        self.btn_add = make_btn("Add Product", "#10ac84", "#2ecc71")
        self.btn_edit = make_btn("Edit Product", "#f39c12", "#f1c40f")
        self.btn_sell = make_btn("Sell Product", "#12f312", "#c6c9cb")
        self.btn_search = make_btn("Search Product", "#0abde3", "#00a8ff")
        self.btn_remove = make_btn("Remove Product", "#e74c3c", "#ff6b6b")
        self.btn_report = make_btn("Sales Report", "#3498db", "#2ecc71")
        self.btn_inventory = make_btn("Total Inventory", "#d7deabff", "#485500ff")
        self.btn_clear_sales = make_btn("Clear Sales History", "#fc008f", "#fc008f")
        self.btn_quit = make_btn("Exit", "#c0392b", "#e74c3c")
        self.btn_low_stock = make_btn("Low Stock Products", "#ff7700", "#ff8c00")

        for b in [
            self.btn_show_all,
            self.btn_add,
            self.btn_edit,
            self.btn_sell,
            self.btn_search,
            self.btn_remove,
            self.btn_report,
            self.btn_inventory,
            self.btn_low_stock,
            self.btn_clear_sales,
            self.btn_quit,
        ]:
            left_layout.addWidget(b)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)

        # ---------- Right panel: form + table ----------
        right_panel = QtWidgets.QFrame()
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_panel.setLayout(right_layout)

        # Top form: name, number, price
        form_frame = QtWidgets.QFrame()
        form_layout = QtWidgets.QGridLayout()
        form_layout.setHorizontalSpacing(8)
        form_layout.setVerticalSpacing(8)
        form_frame.setLayout(form_layout)

        lbl_name = QtWidgets.QLabel("Product Name:")
        lbl_number = QtWidgets.QLabel("Quantity:")
        lbl_price = QtWidgets.QLabel("Price (Toman):")

        lbl_name.setStyleSheet("color: white; font-size: 16pt;")
        lbl_number.setStyleSheet("color: white; font-size: 16pt;")
        lbl_price.setStyleSheet("color: white; font-size: 16pt;")

        self.input_name = QtWidgets.QLineEdit()
        self.input_name.setPlaceholderText("Enter product name")
        self.input_number = QtWidgets.QLineEdit()
        self.input_number.setPlaceholderText("e.g. 10")
        self.input_price = QtWidgets.QLineEdit()
        self.input_price.setPlaceholderText("e.g. 25000")

        # Right-to-left alignment for Persian compatibility
        for w in (self.input_name, self.input_number, self.input_price):
            w.setLayoutDirection(QtCore.Qt.RightToLeft)
            w.setFixedHeight(40)
            w.setStyleSheet("font-size:13pt; padding-right:8px;")

        form_layout.addWidget(self.input_name, 0, 0)
        form_layout.addWidget(lbl_name, 0, 1)
        form_layout.addWidget(self.input_number, 1, 0)
        form_layout.addWidget(lbl_number, 1, 1)
        form_layout.addWidget(self.input_price, 2, 0)
        form_layout.addWidget(lbl_price, 2, 1)
        right_layout.addWidget(form_frame)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Price (Toman)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("font-size:17pt;")
        right_layout.addWidget(self.table)
        main_layout.addWidget(right_panel, stretch=1)

        # Button connections
        self.btn_show_all.clicked.connect(self.refresh_table)
        self.btn_add.clicked.connect(self.on_add_product)
        self.btn_edit.clicked.connect(self.on_edit_product)
        self.btn_sell.clicked.connect(self.on_sell_product)
        self.btn_search.clicked.connect(self.on_search_product)
        self.btn_remove.clicked.connect(self.on_remove_product)
        self.btn_report.clicked.connect(self.on_report)
        self.btn_inventory.clicked.connect(self.on_inventory)
        self.btn_clear_sales.clicked.connect(self.on_clear_sales)
        self.btn_quit.clicked.connect(self.close)
        self.btn_low_stock.clicked.connect(self.on_low_stock)

        # Shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self.input_name, activated=self.select_all_input)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self.input_number, activated=self.select_all_input)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+A"), self.input_price, activated=self.select_all_input)

        # Overall window style (gradient background)
        self.setStyleSheet(
            """
            QMainWindow { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
            }
            QTableWidget { background: rgba(255,255,255,0.95); border-radius:8px; }
            """
        )

    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------
    def select_all_input(self):
        w = self.focusWidget()
        if isinstance(w, QtWidgets.QLineEdit):
            w.selectAll()

    # ----------------------------------------------------------------------
    # Table management
    # ----------------------------------------------------------------------
    def refresh_table(self):
        """Refresh the table with all products."""
        self.store.load_products_from_db()
        products = self.store.products
        self.table.setRowCount(0)
        for row_idx, p in enumerate(products):
            self.table.insertRow(row_idx)
            name_item = QtWidgets.QTableWidgetItem(str(p[1]))
            name_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            number_item = QtWidgets.QTableWidgetItem(str(p[3]))
            number_item.setTextAlignment(QtCore.Qt.AlignCenter)
            price_item = QtWidgets.QTableWidgetItem(str(int(p[2])))
            price_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, number_item)
            self.table.setItem(row_idx, 2, price_item)


    def get_selected_product_id(self):
        """Return the ID of the selected product in the table."""
        sel = self.table.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        name = self.table.item(row, 0).text()
        for p in self.store.products:
            if p[1] == name:
                return p[0]
        return None

    # ----------------------------------------------------------------------
    # Button actions
    # ----------------------------------------------------------------------
    def on_add_product(self):
        """Handle 'Add Product' action."""
        name = self.input_name.text().strip()
        try:
            number_text = persian_to_english_number(self.input_number.text().strip())
            price_text = persian_to_english_number(self.input_price.text().strip())
            number = int(number_text) if number_text != "" else 0
            price = float(price_text) if price_text != "" else 0.0
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Please enter valid numeric values.")
            return

        ok, msg = self.store.add_product(name, price, number)
        if ok:
            QtWidgets.QMessageBox.information(self, "Success", msg)
            self.input_name.clear()
            self.input_number.clear()
            self.input_price.clear()
            self.refresh_table()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", msg)

    def on_edit_product(self):
        """Handle 'Edit Product' action."""
        pid = self.get_selected_product_id()
        if pid is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "No product selected.")
            return

        cur = next((p for p in self.store.products if p[0] == pid), None)
        if cur is None:
            QtWidgets.QMessageBox.warning(self, "Error", "Product not found.")
            return

        name, number, price = cur[1], cur[3], cur[2]

        new_name, ok1 = QtWidgets.QInputDialog.getText(self, "Edit Name", "New name:", QtWidgets.QLineEdit.Normal, name)
        if not ok1:
            return
        new_number, ok2 = QtWidgets.QInputDialog.getInt(self, "Edit Quantity", "New quantity:", number, 0, 10**9)
        if not ok2:
            return
        new_price, ok3 = QtWidgets.QInputDialog.getDouble(self, "Edit Price", "New price:", price, 0, 10**12, 2)
        if not ok3:
            return

        self.store.edit_product(pid, new_name, float(new_price), int(new_number))
        QtWidgets.QMessageBox.information(self, "Success", "Product updated successfully.")
        self.refresh_table()

    def on_sell_product(self):
        """Handle 'Sell Product' action."""
        pid = self.get_selected_product_id()
        if pid is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "No product selected.")
            return

        prod = next((p for p in self.store.products if p[0] == pid), None)
        if not prod:
            QtWidgets.QMessageBox.warning(self, "Error", "Product not found.")
            return

        max_count = prod[3]
        count, ok = QtWidgets.QInputDialog.getInt(
            self, "Sell Product", "Quantity to sell:", 1, 1, max_count if max_count > 0 else 1
        )
        if not ok:
            return

        ok_flag, msg = self.store.sell_product(prod[1], count)
        if ok_flag:
            QtWidgets.QMessageBox.information(self, "Result", msg)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", msg)
        self.refresh_table()

    def on_search_product(self):
        """Handle 'Search Product' action."""
        text, ok = QtWidgets.QInputDialog.getText(self, "Search", "Enter product name or part of it:")
        if not ok:
            return

        results = self.store.search_product(text)
        self.table.setRowCount(0)
        for row_idx, p in enumerate(results):
            self.table.insertRow(row_idx)
            name_item = QtWidgets.QTableWidgetItem(str(p[1]))
            name_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            number_item = QtWidgets.QTableWidgetItem(str(p[3]))
            number_item.setTextAlignment(QtCore.Qt.AlignCenter)
            price_item = QtWidgets.QTableWidgetItem(str(int(p[2])))
            price_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, number_item)
            self.table.setItem(row_idx, 2, price_item)

        if not results:
            QtWidgets.QMessageBox.information(self, "Result", "No product found.")

    def on_remove_product(self):
        """Handle 'Remove Product' action."""
        pid = self.get_selected_product_id()
        if pid is None:
            QtWidgets.QMessageBox.warning(self, "Warning", "No product selected.")
            return

        ret = QtWidgets.QMessageBox.question(
            self, "Delete", "Are you sure you want to delete this product?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if ret == QtWidgets.QMessageBox.Yes:
            self.store.remove_product(pid)
            QtWidgets.QMessageBox.information(self, "Success", "Product deleted successfully.")
            self.refresh_table()

    def on_report(self):
        """Handle 'Sales Report' action."""
        start_date, ok1 = QtWidgets.QInputDialog.getText(self, "Start Date", "Enter start date (YYYY-MM-DD):")
        if not ok1 or not start_date.strip():
            return
        end_date, ok2 = QtWidgets.QInputDialog.getText(self, "End Date", "Enter end date (YYYY-MM-DD):")
        if not ok2 or not end_date.strip():
            return

        total = self.store.sales_report(start_date.strip(), end_date.strip())
        QtWidgets.QMessageBox.information(
            self, "Sales Report", f"Total sales between {start_date} and {end_date}: {total} Toman"
        )

    def on_inventory(self):
        """Handle 'Total Inventory' action."""
        val = self.store.total_inventory_value()
        QtWidgets.QMessageBox.information(
            self, "Total Inventory", f"Total inventory value based on product prices: {val} Toman"
        )

    def on_clear_sales(self):
        """Handle 'Clear Sales History' action."""
        ret = QtWidgets.QMessageBox.question(
            self, "Clear History", "Delete all sales history?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if ret == QtWidgets.QMessageBox.Yes:
            self.store.clear_sales_history()
            QtWidgets.QMessageBox.information(self, "Success", "Sales history cleared.")

    def on_low_stock(self):
        """Display products with low stock (≤ 2)."""
        self.store.load_products_from_db()
        results = [p for p in self.store.products if p[3] <= 2]
        self.table.setRowCount(0)
        for row_idx, p in enumerate(results):
            self.table.insertRow(row_idx)
            name_item = QtWidgets.QTableWidgetItem(str(p[1]))
            name_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            number_item = QtWidgets.QTableWidgetItem(str(p[3]))
            number_item.setTextAlignment(QtCore.Qt.AlignCenter)
            price_item = QtWidgets.QTableWidgetItem(str(int(p[2])))
            price_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(row_idx, 0, name_item)
            self.table.setItem(row_idx, 1, number_item)
            self.table.setItem(row_idx, 2, price_item)

        if not results:
            QtWidgets.QMessageBox.information(self, "Result", "No low-stock products found.")


# ========================= Main Application =========================
def main():
    """Launch the main application."""
    app = QtWidgets.QApplication(sys.argv)

    # Set font (for better Persian/Unicode display if supported)
    font = QtGui.QFont("Tahoma", 10)
    app.setFont(font)

    store = Store()
    w = MainWindow(store)
    w.showFullScreen()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
