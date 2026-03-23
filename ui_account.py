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
    
# clears page & adds main screen components
    def main_screen():
        page.clean()
        page.add(
            flet.Text("Welcome to Snuzzl!", color='black', size=25,
                      weight='bold'),
            flet.Button("Enter", on_click=login_screen)            
        )

# clears page & adds login screen components
    def login_screen(e=None):
        page.clean()

        # creates each text field and assigns to a varaible
        username_field = create_input("Username", "username")
        fname_field = create_input("First Name", "Jane")
        email_field = create_input("Email", "example@gmail.com")
        password_field = create_input("Password", "Enter password")
     
        def on_submit(e):
            submit(username_field.value,
                   fname_field.value,
                   email_field.value,
                   password_field.value)
        
        page.add(
            flet.Text("Enter Details", color='black', size=25, weight='bold'),
            username_field,
            fname_field,
            email_field,
            password_field,
            flet.ElevatedButton("Submit", on_click=on_submit)

        )

    def create_input(label_text, hint, width=200):
        return flet.TextField(
            label=label_text,
            hint_text=hint,
            width=width,
            border=flet.InputBorder.UNDERLINE,
            filled=True
            )
    
    def submit(username, fname, email, password):
        page.clean()
        page.add(
            flet.Text(f"Hello, {fname}.",
                      color='black', size=25, weight='bold'),
            flet.Row([
                flet.Text(f"Username: {username}", color='black', size=15),
                flet.Button("Change Username", on_click=lambda e:
                            username_change(fname, email, password)),
            ]),
            flet.Row([ 
                flet.Text(f"Email: {email}", color='black', size=15),
                flet.Button("Change Email", on_click=lambda e:
                            email_change(username, fname, password)),
            ]),
            flet.Row([ 
                flet.Text(f"Password: {password}", color='black', size=15),
                flet.Button("Change Password", on_click=lambda e:
                            pass_change(username, fname, email)),
            ])
        )
    
    def email_change(username, fname, password):
        page.clean()
        email_field = create_input("Email", "example@gmail.com")
        
        def on_submit(e):
            submit(username, fname, email_field.value, password)

        page.add(
            flet.Text("Change Email",
                      color='black', size=25, weight='bold'),
            email_field,
            flet.Button("Submit", on_click=on_submit)
        )

    def username_change(fname, email, password):
        page.clean()
        username_field = create_input("Username", "username")

        def on_submit(e):
            submit(username_field.value, fname, email, password)

        page.add(
            flet.Text("Change Username",
                      color='black', size=25, weight='bold'),
            username_field,
            flet.Button("Submit", on_click=on_submit)
        )

    def pass_change(username, fname, email):
        page.clean()
        password_field = create_input("Password", "Enter password")

        def on_submit(e):
            submit(username, fname, email, password_field.value)

        page.add(
            flet.Text("Change Password",
                      color='black', size=25, weight='bold'),
            password_field,
            flet.Button("Submit", on_click=on_submit)
        )
        
    main_screen()
    

flet.run(main)