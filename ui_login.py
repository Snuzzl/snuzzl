import flet as ft
import re
from ui_account import homePage
from ui_metrics import Metrics

from account_manager import AccountManager
from account_manager import login

import asyncio 


def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)


class Account:
    def __init__(self):
        self.username = ""
        self.fname = ""
        self.email = ""
        self.password = ""
        self.dob = ""
        self.id = None

# Main screen with options to login or create account

class MainScreen:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()
        self.page.add(
            ft.Text("Welcome to Snuzzl!",
                    color='black', size=25, weight='bold'),
            ft.Row([
                ft.Button("Login",
                          on_click=self.login),
                ft.Button("Create Account",
                          on_click=self.create_account)
            ], alignment='center', spacing=20),
            ft.Button("View Metrics",
                      on_click=lambda e:
                      Metrics(self.page, self.acc).show()
                      )
        )

    def login(self, e):
        Login(self.page, self.acc).show()

    def create_account(self, e):
        CreateAccount(self.page, self.acc).show()

# Screen for creating a new account


class CreateAccount:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

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

    def show(self):
        self.page.clean()

        # creates each text field and assigns to a varaible
        self.username_field = self.create_input("Username", "username")
        self.fname_field = self.create_input("First Name", "Jane")
        self.email_field = self.create_input("Email", "example@gmail.com")
        self.password_field = self.create_input("Password", "Enter password",
                                                password=True)
        self.confirm_password_field = self.create_input("Confirm Password",
                                                        "Re-enter password",
                                                        password=True)
        
        self.dob_picker = ft.DatePicker(on_change=self.update_dob)
        self.page.overlay.append(self.dob_picker)

        self.dob_field = ft.TextField(
            label="Date of Birth",
            hint_text="Select date of birth",
            read_only=True,
            width=200,
            on_click=lambda e: self.open_dob()
        )

        self.error_message = ft.Text("", color='red')

        self.page.add(
            ft.Text("Enter Details", color='black', size=25, weight='bold'),
            self.username_field,
            self.fname_field,
            self.email_field,
            self.password_field,
            self.confirm_password_field,
            self.dob_field,
            ft.Row([
                ft.Button("Back", on_click=lambda e:
                          MainScreen(self.page, self.acc).show()),
                ft.Button("Submit", on_click=self.submit),
            ], alignment='center', spacing=20),
            self.error_message
        )

    def open_dob(self):
        self.dob_picker.open = True
        self.page.update()

    def update_dob(self, e):
        if self.dob_picker.value:
            self.dob_field.value = self.dob_picker.value.strftime("%Y/%m/%d")
            self.page.update()

    async def submit(self, e):

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

        if not is_valid_email(self.email_field.value):
            self.email_field.error_text = "Invalid email format"
            self.error_message.value = "Please enter a valid email address"
            self.page.update()
            return

        create_account = AccountManager(
            email=self.email_field.value,
            username=self.username_field.value,
            fname=self.fname_field.value,
            dob=self.dob_field.value,
            password=self.password_field.value
        )
        await create_account.createAccount()

        homePage(self.page, self.acc).show()


# Screen for logging into an existing account


class Login:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()

        self.username_field = self.create_input("Username", "username")
        self.password_field = self.create_input("Password", "Enter password",
                                                password=True)

        self.page.add(
            ft.Text("Login", color='black', size=25, weight='bold'),
            self.username_field,
            self.password_field,
            ft.Row([
                ft.Button("Back", on_click=lambda e:
                          MainScreen(self.page, self.acc).show()),
                ft.Button("Submit", on_click=self.submit),
            ], alignment='center', spacing=20)
        )

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

    async def submit(self, e):
        user_login = login(
            username=self.username_field.value,
            password=self.password_field.value
        )
        result = await user_login.userLogin()
        if result['success']:
            self.acc.username = result['username']
            self.acc.email = result['email']
            self.acc.fname = result['fname']
            self.acc.dob = result['dob']
            print(f"✓ Login successful for {self.acc.username}")
            homePage(self.page, self.acc).show()
        else:
            # Show error message
            print(f"✗ Login failed: {result['message']}")
            self.page.update()


#test

def main(page: ft.Page):
    page.title = "Snuzzl"
    acc = Account()
    MainScreen(page, acc).show()

if __name__ == "__main__":
    ft.app(target=main)
