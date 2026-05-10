import flet as ft
import httpx
from typing import cast

user_id = 1
BASE = f"http://127.0.0.1:8000"


# ----------------------------------------------------------------------------
# Section 1 — Add Custom Task form
# ----------------------------------------------------------------------------
class CustomTaskForm(ft.ExpansionTile):
    """Collapsible form for creating a new custom task."""

    def __init__(self, on_added):
        self.on_added = on_added

        self.name_field = ft.TextField(label="Task name", autofocus=True)
        self.desc_field = ft.TextField(label="Description (optional)", multiline=True)

        self.status_text = ft.Text("", size=12, color=ft.Colors.GREY_600)

        super().__init__(
            title=ft.Text("Add Custom Task", weight=ft.FontWeight.BOLD),
            subtitle=ft.Text("Create your own task"),
            leading=ft.Icon(ft.Icons.ADD),
            collapsed_text_color=ft.Colors.GREY_700,
            controls=[
                self.name_field,
                self.desc_field,
                ft.Button("Add Task", on_click=self.submit),
                self.status_text,
            ],
        )

    async def submit(self, e):
        name = self.name_field.value.strip()
        if not name:
            self.status_text.value = "Please enter a task name."
            self.status_text.color = ft.Colors.RED
            self.update()
            return

        payload = {
            "name": name,
            "description": self.desc_field.value.strip() or None,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{BASE}/tasks/{user_id}", json=payload)
                response.raise_for_status()
            except Exception as ex:
                self.status_text.value = f"Error: {ex}"
                self.status_text.color = ft.Colors.RED
                self.update()
                return

        # Clear form.
        self.name_field.value = ""
        self.desc_field.value = ""
        self.status_text.value = "Task added!"
        self.status_text.color = ft.Colors.GREEN
        self.update()

        # Notify parent to refresh the task list.
        await self.on_added()


# ----------------------------------------------------------------------------
# Section 2 — Predefined Task Catalog browser
# ----------------------------------------------------------------------------
class AssignRow(ft.Row):
    """Inline assign form shown inside each catalog task."""

    def __init__(self, task_id, task_name, on_assigned):
        self.task_id = task_id
        self.task_name = task_name
        self.on_assigned = on_assigned

        self.date_field = ft.TextField(
            label="Date (YYYY-MM-DD)", width=150
        )
        self.stime_field = ft.TextField(label="Start (HH:MM)", width=100)
        self.etime_field = ft.TextField(label="End (HH:MM)", width=100)
        self.assign_btn = ft.Button("Assign", on_click=self.do_assign)
        self.cancel_btn = ft.Button("Cancel", on_click=self.hide)
        self.feedback = ft.Text("", size=12)

        super().__init__(
            controls=[
                self.date_field,
                self.stime_field,
                self.etime_field,
                self.assign_btn,
                self.cancel_btn,
            ]
        )

    async def do_assign(self, e):
        if not self.date_field.value or not self.stime_field.value or not self.etime_field.value:
            self.feedback.value = "Fill all fields to assign."
            self.feedback.color = ft.Colors.RED
            self.update()
            return

        payload = {
            "task_id": self.task_id,
            "date": self.date_field.value,
            "start_time": self.stime_field.value,
            "end_time": self.etime_field.value,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{BASE}/tasks/{user_id}/assign", json=payload)
                response.raise_for_status()
            except Exception as ex:
                self.feedback.value = f"Error: {ex}"
                self.feedback.color = ft.Colors.RED
                self.update()
                return

        self.feedback.value = f'"{self.task_name}" assigned!'
        self.feedback.color = ft.Colors.GREEN
        self.update()
        await self.on_assigned()

    def hide(self, e):
        self.visible = False
        self.feedback.visible = False
        if self.parent and hasattr(self.parent, "update"):
            self.parent.update()


class CatalogTaskRow(ft.Container):
    """Single predefined task entry inside a category, with an Assign button."""

    def __init__(self, task_info, on_assigned):
        self.task_info = task_info
        self.on_assigned = on_assigned

        self.assign_row = None
        self.feedback_text = ft.Text("", size=12, color=ft.Colors.GREEN)

        name_text = ft.Text(task_info["task_name"], weight=ft.FontWeight.W_500)
        desc_text = ft.Text(
            task_info["task_desc"] or "No description",
            size=12, color=ft.Colors.GREY_600,
        )
        self.assign_btn = ft.Button(
            "Assign",
            icon=ft.Icons.ADD_TASK,
            on_click=self.show_assign_form,
        )

        self.content_col = ft.Column(
            controls=[name_text, desc_text, self.assign_btn, self.feedback_text]
        )

        super().__init__(
            content=self.content_col, padding=ft.Padding(left=8, right=0, top=0, bottom=0)
        )

    def show_assign_form(self, e):
        if self.assign_row is None:
            self.assign_row = AssignRow(
                self.task_info["task_id"],
                self.task_info["task_name"],
                self.on_assigned,
            )
            self.content_col.controls.insert(3, self.assign_row)
        else:
            self.assign_row.visible = True
            self.assign_row.feedback.visible = True
        self.update()


class CatalogCategory(ft.ExpansionTile):
    """One expandable category in the catalog, e.g. 'Exercise'."""

    def __init__(self, type_name, tasks, on_assigned):
        self.type_name = type_name
        task_rows = [
            CatalogTaskRow(t, on_assigned) for t in tasks
        ]
        super().__init__(
            title=ft.Text(type_name, weight=ft.FontWeight.BOLD),
            leading=ft.Icon(self._icon_for_category(type_name)),
            controls=cast(list[ft.Control], task_rows),
            tile_padding=ft.Padding(left=0, right=0, top=0, bottom=0),
        )

    def _icon_for_category(self, name):
        icons = {
            "Cleaning": ft.Icons.CLEANING_SERVICES,
            "Exercise": ft.Icons.FITNESS_CENTER,
            "Self Care": ft.Icons.SELF_IMPROVEMENT,
            "Work": ft.Icons.WORK,
            "Food/Drinks": ft.Icons.RESTAURANT,
            "Downtime": ft.Icons.WEEKEND,
        }
        return icons.get(name, ft.Icons.TASK)


class CatalogBrowser(ft.ExpansionTile):
    """Section 2 — browse the predefined task catalog and assign tasks."""

    def __init__(self, on_assigned):
        self.on_assigned = on_assigned
        self.loading = ft.ProgressRing()
        self.category_tiles = ft.Column()
        self.status_text = ft.Text("", size=12)

        super().__init__(
            title=ft.Text("Predefined Tasks", weight=ft.FontWeight.BOLD),
            subtitle=ft.Text("Browse and assign from the task catalog"),
            leading=ft.Icon(ft.Icons.LIBRARY_BOOKS),
            expanded=False,
            controls=[
                self.loading,
                self.category_tiles,
                self.status_text,
            ],
        )

    async def load_catalog(self):
        self.loading.visible = True
        self.update()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{BASE}/catalog")
                response.raise_for_status()
                data = response.json()
            except Exception as ex:
                self.status_text.value = f"Failed to load catalog: {ex}"
                self.status_text.color = ft.Colors.RED
                self.loading.visible = False
                self.update()
                return

        self.category_tiles.controls.clear()
        for category in data.get("catalog", []):
            self.category_tiles.controls.append(
                CatalogCategory(category["type_name"], category["tasks"], self.on_assigned)
            )

        self.loading.visible = False
        self.status_text.value = ""
        self.update()


# ----------------------------------------------------------------------------
# Section 3 — My Tasks (all assigned tasks, both predefined and custom)
# ----------------------------------------------------------------------------
class MyTaskItem(ft.Container):
    """
    Single task row in the user's task list.
    Handles both predefined and custom task types.
    """

    def __init__(self, task_data, on_update, on_delete):
        super().__init__()
        self.task_data = task_data
        self.on_update = on_update
        self.on_delete = on_delete
        self.is_custom = task_data["task_type"] == "custom"
        self.is_complete = task_data["task_complete"]

        # Top row: type badge, name, status toggle.
        self.type_badge = ft.Container(
            content=ft.Text(
                task_data["type_name"],
                size=10,
                color=ft.Colors.WHITE,
            ),
            bgcolor=self._badge_color(),
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            border_radius=4,
        )

        self.name_text = ft.Text(task_data["name"], weight=ft.FontWeight.W_500)
        self.desc_text = ft.Text(
            task_data["description"] or "No description",
            size=12, color=ft.Colors.GREY_600,
        )
        self.time_text = ft.Text(
            f"{task_data['task_date']}  {task_data['task_stime']}–{task_data['task_etime']}",
            size=11, color=ft.Colors.GREY_500,
        )

        self.status_icon_name = (
            ft.Icons.CHECK_CIRCLE if self.is_complete else ft.Icons.RADIO_BUTTON_UNCHECKED
        )
        self.status_btn = ft.Button(
            f"Mark {'incomplete' if self.is_complete else 'complete'}",
            icon=self.status_icon_name,
            on_click=self.toggle_complete,
        )

        edit_label = "Edit" if self.is_custom else "Edit schedule"
        self.edit_btn = ft.Button(
            edit_label,
            icon=ft.Icons.EDIT,
            on_click=self.show_edit,
        )

        delete_label = "Delete" if self.is_custom else "Unassign"
        self.delete_btn = ft.Button(
            delete_label,
            icon=ft.Icons.DELETE,
            on_click=self.delete_task,
        )

        # Edit form fields.
        if self.is_custom:
            self.edit_name = ft.TextField(label="Name", value=task_data["name"])
            self.edit_desc = ft.TextField(label="Description", value=task_data["description"] or "")
        self.edit_date = ft.TextField(label="Date (YYYY-MM-DD)", value=task_data["task_date"])
        self.edit_stime = ft.TextField(label="Start (HH:MM)", value=task_data["task_stime"])
        self.edit_etime = ft.TextField(label="End (HH:MM)", value=task_data["task_etime"])

        # Assign button for custom tasks that aren't assigned yet.
        self.assign_btn = None
        if self.is_custom and not task_data.get("task_date"):
            self.assign_btn = ft.Button(
                "Assign",
                icon=ft.Icons.ADD_TASK,
                on_click=self.show_assign_form,
            )
            self.assign_date = ft.TextField(label="Date (YYYY-MM-DD)")
            self.assign_stime = ft.TextField(label="Start (HH:MM)")
            self.assign_etime = ft.TextField(label="End (HH:MM)")
            self.assign_form = ft.Column(
                visible=False,
                controls=[
                    ft.Text("Schedule this task:", weight=ft.FontWeight.BOLD),
                    self.assign_date,
                    ft.Row([self.assign_stime, self.assign_etime]),
                    ft.Row([
                        ft.Button("Save", on_click=self.save_assign),
                        ft.Button("Cancel", on_click=self.hide_assign),
                    ]),
                ],
            )

        edit_fields = []
        if self.is_custom:
            edit_fields.extend([self.edit_name, self.edit_desc])
        edit_fields.extend([self.edit_date, self.edit_stime, self.edit_etime])

        self.edit_view = ft.Column(
            visible=False,
            controls=[
                *edit_fields,
                ft.Row([
                    ft.Button("Save", on_click=self.save_edit),
                    ft.Button("Cancel", on_click=self.hide_edit),
                ]),
            ],
        )

        # Assemble the row.
        header_controls = [
            self.type_badge,
            self.name_text,
            self.status_btn,
            self.edit_btn,
            self.delete_btn,
        ]
        if self.assign_btn:
            header_controls.insert(3, self.assign_btn)

        header = ft.Row(controls=header_controls)
        content_controls = [header, self.desc_text, self.time_text, self.edit_view]
        if self.assign_btn:
            content_controls.append(self.assign_form)
        self.content = ft.Column(controls=content_controls)
        self.border = ft.Border.all(1, ft.Colors.GREY_300)
        self.border_radius = 8
        self.padding = 10
        self.margin = ft.Margin(left=0, right=0, top=0, bottom=6)

    def _badge_color(self):
        if not self.is_custom:
            colors = {
                "Exercise": ft.Colors.ORANGE,
                "Cleaning": ft.Colors.BLUE,
                "Self Care": ft.Colors.PINK,
                "Work": ft.Colors.PURPLE,
                "Food/Drinks": ft.Colors.BROWN,
                "Downtime": ft.Colors.TEAL,
            }
            return colors.get(self.task_data["type_name"], ft.Colors.GREY)
        return ft.Colors.GREY

    async def toggle_complete(self, e):
        endpoint = ""
        if self.is_custom:
            cid = self.task_data["cust_id"]
            endpoint = f"{BASE}/tasks/{user_id}/{cid}/{'complete' if not self.is_complete else 'incomplete'}"
        else:
            uid = self.task_data["usertask_id"]
            endpoint = f"{BASE}/tasks/{user_id}/predefined/{uid}/{'complete' if not self.is_complete else 'incomplete'}"

        payload = {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(endpoint)
                response.raise_for_status()
                payload = response.json() if response.content else {}
            except Exception:
                return

        self.is_complete = not self.is_complete
        self.task_data["task_complete"] = self.is_complete
        self.status_icon_name = (
            ft.Icons.CHECK_CIRCLE if self.is_complete else ft.Icons.RADIO_BUTTON_UNCHECKED
        )
        self.status_btn.icon = self.status_icon_name
        setattr(self.status_btn, "text", f"Mark {'incomplete' if self.is_complete else 'complete'}")

        if self.is_complete:
            rewards_awarded = payload.get("rewards_awarded") if isinstance(payload, dict) else None
            if rewards_awarded:
                reward_list = ", ".join(rewards_awarded)
                self._show_reward_notification(f"Reward earned: {reward_list}")

        self.update()
        await self.on_update(self.task_data)

    def _show_reward_notification(self, message):
        try:
            if self.page is None:
                return
            snack_bar = ft.SnackBar(
                ft.Text(message),
                bgcolor=ft.Colors.GREEN_700,
                action="Dismiss",
            )
            show_snack_bar = getattr(self.page, "show_snack_bar", None)
            open_control = getattr(self.page, "open", None)
            if callable(show_snack_bar):
                show_snack_bar(snack_bar)
            elif callable(open_control):
                open_control(snack_bar)
            self.page.update()
        except Exception:
            pass

    async def show_edit(self, e):
        if self.is_custom:
            self.edit_name.value = self.task_data["name"]
            self.edit_desc.value = self.task_data["description"] or ""
        self.edit_date.value = self.task_data["task_date"]
        self.edit_stime.value = self.task_data["task_stime"]
        self.edit_etime.value = self.task_data["task_etime"]
        self.edit_view.visible = True
        self.update()

    def hide_edit(self, e):
        self.edit_view.visible = False
        self.update()

    async def save_edit(self, e):
        if self.is_custom:
            payload = {
                "cust_name": self.edit_name.value,
                "cust_desc": self.edit_desc.value or None,
                "task_date": self.edit_date.value,
                "task_stime": self.edit_stime.value,
                "task_etime": self.edit_etime.value,
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.put(
                        f"{BASE}/tasks/{user_id}/{self.task_data['cust_id']}", json=payload
                    )
                    response.raise_for_status()
                except Exception:
                    return
            self.task_data["name"] = self.edit_name.value
            self.task_data["description"] = self.edit_desc.value or None
            self.name_text.value = self.edit_name.value
        else:
            payload = {
                "task_date": self.edit_date.value,
                "task_stime": self.edit_stime.value,
                "task_etime": self.edit_etime.value,
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.put(
                        f"{BASE}/tasks/{user_id}/predefined/{self.task_data['usertask_id']}",
                        json=payload,
                    )
                    response.raise_for_status()
                except Exception:
                    return

        self.task_data["task_date"] = self.edit_date.value
        self.task_data["task_stime"] = self.edit_stime.value
        self.task_data["task_etime"] = self.edit_etime.value

        self.time_text.value = (
            f"{self.task_data['task_date']}  "
            f"{self.task_data['task_stime']}–{self.task_data['task_etime']}"
        )
        self.edit_view.visible = False
        self.update()
        await self.on_update(self.task_data)

    async def save_assign(self, e):
        if not self.assign_date.value or not self.assign_stime.value or not self.assign_etime.value:
            return

        payload = {
            "cust_id": self.task_data["cust_id"],
            "date": self.assign_date.value,
            "start_time": self.assign_stime.value,
            "end_time": self.assign_etime.value,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BASE}/tasks/{user_id}/assign-custom", json=payload
                )
                response.raise_for_status()
            except Exception:
                return

        self.assign_form.visible = False
        if self.assign_btn is not None:
            self.assign_btn.visible = False
        self.update()
        await self.on_update(self.task_data)

    def show_assign_form(self, e):
        self.assign_form.visible = True
        self.update()

    def hide_assign(self, e):
        self.assign_form.visible = False
        self.update()

    async def delete_task(self, e):
        if self.is_custom:
            endpoint = f"{BASE}/tasks/{user_id}/{self.task_data['cust_id']}"
        else:
            endpoint = f"{BASE}/tasks/{user_id}/unassign/{self.task_data['usertask_id']}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(endpoint)
                response.raise_for_status()
            except Exception:
                return

        await self.on_delete(self)


class MyTasksSection(ft.Column):
    """Section 3 — shows all tasks assigned to the current user."""

    def __init__(self):
        super().__init__()
        self.task_items = ft.Column()
        self.loading = ft.ProgressRing()
        self.empty_text = ft.Text(
            "No tasks yet. Add a custom task or assign one from the catalog above.",
            color=ft.Colors.GREY_500,
            italic=True,
        )
        self.controls = [self.loading, self.empty_text]

    async def load_tasks(self):
        self.controls = [self.loading]
        self.update()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{BASE}/tasks/{user_id}")
                response.raise_for_status()
                data = response.json()
            except Exception as ex:
                self.controls = [
                    ft.Text(f"Failed to load tasks: {ex}", color=ft.Colors.RED)
                ]
                self.update()
                return

        self.task_items.controls.clear()
        tasks = data.get("tasks", [])
        for t in tasks:
            self.task_items.controls.append(
                MyTaskItem(t, self._on_task_updated, self._on_task_deleted)
            )

        if tasks:
            self.controls = [self.task_items]
        else:
            self.controls = [self.empty_text]
        self.update()

    async def _on_task_updated(self, task_data):
        # Refresh keeps data in sync with the server.
        await self.load_tasks()

    async def _on_task_deleted(self, task_item):
        self.task_items.controls.remove(task_item)
        self.update()


# ----------------------------------------------------------------------------
# Main app — three-section layout
# ----------------------------------------------------------------------------
class SnuzzlTaskApp(ft.Column):
    def __init__(self, user_id_value):
        super().__init__()
        global user_id
        user_id = user_id_value
        self.my_tasks = MyTasksSection()

        # Wrap My Tasks in its own ExpansionTile for collapsible behaviour.
        self.my_tasks_tile = ft.ExpansionTile(
            title=ft.Text("My Tasks", weight=ft.FontWeight.BOLD),
            subtitle=ft.Text("All your assigned tasks"),
            leading=ft.Icon(ft.Icons.CHECKLIST),
            controls=[self.my_tasks],
            expanded=True,
        )

        self.controls = [
            ft.Text(
                "Snuzzl Task Manager",
                size=22,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Divider(),
            CustomTaskForm(on_added=self.refresh_tasks),
            ft.Divider(),
            CatalogBrowser(on_assigned=self.refresh_tasks),
            ft.Divider(),
            self.my_tasks_tile,
        ]

    async def refresh_tasks(self):
        """Called after adding or assigning a task to refresh the list."""
        await self.my_tasks.load_tasks()
