import dbm
import re
import flet as ft
from account_manager import AccountManager
import asyncio

from database_models import Metrics
from metric_manager import MetricManager
from noti_manager import NotificationManager
from task_manager import TaskManager
# import httpx

class homePage:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc
        self.noti_manager = NotificationManager(self.acc.id)
        self.task_manager = TaskManager()

    def show(self):
        self.page.clean()
        self.page.add(
            ft.Text("Welcome to Snuzzl!", color='black', size=25, weight='bold'),
            ft.Text(f"Hello, {self.acc.fname}.",
                        color='black', size=25, weight='bold'),
            ft.Row([
                ft.Button("View Metrics", on_click=lambda e: Metrics(self.page, self.acc).show()),
                ft.Button("Account Summary", on_click=lambda e: Summary(self.page, self.acc).show())
            ], alignment='center', spacing=20),
            ft.Text("Daily Summary", color='black', size=25, weight='bold'),
            ft.Row([
                ft.Container(
                        margin=10,
                        padding=10,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.CYAN_200,
                        width=500,
                        height=150,
                        border_radius=10,
                        ink=True,
                        on_click=lambda e: print("Clickable with Ink clicked!"),
                        content=ft.Text("Clickable with Ink")
                ),
            ],  alignment='center', spacing=20),
            ft.Row([
                ft.Text("Notifications", color='black', size=15, weight='medium'),
                ft.Text("Tasks", color='black', size=15, weight='medium'),
            ], alignment='center', spacing=200),
            ft.Row([
                ft.Container(
                        margin=10,
                        padding=10,
                        alignment=ft.Alignment.TOP_LEFT,
                        bgcolor=ft.Colors.CYAN_200,
                        width=230,
                        height=400,
                        border_radius=10,
                        ink=True,
                        content=ft.Text(
                            f"Friend Notifications: {str(self.noti_manager.get_friend_requests()) if self.noti_manager.get_friend_requests() != [False] else 'No new friend requests'}\n\n"
                            f"Competition Invites: {str(self.noti_manager.get_competition_invites()) if self.noti_manager.get_competition_invites() != [False] else 'No new competition invites'}\n\n"
                            f"Competition Deadlines: {str(self.noti_manager.get_competition_deadlines()) if self.noti_manager.get_competition_deadlines() != [False] else 'No upcoming competition deadlines'}"
                        ),
                ),
                ft.Container(
                        margin=10,
                        padding=10,
                        alignment=ft.Alignment.TOP_LEFT,
                        bgcolor=ft.Colors.CYAN_200,
                        width=230,
                        height=400,
                        border_radius=10,
                        ink=True,
                        content=ft.Text(
                            f"Today's Tasks:\n\n{str(self.task_manager.get_tasks(self.acc.id)) if self.task_manager.get_tasks(self.acc.id) != [False] else 'No tasks for today'}"
                        ),
                ),
            ], alignment='center', spacing=20),)

class Summary:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def show(self):
        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Text("Account Settings", color='black', size=25, weight='bold'),
                ft.Text(f"Hello, {self.acc.fname}.",
                        color='black', size=25, weight='bold'),
                ft.Row([
                    ft.Text(f"Username: {self.acc.username}",
                            color='black', size=15, weight='bold'),
                    ft.Button("Change Username", on_click=lambda e:
                              UsernameChange(self.page, self.acc).show()),
                ], alignment='start'),
                ft.Row([
                    ft.Text(f"Email: {self.acc.email}",
                            color='black', size=15, weight='bold'),
                    ft.Button("Change Email", on_click=lambda e:
                              EmailChange(self.page, self.acc).show()),
                ], alignment='start'),
                ft.Row([
                    ft.Text(f"Password: {self.acc.password}",
                            color='black', size=15, weight='bold'),
                    ft.Button("Change Password", on_click=lambda e:
                              PassChange(self.page, self.acc).show()),
                ], alignment='start'),
                ft.Row([
                    ft.Text(f"Date of Birth: {self.acc.dob}",
                            color='black', size=15, weight='bold'),
                ], alignment='start'),
                ft.Button("Logout", on_click=self.logout),
                ft.Button("Back", on_click=lambda e: homePage(self.page, self.acc).show()),
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10)
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
            ft.Column([
                ft.Text("Change Username", 
                        color='black', size=25, weight='bold'), 
                self.username_field,
                ft.Button("Submit", on_click=self.submit)
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10)
        )

    def submit(self, e):
        self.acc.username = self.username_field.value
        Summary(self.page, self.acc).show()


class EmailChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def is_valid_email(self, email):
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

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
        self.error_message = ft.Text("", color="red")

        self.page.add(
            ft.Column([
                ft.Text("Change Email",
                        color='black', size=25, weight='bold'),
                self.email_field,
                ft.Button("Submit", on_click=self.submit),
                self.error_message
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10)
        )

    def submit(self, e):
        new_email = self.email_field.value
        if not self.is_valid_email(new_email):
            self.error_message.value = "Please enter a valid email address."
            self.page.update()
            return

        self.acc.email = new_email
        Summary(self.page, self.acc).show()


class PassChange:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

    def create_input(self, label, hint, password=False):
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
        )

    def show(self):
        self.page.clean()

        self.password_field = self.create_input("Password", "Enter password",
                                                password=True)
        self.confirm_password_field = self.create_input("Confirm Password",
                                                        "Re-enter password",
                                                        password=True)
        self.error_message = ft.Text("", color="red")

        self.page.add(
            ft.Column([
                ft.Text("Change Password",
                        color='black', size=25, weight='bold'),
                self.password_field,
                self.confirm_password_field,
                ft.Button("Submit", on_click=self.submit),
                self.error_message
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10)
        )

    def submit(self, e):
        if self.password_field.value != self.confirm_password_field.value:
            self.confirm_password_field.error_text = "Passwords do not match"
            self.error_message.value = "Please ensure passwords match"
            self.page.update()
            return
        
        self.acc.password = self.password_field.value
        Summary(self.page, self.acc).show()
