import flet
import re
import httpx


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
            flet.Text("Welcome to Snuzzl!", color='black', size=25,
                      weight='bold'),
            flet.Button("Enter", on_click=lambda e:
                        Login(self.page, self.acc).show()
                        )
        )


class Login:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label_text, hint,):
        return flet.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
            filled=True
            )

    def show(self):
        self.page.clean()

        # creates each text field and assigns to a varaible
        self.username_field = self.create_input("Username", "username")
        self.fname_field = self.create_input("First Name", "Jane")
        self.email_field = self.create_input("Email", "example@gmail.com")
        self.password_field = self.create_input("Password", "Enter password")

        self.page.add(
            flet.Text("Enter Details", color='black', size=25, weight='bold'),
            self.username_field,
            self.fname_field,
            self.email_field,
            self.password_field,
            flet.ElevatedButton("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.username = self.username_field.value
        self.acc.fname = self.fname_field.value
        self.acc.email = self.email_field.value
        self.acc.password = self.password_field.value

        Summary(self.page, self.acc).show()


class Summary:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()
        self.page.add(
            flet.Text(f"Hello, {self.acc.fname}.",
                      color='black', size=25, weight='bold'),
            flet.Row([
                flet.Text(f"Username: {self.acc.username}",
                          color='black', size=15),
                flet.Button("Change Username", on_click=lambda e:
                            UsernameChange(self.page, self.acc).show()),
            ]),
            flet.Row([
                flet.Text(f"Email: {self.acc.email}",
                          color='black', size=15),
                flet.Button("Change Email", on_click=lambda e:
                            EmailChange(self.page, self.acc).show()),
            ]),
            flet.Row([
                flet.Text(f"Password: {self.acc.password}",
                          color='black', size=15),
                flet.Button("Change Password", on_click=lambda e:
                            PassChange(self.page, self.acc).show()),
            ])
        )


class UsernameChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return flet.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.username_field = self.create_input("Username", "username")

        self.page.add(
            flet.Text("Change Username",
                      color='black', size=25, weight='bold'),
            self.username_field,
            flet.ElevatedButton("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.username = self.username_field.value
        Summary(self.page, self.acc).show()


class EmailChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return flet.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.email_field = self.create_input("Email", "email")

        self.page.add(
            flet.Text("Change Email",
                      color='black', size=25, weight='bold'),
            self.email_field,
            flet.ElevatedButton("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.email = self.email_field.value
        Summary(self.page, self.acc).show()


class PassChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return flet.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=flet.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.password_field = self.create_input("Password", "password")

        self.page.add(
            flet.Text("Change Password",
                      color='black', size=25, weight='bold'),
            self.password_field,
            flet.ElevatedButton("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.password = self.password_field.value
        Summary(self.page, self.acc).show()


def main(page: flet.Page):
    page.title = "Snuzzl"
    page.window.width = 360
    page.window.height = 414
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'  
    page.bgcolor = 'white'

    acc = Account()

    def is_valid_email(email: str) -> bool:
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

    MainScreen(page, acc).show()


flet.run(main)
