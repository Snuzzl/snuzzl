import flet
import re
from ui_account import Summary


def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)


class Account:
    def __init__(self):
        self.username = ""
        self.fname = ""
        self.email = ""
        self.password = ""


class MainScreen:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()
        self.page.add(
            flet.Text("Welcome to Snuzzl!",
                      color='black', size=25, weight='bold'),
            flet.Row([
                flet.Button("Login",
                            on_click=self.login),
                flet.Button("Create Account",
                            on_click=self.create_account)
            ], alignment='center', spacing=20)
        )

    def login(self, e):
        Login(self.page, self.acc).show()

    def create_account(self, e):
        CreateAccount(self.page, self.acc).show()


class CreateAccount:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label_text, hint, password=False):
        return flet.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
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

        self.error_message = flet.Text("", color='red')

        self.page.add(
            flet.Text("Enter Details", color='black', size=25, weight='bold'),
            self.username_field,
            self.fname_field,
            self.email_field,
            self.password_field,
            self.confirm_password_field,
            flet.Button("Submit", on_click=self.submit),
            self.error_message,
        )

    def submit(self, e):

        self.error_message.value = ""

        fields = [
            (self.username_field, "Username cannot be empty"),
            (self.fname_field, "First name cannot be empty"),
            (self.email_field, "Email cannot be empty"),
            (self.password_field, "Password cannot be empty")
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

        Summary(self.page, self.acc).show()


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
            flet.Text("Login", color='black', size=25, weight='bold'),
            self.username_field,
            self.password_field,
            flet.Button("Submit", on_click=self.submit)
        )

    def create_input(self, label_text, hint, password=False):
        return flet.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
        )

    def submit(self, e):
        # Placeholder for actual login logic
        print(">>> LOGIN SUBMITTED")

        Summary(self.page, self.acc).show()