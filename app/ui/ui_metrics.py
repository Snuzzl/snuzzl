import flet as ft
import httpx
from datetime import date, timedelta
from app.config import API_ROOT


class MetricItem(ft.Column):
    """
    A UI component representing a single metric item.

    Displays metric details, allows viewing additional information,
    and supports updating the metric value via an API call.

    Attributes:
        metric_data (dict): Dictionary containing metric metadata and values.
        user_id (str | int): Identifier for the current user.
    """

    def __init__(self, metric_data, user_id):
        """
        Initialize a MetricItem component.

        Args:
            metric_data (dict): Metric information including name, value, bounds, etc.
            user_id (str | int): ID of the user, used for editing metric value.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.metric_data = metric_data
        self.system_metrics = ["Productivity", "Lifestyle", "Rest", "Emotional Health", "Physical Health"]
        self.user_id = user_id

        self.title = ft.Text(self.metric_data["metric_name"], weight=ft.FontWeight.BOLD)
        self.value_text = ft.Text(self._value_text())

        self.view_btn = ft.Button(content="Info", on_click=self.toggle_info)
        if self.metric_data["metric_name"] in self.system_metrics:
            self.update_btn = ft.Button(content="Update", on_click=self.show_edit, visible=False)
        else:
            self.update_btn = ft.Button(content="Update", on_click=self.show_edit)

        self.info_section = ft.Column(
            visible=False,
            controls=[
                ft.Text(f"Description: {self.metric_data['metric_desc']}"),
                ft.Text(f"Last updated: {self.metric_data['last_updated']}"),
                ft.Text(f"Min value: {self.metric_data['metric_min']}"),
                ft.Text(f"Max value: {self.metric_data['metric_max']}")
            ]
        )

        self.value_field = ft.TextField(label="New value", align=ft.Alignment.CENTER)
        self.save_btn = ft.Button(content="Save", on_click=self.save_update)
        self.cancel_btn = ft.Button(content="Cancel", on_click=self.hide_edit)
        self.error_message = ft.Text("", visible=False)

        self.edit_section = ft.Column(
            visible=False,
            controls=[
                self.value_field,
                ft.Row([self.save_btn, self.cancel_btn], alignment=ft.CrossAxisAlignment.CENTER),
                self.error_message
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        self.controls = [
            self.title,
            self.value_text,
            ft.Row([self.view_btn, self.update_btn], alignment=ft.CrossAxisAlignment.CENTER),
            self.info_section,
            self.edit_section,
            ft.Divider()
        ]

    def _value_text(self):
        """Return formatted metric value string."""
        return f"Value: {self.metric_data['metric_value']}"

    def _refresh_display(self):
        """Refresh displayed metric value and reset error state."""
        self.value_text.value = self._value_text()
        self.error_message.visible = False
        self.update()

    def toggle_info(self, e):
        """
        Toggle visibility of the metric info section.

        Args:
            e: Flet event object.
        """
        self.info_section.visible = not self.info_section.visible
        self.update()

    async def show_edit(self, e):
        """
        Show the edit interface and populate it with the current value.

        Args:
            e: Flet event object.
        """
        self.value_field.value = str(self.metric_data["metric_value"])
        self.edit_section.visible = True
        self.update()
        await self.value_field.focus()

    def hide_edit(self, e):
        """
        Hide the edit interface and clear any error messages.

        Args:
            e: Flet event object.
        """
        self.edit_section.visible = False
        self.error_message.visible = False
        self.update()

    async def save_update(self, e):
        """
        Validate and submit updated metric value to the server.

        Performs input validation, range checking, and sends an HTTP PUT request.
        Updates local state if successful.

        Args:
            e: Flet event object, not used.
        """
        metric_id = self.metric_data["metric_id"]
        value = self.value_field.value

        try:
            value = int(value)
            self.error_message.visible = False
        except ValueError:
            self.error_message.value = "Input must be an integer"
            self.error_message.visible = True
            self.update()
            return

        if self.metric_data["metric_min"] <= value <= self.metric_data["metric_max"]:
            payload = {"value": value}
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.put(f"{API_ROOT}/metrics/{self.user_id}/{metric_id}", json=payload)
                    response.raise_for_status()
                self.metric_data["metric_value"] = value
                self.info_section.controls[1].value = (f"Last Updated: {date.today().strftime('%Y-%m-%d')}")
                self.edit_section.visible = False
                self._refresh_display()
            except Exception as ex:
                self.error_message.value = f"Response error: {ex}"
                self.error_message.visible = True
                self.update()
        else:
            self.error_message.value = (
                f"Input between {self.metric_data['metric_min']} and {self.metric_data['metric_max']}"
            )
            self.error_message.visible = True
            self.update()


class MetricManagerApp(ft.Column):
    """
    Main application component for managing and displaying user metrics.

    Handles loading metrics from the backend, week navigation, and
    aggregation of wellbeing scores.
    """

    def __init__(self, user_id):
        """
        Initialize the MetricManagerApp.

        Args:
            user_id (str | int): Identifier for the current user.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.user_id = user_id

        self.current_date = date.today() - timedelta(days=date.weekday(date.today()))
        self.metric_list = ft.Column()
        self.error_message = ft.Text("Loading...")
        self.wellbeing_score = ft.Text("Wellbeing Score: ")

        self.current_date_text = ft.Text(
            self.current_date.strftime("%Y-%m-%d")
            + " To "
            + (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d")
        )

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
        """
        Update navigation button labels and visibility based on current date.
        """
        self.current_date_text.value = (
            self.current_date.strftime("%Y-%m-%d")
            + " To "
            + (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d")
        )

        self.back_button.content = "← " + (self.current_date - timedelta(days=7)).strftime("%Y-%m-%d")

        if self.current_date != (date.today() - timedelta(days=date.weekday(date.today()))):
            self.forward_button.content = (self.current_date + timedelta(days=7)).strftime("%Y-%m-%d") + " →"
            self.forward_button.visible = True
        else:
            self.forward_button.visible = False

    async def go_back(self, e):
        """
        Navigate to the previous week and reload metrics.

        Args:
            e: Flet event object.
        """
        self.current_date -= timedelta(days=7)
        self.update_buttons()
        await self.load_metrics(self.current_date + timedelta(days=7))
        self.update()

    async def go_forward(self, e):
        """
        Navigate to the next week and reload metrics.

        Args:
            e: Flet event object.
        """
        self.current_date += timedelta(days=7)
        self.update_buttons()
        await self.load_metrics(self.current_date + timedelta(days=7))
        self.update()

    async def load_metrics(self, date=date.today()):
        """
        Load metrics for a given date from the backend API.

        Args:
            date (datetime.date, optional): Date for which to load metrics.
                Defaults to today's date.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/metrics/{self.user_id}/{date.strftime('%Y-%m-%d')}")
                response.raise_for_status()
                data = response.json()
            self.metric_list.controls.clear()
            wellbeing_score = 0
            for metric_data in data:
                self.metric_list.controls.append(MetricItem(metric_data, self.user_id))
                wellbeing_score += metric_data["metric_value"]
            self.wellbeing_score.value = f"Wellbeing Score: {wellbeing_score}"
            self.error_message.value = ""
            self.update()
        except Exception as ex:
            self.error_message.value = f"Server error: {ex}"
            self.update()