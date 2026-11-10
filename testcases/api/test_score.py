import allure
import pytest

from api.score_api import ScoreApi
from utils.assert_util import assert_biz

TERM = "2025-2026-1"


def _scores_of(api, sid):
    body = assert_biz(api.scores_of(sid), 200)
    data = body["data"]
    if isinstance(data, dict):
        return data.get("scores", [])
    return data or []


@allure.feature("成绩录入")
@allure.story("总分计算")
class TestScore:

    @allure.title("录入成绩后总分 = 平时分*0.4 + 期末分*0.6")
    @pytest.mark.p0
    def test_total_computed(self, teacher, env, temp_student, course_id):
        api = ScoreApi(teacher, env)
        payload = {"sid": temp_student["sid"], "cid": course_id, "term": TERM, "usual": 80, "finalScore": 90}
        assert_biz(api.save(payload), 200)

        records = [s for s in _scores_of(api, temp_student["sid"]) if s.get("cid") == course_id and s.get("term") == TERM]
        assert records, "保存成功但查不到成绩记录"
        assert records[0]["total"] == 86, f"总分计算错误：期望 86，实际 {records[0]['total']}"

    @allure.title("前端传入的 total 必须被后端覆盖，防止改分")
    @pytest.mark.p0
    def test_total_cannot_be_tampered(self, teacher, env, temp_student, course_id):
        api = ScoreApi(teacher, env)
        payload = {
            "sid": temp_student["sid"],
            "cid": course_id,
            "term": TERM,
            "usual": 60,
            "finalScore": 60,
            "total": 100,
        }
        assert_biz(api.save(payload), 200)

        records = [s for s in _scores_of(api, temp_student["sid"]) if s.get("cid") == course_id and s.get("term") == TERM]
        assert records, "保存成功但查不到成绩记录"
        assert records[0]["total"] == 60, f"传入 total=100 生效了，存在改分风险，实际 {records[0]['total']}"


@allure.feature("成绩录入")
@allure.story("参数校验")
class TestScoreValidation:

    @allure.title("缺少学期字段返回业务错误")
    @pytest.mark.p1
    def test_missing_term(self, teacher, env, temp_student, course_id):
        api = ScoreApi(teacher, env)
        payload = {"sid": temp_student["sid"], "cid": course_id, "usual": 80, "finalScore": 90}
        assert_biz(api.save(payload), 400)

    @allure.title("缺少平时分返回业务错误")
    @pytest.mark.p1
    def test_missing_usual(self, teacher, env, temp_student, course_id):
        api = ScoreApi(teacher, env)
        payload = {"sid": temp_student["sid"], "cid": course_id, "term": TERM, "finalScore": 90}
        assert_biz(api.save(payload), 400)

    @allure.title("分数超出 0-100 应被拒绝")
    @pytest.mark.p1
    @pytest.mark.xfail(reason="已知缺陷：Service 未校验分数区间，传入 120 / -10 仍会写入并算出总分", strict=False)
    def test_score_out_of_range(self, teacher, env, temp_student, course_id):
        api = ScoreApi(teacher, env)
        payload = {"sid": temp_student["sid"], "cid": course_id, "term": "2025-2026-2", "usual": 120, "finalScore": -10}
        body = api.save(payload).json()
        assert body["code"] == 400, "分数越界未被拦截"
