"""api 测试专用 fixture：测试数据的建与清。"""
from pathlib import Path

import pytest
import yaml

from api.score_api import ScoreApi
from api.student_api import StudentApi
from utils.assert_util import assert_biz
from utils.data_util import as_list, gen_sid

BASE = yaml.safe_load((Path(__file__).parents[2] / "data" / "student.yaml").read_text(encoding="utf-8"))["valid"]


@pytest.fixture
def temp_student(admin, env):
    """建一条测试学生，用例结束无论成败都删除，避免污染数据。"""
    api = StudentApi(admin, env)
    sid = gen_sid()
    payload = {"sid": sid, **BASE}
    assert_biz(api.add(payload), 200)
    yield {"sid": sid, **BASE}
    api.remove(sid)


@pytest.fixture(scope="session")
def course_id(teacher, env):
    """取课程表里的第一门课，供成绩用例使用。课程为空时跳过对应用例。"""
    body = ScoreApi(teacher, env).courses().json()
    items = as_list(body.get("data"))
    if not items:
        pytest.skip("课程表为空，先在系统里准备至少一门课程再跑成绩用例")
    for key in ("cid", "id", "courseId", "cno"):
        if key in items[0]:
            return items[0][key]
    pytest.skip(f"无法从课程列表识别课程编号字段，实际返回：{items[0]}")
