import flet as ft
from app.ui.ui_metrics import MetricManagerApp
from app.ui.ui_social import SocialManagerApp
from app.ui.ui_task_manager import SnuzzlTaskApp
from app.ui.ui_login import MainScreen


class ID:
    def __init__(self):
        self.user_id = None


class Menu(ft.Column):
    def __init__(self, task_menu, metric_menu, social_menu):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.controls = [
            ft.Text("Main Menu", size=30, weight=ft.FontWeight.BOLD),
            ft.Button("Open Task Manager", on_click=task_menu),
            ft.Button("Open Metric Manager", on_click=metric_menu),
            ft.Button("Open Social Manager", on_click=social_menu),
        ]


async def main(page: ft.Page):
    page.title = "Snuzzl App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    id = ID()

    async def menu(e=None):
        page.controls.clear()
        page.add(Menu(task_menu, metric_menu, social_menu))
        page.update()
        
    menu_button = ft.Button("← Back to Menu", on_click=menu)

    async def login_menu():
        page.controls.clear()
        screen = MainScreen(id, page, on_login_success=menu)
        page.add(screen)
        page.update()
        screen.show_menu()

    async def task_menu(e=None):
        page.controls.clear()
        app = SnuzzlTaskApp()
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing tasks when page loads.
        catalog_tile = app.controls[4]  # CatalogBrowser is after title, divider, form, divider.
        await catalog_tile.load_catalog()
        await app.my_tasks.load_tasks()

    async def metric_menu(e=None):
        page.controls.clear()
        app = MetricManagerApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load existing metrics when page loads
        await app.load_metrics()

    async def social_menu(e=None):
        page.controls.clear()
        app = SocialManagerApp(id.user_id)
        page.add(ft.Column([menu_button, app]))
        page.update()
        # Load friends when page loads
        await app.load_friends()

    # Load login menu on app start
    await login_menu()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)