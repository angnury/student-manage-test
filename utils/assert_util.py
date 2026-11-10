"""断言工具：把 HTTP 状态码 + 业务 code 两层校验收敛到一处。"""


def assert_biz(resp, expect_code: int = 200, expect_http: int = 200):
    """校验 HTTP 状态码与响应体里的业务 code，返回解析后的 body。

    业务异常（BizException）走全局异常处理，HTTP 恒为 200、业务 code 为 400；
    鉴权失败由拦截器直接写响应，HTTP 与业务 code 一致（401/403）。
    """
    assert resp.status_code == expect_http, (
        f"HTTP 状态码期望 {expect_http}，实际 {resp.status_code}；响应：{resp.text[:300]}"
    )
    body = resp.json()
    assert body.get("code") == expect_code, (
        f"业务 code 期望 {expect_code}，实际 {body.get('code')}；message={body.get('message')}"
    )
    return body


def assert_reject(resp, expect_code: int):
    """鉴权类响应：HTTP 状态码与 body.code 都应为 401 / 403。"""
    assert resp.status_code == expect_code, (
        f"HTTP 状态码期望 {expect_code}，实际 {resp.status_code}；响应：{resp.text[:300]}"
    )
    body = resp.json()
    assert body.get("code") == expect_code, f"body.code 期望 {expect_code}，实际 {body.get('code')}"
    return body
