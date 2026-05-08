import flet as ft
import httpx
import re
import hashlib
from client import API_ROOT, main

from app.ui.ui_account import Summary

from app.managers.account_manager import AccountManager
from app.managers.account_manager import login

import asyncio 


# Main screen with options to login or create account
class MainScreen(ft.Column):
    def __init__(self, id, page):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # user_id for application state
        self.id = id
        self.page = page

        self.back_button = ft.Button("Back", on_click=self.show_menu)

        self.menu_controls = [
            ft.Text("Welcome to Snuzzl!", color='black', size=25, weight='bold'),
            ft.Row([
                ft.Button("Login", on_click=self.login),
                ft.Button("Create Account", on_click=self.create_account)
            ], alignment='center', spacing=20)
        ]

    def show_menu(self, e=None):
        self.controls.clear()
        self.controls = self.menu_controls
        self.update()

    def login(self, e=None):
        self.controls.clear()
        self.controls = [Login(self.id, self.back_button)]
        self.update()

    def create_account(self, e=None):
        self.controls.clear()
        self.controls = [CreateAccount(self.id, self.back_button, self.page)]
        self.update()

class CreateAccount(ft.Column):
    def __init__(self, back_button, page):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.page = page

        # creates each text field and assigns to a varaible
        self.username_field = self.create_input("Username", "username")
        self.fname_field = self.create_input("First Name", "Jane")
        self.email_field = self.create_input("Email", "example@gmail.com")
        self.password_field = self.create_input("Password", "Enter password", password=True)
        self.confirm_password_field = self.create_input("Confirm Password", "Re-enter password", password=True)
        
        self.dob_picker = ft.DatePicker(on_change=self.update_dob)
        self.page.overlay.append(self.dob_picker)

        self.dob_field = ft.TextField(
            label="Date of Birth",
            hint_text="Select date of birth",
            read_only=True,
            width=200,
            on_click=self.open_dob
        )

        self.error_message = ft.Text("", color='red')

        self.controls = [
            ft.Text("Enter Details", color='black', size=25, weight='bold'),
            self.username_field,
            self.fname_field,
            self.email_field,
            self.password_field,
            self.confirm_password_field,
            self.dob_field,
            ft.Row([
                back_button,
                ft.Button("Submit", on_click=self.submit),
            ], alignment='center', spacing=20),
            self.error_message
        ]

    def create_input(self, label_text, hint, password=False):
        return ft.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
            )

    def is_valid_email(email):
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

    def open_dob(self):
        self.dob_picker.open = True
        self.page.update()

    def update_dob(self, e):
        if self.dob_picker.value:
            self.dob_field.value = self.dob_picker.value.strftime("%Y/%m/%d")
            self.page.update()

    def _validate_password(self, password):
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return True

    async def submit(self, e=None):

        self.error_message.value = ""

        fields = [
            (self.username_field, "Username cannot be empty"),
            (self.fname_field, "First name cannot be empty"),
            (self.email_field, "Email cannot be empty"),
            (self.password_field, "Password cannot be empty"),
            (self.dob_field, "Date of birth cannot be empty")
        ]

        for field, message in fields:
            if not field.value or not field.value.strip():
                field.error_text = message
                self.error_message.value = "Please fill in all fields"
                self.page.update()
                return
            else:
                field.error_text = None

        if self.password_field.value != self.confirm_password_field.value:
            self.confirm_password_field.error_text = "Passwords do not match"
            self.error_message.value = "Please ensure passwords match"
            self.page.update()
            return

        if not self.is_valid_email(self.email_field.value):
            self.email_field.error_text = "Invalid email format"
            self.error_message.value = "Please enter a valid email address"
            self.page.update()
            return

        try:
            self._validate_password(self.password_field.value)
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"

        payload = {
            "email": self.email_field.value,
            "username": self.username_field.value,
            "fname": self.fname_field.value,
            "dob": self.dob_field.value,
            "password": hashlib.sha256(self.password_field.value.encode('utf-8')).hexdigest()
        }

        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/create_account", json=payload)
            result = result.json()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"

        main.menu()


# Screen for logging into an existing account
class Login(ft.Column):
    def __init__(self, id, back_button):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # A user_id object from client.py, used to track application state
        self.id = id

        self.username_field = self.create_input("Username", "username")
        self.password_field = self.create_input("Password", "Enter password", password=True)
        self.error_message = ft.Text("")

        self.controls = [
            ft.Text("Login", color='black', size=25, weight='bold'),
            self.username_field,
            self.password_field,
            ft.Row([
                back_button,
                ft.Button("Submit", on_click=self.submit),
            ], alignment='center', spacing=20),
            self.error_message
        ]

    def create_input(self, label_text, hint, password=False):
        return ft.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
        )

    async def submit(self, e=None):
        if self.username_field.value == "":
            self.error_message.value = "Missing Username"
            return
        if self.password_field.value == "":
            self.error_message.value = "Missing Password"
            return

        payload = {
            "username": self.username_field.value,
            "password": hashlib.sha256(self.password_field.value.encode('utf-8')).hexdigest()
        }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/login", json=payload)
            result = result.json()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
        if result['success']:
            id.user_id = result['user_id']
            main.menu()
        else:
            # Show error message
            self.error_message.value = f"Login failed: {result['message']}"
            self.update()