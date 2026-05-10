# ChallengesUI: shows a users challenges
# RewardsChallengesScreen: the combined screen used by client.py
# can run standalone for testing: python -m app.ui.ui_challenges

import flet as ft
import httpx
import os
from datetime import datetime


API_ROOT = os.getenv("SNUZZL_API_ROOT", "http://127.0.0.1:8000")


def _color(name: str, fallback):
    """Get a Flet color constant with a fallback for older Flet versions."""
    try:
        return getattr(ft.Colors, name)
    except Exception:
        return fallback


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


def _group_rewards_by_challenge(rewards):
    grouped = {}
    for reward in rewards:
        chall_id = reward.get("chall_id") if isinstance(reward, dict) else None
        if chall_id is None:
            continue
        grouped.setdefault(chall_id, []).append(reward)
    return grouped


def _normalize_api_list(payload, keys=None):
    """Normalize API payloads into a list of dict records."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in (keys or ["items", "data", "results"]):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for value in payload.values():
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _friendly_date(value: str) -> str:
    """Format YYYY-MM-DD to a shorter readable date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return value or "unknown"


def _loading_placeholder(label: str):
    return ft.Row(
        [
            ft.ProgressRing(width=14, height=14, stroke_width=2),
            ft.Text(label, size=12, color=ft.Colors.OUTLINE),
        ],
        spacing=8,
    )


