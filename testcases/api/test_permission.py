import allure
import pytest

from utils.assert_util import assert_reject

STUDENTS = "/api/admin/students"
STATS = "/api/admin/statistics/overview"
TEACHER_SCORES = "/api/teacher/scores"


@allure.feature("权限控制")
@allure.story("鉴权拦截")
class TestAuth:

    @allure.title("无 token 访问受保护接口返回 401")
    @pytest.mark.p0
    def test_no_token(self, anon, env):
        assert_reject(anon.get(f"{env['base_url']}{STUDENTS}", timeout=10), 401)

    @allure.title("伪造 token 返回 401")
    @pytest.mark.p0
    def test_fake_token(self, env):
        import requests

        resp = requests.get(
            f"{env['base_url']}{STUDENTS}",
            headers={"Authorization": "Bearer fake.token.value"},
            timeout=10,
        )
        assert_reject(resp, 401)

    @allure.title("Authorization 头格式错误（缺 Bearer 前缀）返回 401")
    @pytest.mark.p1
    def test_wrong_header_format(self, admin_token, env):
        import requests

        resp = requests.get(f"{env['base_url']}{STUDENTS}", headers={"Authorization": admin_token}, timeout=10)
        assert_reject(resp, 401)


@allure.feature("权限控制")
@allure.story("角色越权")
class TestPermission:

    @allure.title("学生角色访问管理员的学生管理接口返回 403")
    @pytest.mark.p0
    def test_student_cannot_access_admin(self, student, env):
        assert_reject(student.get(f"{env['base_url']}{STUDENTS}", timeout=10), 403)

    @allure.title("教师角色访问管理员的学生管理接口返回 403")
    @pytest.mark.p0
    def test_teacher_cannot_access_admin(self, teacher, env):
        assert_reject(teacher.get(f"{env['base_url']}{STUDENTS}", timeout=10), 403)

    @allure.title("教师角色访问统计报表返回 403")
    @pytest.mark.p0
    def test_teacher_cannot_access_statistics(self, teacher, env):
        assert_reject(teacher.get(f"{env['base_url']}{STATS}", timeout=10), 403)

    @allure.title("学生角色录入成绩返回 403")
    @pytest.mark.p0
    def test_student_cannot_save_score(self, student, env):
        payload = {"sid": "T000000", "cid": "C001", "term": "2025-2026-1", "usual": 90, "finalScore": 90}
        assert_reject(student.post(f"{env['base_url']}{TEACHER_SCORES}", json=payload, timeout=10), 403)

    @allure.title("管理员访问管理员接口正常返回 200")
    @pytest.mark.p0
    def test_admin_allowed(self, admin, env):
        resp = admin.get(f"{env['base_url']}{STUDENTS}", timeout=10)
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
