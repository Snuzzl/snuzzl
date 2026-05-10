import flet as ft
import httpx
from app.config import API_ROOT

class FriendRequest(ft.Column):
    def __init__(self, data, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.data = data

        self.status = ft.Text(f"Status: {self.data['status']}")
        self.accpet_button = ft.Button("Accept", on_click=self.accept_request)
        self.deny_button = ft.Button("Deny", on_click=self.deny_request)
        self.error_message = ft.Text("", color=ft.Colors.RED)

        self.controls = [
            ft.Row([
                ft.Text(f"ID: {self.data['from_user_id']}"),
                ft.Text(f"Username: {self.data['from_username']}" ),
                self.status,
                self.accpet_button,
                self.deny_button 
            ], alignment=ft.CrossAxisAlignment.CENTER),
            self.error_message
            ]

    async def accept_request(self, e=None):
        payload = {
            "user_id": self.user_id,
            "friend_id": self.data['from_user_id']
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{API_ROOT}/notifications/accept_request", json=payload)
                response.raise_for_status()
                data = response.json()
            if data['success']:
                self.status.value = data['message']
                self.error_message.value = ""
                self.update()
            elif not data['success']:
                self.error_message.value = f"Error: {data['error']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()

    async def deny_request(self, e=None):
        payload = {
            "user_id": self.user_id,
            "friend_id": self.data['from_user_id']
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_ROOT}/notifications/deny_request", json=payload)
                response.raise_for_status()
                data = response.json()
            if data['success']:
                self.status.value = data['message']
                self.error_message.value = ""
                self.update()
            elif not data['success']:
                self.error_message.value = f"Error: {data['error']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()


class CompInvite(ft.Column):
    def __init__(self, data, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.data = data

        self.status = ft.Text(f"Status: {self.data['status']}")
        self.accpet_button = ft.Button("Accept", on_click=self.accept_invite)
        self.deny_button = ft.Button("Deny", on_click=self.deny_invite)
        self.error_message = ft.Text("", color=ft.Colors.RED)

        self.controls = [
            ft.Row([
                ft.Text(f"ID: {self.data['competition_id']}"),
                ft.Text(f"Competition Name: {self.data['competition_name']}" ),
                self.status,
                self.accpet_button,
                self.deny_button 
            ], alignment=ft.CrossAxisAlignment.CENTER),
            self.error_message
            ]

    async def accept_invite(self, e=None):
        payload = {
            "user_id": self.user_id,
            "comp_id": self.data['competition_id']
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{API_ROOT}/notifications/accept_invite", json=payload)
                response.raise_for_status()
                data = response.json()
            if data['success']:
                self.status.value = data['message']
                self.error_message.value = ""
                self.update()
            elif not data['success']:
                self.error_message.value = f"Error: {data['error']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()

    async def deny_invite(self, e=None):
        payload = {
            "user_id": self.user_id,
            "comp_id": self.data['competition_id']
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_ROOT}/notifications/deny_invite", json=payload)
                response.raise_for_status()
                data = response.json()
            if data['success']:
                self.status.value = data['message']
                self.error_message.value = ""
                self.update()
            elif not data['success']:
                self.error_message.value = f"Error: {data['error']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()


class CompDeadline(ft.Column):
    def __init__(self, data, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id
        self.data = data

        self.controls = [
            ft.Row([
                ft.Text(f"ID: {self.data['competition_id']}"),
                ft.Text(f"Competition Name: {self.data['competition_name']}"),
                ft.Text(f"End Date: {self.data['end_date']}"),
                ft.Text(f"Days until end: {self.data['days_left']}")
            ], alignment=ft.CrossAxisAlignment.CENTER)
            ]


class NotificationManagerApp(ft.Column):
    def __init__(self, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id

        # Buttons to load notifications
        self.friend_requests = ft.Button("Friend Requests", on_click=self.load_friend_requests)
        self.competition_invites = ft.Button("Competition Invites", on_click=self.load_competition_invites)
        self.competition_deadlines = ft.Button("Competition Deadlines", on_click=self.load_competition_deadlines)
        # List for currently loaded notifications
        self.notification_list = ft.Column()
        self.error_message = ft.Text("", color=ft.Colors.RED)

        self.controls = [
            ft.Text("Notification Manager", size=25,
                weight=ft.FontWeight.BOLD
            ),
            ft.Row([
                self.friend_requests,
                self.competition_invites,
                self.competition_deadlines
            ], alignment=ft.CrossAxisAlignment.CENTER),
            self.error_message,
            ft.Divider(),
            self.notification_list
        ]

    async def load_friend_requests(self, e=None):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/notifications/friends/{self.user_id}")
                response.raise_for_status()
                data = response.json()
            if data:
                self.notification_list.controls.clear()
                for item in data:
                    self.notification_list.controls.append(FriendRequest(item, self.user_id))
                self.error_message.value = ""
            else:
                # Update message if there are no notifications
                self.error_message.value = f"No friend requests to show"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()

    async def load_competition_invites(self, e=None):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/notifications/invites/{self.user_id}")
                response.raise_for_status()
                data = response.json()
            if data:
                self.notification_list.controls.clear()
                for invite in data:
                    self.notification_list.controls.append(CompInvite(invite, self.user_id))
                self.error_message.value = ""
            else:
                # Update message if there are no notifications
                self.error_message.value = f"No competition invites to show"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()

    async def load_competition_deadlines(self, e=None):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/notifications/deadlines/{self.user_id}")
                response.raise_for_status()
                data = response.json()
            if data:
                self.notification_list.controls.clear()
                for item in data:
                    self.notification_list.controls.append(CompDeadline(item, self.user_id))
                self.error_message.value = ""
            else:
                # Update message if there are no notifications
                self.error_message.value = f"No competition deadlines to show"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()