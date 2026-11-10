"""接口层基类：统一拼 URL、记日志、缓存最后一次响应（失败时附到报告里）。"""
import json
import logging

logger = logging.getLogger("api")

# 保存最后一次请求的完整响应，供 conftest 的失败钩子读取
LAST_RESPONSE = {"text": ""}


class BaseApi:
    def __init__(self, client, env):
        self.client = client
        self.base_url = env["base_url"]

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", 15)
        logger.info("→ %s %s %s", method, url, kwargs.get("json") or kwargs.get("params") or "")
        resp = self.client.request(method, url, **kwargs)
        logger.info("← %s %s", resp.status_code, resp.text[:400])
        LAST_RESPONSE["text"] = (
            f"{method} {url}\n"
            f"params/json: {json.dumps(kwargs.get('json') or kwargs.get('params') or {}, ensure_ascii=False)}\n"
            f"status: {resp.status_code}\n"
            f"body: {resp.text}"
        )
        return resp

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)
