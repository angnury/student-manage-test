

import allure
import pytest

from pages.student_page import StudentPage


@pytest.fixture
def student_page(admin_page):
    """以管理员登录后进入学生管理页。"""
    return StudentPage(admin_page.driver, admin_page.base_url).open_page()


@allure.feature("UI-学生管理")
class TestStudentUI:

    @allure.title("列表加载：显示真实总数，且每页不超过 10 条")
    @pytest.mark.ui
    @pytest.mark.p0
    def test_list_loaded(self, student_page):
        total = student_page.total()
        assert total > 0, f"列表总数异常：{total}"
        assert student_page.row_count() == min(total, 10), (
            f"total={total}，但本页渲染了 {student_page.row_count()} 行"
        )

    @allure.title("按学号搜索：结果只包含匹配学号")
    @pytest.mark.ui
    @pytest.mark.p0
    def test_search_by_sid(self, student_page):
        target = student_page.sids()[0]
        student_page.search_by_sid(target)

        def _filtered(driver):
            sids = student_page.sids()
            return sids if sids and all(target == sid for sid in sids) else False

        from selenium.webdriver.support.ui import WebDriverWait

        sids = WebDriverWait(student_page.driver, 10).until(
            _filtered, message=f"搜索 {target} 后结果里出现了不匹配的学号"
        )
        assert target in sids

    @allure.title("重置搜索：清空条件后恢复完整列表")
    @pytest.mark.ui
    @pytest.mark.p1
    def test_reset_search(self, student_page):
        before = student_page.total()
        student_page.search_by_sid("不存在的学号999")
        student_page.wait_total(0)
        student_page.reset_search()
        student_page.wait_total(before)

    @allure.title("新增学生：列表总数 +1，能按学号搜到")
    @pytest.mark.ui
    @pytest.mark.p0
    def test_add_student(self, student_page, temp_ui_student):
        before = student_page.total()
        sid = temp_ui_student

        student_page.open_add_dialog().fill_add_form(sid, "UI自动化").submit_dialog()
        student_page.wait_message("成功")
        student_page.wait_total(before + 1)

        student_page.search_by_sid(sid)
        assert sid in student_page.sids(), "新增成功但列表里搜不到该学号"

        # 顺手验证删除链路（清理由 fixture 兜底，断言失败也不会留脏数据）
        student_page.delete_student(sid)
        student_page.wait_message("删除成功")
        student_page.reset_search()
        student_page.wait_total(before)

    @allure.title("学号重复：弹窗提示已存在，不新增记录")
    @pytest.mark.ui
    @pytest.mark.p1
    def test_add_duplicate_sid(self, student_page):
        before = student_page.total()
        existing = student_page.sids()[0]

        student_page.open_add_dialog().fill_add_form(existing, "重复学号").submit_dialog()
        message = student_page.wait_message("已存在")
        assert "已存在" in message
        student_page.wait_total(before)
