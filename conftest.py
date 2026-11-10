"""全局 fixture 与配置加载。

约定：
- 环境由环境变量 TEST_ENV 决定（默认 local），对应 config/config.yaml 里的同名节点；
- CI 环境可用环境变量覆盖密码，避免把口令写进仓库；
- 所有 client fixture 都是 requests.Session，已带 Authorization 头。
"""
import os
from pathlib import Path

import allure
import pytest
import requests
import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config" / "config.yaml"
ENV_NAME = os.getenv("TEST_ENV", "local")


def _load_env():
    if not CONFIG_FILE.exists():
        pytest.exit(
            "缺少 config/config.yaml。请先执行：\n"
            "  cp config/config.example.yaml config/config.yaml\n"
            "并填入真实的数据库密码与三个角色的账号。",
            returncode=2,
        )
    configs = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    if ENV_NAME not in configs:
        pytest.exit(f"config/config.yaml 中没有环境节点：{ENV_NAME}", returncode=2)
    return configs[ENV_NAME]


ENV = _load_env()

# CI / 本地临时覆盖密码
for _role, _var in (("admin", "ADMIN_PASSWORD"), ("teacher", "TEACHER_PASSWORD"), ("student", "STUDENT_PASSWORD")):
    if os.getenv(_var) and _role in ENV:
        ENV[_role]["password"] = os.getenv(_var)


@pytest.fixture(scope="session")
def env():
    """当前环境配置（base_url、数据库、三种角色账号）。"""
    return ENV


def _login_by_role(role: str) -> str:
    account = ENV[role]
    resp = requests.post(
        f"{ENV['base_url']}/api/auth/login",
        json={"username": account["username"], "password": account["password"]},
        timeout=10,
    )
    assert resp.status_code == 200, (
        f"{role} 登录失败：HTTP {resp.status_code} {resp.text[:200]}\n"
        f"请检查 config/config.yaml 里 {role} 的账号密码（当前 username={account['username']}），"
        f"以及被测系统是否已启动：{ENV['base_url']}"
    )
    body = resp.json()
    assert body.get("code") == 200, f"{role} 登录失败：{body}"
    return body["data"]["token"]


def _new_client(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def admin_token():
    return _login_by_role("admin")


@pytest.fixture(scope="session")
def teacher_token():
    return _login_by_role("teacher")


@pytest.fixture(scope="session")
def student_token():
    return _login_by_role("student")


@pytest.fixture(scope="session")
def admin(admin_token):
    session = _new_client(admin_token)
    yield session
    session.close()


@pytest.fixture(scope="session")
def teacher(teacher_token):
    session = _new_client(teacher_token)
    yield session
    session.close()


@pytest.fixture(scope="session")
def student(student_token):
    session = _new_client(student_token)
    yield session
    session.close()


@pytest.fixture(scope="session")
def anon():
    """不带 token 的客户端，用于验证鉴权拦截。"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="session")
def db(env):
    """直连数据库的游标，用于校验接口落库结果。数据库不可达时整条链路跳过。"""
    pymysql = pytest.importorskip("pymysql", reason="未安装 pymysql")
    if "db" not in env:
        pytest.skip(f"环境 {ENV_NAME} 未配置数据库连接（线上库不对外暴露），跳过落库校验")
    try:
        # autocommit=True 很关键：否则 InnoDB 可重复读会让后续 SELECT 一直看会话开始时的快照，
        # 用例刚插入的数据在断言里"查不到"，误报成数据没落库。
        conn = pymysql.connect(
            **env["db"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"数据库不可达，跳过落库校验：{exc}")
    yield conn
    conn.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时把接口请求/响应附到 Allure 报告里，便于定位。"""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    from api.base_api import LAST_RESPONSE

    if LAST_RESPONSE.get("text"):
        allure.attach(LAST_RESPONSE["text"], name="最后一次接口响应", attachment_type=allure.attachment_type.TEXT)
