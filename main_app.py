# Author: Robert Perales
# Date: 05/05/2024
# Version: 1
# Description: This program implements a simple account management system with a GUI using Tkinter.
# Users can create accounts, login, reset their PINs, and access a main menu with various options.
# The program stores user data in an SQLite database and hashes PINs for security.

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import sqlite3
import hashlib
import os
import webbrowser

# Predefined security questions for account creation
SECURITY_QUESTIONS = [
    "-- Select --", "What is your mother's maiden name?", "What city were you born in?",
    "What is the name of your first pet?", "What is your favorite color?",
    "What is the name of your elementary school?"
]

# Predefined account types for accoeunt creation
ACCOUNT_TYPES = ["-- Select --", "User", "Vendor"]


def connect_db():
    """Connect to the SQLite database."""
    return sqlite3.connect("accounts.db")


def setup_db():
    """Set up the SQLite database."""
    with connect_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS accounts
                        (first_name TEXT, last_name TEXT, address_line1 TEXT, address_line2 TEXT,
                         account_type TEXT, username TEXT, pin TEXT, security_question TEXT, security_answer TEXT)''')


def hash_pin(pin):
    """Hash the PIN using SHA-256."""
    return hashlib.sha256(pin.encode()).hexdigest()


def exit_program():
    """Exit the program."""
    sys.exit()


class BaseWindow(tk.Tk):
    """Base window class with common functionality."""

    def __init__(self, title):
        super().__init__()
        self.title(title)
        self.default_font = tkFont.Font(family="Helvetica", size=12)
        self.option_add("*Font", self.default_font)
        self.center_window()

    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        self.geometry(f"+{x_coordinate}+{y_coordinate}")

    def add_exit_button(self):
        """Add an exit button to the window."""
        exit_button = tk.Button(self, text="Exit", command=exit_program, font=self.default_font)
        exit_button.grid(row=11, columnspan=2, padx=10, pady=10, sticky="e")


class CreateAccountWindow(BaseWindow):
    """Window for creating a new account."""

    def __init__(self, parent):
        super().__init__("Create Account")
        self.entries = None
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        """Create GUI elements for account creation."""
        self.entries = {}
        labels = ["First Name:", "Last Name:", "Address Line 1:", "Address Line 2:", "Account Type:",
                  "Username:", "PIN (4 digits):", "Confirm PIN:", "Security Question:", "Security Answer:"]
        max_label_width = max(len(label) for label in labels)
        for idx, label in enumerate(labels):
            tk.Label(self, text=label, width=max_label_width, anchor="w", font=self.default_font).grid(row=idx,
                                                                                                       column=0,
                                                                                                       padx=10, pady=5)
            entry = ttk.Entry(self, font=self.default_font, show="*" if "PIN" in label else None, width=30)
            entry.grid(row=idx, column=1, sticky="ew", padx=10, pady=5)
            self.entries[label] = entry

        self.setup_combobox("Account Type:", 4, ACCOUNT_TYPES)
        self.setup_combobox("Security Question:", 8, SECURITY_QUESTIONS)

        tk.Button(self, text="Create Account", command=self.create_account_button_click, font=self.default_font,
                  width=20).grid(row=10, columnspan=2, padx=10, pady=10)
        self.add_exit_button()

    def setup_combobox(self, label, row, values):
        """Set up a combobox widget."""
        combobox = ttk.Combobox(self, values=values, width=max(len(label) for label in values), font=self.default_font,
                                state="readonly")
        combobox.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        combobox.set("-- Select --")
        self.entries[label] = combobox

    def create_account_button_click(self):
        """Handle the 'Create Account' button click."""
        entries = self.entries
        first_name = entries["First Name:"].get().strip()
        last_name = entries["Last Name:"].get().strip()
        address_line1 = entries["Address Line 1:"].get().strip()
        address_line2 = entries["Address Line 2:"].get().strip()
        account_type = entries["Account Type:"].get().strip()
        username = entries["Username:"].get().strip()
        pin = entries["PIN (4 digits):"].get().strip()
        confirm_pin = entries["Confirm PIN:"].get().strip()
        security_question = entries["Security Question:"].get().strip()
        security_answer = entries["Security Answer:"].get().strip()

        if not (
                first_name and last_name and address_line1 and account_type and username and pin and confirm_pin and security_question and security_answer):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if not pin.isdigit() or len(pin) != 4:
            messagebox.showerror("Error", "PIN must be a 4-digit number.")
            return

        if pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match.")
            return

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE username=?", (username,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Username already exists. Please choose another one.")
                return

        pin_hash = hash_pin(pin)
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO accounts (first_name, last_name, address_line1, address_line2,
                              account_type, username, pin, security_question, security_answer)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (first_name, last_name, address_line1, address_line2, account_type, username,
                            pin_hash, security_question, security_answer))
            conn.commit()

        messagebox.showinfo("Success", "Account created successfully. You can now login.")
        self.destroy()
        self.parent.deiconify()


def open_link_browser(link):
    """Open a link in the default web browser."""
    os.system(f"start {link}")


def open_link(link):
    """Open a link in the default web browser."""
    webbrowser.open_new(link)


class MainMenuWindow(BaseWindow):
    """Window for the main menu."""

    def __init__(self, parent):
        super().__init__("Main Menu")
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        """Create GUI elements for the main menu."""
        ttk.Button(self, text="1", command=lambda: open_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                                                             "&ab_channel=RickAstley"), style="TButton",
                   width=60).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ttk.Button(self, text="2", command=lambda: open_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                                                             "&ab_channel=RickAstley"), style="TButton",
                   width=60).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ttk.Button(self, text="3", command=lambda: open_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                                                             "&ab_channel=RickAstley"), style="TButton",
                   width=60).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        ttk.Button(self, text="4", command=lambda: open_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                                                             "&ab_channel=RickAstley"), style="TButton",
                   width=60).grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ttk.Button(self, text="Cat1", command=lambda: open_link_browser(
            "https://drive.google.com/file/d/10WXq4WZX0j365DwTPbYnXTkxaX0HtDxw/view?usp=sharing"), style="TButton",
                   width=60).grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ttk.Button(self, text="Cat2", command=lambda: open_link_browser(
            "https://drive.google.com/file/d/13zeFjUGoa59GM0acTMV8tX3t0_4FS1N9/view?usp=sharing"), style="TButton",
                   width=60).grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        logout_button = tk.Button(self, text="Logout", command=self.logout, font=self.default_font, width=10)
        logout_button.grid(row=3, column=1, padx=10, pady=10, sticky="se")

    def logout(self):
        """Handle the 'Logout' button click."""
        try:
            self.parent.deiconify()
        except Exception as e:
            print(f"Error: {str(e)} - Reinitializing LoginWindow.")
            self.parent = LoginWindow()
            self.parent.mainloop()
        finally:
            self.destroy()


class ResetPinWindow(tk.Toplevel):
    """Window for resetting the PIN."""

    def __init__(self, parent, username):
        super().__init__(parent)
        self.confirm_pin_entry = None
        self.new_pin_entry = None
        self.title("Reset PIN")
        self.parent = parent
        self.username = username
        self.create_widgets()

    def create_widgets(self):
        """Create GUI elements for PIN reset."""
        tk.Label(self, text="New PIN:", font=self.parent.default_font).pack(pady=5)
        self.new_pin_entry = ttk.Entry(self, show="*", font=self.parent.default_font)
        self.new_pin_entry.pack(pady=5)

        tk.Label(self, text="Confirm New PIN:", font=self.parent.default_font).pack(pady=5)
        self.confirm_pin_entry = ttk.Entry(self, show="*", font=self.parent.default_font)
        self.confirm_pin_entry.pack(pady=5)

        tk.Button(self, text="Reset PIN", command=self.reset_pin, font=self.parent.default_font, width=20).pack(pady=10)

    def reset_pin(self):
        """Handle the 'Reset PIN' button click."""
        new_pin = self.new_pin_entry.get().strip()
        confirm_pin = self.confirm_pin_entry.get().strip()

        if not (new_pin and confirm_pin):
            messagebox.showerror("Error", "Please enter both new PIN and confirm PIN.")
            return

        if new_pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match.")
            return

        if not new_pin.isdigit() or len(new_pin) != 4:
            messagebox.showerror("Error", "PIN must be a 4-digit number.")
            return

        # Update the PIN in the database
        pin_hash = hash_pin(new_pin)
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET pin=? WHERE username=?", (pin_hash, self.username))
            conn.commit()

        messagebox.showinfo("Success", "PIN reset successfully.")
        self.destroy()
        self.parent.deiconify()


class LoginWindow(BaseWindow):
    """Window for user login."""

    def __init__(self):
        super().__init__("Login")
        self.pin_entry = None
        self.username_entry = None
        self.create_widgets()

    def create_widgets(self):
        """Create GUI elements for login."""
        tk.Label(self, text="Username:", font=self.default_font).grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = ttk.Entry(self, font=self.default_font, width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(self, text="PIN:", font=self.default_font).grid(row=1, column=0, padx=10, pady=5)
        self.pin_entry = ttk.Entry(self, show="*", font=self.default_font, width=30)
        self.pin_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Button(self, text="Login", command=self.login, font=self.default_font, width=20).grid(row=2, columnspan=2,
                                                                                                 padx=10, pady=10)
        tk.Button(self, text="Create Account", command=self.open_create_account_window, font=self.default_font,
                  width=20).grid(row=3, columnspan=2, padx=10, pady=10)
        tk.Button(self, text="Forgot PIN?", command=self.forgot_pin, font=self.default_font, width=20).grid(row=4,
                                                                                                            columnspan=2,
                                                                                                            padx=10,
                                                                                                            pady=10)
        self.add_exit_button()

    def login(self):
        """Handle the 'Login' button click."""
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()

        if not (username and pin):
            messagebox.showerror("Error", "Please enter both username and PIN.")
            return

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE username=? AND pin=?", (username, hash_pin(pin)))
            account = cursor.fetchone()

        if account:
            messagebox.showinfo("Success", "Login successful!")
            self.withdraw()
            main_menu = MainMenuWindow(self)
            main_menu.mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or PIN.")

    def open_create_account_window(self):
        """Open the 'Create Account' window."""
        self.withdraw()
        create_account_window = CreateAccountWindow(self)
        create_account_window.mainloop()

    def forgot_pin(self):
        """Handle the 'Forgot PIN?' button click."""
        # Retrieve username from entry widget
        username = self.username_entry.get().strip()

        if not username:
            messagebox.showerror("Error", "Please enter your username.")
            return

        # Query the database to get security question
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT security_question FROM accounts WHERE username=?", (username,))
            result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Username not found.")
            return

        security_question = result[0]

        # Create a new window to display security question and get answer
        self.withdraw()  # Hide the login window

        security_window = tk.Toplevel()
        security_window.title("Security Question")
        security_window.protocol("WM_DELETE_WINDOW",
                                 lambda: self.on_close_security(security_window))  # Handle window close event

        tk.Label(security_window, text=security_question, font=self.default_font).pack(pady=10)

        answer_entry = ttk.Entry(security_window, font=self.default_font)
        answer_entry.pack(pady=5)

        submit_button = tk.Button(security_window, text="Submit",
                                  command=lambda: self.submit_answer(username, answer_entry.get(), security_window),
                                  font=self.default_font)
        submit_button.pack(pady=5)

    def submit_answer(self, username, answer, window):
        """Submit the security answer."""
        # Retrieve stored security answer
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT security_answer FROM accounts WHERE username=?", (username,))
            correct_answer = cursor.fetchone()[0]

        if answer == correct_answer:
            # Security answer is correct, allow PIN reset
            messagebox.showinfo("Success", "Security answer correct. You can now reset your PIN.")
            window.destroy()  # Close the security question window
            reset_pin_window = ResetPinWindow(self, username)
            reset_pin_window.mainloop()
        else:
            messagebox.showerror("Error", "Incorrect answer to security question.")

    def on_close_security(self, window):
        """Handle the close event of the security question window."""
        self.deiconify()
        window.destroy()


if __name__ == "__main__":
    setup_db()
    app = LoginWindow()
    app.mainloop()
