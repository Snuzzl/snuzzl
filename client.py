import flet as ft
import httpx
from datetime import date, timedelta

user_id = 1
api_root = "http://127.0.0.1:8000"
base_url = f"{api_root}/tasks/{user_id}"
rewards_url = f"{api_root}/rewards"
user_rewards_url = f"{api_root}/rewards/user/{user_id}"
challenges_url = f"{api_root}/challenges/{user_id}"

class Menu(ft.Column):
    def __init__(self, go_to_tasks, go_to_metrics, go_to_rewards):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.controls = [
            ft.Text("Main Menu", size=30, weight=ft.FontWeight.BOLD),
            ft.Button("Open Task Manager", on_click=go_to_tasks),
            ft.Button("Open Metric Manager", on_click=go_to_metrics),
            ft.Button("Open Rewards and Challenges", on_click=go_to_rewards),
        ]


class TaskItem(ft.Row):
    def __init__(self, task_data, on_complete, on_incomplete, on_delete):
        super().__init__(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.task_data = task_data
        self.on_complete = on_complete
        self.on_incomplete = on_incomplete
        self.on_delete = on_delete

        complete = task_data["task_complete"]
        status_text = "complete" if complete else "incomplete"
        status_color = ft.Colors.GREEN if complete else ft.Colors.ORANGE

        self.controls = [
            ft.Column(
                [
                    ft.Text(task_data["task_name"], weight=ft.FontWeight.BOLD),
                    ft.Text(task_data.get("task_desc") or "no description"),
                    ft.Text(
                        f"{task_data['task_date']} {task_data['task_stime']} - {task_data['task_etime']}",
                        size=12,
                    ),
                    ft.Text(status_text, color=status_color, size=12),
                ],
                spacing=2,
                expand=True,
            ),
            ft.Row(
                [
                    ft.Button("Complete", data=task_data["task_id"], on_click=self.on_complete),
                    ft.Button("Incomplete", data=task_data["task_id"], on_click=self.on_incomplete),
                    ft.Button("Delete", data=task_data["task_id"], on_click=self.on_delete),
                ],
                spacing=6,
            ),
        ]


class TaskManagerApp(ft.Column):
    def __init__(self):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.task_name = ft.TextField(label="task name")
        self.task_desc = ft.TextField(label="task description (optional)")
        self.task_date = ft.TextField(label="date (yyyy-mm-dd)")
        self.task_start = ft.TextField(label="start time (hh:mm:ss)")
        self.task_end = ft.TextField(label="end time (hh:mm:ss)")

        self.add_btn = ft.Button("Add Task", on_click=self.add_task)
        self.feedback = ft.Text("loading tasks...")
        self.task_list = ft.Column(spacing=10)

        self.controls = [
            ft.Text("Task Manager", size=25, weight=ft.FontWeight.BOLD),
            self.task_name,
            self.task_desc,
            self.task_date,
            self.task_start,
            self.task_end,
            self.add_btn,
            self.feedback,
            ft.Divider(),
            self.task_list,
        ]

    async def load_tasks(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url)
                response.raise_for_status()
                data = response.json().get("tasks", [])

            self.task_list.controls.clear()
            if not data:
                self.task_list.controls.append(ft.Text("no tasks yet"))
            else:
                for task in data:
                    self.task_list.controls.append(
                        TaskItem(task, self.mark_complete, self.mark_incomplete, self.delete_task)
                    )
            self.feedback.value = ""
        except Exception as err:
            self.feedback.value = f"couldn't load tasks: {err}"
            self.feedback.color = ft.Colors.RED
        self.update()

    async def add_task(self, e):
        name = self.task_name.value.strip() if self.task_name.value else ""
        date_value = self.task_date.value.strip() if self.task_date.value else ""
        start_value = self.task_start.value.strip() if self.task_start.value else ""
        end_value = self.task_end.value.strip() if self.task_end.value else ""
        desc = self.task_desc.value.strip() if self.task_desc.value else ""

        if not name or not date_value or not start_value or not end_value:
            self.feedback.value = "fill in task name, date, start, and end"
            self.feedback.color = ft.Colors.RED
            self.update()
            return

        payload = {
            "name": name,
            "description": desc or None,
            "date": date_value,
            "start_time": start_value,
            "end_time": end_value,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(base_url, json=payload)
                response.raise_for_status()
            self.feedback.value = "task added"
            self.feedback.color = ft.Colors.GREEN
            self.task_name.value = ""
            self.task_desc.value = ""
            self.task_date.value = ""
            self.task_start.value = ""
            self.task_end.value = ""
            await self.load_tasks()
        except Exception as err:
            self.feedback.value = f"couldn't add task: {err}"
            self.feedback.color = ft.Colors.RED
            self.update()

    async def mark_complete(self, e):
        task_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{base_url}/{task_id}/complete")
                response.raise_for_status()
            await self.load_tasks()
        except Exception as err:
            self.feedback.value = f"couldn't mark complete: {err}"
            self.feedback.color = ft.Colors.RED
            self.update()

    async def mark_incomplete(self, e):
        task_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{base_url}/{task_id}/incomplete")
                response.raise_for_status()
            await self.load_tasks()
        except Exception as err:
            self.feedback.value = f"couldn't mark incomplete: {err}"
            self.feedback.color = ft.Colors.RED
            self.update()

    async def delete_task(self, e):
        task_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{base_url}/{task_id}")
                response.raise_for_status()
            await self.load_tasks()
        except Exception as err:
            self.feedback.value = f"couldn't delete task: {err}"
            self.feedback.color = ft.Colors.RED
            self.update()


class RewardsChallengesApp(ft.Column):
    def __init__(self):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.rewards_feedback = ft.Text("")
        self.rewards_list = ft.Column(spacing=8)
        self.challenges_list = ft.Column(spacing=8)

        self.controls = [
            ft.Text("Rewards and Challenges", size=25, weight=ft.FontWeight.BOLD),
            ft.Text("rewards", weight=ft.FontWeight.BOLD),
            self.rewards_list,
            ft.Divider(),
            ft.Text("your challenges", weight=ft.FontWeight.BOLD),
            self.challenges_list,
            self.rewards_feedback,
        ]

    async def load_page_data(self):
        await self.load_rewards()
        await self.load_challenges()

    async def load_rewards(self):
        self.rewards_list.controls = [ft.Text("loading rewards...")]
        self.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(rewards_url)
                response.raise_for_status()
                rewards = response.json()

            self.rewards_list.controls.clear()
            if not rewards:
                self.rewards_list.controls.append(ft.Text("no rewards yet"))
            else:
                for reward in rewards:
                    reward_id = reward["reward_id"]
                    self.rewards_list.controls.append(
                        ft.Row(
                            [
                                ft.Text(
                                    f"[{reward_id}] {reward['reward_name']} | challenge: {reward['chall_id']} | type: {reward['reward_type']}",
                                    expand=True,
                                ),
                                ft.Button("Claim", data=reward_id, on_click=self.claim_reward),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        )
                    )
        except Exception as err:
            self.rewards_list.controls = [ft.Text(f"couldn't load rewards: {err}", color=ft.Colors.RED)]
        self.update()

    async def claim_reward(self, e):
        reward_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_root}/rewards/user/{user_id}/claim",
                    json={"reward_id": reward_id},
                )
                response.raise_for_status()
            self.rewards_feedback.value = f"claimed reward {reward_id}"
            self.rewards_feedback.color = ft.Colors.GREEN
        except httpx.HTTPStatusError as err:
            try:
                detail = err.response.json().get("detail", str(err))
            except Exception:
                detail = str(err)
            self.rewards_feedback.value = f"couldn't claim it: {detail}"
            self.rewards_feedback.color = ft.Colors.RED
        except Exception as err:
            self.rewards_feedback.value = f"something went wrong: {err}"
            self.rewards_feedback.color = ft.Colors.RED
        self.update()

    async def load_challenges(self):
        self.challenges_list.controls = [ft.Text("loading challenges...")]
        self.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(challenges_url)
                response.raise_for_status()
                challenges = response.json()

            self.challenges_list.controls.clear()
            if not challenges:
                self.challenges_list.controls.append(ft.Text("no challenges yet"))
            else:
                for challenge in challenges:
                    self.challenges_list.controls.append(
                        ft.Text(
                            f"[{challenge['chall_id']}] {challenge['chall_name']} | {challenge['chall_sdate']} to {challenge['chall_edate']}"
                        )
                    )
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {err}", color=ft.Colors.RED)]
        self.update()


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
        page.add(Menu(show_tasks, show_metrics, show_rewards))
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

    async def show_rewards(e=None):
        page.controls.clear()
        app = RewardsChallengesApp()
        page.add(ft.Column([menu_button, app]))
        page.update()
        await app.load_page_data()

    # Load menu on app start
    await show_menu()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
