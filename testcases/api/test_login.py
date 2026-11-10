import allure
import pytest
import yaml
from pathlib import Path

from api.auth_api import AuthApi

DATA = yaml.safe_load((Path(__file__).parents[2] / "data" / "login.yaml").read_text(encoding="utf-8"))


@allure.feature("登录鉴权")
class TestLogin:

    @allure.story("登录接口")
    @allure.title("{case}")
    @pytest.mark.p0
    @pytest.mark.parametrize("case", DATA, ids=[d["case"] for d in DATA])
    def test_login(self, admin, env, case):
        api = AuthApi(admin, env)
        resp = api.login(
            case["payload"].get("username"),
            case["payload"].get("password"),
        )

        assert resp.status_code == case["expect_http"], f"HTTP 期望 {case['expect_http']}，实际 {resp.status_code}"
        body = resp.json()
        assert body["code"] == case["expect_code"], f"业务码期望 {case['expect_code']}，实际 {body['code']}"

        if case["expect_code"] == 200:
            data = body["data"]
            assert data["token"], "登录成功但未返回 token"
            assert data["role"], "登录成功但未返回角色，前端无法做菜单鉴权"

    @allure.story("Token 可用性")
    @allure.title("登录拿到的 token 能正常访问受保护接口")
    @pytest.mark.p0
    def test_token_works(self, admin, env):
        resp = admin.get(f"{env['base_url']}/api/user/me", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
