"""UI 自动化基类：统一等待、定位、截图。

定位约定
--------
所有元素一律用 ``data-testid`` 定位，不依赖 class / 文案 / DOM 层级：
- class 是给样式用的，改样式就断；
- 文案会改，而且同一个 placeholder 可能出现在页面和弹窗里（本项目就有）；
- 层级选择器（:nth-child）改个布局就全废。

一个必须注意的点（实测结论，和文档说法不一样）
------------------------------------------------
Element Plus 的 ``el-input`` 用 ``inheritAttrs: false`` + ``v-bind="$attrs"`` 把非 prop 属性
**直接透传到内部的 ``<input>``**，不是外层 div。实测 DOM：

    <input class="el-input__inner" data-testid="login-username" ...>

所以 ``[data-testid='login-username']`` 命中的就是输入框本身，**不能再拼 `` input``**。
但不同版本/组件的透传行为可能不同，所以 :meth:`fill` 做了一层兼容：命中元素不是 input 时，
自动往下找一层 ``input``。这样两种行为都能跑。
"""
import os

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:

    def __init__(self, driver, base_url: str, timeout: int = 10):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ---------- 定位 ----------

    @staticmethod
    def _locator(testid: str, inner: str | None = None):
        css = f"[data-testid='{testid}']"
        return (By.CSS_SELECTOR, f"{css} {inner}" if inner else css)

    def el(self, testid: str, inner: str | None = None, timeout: int | None = None):
        """等元素出现在 DOM 里（不要求可见）。"""
        return WebDriverWait(self.driver, timeout or self.timeout).until(
            EC.presence_of_element_located(self._locator(testid, inner))
        )

    def visible(self, testid: str, inner: str | None = None, timeout: int | None = None):
        """等元素可见，适合断言弹窗、提示等。"""
        return WebDriverWait(self.driver, timeout or self.timeout).until(
            EC.visibility_of_element_located(self._locator(testid, inner))
        )

    def exists(self, testid: str, inner: str | None = None, timeout: int = 3) -> bool:
        try:
            self.el(testid, inner, timeout)
            return True
        except TimeoutException:
            return False

    # ---------- 操作 ----------

    def open(self, path: str = "/"):
        self.driver.get(f"{self.base_url}{path}")
        return self

    def click(self, testid: str, inner: str | None = None, timeout: int | None = None):
        element = WebDriverWait(self.driver, timeout or self.timeout).until(
            EC.element_to_be_clickable(self._locator(testid, inner))
        )
        element.click()
        return self

    def fill(self, testid: str, text: str):
        """给输入框填值。

        兼容两种透传行为：data-testid 落在 <input> 上（Element Plus 的 el-input 就是这种），
        或者落在包裹 div 上（需要再往下找 input）。
        """
        element = self.el(testid)
        box = element if element.tag_name == "input" else element.find_element(By.CSS_SELECTOR, "input")
        box.clear()
        if box.get_attribute("value"):
            from selenium.webdriver.common.keys import Keys

            box.send_keys(Keys.CONTROL, "a")
            box.send_keys(Keys.DELETE)
        box.send_keys(text)
        return self

    def text(self, testid: str) -> str:
        return self.el(testid).text.strip()

    def wait_text_contains(self, testid: str, keyword: str, timeout: int | None = None) -> str:
        def _contains(driver):
            element = driver.find_element(*self._locator(testid))
            return element.text.strip() if keyword in element.text else False

        return WebDriverWait(self.driver, timeout or self.timeout).until(_contains)

    # ---------- 通用断言辅助 ----------

    def wait_message(self, keyword: str, timeout: int = 10) -> str:
        """等 ElMessage 轻提示出现并包含关键字，返回提示全文。"""

        def _has_message(driver):
            for element in driver.find_elements(By.CSS_SELECTOR, ".el-message__content"):
                if keyword in element.text:
                    return element.text.strip()
            return False

        return WebDriverWait(self.driver, timeout).until(
            _has_message,
            message=f"{timeout} 秒内没有出现包含「{keyword}」的提示",
        )

    def wait_url_contains(self, fragment: str, timeout: int | None = None):
        WebDriverWait(self.driver, timeout or self.timeout).until(EC.url_contains(fragment))
        return self

    def screenshot(self, name: str):
        """截图并挂到 Allure 报告里（本地跑也能留档）。"""
        path = os.path.join("screenshots", f"{name}.png")
        os.makedirs("screenshots", exist_ok=True)
        self.driver.save_screenshot(path)
        allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)
        return path
