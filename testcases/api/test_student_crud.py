import allure
import pytest
import yaml
from pathlib import Path

from api.student_api import StudentApi
from utils.assert_util import assert_biz
from utils.data_util import gen_sid

BASE = yaml.safe_load((Path(__file__).parents[2] / "data" / "student.yaml").read_text(encoding="utf-8"))["valid"]

# temp_student 定义在 testcases/api/conftest.py，供本模块与成绩用例共用


@allure.feature("学生管理")
class TestStudentCrud:

    @allure.story("新增")
    @allure.title("新增学生后能按学号查到")
    @pytest.mark.p0
    def test_add_and_query(self, admin, env, temp_student):
        api = StudentApi(admin, env)
        body = assert_biz(api.query_by_sid(temp_student["sid"]), 200)
        assert body["data"]["total"] >= 1, "新增成功但查不到该学号"
        assert body["data"]["records"][0]["sid"] == temp_student["sid"]

    @allure.story("新增")
    @allure.title("学号重复时返回业务错误，不允许覆盖")
    @pytest.mark.p1
    def test_add_duplicate(self, admin, env, temp_student):
        api = StudentApi(admin, env)
        resp = api.add({"sid": temp_student["sid"], **BASE})
        assert_biz(resp, 400)

    @allure.story("修改")
    @allure.title("按学号更新姓名后查询结果同步变化")
    @pytest.mark.p0
    def test_update(self, admin, env, temp_student):
        api = StudentApi(admin, env)
        assert_biz(api.update(temp_student["sid"], {**BASE, "sname": "改名后"}), 200)
        body = assert_biz(api.query_by_sid(temp_student["sid"]), 200)
        assert body["data"]["records"][0]["sname"] == "改名后"

    @allure.story("删除")
    @allure.title("删除学生后按学号查不到")
    @pytest.mark.p0
    def test_delete(self, admin, env):
        api = StudentApi(admin, env)
        sid = gen_sid()
        assert_biz(api.add({"sid": sid, **BASE}), 200)
        assert_biz(api.remove(sid), 200)
        body = assert_biz(api.query_by_sid(sid), 200)
        assert body["data"]["total"] == 0, "删除后仍能查到该学号，可能存在脏数据"

    @allure.story("数据一致性")
    @allure.title("新增学生后学籍与登录账号都应落库")
    @pytest.mark.p1
    def test_account_created_with_student(self, admin, env, db, temp_student):
        api = StudentApi(admin, env)
        sid = temp_student["sid"]
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM student WHERE sid = %s", (sid,))
            assert cur.fetchone()["c"] == 1, "student 表未写入"
            cur.execute("SELECT COUNT(*) AS c FROM sys_user WHERE username = %s", (sid,))
            assert cur.fetchone()["c"] == 1, "新增学生未同步创建登录账号，学生无法登录"

    @allure.story("数据一致性")
    @allure.title("删除学生后其登录账号应同步清理")
    @pytest.mark.p1
    def test_account_removed_with_student(self, admin, env, db):
        api = StudentApi(admin, env)
        sid = gen_sid()
        assert_biz(api.add({"sid": sid, **BASE}), 200)
        assert_biz(api.remove(sid), 200)
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM sys_user WHERE username = %s", (sid,))
            assert cur.fetchone()["c"] == 0, "删除学生后登录账号残留，会留下可登录的僵尸账号"
