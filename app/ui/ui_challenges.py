# ChallengesUI: shows a users challenges
# RewardsChallengesScreen: the combined screen used by client.py
# can run standalone for testing: python -m app.ui.ui_challenges

import flet as ft
import httpx
import os
import asyncio
from datetime import datetime
from app.ui.ui_rewards import RewardsUI


API_ROOT = os.getenv("SNUZZL_API_ROOT", "http://127.0.0.1:8000")


def _http_error_detail(err: httpx.HTTPStatusError) -> str:
    """Return a readable error detail from an HTTPStatusError."""
    try:
        return err.response.json().get("detail", str(err))
    except Exception:
        return f"server error {err.response.status_code}"


def _is_challenge_expired(end_date_str: str) -> bool:
    """Check if a challenge end date has passed."""
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        return end_date < datetime.now().date()
    except Exception:
        return False


class ChallengesUI(ft.Column):
    """Displays challenges for a user."""

    def __init__(self, user_id, feedback_callback=None):
        """Initialize ChallengesUI.
        
        Args:
            user_id: The user ID for loading challenges.
            feedback_callback: Optional callback for UI feedback messages.
        """
        super().__init__(spacing=8)
        self.user_id = user_id
        self.feedback_callback = feedback_callback
        self._view_mode = "your"
        self.available_list = ft.Column([ft.Text("loading available challenges...")], spacing=8)
        self.challenges_list = ft.Column([ft.Text("loading challenges...")], spacing=8)
        self.your_section = ft.Column([
            self.challenges_list,
        ], spacing=8)
        self.all_section = ft.Column([
            self.available_list,
        ], spacing=8, visible=False)

        self.your_btn = ft.Button("your challenges", on_click=self.show_your_challenges)
        self.all_btn = ft.Button("all challenges", on_click=self.show_all_challenges)

        self.controls = [
            ft.Row(
                [
                    self.your_btn,
                    self.all_btn,
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            self.your_section,
            self.all_section,
        ]

    def _send_feedback(self, message, color):
        if callable(self.feedback_callback):
            self.feedback_callback(message, color)

    def _apply_view_mode(self):
        self.your_section.visible = self._view_mode == "your"
        self.all_section.visible = self._view_mode == "all"
        self.your_btn.disabled = self._view_mode == "your"
        self.all_btn.disabled = self._view_mode == "all"
        self.update()

    async def show_your_challenges(self, e):
        self._view_mode = "your"
        self._apply_view_mode()

    async def show_all_challenges(self, e):
        self._view_mode = "all"
        self._apply_view_mode()

    async def load_challenges(self):
        """Load and display enrolled and available challenges."""
        self.challenges_list.controls = [ft.Text("loading challenges...")]
        self.available_list.controls = [ft.Text("loading available challenges...")]
        self.update()
        try:
            async with httpx.AsyncClient() as client:
                user_response = await client.get(f"{API_ROOT}/challenges/{self.user_id}")
                user_response.raise_for_status()
                user_challenges = user_response.json()

                all_response = await client.get(f"{API_ROOT}/challenges")
                all_response.raise_for_status()
                all_challenges = all_response.json()

            self.challenges_list.controls.clear()
            if not user_challenges:
                self.challenges_list.controls.append(ft.Text("no challenges yet"))

            enrolled_ids = set()
            for challenge in user_challenges:
                chall_id = challenge["chall_id"]
                enrolled_ids.add(chall_id)
                expired = _is_challenge_expired(challenge["chall_edate"])
                status_badge = " [FAILED]" if expired else ""
                text = (
                    f"[{chall_id}] {challenge['chall_name']}{status_badge} | "
                    f"{challenge['chall_sdate']} to {challenge['chall_edate']}"
                )
                self.challenges_list.controls.append(
                    ft.Row(
                        [
                            ft.Text(text, expand=True, color=ft.Colors.RED if expired else None),
                            ft.Button("Leave", data=chall_id, on_click=self.leave_challenge, disabled=expired),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )

            self.available_list.controls.clear()
            if not all_challenges:
                self.available_list.controls.append(ft.Text("no challenge templates found"))
            for challenge in all_challenges:
                chall_id = challenge["chall_id"]
                joined = chall_id in enrolled_ids
                expired = _is_challenge_expired(challenge.get("chall_edate", ""))
                status_badge = " [EXPIRED]" if expired else ""
                row_text = f"[{chall_id}] {challenge['chall_name']}{status_badge}"
                if challenge.get("chall_desc"):
                    row_text += f" | {challenge['chall_desc']}"
                self.available_list.controls.append(
                    ft.Row(
                        [
                            ft.Text(row_text, expand=True, color=ft.Colors.RED if expired else None),
                            ft.Button(
                                "Joined" if joined else "Join",
                                data=chall_id,
                                on_click=self.join_challenge,
                                disabled=joined or expired,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )
        except httpx.HTTPStatusError as err:
            detail = _http_error_detail(err)
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {detail}", color=ft.Colors.RED)]
            self.available_list.controls = []
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"error loading challenges: {err}", color=ft.Colors.RED)]
            self.available_list.controls = []
        self._apply_view_mode()
        self.update()

    async def join_challenge(self, e):
        chall_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_ROOT}/challenges/{self.user_id}/join",
                    json={"chall_id": chall_id},
                )
                response.raise_for_status()
            self._send_feedback(f"joined challenge {chall_id}", ft.Colors.GREEN)
        except httpx.HTTPStatusError as err:
            detail = _http_error_detail(err)
            self._send_feedback(f"couldn't join challenge: {detail}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error joining challenge: {err}", ft.Colors.RED)
        await self.load_challenges()

    async def leave_challenge(self, e):
        chall_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{API_ROOT}/challenges/{self.user_id}/{chall_id}")
                response.raise_for_status()
            self._send_feedback(f"left challenge {chall_id}", ft.Colors.BLUE)
        except httpx.HTTPStatusError as err:
            detail = _http_error_detail(err)
            self._send_feedback(f"couldn't leave challenge: {detail}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error leaving challenge: {err}", ft.Colors.RED)
        await self.load_challenges()


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
        self.challenges_ui = ChallengesUI(user_id, feedback_callback=self.update_feedback)
        
        self.controls = [
            ft.Text("Rewards and Challenges", size=25, weight=ft.FontWeight.BOLD),
            self.challenges_ui,
            ft.Divider(),
            self.rewards_ui,
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
