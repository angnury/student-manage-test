"""UI 自动化 fixture：浏览器驱动、登录态、失败截图。

运行前提（缺一个就跑不起来）：
1. 后端已启动：http://localhost:8080
2. 前端 dev 已启动：http://localhost:5173（vite 默认端口）
3. 本机有 Edge 或 Chrome

可用环境变量覆盖：
- UI_BASE_URL   默认 http://localhost:5173
- UI_BROWSER    edge（默认）/ chrome
- UI_HEADLESS   1（默认无头）/ 0（有头，调试时用）
"""
import os

import allure
import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from pages.login_page import LoginPage

UI_BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:5173")
UI_BROWSER = os.getenv("UI_BROWSER", "edge").lower()
UI_HEADLESS = os.getenv("UI_HEADLESS", "1") != "0"


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    return UI_BASE_URL


@pytest.fixture(scope="session", autouse=True)
def _require_frontend(ui_base_url):
    """前端没起就把整组 UI 用例标记为跳过，而不是让每条用例各报一次连接错误。"""
    try:
        # 线上站点跨境访问首包可能较慢，探测超时给到 20 秒，避免误判成"服务没起"
        requests.get(ui_base_url, timeout=20)
    except Exception:  # noqa: BLE001
        pytest.skip(f"前端服务未启动（{ui_base_url}），UI 用例跳过。先执行：npm run dev")


def _driver_service(browser_name: str):
    """优先用项目内自带的驱动，避免 Selenium Manager 联网下载 / 被安全策略拦截。

    把 msedgedriver.exe（或 chromedriver.exe）放到项目根目录的 drivers/ 下即可，
    也可以用环境变量 UI_DRIVER_PATH 指定完整路径。
    """
    from pathlib import Path

    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.edge.service import Service as EdgeService

    root = Path(__file__).resolve().parents[2]
    explicit = os.getenv("UI_DRIVER_PATH")
    default_name = "chromedriver.exe" if browser_name == "chrome" else "msedgedriver.exe"
    candidate = Path(explicit) if explicit else root / "drivers" / default_name
    if not candidate.is_file():
        return None
    service_cls = ChromeService if browser_name == "chrome" else EdgeService
    return service_cls(executable_path=str(candidate))


def _new_driver():
    options = ChromeOptions() if UI_BROWSER == "chrome" else EdgeOptions()
    if UI_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=zh-CN")
    # 只等 DOM 就绪，不等图片等次要资源：跨境访问线上站点时能省一半时间
    options.page_load_strategy = "eager"
    factory = webdriver.Chrome if UI_BROWSER == "chrome" else webdriver.Edge
    service = _driver_service(UI_BROWSER)
    browser = factory(service=service, options=options) if service else factory(options=options)
    # 页面级超时单独放大：CI 跑在海外 runner，访问国内服务器首屏可能要 20s 以上
    browser.set_page_load_timeout(60)
    return browser


@pytest.fixture
def driver():
    browser = _new_driver()
    browser.implicitly_wait(0)  # 只用显式等待，避免隐式等待拖慢失败用例
    yield browser
    browser.quit()


@pytest.fixture
def login_page(driver, ui_base_url):
    return LoginPage(driver, ui_base_url)


@pytest.fixture
def admin_page(driver, ui_base_url, env):
    """以管理员身份登录，返回停留在工作台的 LoginPage（可继续链式跳转）。

    CI 跑在海外 runner 上访问国内服务器，首次加载经常要 15-25 秒；偶发超时时重试一次，
    并把第一次失败的截图留档，避免"整组 UI 用例全 broken"却查不出原因。
    """
    page = LoginPage(driver, ui_base_url)
    last_error = None
    for attempt in range(2):
        try:
            page.open_login().login(env["admin"]["username"], env["admin"]["password"])
            page.wait_url_contains("/dashboard", timeout=30)
            return page
        except TimeoutException as exc:
            last_error = exc
            try:
                driver.save_screenshot(f"screenshots/login_attempt{attempt + 1}.png")
                allure.attach(driver.get_screenshot_as_png(),
                              name=f"第 {attempt + 1} 次登录失败现场",
                              attachment_type=allure.attachment_type.PNG)
            except Exception:  # noqa: BLE001
                pass
    raise last_error


@pytest.fixture
def temp_ui_student(env):
    """提供一个 UI 用例专用的测试学号，用例结束后无论成败都通过接口清掉。

    只在用例里删容易漏：断言失败会跳过删除逻辑，脏数据就留在库里。
    所以清理放到 teardown，并且不走 UI（UI 可能已经崩了），直接打接口。
    """
    import time

    sid = "T" + str(int(time.time()))[-7:]
    yield sid

    try:
        token = requests.post(
            f"{env['base_url']}/api/auth/login",
            json={"username": env["admin"]["username"], "password": env["admin"]["password"]},
            timeout=10,
        ).json()["data"]["token"]
        requests.delete(
            f"{env['base_url']}/api/admin/students/{sid}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[警告] UI 测试数据清理失败 {sid}：{exc}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """UI 用例失败时自动截图并挂到 Allure 报告。"""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    driver = item.funcargs.get("driver")
    if driver is None:
        return
    import allure

    path = os.path.join("screenshots", f"{item.name}.png")
    os.makedirs("screenshots", exist_ok=True)
    try:
        driver.save_screenshot(path)
        allure.attach.file(path, name="失败截图", attachment_type=allure.attachment_type.PNG)
    except Exception:  # noqa: BLE001
        pass
