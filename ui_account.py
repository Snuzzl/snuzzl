import flet
import re
import httpx


def main(page: flet.Page):
    page.title = "Snuzzl"
    page.window.width = 360
    page.window.height = 414
    page.vertical_alignment = 'center'
    page.horizontal_alignment = 'center'  
    page.bgcolor = 'white'
    
    def is_valid_email(email: str) -> bool:
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None
    
    def button_click(e):
        if not email_name.value:
            #page.add(flet.Text("Please enter an email address.", color='red',
                               #size=15))
            response = httpx.get("http://127.0.0.1:8000/")
        else:
            email = email_name.value
            page.add(flet.Text(f"{email} is registered!", color='black',
                               size=15))
            
    def create_row(label_text, hint, width=200):
        return flet.Row([
            flet.TextField(label=label_text,
                           hint_text=hint,
                           width=width,
                           border=flet.InputBorder.UNDERLINE,
                           filled=True,
                           width=width),
            flet.ElevatedButton("Click me", on_click=button_click)
        ], alignment=flet.MainAxisAlignment.CENTER)
    page.add(
        flet.Text("Enter details", color='black', size=25, weight='bold'),
        
        create_row("Email", "example@gmail.com"),
        create_row("Password", "Enter password"),
        create_row("First Name", "Jane"),
        create_row("Last Name", "Doe"),
    )


flet.run(main)