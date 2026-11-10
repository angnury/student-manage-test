"""测试数据辅助函数。"""


def gen_sid() -> str:
    """生成不会与真实学号冲突的测试学号，前缀 T，便于事后批量清理。"""
    import uuid

    return "T" + uuid.uuid4().hex[:7].upper()


def as_list(data):
    """列表接口可能直接返回数组，也可能包一层分页对象，统一取出列表。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("records", "list", "courses", "students"):
            if isinstance(data.get(key), list):
                return data[key]
    return []