def _status_theme(status: str):
    muted_bg = _color("SURFACE_VARIANT", _color("SURFACE", None))
    muted_border = _color("OUTLINE_VARIANT", ft.Colors.OUTLINE)
    muted_text = _color("ON_SURFACE", ft.Colors.BLACK)
    if status == "completed":
        return {
            "badge": "completed",
            "text_color": _color("ON_SECONDARY_CONTAINER", muted_text),
            "border_color": _color("SECONDARY", muted_border),
            "bg_color": _color("SECONDARY_CONTAINER", muted_bg),
        }
    if status == "failed":
        return {
            "badge": "failed",
            "text_color": _color("ON_ERROR_CONTAINER", muted_text),
            "border_color": _color("ERROR", muted_border),
            "bg_color": _color("ERROR_CONTAINER", muted_bg),
        }
    return {
        "badge": "active",
        "text_color": muted_text,
        "border_color": muted_border,
        "bg_color": muted_bg,
    }


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
        self._expanded_reward_ids = set()
        self._user_challenges: list[dict] = []
        self._all_challenges: list[dict] = []
        self._rewards_by_challenge: dict[int, list[dict]] = {}
        self.available_list = ft.Column([_loading_placeholder("loading challenge catalog")], spacing=8)
        self.challenges_list = ft.Column([_loading_placeholder("loading your challenges")], spacing=8)
        self.your_section = ft.Column([
            ft.Text("your challenges", size=14, weight=ft.FontWeight.BOLD),
            self.challenges_list,
        ], spacing=8)
        self.all_section = ft.Column([
            ft.Text("all challenges", size=14, weight=ft.FontWeight.BOLD),
            self.available_list,
        ], spacing=8, visible=False)

        self.your_btn = ft.Button("your challenges", on_click=self.show_your_challenges)
        self.all_btn = ft.Button("all challenges", on_click=self.show_all_challenges)

        self.controls = [
            ft.Text("challenges", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("join a challenge to start working toward its rewards", size=12, color=ft.Colors.OUTLINE),
            ft.Text("accessibility: use Tab/Shift+Tab to move and Enter to activate", size=11, color=ft.Colors.OUTLINE),
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

    def _safe_update(self):
        """Update only when attached to a page to avoid mount-timing crashes."""
        try:
            self.update()
        except Exception:
            # Control not attached yet; skip redraw until mounted.
            pass

    def _apply_view_mode(self):
        self.your_section.visible = self._view_mode == "your"
        self.all_section.visible = self._view_mode == "all"
        self.your_btn.disabled = self._view_mode == "your"
        self.all_btn.disabled = self._view_mode == "all"
        self._safe_update()

    async def show_your_challenges(self, e):
        self._view_mode = "your"
        self._apply_view_mode()

    async def show_all_challenges(self, e):
        self._view_mode = "all"
        self._apply_view_mode()

    async def load_challenges(self):
        """Load and display enrolled and available challenges."""
        self.challenges_list.controls = [_loading_placeholder("loading your challenges")]
        self.available_list.controls = [_loading_placeholder("loading challenge catalog")]
        self._safe_update()
        warnings = []
        try:
            user_challenges = self._user_challenges
            all_challenges = self._all_challenges
            rewards = []
            async with httpx.AsyncClient() as client:
                try:
                    user_response = await client.get(f"{API_ROOT}/challenges/{self.user_id}")
                    user_response.raise_for_status()
                    user_challenges = _normalize_api_list(user_response.json(), ["challenges", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"your challenges: {type(err).__name__}")

                try:
                    all_response = await client.get(f"{API_ROOT}/challenges")
                    all_response.raise_for_status()
                    all_challenges = _normalize_api_list(all_response.json(), ["challenges", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"all challenges: {type(err).__name__}")

                try:
                    rewards_response = await client.get(f"{API_ROOT}/rewards")
                    rewards_response.raise_for_status()
                    rewards = _normalize_api_list(rewards_response.json(), ["rewards", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"rewards: {type(err).__name__}")

            self._user_challenges = user_challenges
            self._all_challenges = all_challenges
            self._rewards_by_challenge = _group_rewards_by_challenge(rewards)
        except httpx.HTTPStatusError as err:
            detail = _http_error_detail(err)
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {detail}", color=ft.Colors.RED)]
            self.available_list.controls = []
            self._safe_update()
            return
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"error loading challenges: {err}", color=ft.Colors.RED)]
            self.available_list.controls = []
            self._safe_update()
            return

        self._render_from_cache()
        if warnings:
            self._send_feedback(f"partial load warning: {', '.join(warnings)}", ft.Colors.RED)

    def _render_from_cache(self):
        user_challenges = self._user_challenges
        all_challenges = self._all_challenges
        rewards_by_challenge = self._rewards_by_challenge

        self.challenges_list.controls.clear()
        if not user_challenges:
            self.challenges_list.controls.append(ft.Text("no challenges yet"))

        enrolled_ids = set()
        enrolled_statuses = {}
        for challenge in user_challenges:
            chall_id = challenge.get("chall_id")
            if chall_id is None:
                continue
            enrolled_ids.add(chall_id)
            status = challenge.get("challenge_status", "active")
            enrolled_statuses[chall_id] = status
            theme = _status_theme(status)
            reward_count = len(rewards_by_challenge.get(chall_id, []))
            challenge_rewards = rewards_by_challenge.get(chall_id, [])
            show_rewards = chall_id in self._expanded_reward_ids
            challenge_card = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(f"{challenge.get('chall_name', 'unnamed challenge')} {theme['badge']}", weight=ft.FontWeight.BOLD, color=theme["text_color"]),
                                    ft.Text(f"{reward_count} reward{'s' if reward_count != 1 else ''} | ends {_friendly_date(challenge.get('chall_edate', 'unknown'))}", size=11, color=ft.Colors.OUTLINE),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Button("Leave", data=chall_id, on_click=self.leave_challenge, disabled=status == "failed"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text("challenge failed: rewards are locked", size=10, color=_color("ERROR", ft.Colors.RED)) if status == "failed" else ft.Container(),
                    ft.Text("go to Tasks to complete this challenge", size=10, color=ft.Colors.OUTLINE) if status == "active" else ft.Container(),
                    self._build_rewards_block(
                        chall_id=chall_id,
                        challenge_rewards=challenge_rewards,
                        show_rewards=show_rewards,
                        can_claim=status != "failed",
                        preview_only=False,
                        joined=True,
                        status=status,
                    ),
                ],
                spacing=6,
            )
            self.challenges_list.controls.append(
                ft.Container(
                    content=challenge_card,
                    padding=10,
                    border=ft.border.all(1, theme["border_color"]),
                    bgcolor=theme["bg_color"],
                    border_radius=10,
                )
            )

        self.available_list.controls.clear()
        if not all_challenges:
            self.available_list.controls.append(ft.Text("no challenge templates found"))
        for challenge in all_challenges:
            chall_id = challenge.get("chall_id")
            if chall_id is None:
                continue
            joined = chall_id in enrolled_ids
            status = enrolled_statuses.get(chall_id)
            reward_count = len(rewards_by_challenge.get(chall_id, []))
            challenge_rewards = rewards_by_challenge.get(chall_id, [])
            show_rewards = chall_id in self._expanded_reward_ids
            status_badge = f" {_status_theme(status)['badge']}" if status else ""
            action_row = [
                ft.Column(
                    [
                        ft.Text(f"{challenge.get('chall_name', 'unnamed challenge')}{status_badge}", weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{reward_count} reward{'s' if reward_count != 1 else ''}" + (f" | {challenge.get('chall_desc', '')[:50]}" if challenge.get("chall_desc") else ""),
                            size=11,
                            color=ft.Colors.OUTLINE,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Button(
                    "Joined" if joined else "Join",
                    data=chall_id,
                    on_click=self.join_challenge,
                    disabled=joined,
                ),
            ]
            card_border_color = _color("OUTLINE_VARIANT", ft.Colors.OUTLINE)
            card_bg_color = _color("SURFACE_CONTAINER_LOW", _color("SURFACE", None))
            if status:
                theme = _status_theme(status)
                card_border_color = theme["border_color"]
                card_bg_color = theme["bg_color"]
            challenge_card = ft.Column(
                [
                    ft.Row([r for r in action_row if r], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                    ft.Text("challenge failed: rewards are locked", size=10, color=_color("ERROR", ft.Colors.RED)) if status == "failed" else ft.Container(),
                    self._build_rewards_block(
                        chall_id=chall_id,
                        challenge_rewards=challenge_rewards,
                        show_rewards=show_rewards,
                        can_claim=joined and status != "failed",
                        preview_only=not joined,
                        joined=joined,
                        status=status,
                    ),
                ],
                spacing=6,
            )
            self.available_list.controls.append(
                ft.Container(
                    content=challenge_card,
                    padding=10,
                    border=ft.border.all(1, card_border_color),
                    bgcolor=card_bg_color,
                    border_radius=10,
                )
            )

        self._apply_view_mode()
        self._safe_update()

    def _build_rewards_block(self, chall_id, challenge_rewards, show_rewards, can_claim, preview_only, joined, status):
        if not challenge_rewards:
            return ft.Container()

        is_open = show_rewards
        chevron = "▾" if is_open else "▸"
        toggle_label = f"{chevron} rewards ({len(challenge_rewards)})"
        reward_rows: list[ft.Control] = [
            ft.TextButton(
                toggle_label,
                data=chall_id,
                on_click=self.toggle_reward_preview,
            )
        ]

        if not is_open:
            return ft.Container(content=ft.Column(reward_rows, spacing=4), padding=ft.padding.only(left=2, top=2, bottom=2))

        for reward in challenge_rewards:
            if preview_only:
                claim_label = "join challenge first"
                claim_disabled = True
            elif status == "failed":
                claim_label = "challenge failed"
                claim_disabled = True
            elif can_claim:
                claim_label = "claim reward"
                claim_disabled = reward.get("reward_id") is None
            elif joined:
                claim_label = "complete tasks first"
                claim_disabled = True
            else:
                claim_label = "join challenge first"
                claim_disabled = True

            reward_rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(reward.get('reward_name', 'unnamed reward'), weight=ft.FontWeight.BOLD, size=12),
                                    ft.Text(f"category: {reward.get('reward_type', 'unknown')}", size=10, color=ft.Colors.OUTLINE),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Button(
                                claim_label,
                                data=reward.get("reward_id"),
                                on_click=self.claim_reward,
                                disabled=claim_disabled,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=8,
                    bgcolor=_color("SURFACE_VARIANT", _color("SURFACE", None)),
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=6,
                )
            )
        return ft.Container(content=ft.Column(reward_rows, spacing=6), padding=ft.padding.only(left=2, top=2, bottom=2))

    async def toggle_reward_preview(self, e):
        chall_id = e.control.data
        if chall_id in self._expanded_reward_ids:
            self._expanded_reward_ids.remove(chall_id)
        else:
            self._expanded_reward_ids.add(chall_id)
        self._render_from_cache()

    async def claim_reward(self, e):
        reward_id = e.control.data
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_ROOT}/rewards/user/{self.user_id}/claim",
                    json={"reward_id": reward_id},
                )
                response.raise_for_status()
            payload = response.json()
            if payload.get("claimed"):
                self._send_feedback(f"claimed reward {reward_id}", ft.Colors.GREEN)
            else:
                self._send_feedback(f"unclaimed reward {reward_id}", ft.Colors.BLUE)
        except httpx.HTTPStatusError as err:
            detail = _http_error_detail(err)
            if "complete all challenge tasks" in detail.lower():
                detail = "complete required challenge tasks first (check Tasks screen), then claim this reward"
            self._send_feedback(f"couldn't claim reward: {detail}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error claiming reward: {err}", ft.Colors.RED)
        await self.load_challenges()

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
        self.challenges_ui = ChallengesUI(user_id, feedback_callback=self.update_feedback)
        
        self.controls = [
            ft.Text("Rewards and Challenges", size=25, weight=ft.FontWeight.BOLD),
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
        try:
            self.update()
        except Exception:
            pass

    async def load_all_data(self):
        """Load both rewards and challenges."""
        await self.challenges_ui.load_challenges()


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
