import re
import flet as ft
import httpx
import hashlib
from app.config import API_ROOT

class Summary(ft.Column):
    def __init__(self, id, page, on_logout):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.id = id
        self._page = page
        self.on_logout = on_logout

        # Values updated by load_account method and used for validation when account info is being changed
        self.username = ""
        self.email = ""
        self.password = ""

        self._page_title = ft.Text("Account Summary", size=25, weight=ft.FontWeight.BOLD)
        self.back_button = ft.Button("Back", on_click=self.load_account)
        self.error_message = ft.Text("", color='red')

        # Delete button and confirm dialog
        self.confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Action"),
            content=ft.Text("Are you sure you want to proceed?"),
            actions=[
                ft.Button("Yes", on_click=self.delete_account),
                ft.Button("No", on_click=self.toggle_confirm_window),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.overlay.append(self.confirm_dialog)
        self.delete_button = ft.Button("Delete Account", color='red', on_click=self.toggle_confirm_window)

        self.controls = [
            self._page_title,
            self.error_message
        ]

    async def load_account(self, e=None):
        try:
            async with httpx.AsyncClient() as client:
                result = await client.get(f"{API_ROOT}/account/{self.id.user_id}")
                result.raise_for_status()
            result = result.json()
            if result['success']:
                # If account info retrieval successful, add information to the page
                self.controls.clear()
                self.controls.extend([
                    self._page_title,
                    ft.Text(f"Hello, {result['fname']}.", size=25, weight='bold'),
                    ft.Row([
                        ft.Text(f"Username: {result['username']}", size=15, weight='bold'),
                        ft.Button("Change Username", on_click=self.load_username_change),
                    ], alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([
                        ft.Text(f"Email: {result['email']}", size=15, weight='bold'),
                        ft.Button("Change Email", on_click=self.load_email_change),
                    ], alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(f"Date of Birth: {result['dob']}", size=15, weight='bold'),
                    ft.Button("Change Password", on_click=self.load_password_change),
                    ft.Button("Logout", on_click=self.logout),
                    self.delete_button
                ])
                self.username = result['username']
                self.email = result['email']
                self.password = result['password']
                self.update()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Response Error: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Server Error: {ex}"
            self.update()

    def load_username_change(self):
        self.controls.clear()
        self.controls.extend([UsernameChange(self.id.user_id, self.username, self.load_account), self.back_button])
        self.update()

    def load_email_change(self):
        self.controls.clear()
        self.controls.extend([EmailChange(self.id.user_id, self.email, self.load_account), self.back_button])
        self.update()

    def load_password_change(self):
        self.controls.clear()
        self.controls.extend([PassChange(self.id.user_id, self.password, self.load_account), self.back_button])
        self.update()

    async def logout(self, e=None):
        self.id.user_id = None
        await self.on_logout()

    async def delete_account(self, e=None):
        try:
            async with httpx.AsyncClient() as client:
                result = await client.get(f"{API_ROOT}/account/{self.id.user_id}/delete")
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If account delete change successful, load login menu
                self.toggle_confirm_window()
                await self.logout()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Error: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()

    def toggle_confirm_window(self, e=None):
        self.confirm_dialog.open = not self.confirm_dialog.open
        self._page.update()
        

class UsernameChange(ft.Column):
    def __init__(self, user_id, username, load_account):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.current_username = username
        self.load_account = load_account

        self.username_field = self.create_input("Username", "username")
        self.error_message = ft.Text("", color="red")

        self.controls = [
            ft.Text("Change Username", size=25, weight='bold'), 
            self.username_field,
            ft.Button("Submit", on_click=self.submit),
            self.error_message
        ]

    def create_input(self, label, hint):
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True
        )

    async def submit(self, e):
        # Check if new username is same as current
        if self.username_field.value.strip() == self.current_username:
            self.error_message.value = "New username cannot be same as current username"
            self.update()
            return
        # Check if username is empty
        if not self.username_field.value or not self.username_field.value.strip():
            self.error_message.value = "New username can't be empty"
            self.update()
            return
        
        payload = {
            "user_id": self.user_id,
            "username": self.username_field.value.strip()
            }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/account/change_username", json=payload)
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If username change successful, load account summary
                await self.load_account()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Error: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()
        

class EmailChange(ft.Column):
    def __init__(self, user_id, email, load_account):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.email = email
        self.load_account = load_account

        self.email_field = self.create_input("Email", "email")
        self.error_message = ft.Text("", color="red")

        self.controls = [
            ft.Text("Change Email", size=25, weight='bold'),
            self.email_field,
            ft.Button("Submit", on_click=self.submit),
            self.error_message
        ]

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

    async def submit(self, e):
        # Check if new email is same as current
        if self.email_field.value.strip() == self.email:
            self.error_message.value = "New email cannot be same as current email"
            self.update()
            return
        # Check if email is empty
        if not self.email_field.value or not self.email_field.value.strip():
            self.error_message.value = "New email can't be empty"
            self.update()
            return
        # Check if email is valid
        if not self.is_valid_email(self.email_field.value.strip()):
            self.error_message.value = "Enter a valid email"
            self.update()
            return
        
        payload = {
            "user_id": self.user_id,
            "email": self.email_field.value.strip()
            }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/account/change_email", json=payload)
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If email change successful, load account summary
                await self.load_account()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Error: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()


class PassChange(ft.Column):
    def __init__(self, user_id, password, load_account):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.password = password
        self.load_account = load_account

        self.password_field = self.create_input("Password", "Enter password",password=True)
        self.confirm_password_field = self.create_input("Confirm Password","Re-enter password",password=True)
        self.error_message = ft.Text("", color="red")

        self.controls = [
            ft.Text("Change Password", size=25, weight='bold'),
            self.password_field,
            self.confirm_password_field,
            ft.Button("Submit", on_click=self.submit),
            self.error_message
        ]

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

    async def submit(self, e):
        # Check passowrd fields match
        if self.password_field.value != self.confirm_password_field.value:
            self.confirm_password_field.error_text = "Passwords do not match"
            self.error_message.value = "Please ensure passwords match"
            self.update()
            return
        # Check if password is empty
        if not self.password_field.value or not self.password_field.value.strip():
            self.error_message.value = "New password can't be empty"
            self.update()
            return
        # check password does not match current password
        if hashlib.sha256(self.password_field.value.strip().encode('utf-8')).hexdigest() == self.password:
            self.error_message.value = "New password cannot be same as current password"
            self.update()
            return
        # Check password is at least 6 characters
        if len(self.password_field.value.strip()) < 6:
            self.error_message.value = "Password must be a minimun of 6 characters"
            self.update()
            return
        
        payload = {
            "user_id": self.user_id,
            "password": hashlib.sha256(self.password_field.value.strip().encode('utf-8')).hexdigest()
            }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/account/change_password", json=payload)
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If password change successful, load account summary
                await self.load_account()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Error: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()
