import flet as ft
from backend import SmartHome
home = SmartHome()

class Plug(ft.Column):
    def __init__(self,plug):
        super().__init__()
        self.plug = plug
        self.status = ft.Button(text=f"SmartPlug is set to a consumption rate of {self.plug.consumption_rate}. Click to change",on_click=self.edit_setting)
        self.rate = ft.TextField(label="Enter new consumption rate",on_submit=self.update_setting)
        self.edit_view = ft.Row(visible=False,controls=[self.rate])
        self.switch = ft.Button(text=f"Toggle switch, currently {self.plug.switch_text}",on_click=self.toggle_switch)
        self.controls = [self.status,self.switch,self.edit_view]

    def edit_setting(self,e):
        self.edit_view.visible = True
        self.update()
        self.rate.focus()

    def update_setting(self,e):
        self.plug.consumption_rate = self.rate.value
        self.status.text = f"SmartPlug is set to a consumption rate of {self.plug.consumption_rate}. Click to change"
        self.edit_view.visible = False
        self.update()

    def toggle_switch(self,e):
        self.plug.toggle_switch()
        self.controls[1].text = f"Toggle switch, currently {self.plug.switch_text}"
        self.update()

class Heater(ft.Column):
    def __init__(self,heater):
        super().__init__()
        self.heater = heater
        self.status = ft.Button(text=f"SmartHeater is on setting {self.heater.setting}. Click to change",on_click=self.edit_setting)
        self.setting = ft.TextField(label="Enter new setting from 1 to 5",on_submit=self.update_setting)
        self.edit_view = ft.Row(visible=False,controls=[self.setting])
        self.switch = ft.Button(text=f"Toggle switch, currently {self.heater.switch_text}",on_click=self.toggle_switch)
        self.controls = [self.status,self.switch,self.edit_view]

    def edit_setting(self,e):
        self.edit_view.visible = True
        self.update()
        self.setting.focus()

    def update_setting(self,e):
        self.heater.setting = self.setting.value
        self.edit_view.visible = False
        self.status.text = f"SmartHeater is on setting {self.heater.setting}. Click to change"
        self.update()

    def toggle_switch(self,e):
        self.heater.toggle_switch()
        self.switch.text = f"Toggle switch, currently {self.heater.switch_text}"
        self.update()

class Door(ft.Column):
    def __init__(self,door):
        super().__init__()
        self.door = door
        self.status = ft.Button(text=f"SmartDoor is currently {self.door.lock_text}. Click to change",on_click=self.toggle_door)
        self.switch = ft.Button(text=f"Toggle switch, currently {self.door.switch_text}",on_click=self.toggle_switch)
        self.controls = [self.status,self.switch]

    def toggle_door(self,e):
        self.door.toggle_lock()
        self.status.text = f"SmartDoor is currently {self.door.lock_text}. Click to change"
        self.update()

    def toggle_switch(self,e):
        self.door.toggle_switch()
        self.switch.text = f"Toggle switch, currently {self.door.switch_text}"
        self.update()

class SmartHomeApp(ft.Column):
    def __init__(self):
        super().__init__()
        self.doors = ft.Column()
        self.heaters = ft.Column()
        self.plugs = ft.Column()
        self.add_door = ft.Button(text="Add a door",on_click=self.create_door)
        self.add_heater = ft.Button(text="Add a heater",on_click=self.create_heater)
        self.add_plug = ft.Button(text="Add a plug",on_click=self.create_plug)
        self.controls=[self.add_door,self.add_heater,self.add_plug,self.doors,self.heaters,self.plugs]

    def create_door(self,e):
        door = home.add_door(False)
        self.doors.controls.append(Door(door))
        self.update()

    def create_heater(self,e):
        heater = home.add_heater(0)
        self.heaters.controls.append(Heater(heater))
        self.update()

    def create_plug(self,e):
        plug = home.add_plug(45)
        self.plugs.controls.append(Plug(plug))
        self.update()

def main(page):
    page.title = "Smart Home App"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.add(SmartHomeApp())
ft.app(main)