"""登录 / 鉴权相关接口。"""

from api.base_api import BaseApi


class AuthApi(BaseApi):
    def login(self, username, password):
        return self.post("/api/auth/login", json={"username": username, "password": password})
