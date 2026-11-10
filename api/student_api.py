"""学生管理接口（仅 ADMIN）。"""

from api.base_api import BaseApi


class StudentApi(BaseApi):
    PATH = "/api/admin/students"

    def page(self, page=1, size=10, **filters):
        """分页 + 多条件模糊查询。"""
        params = {"page": page, "size": size}
        params.update({k: v for k, v in filters.items() if v is not None})
        return self.get(self.PATH, params=params)

    def add(self, student: dict):
        return self.post(self.PATH, json=student)

    def update(self, sid: str, student: dict):
        return self.put(f"{self.PATH}/{sid}", json=student)

    def remove(self, sid: str):
        """注意：不叫 delete，避免覆盖 BaseApi.delete。"""
        return self.delete(f"{self.PATH}/{sid}")

    def query_by_sid(self, sid: str):
        return self.page(page=1, size=100, sid=sid)
