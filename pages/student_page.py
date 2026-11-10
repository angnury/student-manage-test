"""学生管理页 Page Object。"""
import re

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class StudentPage(BasePage):

    TOTAL = "student-total"
    TABLE = "student-table"
    SEARCH_SID = "student-search-sid"
    SEARCH_NAME = "student-search-name"
    SEARCH_BTN = "student-search-btn"
    RESET_BTN = "student-reset-btn"
    ADD_BTN = "student-add-btn"

    DIALOG = "student-dialog"
    DIALOG_SID = "dialog-sid"
    DIALOG_SNAME = "dialog-sname"
    DIALOG_SCLASS = "dialog-sclass"
    DIALOG_PHONE = "dialog-phone"
    DIALOG_SUBMIT = "dialog-submit"
    DIALOG_CANCEL = "dialog-cancel"

    def open_page(self) -> "StudentPage":
        self.open("/students")
        self.wait_loaded()
        return self

    # ---------- 列表 ----------

    def wait_loaded(self, timeout: int = 15):
        """等表格渲染出至少一行数据。"""
        self.visible(self.TABLE, timeout=timeout)

        def _has_rows(driver):
            rows = driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{self.TABLE}'] tbody tr")
            return rows if rows else False

        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(_has_rows, message="学生表格没有加载出任何数据行")

    def row_count(self) -> int:
        return len(self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{self.TABLE}'] tbody tr"))

    def total(self) -> int:
        """从「共 N 条记录」里取出 N。"""
        text = self.wait_text_contains(self.TOTAL, "共")
        match = re.search(r"共\s*(\d+)\s*条", text)
        return int(match.group(1)) if match else -1

    def wait_total(self, expected: int, timeout: int = 10) -> int:
        """等「共 N 条记录」变成期望值，用于增删后的列表刷新断言。"""
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, timeout).until(
            lambda d: self.total() == expected,
            message=f"列表总数没有变成 {expected}，当前 {self.total()}",
        )
        return expected

    def rows(self, retries: int = 3) -> list[list[str]]:
        """读取表格所有行。

        v-loading 刷新时表格节点会被整体重建，遍历中途会抛 StaleElementReferenceException，
        所以这里做重试：重新查一次 DOM，而不是让用例因为"数据刚好在刷新"而假失败。
        """
        import time

        from selenium.common.exceptions import StaleElementReferenceException

        for attempt in range(retries):
            try:
                result = []
                for row in self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{self.TABLE}'] tbody tr"):
                    result.append([cell.text.strip() for cell in row.find_elements(By.TAG_NAME, "td")])
                return result
            except StaleElementReferenceException:
                if attempt == retries - 1:
                    raise
                time.sleep(0.5)
        return []

    def sids(self) -> list[str]:
        """学号是表格第一列。"""
        return [row[0] for row in self.rows() if row]

    # ---------- 查询 ----------

    def search_by_sid(self, sid: str) -> "StudentPage":
        self.fill(self.SEARCH_SID, sid)
        self.click(self.SEARCH_BTN)
        return self

    def reset_search(self) -> "StudentPage":
        self.click(self.RESET_BTN)
        return self

    # ---------- 新增 / 删除 ----------

    def open_add_dialog(self) -> "StudentPage":
        self.click(self.ADD_BTN)
        self.visible(self.DIALOG)
        return self

    def fill_add_form(self, sid: str, sname: str, sclass: str = "计科自动化1班", phone: str = "13800000000"):
        self.fill(self.DIALOG_SID, sid)
        self.fill(self.DIALOG_SNAME, sname)
        self.fill(self.DIALOG_SCLASS, sclass)
        self.fill(self.DIALOG_PHONE, phone)
        return self

    def submit_dialog(self) -> "StudentPage":
        self.click(self.DIALOG_SUBMIT)
        return self

    def delete_student(self, sid: str) -> "StudentPage":
        """按学号删一行：先定位到该行的删除按钮，再确认 ElMessageBox。

        表格刷新会让已拿到的行节点失效，所以整体放在重试里。
        """
        import time

        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        last_error = None
        for _ in range(3):
            try:
                for row in self.driver.find_elements(By.CSS_SELECTOR, f"[data-testid='{self.TABLE}'] tbody tr"):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells and cells[0].text.strip() == sid:
                        row.find_element(By.CSS_SELECTOR, "[data-testid='row-delete']").click()
                        break
                else:
                    last_error = AssertionError(f"表格里找不到学号 {sid} 的行")
                    time.sleep(0.5)
                    continue
                break
            except StaleElementReferenceException as exc:
                last_error = exc
                time.sleep(0.5)
        else:
            raise last_error  # type: ignore[misc]

        confirm = "//div[contains(@class,'el-message-box')]//button[.//span[text()='确定']]"
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, confirm))).click()
        return self
