import flet as ft
import httpx
from datetime import date, timedelta

user_id = 1
api_root = "http://127.0.0.1:8000"
base_url = f"{api_root}/tasks/{user_id}"
rewards_url = f"{api_root}/rewards"
user_rewards_url = f"{api_root}/rewards/user/{user_id}"

class Menu(ft.Column):
    def __init__(self, go_to_tasks, go_to_metrics):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.controls = [
            ft.Text("Main Menu", size=30, weight=ft.FontWeight.BOLD),
            ft.Button("Open Task Manager", on_click=go_to_tasks),
            ft.Button("Open Metric Manager", on_click=go_to_metrics),
        ]


class MetricItem(ft.Column):
    def __init__(self, metric_data):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.metric_data = metric_data
        self.system_metrics = ["Productivity", "Fun", "Rest", "Emotional Health", "Physical Health"]

        # Display elements
        self.title = ft.Text(self.metric_data["metric_name"], weight=ft.FontWeight.BOLD)
        self.value_text = ft.Text(self._value_text())

        self.view_btn = ft.Button(content="Info", on_click=self.toggle_info)
        if self.metric_data["metric_name"] in self.system_metrics:
            self.update_btn = ft.Button(content="Update", on_click=self.show_edit, visible=False)
        else:
            self.update_btn = ft.Button(content="Update", on_click=self.show_edit)

        # Info section (hidden initially)
        self.info_section = ft.Column(
            visible=False,
            controls=[
                ft.Text(f"Description: {self.metric_data['metric_desc']}"),
                ft.Text(f"Last updated: {self.metric_data['last_updated']}"),
                ft.Text(f"Min value: {self.metric_data['metric_min']}"),
                ft.Text(f"Max value: {self.metric_data['metric_max']}")
            ]
        )

        # Edit section (hidden initially)
        self.value_field = ft.TextField(label="New value")
        self.save_btn = ft.Button(content="Save", on_click=self.save_update)
        self.cancel_btn = ft.Button(content="Cancel", on_click=self.hide_edit)
        self.error_message = ft.Text("", visible=False)

        self.edit_section = ft.Column(
            visible=False,
            controls=[
                self.value_field,
                ft.Row([self.save_btn, self.cancel_btn]),
                self.error_message
            ]
        )

        self.controls = [
            self.title,
            self.value_text,
            ft.Row([self.view_btn, self.update_btn], alignment=ft.CrossAxisAlignment.CENTER),
            self.info_section,
            self.edit_section,
            ft.Divider(),
        ]

    def _value_text(self):
        return f"Value: {self.metric_data['metric_value']}"

    def _refresh_display(self):
        self.value_text.value = self._value_text()
        self.error_message.visible = False
        self.update()

    def toggle_info(self, e):
        self.info_section.visible = not self.info_section.visible
        self.update()

    async def show_edit(self, e):
        self.value_field.value = str(self.metric_data["metric_value"])
        self.edit_section.visible = True
        self.update()
        await self.value_field.focus()

    def hide_edit(self, e):
        self.edit_section.visible = False
        self.error_message.visible = False
        self.update()

    async def save_update(self, e):
        metric_id = self.metric_data["metric_id"]
        value = self.value_field.value
        # Try converting input to integer
        try:
            value = int(self.value_field.value)
            self.error_message.visible = False
        except ValueError:
            self.error_message.value = "Input must be an integer"
            self.error_message.visible = True
            self.update()

        # Proceed if input was converted to int
        if isinstance(value, int):
            # Proceed if input value is between min and max values
            if (self.metric_data["metric_min"] <= value <= self.metric_data["metric_max"]):
                payload = {"value": value}
                async with httpx.AsyncClient() as client:
                    response = await client.put(f"http://127.0.0.1:8000/metrics/{user_id}/{metric_id}", json=payload)
                # If server response is successful, update local variables for value and date (saves querying db for page refresh)
                if response.is_success:    
                    self.metric_data["metric_value"] = self.value_field.value
                    self.info_section.controls[1].value = f"Last Updated: {date.today().strftime('%Y-%m-%d')}"
                    self.edit_section.visible = False
                    self._refresh_display()
                # If server response fails, display error message
                else:
                    self.error_message.value = "Response error"
                    self.error_message.visible = True
                    self.update()
            # Error message if input is outside of allowed range
            else:
                self.error_message.value = f"Input between {self.metric_data['metric_min']} and {self.metric_data['metric_max']}"
                #self.error_message.value = f"{type(self.value_field.value)}"
                self.error_message.visible = True
                self.update()        


