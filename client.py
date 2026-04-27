import flet as ft
import httpx

user_id = 1
api_root = "http://127.0.0.1:8000"
base_url = f"{api_root}/tasks/{user_id}"
rewards_url = f"{api_root}/rewards"
user_rewards_url = f"{api_root}/rewards/user/{user_id}"
challenges_url = f"{api_root}/challenges/{user_id}"


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


class RewardsPanel(ft.Column):
    def __init__(self):
        super().__init__()
        self.rewards_list = ft.Column()

        self.rewards_header = ft.Text("rewards", size=20, weight=ft.FontWeight.BOLD)
        self.reload_rewards_btn = ft.Button(content="Reload Rewards", on_click=self.load_rewards)
        self.load_user_rewards_btn = ft.Button(content="Load My Rewards", on_click=self.load_user_rewards)
        self.filter_challenge_field = ft.TextField(label="Filter by Challenge ID", on_submit=self.load_challenge_rewards)
        self.filter_challenge_btn = ft.Button(content="Filter Rewards", on_click=self.load_challenge_rewards)

        self.reward_chall_id_field = ft.TextField(label="Challenge ID")
        self.reward_name_field = ft.TextField(label="Reward name")
        self.reward_type_field = ft.TextField(label="Reward type ID", on_submit=self.add_reward)
        self.add_reward_btn = ft.Button(content="Add Reward", on_click=self.add_reward)

        self.claim_reward_id_field = ft.TextField(label="Reward ID to claim", on_submit=self.claim_reward)
        self.claim_reward_btn = ft.Button(content="Claim Reward", on_click=self.claim_reward)

        self.update_reward_ids_field = ft.TextField(label="Reward IDs to update (comma-separated, optional)")
        self.update_reward_name_field = ft.TextField(label="New reward name (optional)")
        self.update_reward_type_field = ft.TextField(label="New reward type ID (optional)", on_submit=self.update_user_rewards)
        self.update_user_rewards_btn = ft.Button(content="Update User Reward(s)", on_click=self.update_user_rewards)
        self.reward_feedback = ft.Text("")

        self.add_reward_form = ft.Column([
            ft.Text("add a reward", size=16, weight=ft.FontWeight.BOLD),
            self.reward_chall_id_field,
            self.reward_name_field,
            self.reward_type_field,
            self.add_reward_btn,
            ft.Divider(),
            ft.Text("claim a reward", size=16, weight=ft.FontWeight.BOLD),
            self.claim_reward_id_field,
            self.claim_reward_btn,
            ft.Divider(),
            ft.Text("update reward(s)", size=16, weight=ft.FontWeight.BOLD),
            self.update_reward_ids_field,
            self.update_reward_name_field,
            self.update_reward_type_field,
            self.update_user_rewards_btn,
            ft.Divider(),
            self.reward_feedback,
        ])

        self.loading_ring = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2, tooltip="Loading...")
        self.controls = [
            ft.Row([self.rewards_header, self.loading_ring]),
            ft.Row([self.reload_rewards_btn, self.load_user_rewards_btn]),
            ft.Row([self.filter_challenge_field, self.filter_challenge_btn]),
            self.add_reward_form,
            self.rewards_list,
        ]

    def _set_loading(self, loading: bool):
        self.loading_ring.visible = loading
        self.reload_rewards_btn.disabled = loading
        self.load_user_rewards_btn.disabled = loading
        self.filter_challenge_btn.disabled = loading
        self.add_reward_btn.disabled = loading
        self.claim_reward_btn.disabled = loading
        self.update_user_rewards_btn.disabled = loading
        self.update()

    async def load_rewards(self, e=None):
        self._set_loading(True)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(rewards_url)
                data = response.json()
            self.render_rewards(data.get("rewards", []))
        except httpx.HTTPError:
            self.reward_feedback.value = "couldn't load rewards, is the server running?"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
        finally:
            self._set_loading(False)

    async def load_user_rewards(self, e=None):
        self._set_loading(True)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(user_rewards_url)
                data = response.json()
            self.render_rewards(data.get("rewards", []))
        except httpx.HTTPError:
            self.reward_feedback.value = "couldn't load your rewards, is the server running?"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
        finally:
            self._set_loading(False)

    async def load_challenge_rewards(self, e=None):
        chall_id = self.filter_challenge_field.value.strip() if self.filter_challenge_field.value else ""
        if not chall_id:
            await self.load_rewards()
            return

        try:
            challenge_id = int(chall_id)
        except ValueError:
            self.reward_feedback.value = "challenge id needs to be a number"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return

        self._set_loading(True)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{api_root}/rewards/challenge/{challenge_id}")
                data = response.json()
            self.render_rewards(data.get("rewards", []))
        except httpx.HTTPError:
            self.reward_feedback.value = "couldn't load rewards for that challenge"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
        finally:
            self._set_loading(False)

    def render_rewards(self, rewards):
        self.rewards_list.controls.clear()
        if not rewards:
            self.rewards_list.controls.append(ft.Text("nothing here yet"))
        else:
            for reward in rewards:
                text = (
                    f"[{reward['reward_id']}] {reward['reward_name']} | "
                    f"Challenge: {reward['chall_id']} | "
                    f"Type: {reward['reward_type']}"
                )
                self.rewards_list.controls.append(ft.Text(text))
        self.update()

    async def add_reward(self, e):
        name = self.reward_name_field.value.strip() if self.reward_name_field.value else ""
        chall_id = self.reward_chall_id_field.value.strip() if self.reward_chall_id_field.value else ""
        reward_type = self.reward_type_field.value.strip() if self.reward_type_field.value else ""

        if not name or not chall_id or not reward_type:
            self.reward_feedback.value = "fill in all three fields first"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return

        try:
            payload = {
                "chall_id": int(chall_id),
                "reward_name": name,
                "reward_type": int(reward_type),
            }
        except ValueError:
            self.reward_feedback.value = "challenge id and type id need to be numbers"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(rewards_url, json=payload)
                response.raise_for_status()
            self.reward_feedback.value = "reward added!"
            self.reward_feedback.color = ft.Colors.GREEN
            self.reward_chall_id_field.value = ""
            self.reward_name_field.value = ""
            self.reward_type_field.value = ""
            await self.load_rewards()
            await self.reward_name_field.focus()
        except httpx.HTTPError as err:
            self.reward_feedback.value = f"couldn't add it: {err}"
            self.reward_feedback.color = ft.Colors.RED
            self.update()

    async def claim_reward(self, e):
        reward_id_raw = self.claim_reward_id_field.value.strip() if self.claim_reward_id_field.value else ""
        if not reward_id_raw:
            self.reward_feedback.value = "enter a reward id first"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return
        try:
            reward_id = int(reward_id_raw)
        except ValueError:
            self.reward_feedback.value = "that needs to be a number"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_root}/rewards/user/{user_id}/claim",
                    json={"reward_id": reward_id}
                )
                response.raise_for_status()
            self.reward_feedback.value = f"reward {reward_id} claimed!"
            self.reward_feedback.color = ft.Colors.GREEN
            self.claim_reward_id_field.value = ""
            await self.load_user_rewards()
        except httpx.HTTPStatusError as err:
            detail = err.response.json().get("detail", str(err))
            self.reward_feedback.value = f"couldn't claim it: {detail}"
            self.reward_feedback.color = ft.Colors.RED
            self.update()

    async def update_user_rewards(self, e):
        reward_ids_raw = self.update_reward_ids_field.value.strip() if self.update_reward_ids_field.value else ""
        new_name = self.update_reward_name_field.value.strip() if self.update_reward_name_field.value else ""
        new_type = self.update_reward_type_field.value.strip() if self.update_reward_type_field.value else ""

        payload = {}
        if reward_ids_raw:
            try:
                reward_ids = [int(value.strip()) for value in reward_ids_raw.split(",") if value.strip()]
                if len(reward_ids) == 1:
                    payload["reward_ids"] = reward_ids[0]
                else:
                    payload["reward_ids"] = reward_ids
            except ValueError:
                self.reward_feedback.value = "ids need to be numbers, comma separated"
                self.reward_feedback.color = ft.Colors.RED
                self.update()
                return

        if new_name:
            payload["reward_name"] = new_name

        if new_type:
            try:
                payload["reward_type"] = int(new_type)
            except ValueError:
                self.reward_feedback.value = "type id needs to be a number"
                self.reward_feedback.color = ft.Colors.RED
                self.update()
                return

        if not payload:
            self.reward_feedback.value = "nothing to update, fill in at least one field"
            self.reward_feedback.color = ft.Colors.RED
            self.update()
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{api_root}/rewards/user/{user_id}", json=payload)
                response.raise_for_status()
                data = response.json()
            self.reward_feedback.value = f"done, updated {data.get('updated', 0)} reward(s)"
            self.reward_feedback.color = ft.Colors.GREEN
            await self.load_user_rewards()
        except httpx.HTTPError as err:
            self.reward_feedback.value = f"couldn't update: {err}"
            self.reward_feedback.color = ft.Colors.RED
            self.update()


