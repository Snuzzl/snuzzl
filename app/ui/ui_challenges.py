# ChallengesUI: shows a users challenges
# RewardsChallengesScreen: the combined screen used by client.py
# can run standalone for testing: python -m app.ui.ui_challenges

import flet as ft
import httpx
import os
import asyncio
from app.ui.ui_rewards import RewardsUI


API_ROOT = os.getenv("SNUZZL_API_ROOT", "http://127.0.0.1:8000")


def _http_error_detail(err: httpx.HTTPStatusError) -> str:
    """Return a readable error detail from an HTTPStatusError."""
    try:
        return err.response.json().get("detail", str(err))
    except Exception:
        return f"server error {err.response.status_code}"


class ChallengesUI(ft.Column):
    """Displays challenges for a user."""

    def __init__(self, user_id):
        """Initialize ChallengesUI.
        
        Args:
            user_id: The user ID for loading challenges.
        """
        super().__init__(spacing=8)
        self.user_id = user_id
        self.challenges_list = ft.Column([ft.Text("loading challenges...")], spacing=8)
        self.controls = [
            ft.Text("your challenges", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("read-only for now (enroll/leave flow still pending)", size=12, color=ft.Colors.GREY_600),
            self.challenges_list,
        ]

    async def load_challenges(self):
        """Load and display all challenges for the user."""
        self.challenges_list.controls = [ft.Text("loading challenges...")]
        self.update()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_ROOT}/challenges/{self.user_id}")
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
            detail = _http_error_detail(err)
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {detail}", color=ft.Colors.RED)]
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"error loading challenges: {err}", color=ft.Colors.RED)]
        self.update()


class RewardsChallengesScreen(ft.Column):
    """Combined screen for displaying both rewards and challenges."""

    def __init__(self, user_id, on_back):
        """Initialize RewardsChallengesScreen.
        
        Args:
            user_id: The user ID for loading data.
            on_back: Callback function for the back button.
        """
        super().__init__()
        self.user_id = user_id
        self.feedback = ft.Text("", color=ft.Colors.RED)
        self.rewards_ui = RewardsUI(user_id, feedback_callback=self.update_feedback)
        self.challenges_ui = ChallengesUI(user_id)
        
        self.controls = [
            ft.Text("Rewards and Challenges", size=25, weight=ft.FontWeight.BOLD),
            self.rewards_ui,
            ft.Divider(),
            self.challenges_ui,
            ft.Row(
                [
                    ft.Button("Back", on_click=on_back),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            self.feedback,
        ]

    def update_feedback(self, message, color):
        """Update the feedback message.
        
        Args:
            message: The feedback message.
            color: The color for the message.
        """
        self.feedback.value = message
        self.feedback.color = color
        self.update()

    async def load_all_data(self):
        """Load both rewards and challenges."""
        await asyncio.gather(
            self.rewards_ui.load_rewards(),
            self.challenges_ui.load_challenges(),
        )


def main(page: ft.Page):
    """Main entry point for the Snuzzl app."""
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Default demo value; real flow should pass the authenticated user's ID.
    user_id = int(os.getenv("SNUZZL_USER_ID", "1"))
    
    def go_back(e):
        page.clean()
        page.add(ft.Text("Back action is not wired in standalone mode."))
        page.update()
    
    screen = RewardsChallengesScreen(user_id, go_back)
    page.clean()
    page.add(screen)
    page.update()
    page.run_task(screen.load_all_data)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
