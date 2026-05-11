import flet as ft
import httpx
from app.config import API_ROOT

class FriendItem(ft.Column):
    """
    A UI component representing a single friend entry in the friends list.

    Attributes:
        data (dict): Dictionary containing friend information (friend_id, username, status).
        user_id (int | str): ID of the current user.
        on_friend_remove (Callable): Callback triggered after a friend is removed.
        id (ft.Text): UI text element displaying the friend's ID.
        username (ft.Text): UI text element displaying the friend's username.
        status (ft.Text): UI text element displaying the friend's status.
        remove_button (ft.Button): Button used to trigger friend removal.
        error_message (ft.Text): UI element used to display success or error messages.
    """
    def __init__(self, data, user_id, on_friend_remove):
        """
        Initializes a FriendItem component.

        Args:
            data (dict): Friend data containing 'friend_id', 'username', and 'status'.
            user_id (int | str): ID of the current user.
            on_friend_remove (Callable): Callback function triggered after successful removal.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.data = data
        self.user_id = user_id
        self.on_friend_remove = on_friend_remove

        self.id = ft.Text("ID: "+ str(self.data["friend_id"]))
        self.username = ft.Text("Username: " + self.data["username"])
        self.status = ft.Text("Status: " + self.data["status"])
        self.remove_button = ft.Button("Remove Friend", on_click=self.remove_friend)
        self.error_message = ft.Text("", visible=False)

        self.controls = [
            ft.Row([self.id, self.username, self.status, self.remove_button], alignment=ft.CrossAxisAlignment.CENTER),
            self.error_message,
            ft.Divider()
        ]
    
    async def remove_friend(self):
        """
        Sends a request to remove a friend from the user's friend list.

        On success, triggers the on_friend_remove callback to refresh the list.
        Updates the UI with success or error messages.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{API_ROOT}/friends/remove/{self.user_id}/{self.data['friend_id']}")
                # Raises an error if request fails
            response.raise_for_status()
            data = response.json()
            if data['success']:
                self.error_message.value = data['message']
                await self.on_friend_remove()
            if not data['success']:
                self.error_message.value = f"Error: {data['error']}"
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()


class SocialManagerApp(ft.Column):
    """
    Main application UI for managing a user's friends list.

    Attributes:
        user_id (int | str): ID of the current user.
        friends_list (ft.Column): Container holding FriendItem UI elements.
        new_friend_input (ft.TextField): Input field for adding new friends.
        add_friend_button (ft.Button): Button to trigger add friend request.
        error_message (ft.Text): Displays status, loading, or error messages.
    """
    def __init__(self, user_id):
        """
        Initializes the SocialManagerApp UI.

        Args:
            user_id (int | str): ID of the current user used for API requests.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id

        # UI elements
        self.friends_list = ft.Column()
        self.new_friend_input = ft.TextField(label="Enter Friend's Username or ID")
        self.add_friend_button = ft.Button("Add Friend", on_click=self.add_friend)
        self.error_message = ft.Text("Loading...")

        self.controls = [
            ft.Text("Friends List", size=25, weight=ft.FontWeight.BOLD),
            ft.Row([self.new_friend_input, self.add_friend_button], alignment=ft.CrossAxisAlignment.CENTER),
            self.error_message,
            ft.Divider(),
            self.friends_list
        ]

    # Load friends from database into self.friends_list column
    async def load_friends(self):
        """
        Fetches the user's friends from the backend and populates the UI list.

        Clears existing entries and rebuilds the friends list with updated data.
        Displays error messages if the request fails.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/friends/{self.user_id}")
                # Raises an error if request fails
            response.raise_for_status()
            data = response.json()
            self.friends_list.controls.clear()
            for friend_data in data:
                self.friends_list.controls.append(FriendItem(friend_data, self.user_id, self.load_friends))
            self.error_message.value = ""
            self.update()
        except Exception as e:
            self.error_message.value = f"Error: {e}"
            self.update()

    async def add_friend(self, e):
        """
        Sends a friend request using the provided username or ID.

        Args:
            e: Event trigger from the add friend button click.

        Validates input, sends request to backend, and refreshes the friend list on success.
        Displays error messages for invalid input or failed requests.
        """
        # Check if field input is empty
        if not self.new_friend_input.value or not self.new_friend_input.value.strip():
            self.error_message.value = "Enter a username or ID"
            self.update()
            return

        payload = {
            "user_id": self.user_id,
            "username_or_id": self.new_friend_input.value.strip()
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_ROOT}/friends/add", json=payload)
            response.raise_for_status()
            data = response.json()
            if data['success']:
                self.new_friend_input.value = ""
                self.error_message.value = "Friend request sent"
                await self.load_friends()
            elif not data['success']:
                self.error_message.value = f"Error: {data['error']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()