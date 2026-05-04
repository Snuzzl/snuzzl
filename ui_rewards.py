import flet as ft
import httpx


USER_ID = 1
API_ROOT = "http://127.0.0.1:8000"


class RewardsChallenges:
    def __init__(self, page, acc):
        self.page = page
        self.acc = acc

        self.feedback = ft.Text("", color=ft.Colors.RED)
        self.rewards_loading = ft.Text("loading rewards...")
        self.challenges_loading = ft.Text("loading challenges...")
        self.rewards_list = ft.Column([self.rewards_loading], spacing=8)
        self.challenges_list = ft.Column([self.challenges_loading], spacing=8)

    def show(self):
        from ui_login import MainScreen

        self.page.clean()
        self.page.add(
            ft.Text("Rewards and Challenges", color="black", size=25, weight=ft.FontWeight.BOLD),
            ft.Text("rewards", color="black", size=18, weight=ft.FontWeight.BOLD),
            self.rewards_list,
            ft.Divider(),
            ft.Text("your challenges", color="black", size=18, weight=ft.FontWeight.BOLD),
            self.challenges_list,
            ft.Row(
                [
                    ft.Button("Back", on_click=lambda e: MainScreen(self.page, self.acc).show()),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            self.feedback,
        )
        self.page.update()
        self.page.run_task(self.load_page_data)

    async def load_page_data(self):
        await self.load_rewards()
        await self.load_challenges()

    async def load_rewards(self):
        self.rewards_list.controls = [ft.Text("loading rewards...")]
        self.page.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/rewards")
                response.raise_for_status()
                rewards = response.json()

            self.rewards_list.controls.clear()
            if not rewards:
                self.rewards_list.controls.append(ft.Text("no rewards yet"))
            for reward in rewards:
                reward_id = reward["reward_id"]
                row = ft.Row(
                    [
                        ft.Text(
                            f"[{reward_id}] {reward['reward_name']} | challenge: {reward['chall_id']} | type: {reward['reward_type']}",
                            expand=True,
                        ),
                        ft.Button("Claim", data=reward_id, on_click=self.claim_reward),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                self.rewards_list.controls.append(row)
        except httpx.HTTPStatusError as err:
            self.rewards_list.controls = [ft.Text(f"couldn't load rewards: {err}", color=ft.Colors.RED)]
        except Exception as err:
            self.rewards_list.controls = [ft.Text(f"error loading rewards: {err}", color=ft.Colors.RED)]
        self.page.update()

    async def claim_reward(self, e):
        reward_id = e.control.data
        self.feedback.value = ""
        self.feedback.color = ft.Colors.RED
        self.page.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_ROOT}/rewards/user/{USER_ID}/claim",
                    json={"reward_id": reward_id},
                )
                response.raise_for_status()
            payload = response.json()
            if payload.get("claimed"):
                self.feedback.value = f"claimed reward {reward_id}"
                self.feedback.color = ft.Colors.GREEN
            else:
                self.feedback.value = f"unclaimed reward {reward_id}"
                self.feedback.color = ft.Colors.BLUE
        except httpx.HTTPStatusError as err:
            try:
                detail = err.response.json().get("detail", str(err))
            except Exception:
                detail = f"server error {err.response.status_code}"
            self.feedback.value = f"couldn't claim it: {detail}"
        except Exception as err:
            self.feedback.value = f"something went wrong: {err}"
        self.page.update()

    async def load_challenges(self):
        self.challenges_list.controls = [ft.Text("loading challenges...")]
        self.page.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/challenges/{USER_ID}")
                response.raise_for_status()
                challenges = response.json()

            self.challenges_list.controls.clear()
            if not challenges:
                self.challenges_list.controls.append(ft.Text("no challenges yet"))
            for challenge in challenges:
                text = (
                    f"[{challenge['chall_id']}] {challenge['chall_name']} | "
                    f"{challenge['chall_sdate']} to {challenge['chall_edate']}"
                )
                self.challenges_list.controls.append(ft.Text(text))
        except httpx.HTTPStatusError as err:
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {err}", color=ft.Colors.RED)]
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"error loading challenges: {err}", color=ft.Colors.RED)]
        self.page.update()
