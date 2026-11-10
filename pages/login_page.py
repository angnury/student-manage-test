"""登录页 Page Object。"""
from pages.base_page import BasePage


class LoginPage(BasePage):

    USERNAME = "login-username"
    PASSWORD = "login-password"
    SUBMIT = "login-submit"

    def open_login(self) -> "LoginPage":
        self.open("/login")
        self.visible(self.SUBMIT)
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self
