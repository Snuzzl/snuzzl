# ChallengesUI: shows a user's challenges.
# RewardsChallengesScreen: combined screen used by client.py.

import inspect
import os

import flet as ft
import httpx

from app.ui.challenges_utils import (
    color,
    friendly_date,
    group_rewards_by_challenge,
    http_error_detail,
    loading_placeholder,
    normalize_api_list,
    status_theme,
)


API_ROOT = os.getenv("SNUZZL_API_ROOT", "http://127.0.0.1:8000")


class ChallengesUI(ft.Column):
    """Displays challenges for a user."""

    def __init__(self, user_id, feedback_callback=None, on_open_tasks=None):
        super().__init__()
        self.spacing = 8
        self.user_id = user_id
        self.feedback_callback = feedback_callback
        self.on_open_tasks = on_open_tasks
        self._view_mode = "your"
        self._expanded_reward_ids = set()
        self._user_challenges = []
        self._all_challenges = []
        self._rewards_by_challenge = {}
        self._previous_reward_ids = set()
        self._newly_awarded_rewards = []
        self._show_expired = False

        self.available_list = ft.Column()
        self.available_list.spacing = 8
        self.available_list.controls = [loading_placeholder("loading challenge catalog")]

        self.challenges_list = ft.Column()
        self.challenges_list.spacing = 8
        self.challenges_list.controls = [loading_placeholder("loading your challenges")]

        self.your_section = ft.Column()
        self.your_section.spacing = 8
        self.your_section.controls = [ft.Text("your challenges", size=14, weight=ft.FontWeight.BOLD), self.challenges_list]

        self.all_section = ft.Column()
        self.all_section.spacing = 8
        self.all_section.visible = False
        self.all_section.controls = [ft.Text("browse all challenges", size=14, weight=ft.FontWeight.BOLD), self.available_list]

        self.your_btn = ft.TextButton("your challenges", on_click=self.show_your_challenges, tooltip="show challenges you joined")
        self.all_btn = ft.TextButton("all challenges", on_click=self.show_all_challenges, tooltip="show all available challenges")

        self.switch_row = ft.Row()
        self.switch_row.alignment = ft.MainAxisAlignment.START
        self.switch_row.controls = [self.your_btn, self.all_btn]

        self.controls = [
            ft.Text("challenges", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("join a challenge to start working toward its rewards", size=12, color=ft.Colors.OUTLINE),
            self.switch_row,
            self.your_section,
            self.all_section,
        ]

    def _send_feedback(self, message, color_value):
        if callable(self.feedback_callback):
            self.feedback_callback(message, color_value)


    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass

    def _is_dark_mode(self):
        try:
            if self.page is None:
                return False
            if self.page.theme_mode == ft.ThemeMode.DARK:
                return True
            if self.page.theme_mode == ft.ThemeMode.LIGHT:
                return False
            brightness = getattr(self.page, "platform_brightness", None)
            if brightness is not None:
                return brightness == ft.Brightness.DARK
            # If theme mode is SYSTEM and brightness is unavailable, prefer dark
            # to avoid blinding cards when host/editor is in dark mode.
            return True
        except Exception:
            return False

    def _theme_tokens(self):
        if self._is_dark_mode():
            return {
                "panel_bg": "#111419",
                "panel_border": "#222831",
                "card_bg": "#161B22",
                "card_border": "#2B313A",
                "title": "#FFFFFF",
                "subtitle": "#C4CDD8",
            }
        return {
            "panel_bg": "#F5F7FA",
            "panel_border": "#D8DEE7",
            "card_bg": "#ECEFF4",
            "card_border": "#C3CBD7",
            "title": "#111827",
            "subtitle": "#4B5563",
        }

    def _run_task(self, coroutine_fn, *args):
        try:
            if self.page is not None:
                run_task = getattr(self.page, "run_task", None)
                if callable(run_task):
                    run_task(coroutine_fn, *args)
        except Exception:
            pass

    def _apply_view_mode(self):
        self.your_section.visible = self._view_mode == "your"
        self.all_section.visible = self._view_mode == "all"
        self.your_btn.disabled = self._view_mode == "your"
        self.all_btn.disabled = self._view_mode == "all"

    def _make_container(self, content=None, **kwargs):
        container = ft.Container()
        if content is not None:
            container.content = content
        for key, value in kwargs.items():
            setattr(container, key, value)
        return container

    def _make_row(self, controls=None, **kwargs):
        row = ft.Row()
        if controls is not None:
            row.controls = controls
        for key, value in kwargs.items():
            setattr(row, key, value)
        return row

    def _make_column(self, controls=None, **kwargs):
        column = ft.Column()
        if controls is not None:
            column.controls = controls
        for key, value in kwargs.items():
            setattr(column, key, value)
        return column

    def _task_hint_row(self, challenge, status):
        progress = challenge.get("required_progress") or {}
        required_total = int(progress.get("required_total") or challenge.get("required_count") or 0)
        completed_total = int(progress.get("completed_total") or 0)

        if required_total <= 0:
            message = "no challenge requirements configured"
        elif status == "completed":
            message = f"requirements met: {required_total}/{required_total} completed"
        elif status == "failed":
            message = f"challenge ended at {completed_total}/{required_total} requirements completed"
        else:
            message = f"progress: {completed_total}/{required_total} requirements completed"

        return self._make_row(
            [
                ft.Text(
                    message,
                    size=12,
                    color=ft.Colors.OUTLINE,
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=4,
        )

    def _build_user_challenge_card(self, challenge, status, rewards_by_challenge):
        chall_id = challenge.get("chall_id")
        if chall_id is None:
            return None

        tokens = self._theme_tokens()
        theme = status_theme(status)
        required_summary = challenge.get("required_summary") or "no required tasks configured"
        challenge_rewards = rewards_by_challenge.get(chall_id, [])
        show_rewards = chall_id in self._expanded_reward_ids

        header = self._make_row(
            [
                self._make_column(
                    [
                        ft.Text(f"{challenge.get('chall_name', 'unnamed challenge')} {theme['badge']}", weight=ft.FontWeight.BOLD, color=tokens["title"]),
                        ft.Text(f"ends {friendly_date(challenge.get('chall_edate', 'unknown'))}", size=11, color=tokens["subtitle"]),
                        ft.Text(required_summary, size=11, color=tokens["subtitle"]),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Button("Leave", on_click=lambda e, cid=chall_id: self._run_task(self.leave_challenge_by_id, cid), disabled=status == "failed"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if status == "completed":
            accent_color = "#16A34A"
        elif status == "failed":
            accent_color = "#EF4444"
        else:
            accent_color = "#0EA5E9"

        body = self._make_column(
            [
                self._make_container(height=3, bgcolor=accent_color, border_radius=3),
                header,
                ft.Text("challenge failed: rewards are locked", size=12, color="#EF4444") if status == "failed" else self._make_container(),
                self._task_hint_row(challenge, status),
                self._build_rewards_block(chall_id, challenge_rewards, show_rewards, status == "completed", False, True, status),
            ],
            spacing=6,
        )

        return self._make_container(body, padding=10, border=ft.border.all(1, tokens["card_border"]), bgcolor=tokens["card_bg"], border_radius=10)

    def _build_catalog_challenge_card(self, challenge, joined, status, rewards_by_challenge):
        chall_id = challenge.get("chall_id")
        if chall_id is None:
            return None

        tokens = self._theme_tokens()
        required_summary = challenge.get("required_summary") or "no required tasks configured"
        card_bg = tokens["card_bg"]
        card_border = tokens["card_border"]
        if status == "completed":
            accent_color = "#16A34A"
        elif status == "failed":
            accent_color = "#EF4444"
        elif joined:
            accent_color = "#14B8A6"
        else:
            accent_color = "#64748B"
        status_badge = f" {status_theme(status)['badge']}" if status else ""

        header = self._make_row(
            [
                ft.Text(f"{challenge.get('chall_name', 'unnamed challenge')}{status_badge}", color=tokens["title"], weight=ft.FontWeight.BOLD, expand=True),
                ft.Button("Joined" if joined else "Join", on_click=lambda e, cid=chall_id: self._run_task(self.join_challenge_by_id, cid), disabled=joined),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        body = self._make_column(
            [
                self._make_container(height=3, bgcolor=accent_color, border_radius=3),
                header,
                ft.Text(f"requirements: {required_summary}", size=12, color=tokens["subtitle"]),
                ft.Text("status: challenge failed", size=12, color="#EF4444") if status == "failed" else self._make_container(),
            ],
            spacing=4,
        )

        return self._make_container(body, bgcolor=card_bg, border=ft.border.all(1, card_border), border_radius=6, padding=8, margin=ft.margin.only(bottom=6))

    def show_your_challenges(self, e):
        self._view_mode = "your"
        self._render_from_cache()

    def show_all_challenges(self, e):
        self._view_mode = "all"
        self._render_from_cache()

    async def load_challenges(self):
        self.challenges_list.controls = [loading_placeholder("loading your challenges")]
        self.available_list.controls = [loading_placeholder("loading challenge catalog")]
        self._safe_update()

        warnings = []
        user_challenges = []
        all_challenges = []
        rewards = []

        try:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{API_ROOT}/challenges/{self.user_id}")
                    response.raise_for_status()
                    user_challenges = normalize_api_list(response.json(), ["challenges", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"your challenges: {type(err).__name__}")

                try:
                    response = await client.get(f"{API_ROOT}/challenges")
                    response.raise_for_status()
                    all_challenges = normalize_api_list(response.json(), ["challenges", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"all challenges: {type(err).__name__}")

                try:
                    response = await client.get(f"{API_ROOT}/rewards?user_id={self.user_id}")
                    response.raise_for_status()
                    rewards = normalize_api_list(response.json(), ["rewards", "items", "data", "results"])
                except Exception as err:
                    warnings.append(f"rewards: {type(err).__name__}")
        except httpx.HTTPStatusError as err:
            detail = http_error_detail(err)
            self.challenges_list.controls = [ft.Text(f"couldn't load challenges: {detail}", color=ft.Colors.RED)]
            self.available_list.controls = []
            self._safe_update()
            return
        except Exception as err:
            self.challenges_list.controls = [ft.Text(f"error loading challenges: {err}", color=ft.Colors.RED)]
            self.available_list.controls = []
            self._safe_update()
            return

        self._user_challenges = user_challenges
        self._all_challenges = all_challenges
        self._rewards_by_challenge = group_rewards_by_challenge(rewards)
        
        # Track reward changes for future features; no persistent top banner.
        current_claimed_ids = {r["reward_id"] for r in rewards if r.get("user_claimed")}
        newly_awarded = current_claimed_ids - self._previous_reward_ids
        self._previous_reward_ids = current_claimed_ids
        self._newly_awarded_rewards = [
            r["reward_name"]
            for r in rewards
            if r.get("reward_id") in newly_awarded
        ]
        
        self._render_from_cache()
        if warnings:
            self._send_feedback(f"partial load warning: {', '.join(warnings)}", ft.Colors.RED)

    def _render_from_cache(self):
        user_challenges = self._user_challenges
        all_challenges = self._all_challenges
        rewards_by_challenge = self._rewards_by_challenge

        self.challenges_list.controls = []
        if not user_challenges:
            self.challenges_list.controls = [ft.Text("no challenges yet", size=12)]

        enrolled_ids = set()
        enrolled_statuses = {}
        
        # Separate active/completed from failed
        active_challenges = []
        failed_challenges = []
        
        for challenge in user_challenges:
            status = challenge.get("challenge_status", "active")
            if status == "failed":
                failed_challenges.append(challenge)
            else:
                active_challenges.append(challenge)
        
        # Sort active/completed by name
        active_challenges.sort(key=lambda ch: ch.get("chall_name", "").lower())
        
        # Display active/completed first
        for challenge in active_challenges:
            chall_id = challenge.get("chall_id")
            if chall_id is None:
                continue
            enrolled_ids.add(chall_id)
            status = challenge.get("challenge_status", "active")
            enrolled_statuses[chall_id] = status
            card = self._build_user_challenge_card(challenge, status, rewards_by_challenge)
            if card is not None:
                self.challenges_list.controls.append(card)
        
        # Add expired section if there are failed challenges
        if failed_challenges:
            tokens = self._theme_tokens()
            failed_count = len(failed_challenges)
            
            def toggle_expired(e):
                self._show_expired = not self._show_expired
                self._render_from_cache()
            
            toggle_state_text = "expanded" if self._show_expired else "collapsed"
            expired_header = ft.Row(
                [
                    ft.Icon(ft.Icons.FLAG, size=16, color="#EF4444"),
                    ft.Text(f"expired ({failed_count}) - {toggle_state_text}. activate to {'collapse' if self._show_expired else 'expand'}", size=12, color="#EF4444", weight=ft.FontWeight.BOLD, expand=True),
                    ft.Icon(ft.Icons.EXPAND_LESS if self._show_expired else ft.Icons.EXPAND_MORE, size=16, color="#EF4444"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            
            expired_section = self._make_container(
                expired_header,
                on_click=toggle_expired,
                padding=10,
                bgcolor=tokens["panel_bg"],
                border=ft.border.all(1, "#EF4444"),
                border_radius=8,
            )
            self.challenges_list.controls.append(expired_section)
            
            # Show failed challenges if expanded
            if self._show_expired:
                for challenge in failed_challenges:
                    chall_id = challenge.get("chall_id")
                    if chall_id is None:
                        continue
                    enrolled_ids.add(chall_id)
                    status = "failed"
                    enrolled_statuses[chall_id] = status
                    card = self._build_user_challenge_card(challenge, status, rewards_by_challenge)
                    if card is not None:
                        self.challenges_list.controls.append(card)

        self.available_list.controls = []
        tokens = self._theme_tokens()

        if not all_challenges:
            self.available_list.controls.append(self._make_container(ft.Text("no challenges available", color=tokens["title"], size=12), bgcolor=tokens["card_bg"], border=ft.border.all(1, tokens["card_border"]), border_radius=8, padding=10))

        sorted_all_challenges = sorted(all_challenges, key=lambda ch: (enrolled_statuses.get(ch.get("chall_id")) == "failed", ch.get("chall_name", "").lower()))
        for challenge in sorted_all_challenges:
            chall_id = challenge.get("chall_id")
            if chall_id is None:
                continue
            joined = chall_id in enrolled_ids
            status = enrolled_statuses.get(chall_id)
            card = self._build_catalog_challenge_card(challenge, joined, status, rewards_by_challenge)
            if card is not None:
                self.available_list.controls.append(card)

        self._apply_view_mode()
        self._safe_update()

    def _build_rewards_block(self, chall_id, challenge_rewards, show_rewards, can_claim, preview_only, joined, status):
        if not challenge_rewards:
            return self._make_container()

        toggle_label = ("hide rewards" if show_rewards else "show rewards") + f" ({len(challenge_rewards)})"
        tokens = self._theme_tokens()
        toggle_btn = ft.Button(
            toggle_label,
            on_click=lambda e, cid=chall_id: self._run_task(self.toggle_reward_preview_for_challenge, cid),
            color=tokens["title"],
            bgcolor=tokens["panel_bg"],
        )
        reward_rows = [self._make_container(toggle_btn, padding=ft.padding.only(bottom=4))]

        if not show_rewards:
            return self._make_container(self._make_column(reward_rows, spacing=4), padding=ft.padding.only(left=6, top=4, bottom=4))

        for reward in challenge_rewards:
            is_claimed = reward.get("user_claimed", False)
            if is_claimed:
                claim_label = "awarded"
                claim_disabled = True
                reward_bg = None
                reward_border = "#16A34A"
            elif preview_only:
                claim_label = "join first"
                claim_disabled = True
                reward_bg = None
                reward_border = tokens["card_border"]
            elif status == "failed":
                claim_label = "locked"
                claim_disabled = True
                reward_bg = None
                reward_border = "#EF4444"
            elif can_claim:
                claim_label = "awarded"
                claim_disabled = True
                reward_bg = None
                reward_border = "#16A34A"
            elif joined:
                claim_label = "pending"
                claim_disabled = True
                reward_bg = None
                reward_border = tokens["card_border"]
            else:
                claim_label = "join first"
                claim_disabled = True
                reward_bg = None
                reward_border = tokens["card_border"]

            if claim_disabled:
                action_control = self._make_container(
                    ft.Text(claim_label, size=12, weight=ft.FontWeight.BOLD, color=tokens["title"]),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=tokens["panel_bg"],
                    border=ft.border.all(1, reward_border),
                    border_radius=6,
                )
            else:
                action_control = ft.Button(
                    claim_label,
                    on_click=lambda e, rid=reward.get("reward_id"): self._run_task(self.claim_reward_by_id, rid),
                    color=tokens["title"],
                    bgcolor=tokens["panel_bg"],
                    disabled=False,
                )

            reward_rows.append(
                self._make_container(
                    self._make_column(
                        [
                            ft.Text(reward.get("reward_name", "unnamed reward"), weight=ft.FontWeight.BOLD, size=12, color=tokens["title"]),
                            self._make_row(
                                [
                                    ft.Text(f"category: {reward.get('reward_type', 'unknown')}", size=12, color=tokens["subtitle"], expand=True),
                                    action_control,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=8,
                    bgcolor=reward_bg or tokens["card_bg"],
                    border=ft.border.all(1, reward_border),
                    border_radius=8,
                )
            )

        return self._make_container(self._make_column(reward_rows, spacing=6), padding=ft.padding.only(left=6, top=4, bottom=4))

    async def toggle_reward_preview_for_challenge(self, chall_id):
        if chall_id in self._expanded_reward_ids:
            self._expanded_reward_ids.remove(chall_id)
        else:
            self._expanded_reward_ids.add(chall_id)
        self._render_from_cache()

    async def open_tasks_for_challenge_id(self, chall_id):
        if callable(self.on_open_tasks):
            result = self.on_open_tasks(chall_id=chall_id)
            if inspect.isawaitable(result):
                await result
            return
        self._send_feedback("open Task Manager to complete required challenge tasks", ft.Colors.BLUE)

    async def claim_reward_by_id(self, reward_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_ROOT}/rewards/user/{self.user_id}/claim", json={"reward_id": reward_id})
                response.raise_for_status()
            payload = response.json()
            if payload.get("already_claimed"):
                self._send_feedback(f"✓ Reward already earned", ft.Colors.BLUE)
            else:
                self._send_feedback(f"🎉 Reward earned! Check your rewards tab.", ft.Colors.GREEN)
        except httpx.HTTPStatusError as err:
            detail = http_error_detail(err)
            if "complete challenge requirements" in detail.lower():
                detail = "Complete all required tasks first to earn this reward"
            self._send_feedback(f"couldn't claim reward: {detail}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error claiming reward: {err}", ft.Colors.RED)
        await self.load_challenges()

    async def join_challenge_by_id(self, chall_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_ROOT}/challenges/{self.user_id}/join", json={"chall_id": chall_id})
                response.raise_for_status()
            self._send_feedback(f"joined challenge {chall_id}", ft.Colors.GREEN)
        except httpx.HTTPStatusError as err:
            self._send_feedback(f"couldn't join challenge: {http_error_detail(err)}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error joining challenge: {err}", ft.Colors.RED)
        await self.load_challenges()

    async def leave_challenge_by_id(self, chall_id):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{API_ROOT}/challenges/{self.user_id}/{chall_id}")
                response.raise_for_status()
            self._send_feedback(f"left challenge {chall_id}", ft.Colors.BLUE)
        except httpx.HTTPStatusError as err:
            self._send_feedback(f"couldn't leave challenge: {http_error_detail(err)}", ft.Colors.RED)
        except Exception as err:
            self._send_feedback(f"error leaving challenge: {err}", ft.Colors.RED)
        await self.load_challenges()

    async def join_challenge(self, e):
        await self.join_challenge_by_id(e.control.data)

    async def leave_challenge(self, e):
        await self.leave_challenge_by_id(e.control.data)

    async def claim_reward(self, e):
        await self.claim_reward_by_id(e.control.data)


class RewardsChallengesScreen(ft.Column):
    """Combined screen for displaying both rewards and challenges."""

    def __init__(self, user_id, on_back, on_open_tasks=None):
        super().__init__()
        self.user_id = user_id
        self.feedback = ft.Text("", color=ft.Colors.RED)
        self.challenges_ui = ChallengesUI(user_id, feedback_callback=self.update_feedback, on_open_tasks=on_open_tasks)

        self.back_button = ft.TextButton("Back", on_click=on_back)
        self.nav_row = ft.Row()
        self.nav_row.alignment = ft.MainAxisAlignment.START
        self.nav_row.controls = [self.back_button]

        self.controls = [
            ft.Text("Rewards and Challenges", size=25, weight=ft.FontWeight.BOLD),
            self.challenges_ui,
            self.nav_row,
            self.feedback,
        ]

    def update_feedback(self, message, color_value):
        self.feedback.value = message
        self.feedback.color = color_value
        try:
            self.update()
        except Exception:
            pass

    async def load_all_data(self):
        await self.challenges_ui.load_challenges()


def main(page: ft.Page):
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    user_id = int(os.getenv("SNUZZL_USER_ID", "1"))

    def go_back(e):
        page.clean()
        page.add(ft.Text("Back button pressed."))

    app = RewardsChallengesScreen(user_id, go_back)
    page.add(app)
    page.update()
    page.run_task(app.load_all_data)


if __name__ == "__main__":
    ft.app(target=main)