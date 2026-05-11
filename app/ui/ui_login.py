import flet as ft
import httpx
import re
import hashlib
from typing import cast
from app.config import API_ROOT

# Main screen with options to login or create account
class MainScreen(ft.Column):
    """Main landing screen for authentication navigation.

    Displays options for users to either log in or create a new account.
    Handles screen transitions between authentication views.

    Attributes:
        id: Shared application state object containing the current user ID.
        _page: Flet page instance used for UI updates.
        on_login_success: Callback triggered after successful authentication.
        back_button: Button used to return to the main menu.
        menu_controls: Default controls displayed on the landing screen.
    """

    def __init__(self, id, page, on_login_success):
        """Initializes the main authentication screen.

        Args:
            id: Shared application state object.
            page: Current Flet page instance.
            on_login_success: Async callback executed after login success.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # user_id for application state
        self.id = id
        self._page = page
        self.on_login_success = on_login_success

        self.back_button = ft.Button("Back", on_click=self.show_menu)

        self.menu_controls = cast(list[ft.Control], [
            ft.Text("Welcome to Snuzzl!", size=25, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Button("Login", on_click=self.login),
                ft.Button("Create Account", on_click=self.create_account)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ])

    def show_menu(self, e=None):
        """Displays the main authentication menu.

        Args:
            e: Optional Flet event object.
        """
        self.controls.clear()
        self.controls.extend(self.menu_controls)
        self.update()

    def login(self, e=None):
        """Switches the UI to the login screen.

        Args:
            e: Optional Flet event object.
        """
        self.controls.clear()
        self.controls.extend([Login(self.id, self.back_button, self.on_login_success)])
        self.update()

    def create_account(self, e=None):
        """Switches the UI to the account creation screen.

        Args:
            e: Optional Flet event object.
        """
        self.controls.clear()
        self.controls.extend([CreateAccount(self.id, self._page, self.back_button, self.on_login_success)])
        self.update()


# Create account screen
class CreateAccount(ft.Column):
    """Screen for creating a new user account.

    Handles user input validation, date selection, and account creation
    requests through the backend API.

    Attributes:
        id: Shared application state object.
        _page: Current Flet page instance.
        on_login_success: Callback triggered after successful account creation.
        username_field: Username input field.
        fname_field: First name input field.
        email_field: Email input field.
        password_field: Password input field.
        confirm_password_field: Password confirmation input field.
        dob_picker: Date picker control for date of birth selection.
        dob_field: Read-only field displaying selected date of birth.
        error_message: Text control for validation and API errors.
    """

    def __init__(self, id, page, back_button, on_login_success):
        """Initializes the create account screen.

        Args:
            id: Shared application state object.
            page: Current Flet page instance.
            back_button: Navigation button to return to previous screen.
            on_login_success: Async callback executed after successful signup.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.id = id
        self._page = page
        self.on_login_success = on_login_success

        # creates each text field and assigns to a varaible
        self.username_field = self.create_input("Username", "username")
        self.fname_field = self.create_input("First Name", "Jane")
        self.email_field = self.create_input("Email", "example@gmail.com")
        self.password_field = self.create_input("Password", "Enter password", password=True)
        self.confirm_password_field = self.create_input("Confirm Password", "Re-enter password", password=True)
        
        self.dob_picker = ft.DatePicker(on_change=self.update_dob)
        self._page.overlay.append(self.dob_picker)

        self.dob_field = ft.TextField(
            label="Date of Birth",
            hint_text="Select date of birth",
            read_only=True,
            width=200,
            on_click=self.open_dob
        )

        self.error_message = ft.Text("", color='red')

        self.controls = cast(list[ft.Control], [
            ft.Text("Enter Details", size=25, weight=ft.FontWeight.BOLD),
            self.username_field,
            self.fname_field,
            self.email_field,
            self.password_field,
            self.confirm_password_field,
            self.dob_field,
            ft.Row([
                back_button,
                ft.Button("Submit", on_click=self.submit),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            self.error_message
        ])

    def _set_field_error(self, field: ft.TextField, message: str | None):
        """Sets validation error text on a text field.

        Args:
            field: Text field to update.
            message: Error message to display, or None to clear errors.
        """
        try:
            setattr(field, "error_text", message)
        except Exception:
            pass

    def create_input(self, label_text, hint, password=False):
        """Creates a styled text input field.

        Args:
            label_text: Label displayed above the field.
            hint: Placeholder text displayed inside the field.
            password: Whether the field should obscure entered text.

        Returns:
            ft.TextField: Configured Flet text field.
        """
        return ft.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
            )

    def is_valid_email(self, email):
        """Validates email address format using regex.

        Args:
            email: Email address string to validate.

        Returns:
            Match object if valid, otherwise None.
        """
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

    def open_dob(self):
        """Opens the date of birth picker dialog."""
        self.dob_picker.open = True
        self._page.update()

    def update_dob(self, e):
        """Updates the displayed date of birth after selection.

        Args:
            e: Flet date picker change event.
        """
        if self.dob_picker.value:
            self.dob_field.value = self.dob_picker.value.strftime("%Y-%m-%d")
            self._page.update()

    def _validate_password(self, password):
        """Validates password strength requirements.

        Args:
            password: Password string to validate.

        Raises:
            ValueError: If the password is shorter than 6 characters.

        Returns:
            bool: True if password is valid.
        """
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return True

    async def submit(self, e=None):
        """Validates form data and submits account creation request.

        Performs:
            - Required field validation
            - Password confirmation matching
            - Email format validation
            - Password strength validation
            - API request for account creation

        Args:
            e: Optional Flet event object.
        """

        self.error_message.value = ""

        fields = [
            (self.username_field, "Username cannot be empty"),
            (self.fname_field, "First name cannot be empty"),
            (self.email_field, "Email cannot be empty"),
            (self.password_field, "Password cannot be empty"),
            (self.dob_field, "Date of birth cannot be empty")
        ]

        # Check all fields have a value
        for field, message in fields:
            if not field.value or not field.value.strip():
                self._set_field_error(field, message)
                self.error_message.value = "Please fill in all fields"
                self.update()
                return
            else:
                self._set_field_error(field, None)

        # Match password fields
        if self.password_field.value != self.confirm_password_field.value:
            self._set_field_error(self.confirm_password_field, "Passwords do not match")
            self.error_message.value = "Please ensure passwords match"
            self.update()
            return

        # Validate email
        if not self.is_valid_email(self.email_field.value):
            self._set_field_error(self.email_field, "Invalid email format")
            self.error_message.value = "Please enter a valid email address"
            self.update()
            return

        # Validate pasword
        try:
            self._validate_password(self.password_field.value)
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()
            return

        # Create account using API
        payload = {
            "email": self.email_field.value.strip(),
            "username": self.username_field.value.strip(),
            "fname": self.fname_field.value.strip(),
            "dob": self.dob_field.value.strip(),
            "password": hashlib.sha256(self.password_field.value.strip().encode('utf-8')).hexdigest()
        }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/create_account", json=payload)
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If account creation successful, assign user_id for app state and load main menu
                self.id.user_id = result['user_id']
                await self.on_login_success()
            elif not result['success']:
                self.error_message.value = f"{result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()
        

# Screen for logging into an existing account
class Login(ft.Column):
    """Screen for authenticating existing users.

    Handles credential validation and login requests through the backend API.

    Attributes:
        id: Shared application state object.
        on_login_success: Callback triggered after successful login.
        username_field: Username input field.
        password_field: Password input field.
        error_message: Text control for validation and API errors.
    """

    def __init__(self, id, back_button, on_login_success):
        """Initializes the login screen.

        Args:
            id: Shared application state object.
            back_button: Navigation button to return to previous screen.
            on_login_success: Async callback executed after successful login.
        """
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        # A user_id object from client.py, used to track application state
        self.id = id
        self.on_login_success = on_login_success

        self.username_field = self.create_input("Username", "username")
        self.password_field = self.create_input("Password", "Enter password", password=True)
        self.error_message = ft.Text("")

        self.controls = cast(list[ft.Control], [
            ft.Text("Login", size=25, weight=ft.FontWeight.BOLD),
            self.username_field,
            self.password_field,
            ft.Row([
                back_button,
                ft.Button("Submit", on_click=self.submit),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            self.error_message
        ])

    def create_input(self, label_text, hint, password=False):
        """Creates a styled text input field.

        Args:
            label_text: Label displayed above the field.
            hint: Placeholder text displayed inside the field.
            password: Whether the field should obscure entered text.

        Returns:
            ft.TextField: Configured Flet text field.
        """
        return ft.TextField(
            label=label_text,
            hint_text=hint,
            width=200,
            border=ft.InputBorder.UNDERLINE,
            filled=True,
            password=password,
            can_reveal_password=password
        )

    async def submit(self, e=None):
        """Validates credentials and submits login request.

        Args:
            e: Optional Flet event object.
        """
        if self.username_field.value.strip() == "":
            self.error_message.value = "Missing Username"
            self.update()
            return
        if self.password_field.value.strip() == "":
            self.error_message.value = "Missing Password"
            self.update()
            return

        payload = {
            "username": self.username_field.value.strip(),
            "password": hashlib.sha256(self.password_field.value.strip().encode('utf-8')).hexdigest()
        }
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(f"{API_ROOT}/login", json=payload)
            result.raise_for_status()
            result = result.json()
            if result['success']:
                # If login successful, assign user_id for app state and load main menu
                self.id.user_id = result['user_id']
                await self.on_login_success()
            elif not result['success']:
                # Show error message
                self.error_message.value = f"Login failed: {result['message']}"
                self.update()
        except Exception as ex:
            self.error_message.value = f"Error: {ex}"
            self.update()