class ChallengesPanel(ft.Column):
    def __init__(self):
        super().__init__()
        self.challenges_list = ft.Column()
        self.challenges_header = ft.Text("my challenges", size=20, weight=ft.FontWeight.BOLD)
        self.load_challenges_btn = ft.Button(content="load my challenges", on_click=self.load_challenges)
        self.challenges_feedback = ft.Text("")
        self.challenges_loading = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2, tooltip="Loading...")

        self.controls = [
            ft.Row([self.challenges_header, self.challenges_loading]),
            self.load_challenges_btn,
            self.challenges_feedback,
            self.challenges_list,
        ]

    async def load_challenges(self, e=None):
        self.challenges_loading.visible = True
        self.load_challenges_btn.disabled = True
        self.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(challenges_url)
                response.raise_for_status()
                data = response.json()
            self._render_challenges(data.get("challenges", []))
        except httpx.HTTPError:
            self.challenges_feedback.value = "couldn't load challenges, is the server running?"
            self.challenges_feedback.color = ft.Colors.RED
            self.update()
        finally:
            self.challenges_loading.visible = False
            self.load_challenges_btn.disabled = False
            self.update()

    def _render_challenges(self, challenges):
        self.challenges_list.controls.clear()
        if not challenges:
            self.challenges_list.controls.append(ft.Text("no challenges yet"))
        else:
            for ch in challenges:
                desc = ch['chall_desc'] or "no description"
                text = (
                    f"[{ch['chall_id']}] {ch['chall_name']} — {desc} "
                    f"| {ch['chall_sdate']} to {ch['chall_edate']}"
                )
                self.challenges_list.controls.append(ft.Text(text))
        self.challenges_feedback.value = ""
        self.update()


class TaskManagerApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.task_list = ft.Column()
        self.rewards_panel = RewardsPanel()
        self.challenges_panel = ChallengesPanel()

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

        self.controls = [
            self.add_form,
            ft.Divider(),
            self.task_list,
            ft.Divider(),
            self.challenges_panel,
            ft.Divider(),
            self.rewards_panel,
        ]

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
    await app.rewards_panel.load_rewards()
    await app.challenges_panel.load_challenges()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
