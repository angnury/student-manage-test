import allure
import pytest


@allure.feature("UI-登录")
class TestLoginUI:

    @allure.title("管理员登录成功：跳转工作台并显示用户名")
    @pytest.mark.ui
    @pytest.mark.p0
    def test_login_success(self, login_page, env):
        login_page.open_login().login(env["admin"]["username"], env["admin"]["password"])

        login_page.wait_url_contains("/dashboard")
        text = login_page.wait_text_contains("header-username", env["admin"]["username"])
        assert env["admin"]["username"] in text, f"顶栏没有显示登录用户，实际：{text}"

    @allure.title("密码错误：提示错误且停留在登录页")
    @pytest.mark.ui
    @pytest.mark.p1
    def test_login_wrong_password(self, login_page, env):
        login_page.open_login().login(env["admin"]["username"], "wrong_password_123")

        message = login_page.wait_message("用户名或密码错误")
        assert "用户名或密码错误" in message
        assert "/login" in login_page.driver.current_url, "登录失败后不应跳转"
