"""成绩接口（TEACHER / ADMIN）。"""

from api.base_api import BaseApi


class ScoreApi(BaseApi):
    def courses(self):
        return self.get("/api/teacher/courses")

    def students(self, **params):
        return self.get("/api/teacher/students", params=params)

    def scores_of(self, sid: str):
        return self.get(f"/api/teacher/students/{sid}/scores")

    def save(self, payload: dict):
        """录入或更新成绩，total 由后端按 平时分*0.4 + 期末分*0.6 计算。"""
        return self.post("/api/teacher/scores", json=payload)
