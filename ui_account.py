import flet as ft

# import httpx


class Summary:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()
        self.page.add(
            ft.Text(f"Hello, {self.acc.fname}.",
                    color='black', size=25, weight='bold'),
            ft.Row([
                ft.Text(f"Username: {self.acc.username}",
                        color='black', size=15, weight='bold'),
                ft.Button("Change Username", on_click=lambda e:
                          UsernameChange(self.page, self.acc).show()),
            ], alignment='spaceBetween'),
            ft.Row([
                ft.Text(f"Email: {self.acc.email}",
                        color='black', size=15, weight='bold'),
                ft.Button("Change Email", on_click=lambda e:
                          EmailChange(self.page, self.acc).show()),
            ], alignment='spaceBetween'),
            ft.Row([
                ft.Text(f"Password: {self.acc.password}",
                        color='black', size=15, weight='bold'),
                ft.Button("Change Password", on_click=lambda e:
                          PassChange(self.page, self.acc).show()),
            ], alignment='spaceBetween'),
            ft.Row([
                ft.Text(f"Date of Birth: {self.acc.dob}",
                        color='black', size=15, weight='bold'),
            ], alignment='start'),
            ft.Button("Logout", on_click=self.logout),
        )

    def logout(self, e):
        self.acc.username = ""
        self.acc.fname = ""
        self.acc.email = ""
        self.acc.password = ""
        from ui_login import MainScreen

        MainScreen(self.page, self.acc).show()


class UsernameChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.username_field = self.create_input("Username", "username")

        self.page.add(
            ft.Text("Change Username",
                      color='black', size=25, weight='bold'),
            self.username_field,
            ft.Button("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.username = self.username_field.value
        Summary(self.page, self.acc).show()


class EmailChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.email_field = self.create_input("Email", "email")

        self.page.add(
            ft.Text("Change Email",
                      color='black', size=25, weight='bold'),
            self.email_field,
            ft.Button("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.email = self.email_field.value
        Summary(self.page, self.acc).show()


class PassChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint):
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True
        )

    def show(self):
        self.page.clean()

        self.password_field = self.create_input("Password", "password")

        self.page.add(
            ft.Text("Change Password",
                      color='black', size=25, weight='bold'),
            self.password_field,
            ft.Button("Submit", on_click=self.submit)
        )

    def submit(self, e):
        self.acc.password = self.password_field.value
        Summary(self.page, self.acc).show()
