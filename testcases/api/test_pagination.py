import allure
import pytest

from api.student_api import StudentApi


@allure.feature("学生管理")
@allure.story("分页与查询")
class TestPagination:

    @allure.title("分页参数回显：current / size 与请求一致")
    @pytest.mark.p0
    def test_param_echo(self, admin, env):
        body = StudentApi(admin, env).page(page=2, size=5).json()
        assert body["code"] == 200
        assert body["data"]["current"] == 2
        assert body["data"]["size"] == 5

    @allure.title("分页生效：每页返回条数不超过 size")
    @pytest.mark.p0
    def test_size_applied(self, admin, env):
        body = StudentApi(admin, env).page(page=1, size=10).json()
        assert len(body["data"]["records"]) <= 10

    @allure.title("分页生效：total 等于真实记录总数")
    @pytest.mark.p0
    def test_total_is_real(self, admin, env, db):
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM student")
            real = cur.fetchone()["c"]
        body = StudentApi(admin, env).page(page=1, size=10).json()
        assert body["data"]["total"] == real

    @allure.title("页码超界返回空列表而不是报错")
    @pytest.mark.p1
    def test_page_out_of_range(self, admin, env):
        body = StudentApi(admin, env).page(page=9999, size=10).json()
        assert body["code"] == 200
        assert body["data"]["records"] == []

    @allure.title("边界值：size=0 不应返回系统异常")
    @pytest.mark.p1
    def test_size_zero(self, admin, env):
        body = StudentApi(admin, env).page(page=1, size=0).json()
        assert body["code"] != 500, "size=0 触发了系统异常，应返回可读的参数错误或空列表"

    @allure.title("边界值：size 负数不应返回系统异常")
    @pytest.mark.p1
    def test_size_negative(self, admin, env):
        body = StudentApi(admin, env).page(page=1, size=-1).json()
        assert body["code"] != 500, "size=-1 触发了系统异常，应做参数校验"

    @allure.title("边界值：size 超大不应拖垮服务")
    @pytest.mark.p1
    def test_size_huge(self, admin, env):
        body = StudentApi(admin, env).page(page=1, size=100000).json()
        assert body["code"] != 500, "size=100000 触发系统异常；建议后端对 size 设上限"

    @allure.title("模糊查询：按姓名过滤后结果都包含关键字")
    @pytest.mark.p1
    def test_filter_by_name(self, admin, env):
        keyword = "测试"
        body = StudentApi(admin, env).page(page=1, size=100, name=keyword).json()
        assert body["code"] == 200
        for record in body["data"]["records"]:
            assert keyword in record["sname"]

    @allure.title("参数类型错误：page 传非数字")
    @pytest.mark.p1
    def test_page_not_number(self, admin, env):
        body = StudentApi(admin, env).page(page="abc", size=10).json()
        assert body["code"] == 400, f"期望参数校验失败(400)，实际 {body['code']}"
