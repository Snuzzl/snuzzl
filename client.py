import flet as ft
import httpx

user_id = 1
base_url = f"http://127.0.0.1:8000/tasks/{user_id}"


class TaskItem(ft.Column):
    """Single task row with status toggle, edit, and delete."""
    def __init__(self, task_data, on_delete):
        super().__init__()
        self.task_data = task_data
        self.on_delete = on_delete

        # Display elements.
        self.status_btn = ft.Button(
            content=self._status_text(),
            on_click=self.toggle_complete,
        )
        self.info = ft.Text(self._info_text())
        self.delete_btn = ft.Button(content="Delete", on_click=self.delete_task)
        self.edit_btn = ft.Button(content="Edit", on_click=self.show_edit)

        # Edit fields, hidden by default.
        self.name_field = ft.TextField(label="Name", value=task_data["task_name"])
        self.desc_field = ft.TextField(label="Description", value=task_data["task_desc"] or "")
        self.date_field = ft.TextField(label="Date (YYYY-MM-DD)", value=task_data["task_date"])
        self.stime_field = ft.TextField(label="Start time (HH:MM)", value=task_data["task_stime"])
        self.etime_field = ft.TextField(label="End time (HH:MM)", value=task_data["task_etime"])
        self.save_btn = ft.Button(content="Save", on_click=self.save_edit)
        self.cancel_btn = ft.Button(content="Cancel", on_click=self.hide_edit)

        self.edit_view = ft.Column(
            visible=False,
            controls=[
                self.name_field, self.desc_field,
                self.date_field, self.stime_field, self.etime_field,
                ft.Row([self.save_btn, self.cancel_btn]),
            ],
        )

        self.controls = [
            self.status_btn,
            self.info,
            ft.Row([self.edit_btn, self.delete_btn]),
            self.edit_view,
            ft.Divider(),
        ]

    def _status_text(self):
        status = "Done" if self.task_data["task_complete"] else "Pending"
        return f"{self.task_data['task_name']} — {status}. Click to toggle"

    def _info_text(self):
        desc = self.task_data["task_desc"] or "No description"
        return f"{desc} | {self.task_data['task_date']} {self.task_data['task_stime']}–{self.task_data['task_etime']}"

    def _refresh_display(self):
        self.status_btn.content = self._status_text()
        self.info.value = self._info_text()
        self.update()

    async def toggle_complete(self, e):
        tid = self.task_data["task_id"]
        if self.task_data["task_complete"]:
            endpoint = f"{base_url}/{tid}/incomplete"
        else:
            endpoint = f"{base_url}/{tid}/complete"

        async with httpx.AsyncClient() as client:
            await client.put(endpoint)

        self.task_data["task_complete"] = not self.task_data["task_complete"]
        self._refresh_display()

    async def show_edit(self, e):
        # Pre-fill fields with current values.
        self.name_field.value = self.task_data["task_name"]
        self.desc_field.value = self.task_data["task_desc"] or ""
        self.date_field.value = self.task_data["task_date"]
        self.stime_field.value = self.task_data["task_stime"]
        self.etime_field.value = self.task_data["task_etime"]
        self.edit_view.visible = True
        self.update()
        await self.name_field.focus()

    def hide_edit(self, e):
        self.edit_view.visible = False
        self.update()

    async def save_edit(self, e):
        tid = self.task_data["task_id"]
        payload = {
            "task_name": self.name_field.value,
            "task_desc": self.desc_field.value or None,
            "task_date": self.date_field.value,
            "task_stime": self.stime_field.value,
            "task_etime": self.etime_field.value,
        }
        async with httpx.AsyncClient() as client:
            await client.put(f"{base_url}/{tid}", json=payload)

        # Update local data so the display refreshes without re-fetching.
        self.task_data["task_name"] = self.name_field.value
        self.task_data["task_desc"] = self.desc_field.value or None
        self.task_data["task_date"] = self.date_field.value
        self.task_data["task_stime"] = self.stime_field.value
        self.task_data["task_etime"] = self.etime_field.value

        self.edit_view.visible = False
        self._refresh_display()

    async def delete_task(self, e):
        tid = self.task_data["task_id"]
        async with httpx.AsyncClient() as client:
            await client.delete(f"{base_url}/{tid}")
        # Let the parent app remove us from the list.
        await self.on_delete(self)


class TaskManagerApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.task_list = ft.Column()

        # Add-task form fields.
        self.name_field = ft.TextField(label="Task name")
        self.desc_field = ft.TextField(label="Description (optional)")
        self.date_field = ft.TextField(label="Date (YYYY-MM-DD)")
        self.stime_field = ft.TextField(label="Start time (HH:MM)")
        self.etime_field = ft.TextField(label="End time (HH:MM)", on_submit=self.add_task)
        self.add_btn = ft.Button(content="Add Task", on_click=self.add_task)

        self.add_form = ft.Column([
            self.name_field, self.desc_field,
            self.date_field, self.stime_field, self.etime_field,
            self.add_btn,
        ])

        self.controls = [self.add_form, ft.Divider(), self.task_list]

    async def load_tasks(self):
        """Fetch all tasks from the server and populate the list."""
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url)
            data = response.json()

        self.task_list.controls.clear()
        for task_data in data["tasks"]:
            self.task_list.controls.append(TaskItem(task_data, self.remove_task))
        self.update()

    async def add_task(self, e):
        name = self.name_field.value
        if not name or not name.strip():
            return  # Don't submit empty tasks.

        payload = {
            "name": name,
            "description": self.desc_field.value or None,
            "date": self.date_field.value,
            "start_time": self.stime_field.value,
            "end_time": self.etime_field.value,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(base_url, json=payload)
            data = response.json()

        # Build a task_data dict matching what the server returns from GET.
        task_data = {
            "task_id": data["task_id"],
            "task_name": name,
            "task_desc": self.desc_field.value or None,
            "task_complete": False,
            "task_date": self.date_field.value,
            "task_stime": self.stime_field.value,
            "task_etime": self.etime_field.value,
        }
        self.task_list.controls.append(TaskItem(task_data, self.remove_task))

        # Clear the form fields for the next entry.
        self.name_field.value = ""
        self.desc_field.value = ""
        self.date_field.value = ""
        self.stime_field.value = ""
        self.etime_field.value = ""
        self.update()
        await self.name_field.focus()

    async def remove_task(self, task_item):
        self.task_list.controls.remove(task_item)
        self.update()


async def main(page: ft.Page):
    page.title = "Snuzzl Task Manager"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    app = TaskManagerApp()
    page.add(app)

    # Load existing tasks on startup.
    await app.load_tasks()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
