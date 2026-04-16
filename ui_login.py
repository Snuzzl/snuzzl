import flet as ft
import re
from ui_account import Summary
from ui_metrics import Metrics


def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)


class Account:
    def __init__(self):
        self.username = ""
        self.fname = ""
        self.email = ""
        self.password = ""
        self.dob = ""

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

    def submit(self, e):

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

        self.acc.username = self.username_field.value
        self.acc.fname = self.fname_field.value
        self.acc.email = self.email_field.value
        self.acc.password = self.password_field.value
        self.acc.dob = self.dob_field.value

        Summary(self.page, self.acc).show()


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

    def submit(self, e):
        # Placeholder for actual login logic
        print(">>> LOGIN SUBMITTED")

        Summary(self.page, self.acc).show()