class MetricManagerApp(ft.Column):
    def __init__(self):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Set current date to Monday of this week
        self.current_date = date.today() - timedelta(days=date.weekday(date.today()))
        # Column to store MetricItem objects
        self.metric_list = ft.Column()
        self.error_message = ft.Text("Loading...")
        self.wellbeing_score = ft.Text("Wellbeing Score: ")

        # Text for week currently displayed, back and forward buttons
        self.current_date_text = ft.Text(self.current_date.strftime("%Y-%m-%d") + " To " + (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d"))
        self.back_button = ft.Button(content="← " + (self.current_date - timedelta(days=7)).strftime("%Y-%m-%d"), on_click=self.go_back)
        self.forward_button = ft.Button(content="→", on_click=self.go_forward, visible=False)

        self.controls = [
            ft.Text("Metric Manager", size=25, weight=ft.FontWeight.BOLD),
            self.current_date_text,
            ft.Row([self.back_button, self.forward_button], alignment=ft.CrossAxisAlignment.CENTER),
            self.wellbeing_score,
            self.error_message,
            ft.Divider(),
            self.metric_list,
        ]

    def update_buttons(self):
    # Update dates on back and forward buttons
        self.current_date_text.value = self.current_date.strftime("%Y-%m-%d") + " To " + (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d")
        self.back_button.content = "← " + (self.current_date - timedelta(days=7)).strftime("%Y-%m-%d")
        if self.current_date != (date.today() - timedelta(days=date.weekday(date.today()))):
            self.forward_button.content = (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d") + " →"
            self.forward_button.visible = True
        else:
            self.forward_button.visible = False

    async def go_back(self, e):
        #Update current date text, buttons and metrics
        self.current_date -= timedelta(days=7)
        self.update_buttons()
        await self.load_metrics(self.current_date + timedelta(days=7))
        self.update()

    async def go_forward(self, e):
        #Update current date text, buttons and metrics
        self.current_date += timedelta(days=7)
        self.update_buttons()
        await self.load_metrics(self.current_date + timedelta(days=7))
        self.update()

    async def load_metrics(self, date=date.today()):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:8000/metrics/{user_id}/{date.strftime('%Y-%m-%d')}")
                # Raises an error if request fails
                response.raise_for_status()
                data = response.json()

            self.metric_list.controls.clear()
            wellbeing_score = 0
            # Iterate through response to add each metric to the display
            for metric_data in data:
                self.metric_list.controls.append(MetricItem(metric_data))
                wellbeing_score += metric_data["metric_value"]
            # Reset error/loading message
            self.error_message.visible = False
            self.wellbeing_score.value = f"Wellbeing Score: {wellbeing_score}"
            self.update()
        except:
            self.error_message.value = "Server error"


async def main(page: ft.Page):
    # page.title = "Snuzzl Task Manager"
    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    # page.scroll = ft.ScrollMode.ADAPTIVE

    # app = TaskManagerApp()
    # page.add(app)

    # # Load existing tasks on startup.
    # await app.load_tasks()

    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    async def show_menu(e=None):
        page.controls.clear()
        page.add(Menu(show_tasks, show_metrics))
        page.update()
    
    menu_button = ft.Button("← Back to Menu", on_click=show_menu)

    async def show_tasks(e=None):
        page.controls.clear()
        app = TaskManagerApp()
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing tasks when page loads.
        await app.load_tasks()

    async def show_metrics(e=None):
        page.controls.clear()
        app = MetricManagerApp()
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing metrics when page loads
        await app.load_metrics()

    # Load menu on app start
    await show_menu()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
