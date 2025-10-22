# 🛒 Product Sales Management (PySide6)

A desktop application built with **PySide6** for managing product inventory and sales, with full support for Persian language and numbers. Perfect for small shops or personal use! 🇮🇷💻

---

## 🔹 Features

* **📦 Inventory Management**: Add, edit, and remove products easily.
* **💰 Sales Tracking**: Record product sales and calculate total revenue automatically.
* **🔍 Search**: Quickly find products by name (case-insensitive).
* **📊 Sales Reports**: Generate sales reports for any date range.
* **📈 Inventory Value**: Calculate the total value of all products in stock.
* **⚠️ Low Stock Alerts**: Highlight products with very low stock.
* **🗑 Clear Sales History**: Reset all sales data if needed.
* **🌐 Persian/Unicode Friendly**: Proper handling of Persian numbers and text.
* **🎨 Modern UI**: Gradient backgrounds, styled buttons, and an intuitive layout.

---

## 🖥️ How It Works

1. Launch the app. The main window opens in full screen.
2. Use the **left panel** to access actions:

   * Show all products
   * Add a new product
   * Edit or remove a product
   * Sell a product and update inventory
   * View sales reports or total inventory value
   * Clear sales history
   * Highlight low-stock products
   * Exit the application
3. The **right panel** displays:

   * A form to enter product details (name, quantity, price)
   * A dynamic table showing all products

---

## ⚙️ How to Run

1. Install required packages using `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```
2. Make sure `products.db` is in the same folder as the script.
3. Run the application:

   ```bash
   python store_pyside.py
   ```
4. The app will launch in **full screen** with all functionality ready to use.

---

## 📝 Notes

* Persian numbers are automatically converted to English numbers for calculations.
* The database (`products.db`) stores all products and sales history.
* Can be bundled with **PyInstaller** for a standalone executable.

---
## 💡 Screenshots  

You can upload your screenshots to the repository and use them here. Replace the URL with your image path.

![Screenshot 1](https://github.com/The-AR7MS/Product-Sales-Management/blob/main/Screenshot%202025-10-22%20093516.png)


This project makes inventory and sales management simple, colorful, and efficient! 🎉


