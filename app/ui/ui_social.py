import flet as ft
import httpx

class FriendItem(ft.Column):
    def __init__(self, data, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.data = data
        self.user_id = user_id

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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"http://127.0.0.1:8000/friends/remove/{self.user_id}/{self.friend_data['friend_id']}")
                # Raises an error if request fails
                response.raise_for_status()
            
        except:
            self.error_message.value = "Remove friend failed: Server Error"

        
class SocialManagerApp(ft.Column):
    def __init__(self, user_id):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id

        # UI elements
        self.friends_list = ft.Column()
        self.new_friend_input = ft.TextField(label="Enter Friend's Username")
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:8000/friends/{self.user_id}")
                # Raises an error if request fails
                response.raise_for_status()
                data = response.json()
            
            self.friends_list.controls.clear()
            for friend_data in data:
                self.friends_list.controls.append(FriendItem(friend_data, self.user_id))
            self.error_message.visible = False
            self.update()
        except Exception as e:
            self.error_message.visible = True
            self.error_message.value = str(e)


    async def add_friend(self, e):
        username_or_id = self.new_friend_input.value
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"http://127.0.0.1:8000/friends/add/{self.user_id}/{username_or_id}")
                response.raise_for_status()
            
            self.new_friend_input.value = ""
            self.error_message.visible = False
            await self.load_friends()
        except:
            self.error_message.visible = True
            self.error_message.value = "Server Error"
