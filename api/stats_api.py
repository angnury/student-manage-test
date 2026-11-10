"""统计报表接口（仅 ADMIN）。"""

from api.base_api import BaseApi


class StatsApi(BaseApi):
    BASE = "/api/admin/statistics"

    def overview(self):
        return self.get(f"{self.BASE}/overview")

    def score_distribution(self):
        return self.get(f"{self.BASE}/score-distribution")

    def class_average(self):
        return self.get(f"{self.BASE}/class-average")
