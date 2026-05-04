import flet as ft
from app.ui.ui_metrics import MetricManagerApp
from app.ui.ui_social import SocialManagerApp

user_id = 1

class Menu(ft.Column):
    def __init__(self, metrics_menu, social_menu):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.controls = [
            ft.Text("Main Menu", size=30, weight=ft.FontWeight.BOLD),
            #ft.Button("Open Task Manager", on_click=go_to_tasks),
            ft.Button("Open Metric Manager", on_click=metrics_menu),
            ft.Button("Open Social Manager", on_click=social_menu),
        ]


async def main(page: ft.Page):
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    async def show_menu(e=None):
        page.controls.clear()
        page.add(Menu(show_metrics, show_social))
        page.update()
    
    menu_button = ft.Button("← Back to Menu", on_click=show_menu)

    # async def show_tasks(e=None):
    #     page.controls.clear()
    #     app = TaskManagerApp()
    #     page.add(ft.Column([menu_button, app]))
    #     page.update()
    #     # Load existing tasks when page loads.
    #     await app.load_tasks()

    async def show_metrics(e=None):
        page.controls.clear()
        app = MetricManagerApp(user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing metrics when page loads
        await app.load_metrics()

    async def show_social(e=None):
        page.controls.clear()
        app = SocialManagerApp(user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load friends when page loads
        await app.load_friends()

    # Load menu on app start
    await show_menu()


ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
