import allure
import pytest

from api.stats_api import StatsApi


@allure.feature("统计报表")
class TestStatistics:

    @allure.title("工作台概览返回四项计数")
    @pytest.mark.p0
    def test_overview(self, admin, env):
        body = StatsApi(admin, env).overview().json()
        assert body["code"] == 200
        data = body["data"]
        for key in ("studentCount", "classCount", "courseCount", "scoreCount"):
            assert key in data, f"概览缺少字段 {key}"
            assert isinstance(data[key], int), f"{key} 应为数字，实际 {type(data[key])}"

    @allure.title("成绩分布返回各分数段且无空值")
    @pytest.mark.p0
    def test_score_distribution(self, admin, env):
        body = StatsApi(admin, env).score_distribution().json()
        assert body["code"] == 200
        data = body["data"]
        assert isinstance(data, dict) and data, "成绩分布返回为空"
        for segment, count in data.items():
            assert isinstance(count, (int, float)), f"分数段 {segment} 的数量不是数字：{count}"

    @allure.title("班级平均分返回列表结构")
    @pytest.mark.p0
    def test_class_average(self, admin, env):
        body = StatsApi(admin, env).class_average().json()
        assert body["code"] == 200
        data = body["data"]
        assert isinstance(data, list), f"班级平均分应返回列表，实际 {type(data)}"
        for row in data:
            assert isinstance(row, dict), "列表元素应为对象"
