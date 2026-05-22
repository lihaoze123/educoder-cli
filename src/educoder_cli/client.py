import base64
import json
import time
from types import TracebackType
from typing import Any, Self

import httpx

from educoder_cli.errors import (
    EduCoderAPIError,
    EvaluationTimeoutError,
    SessionExpiredError,
    SignatureError,
)
from educoder_cli.models import Course, HomeworkCommon, TaskDetail
from educoder_cli.signature import gen_signature

JsonObject = dict[str, Any]


class EduCoderClient:
    BASE = "https://data.educoder.net/api"

    def __init__(
        self,
        zzud: str,
        cookie_autologin: str,
        cookie_session: str,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.zzud = zzud
        self.cookie = f"autologin_trustie={cookie_autologin}; _educoder_session={cookie_session}"
        self.pc_auth = cookie_session
        self._client = http_client or httpx.Client(timeout=30)
        self._owns_client = http_client is None

        self.course_identifier: str | None = None
        self.homework_common_id: int | None = None
        self.shixun_identifier: str | None = None
        self.myshixun_identifier: str | None = None
        self.game_identifier: str | None = None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def _headers(self, method: str) -> dict[str, str]:
        ts, sig = gen_signature(method)
        return {
            "X-EDU-Type": "pc",
            "X-EDU-Timestamp": str(ts),
            "X-EDU-Signature": sig,
            "Pc-Authorization": self.pc_auth,
            "Cookie": self.cookie,
            "Accept": "application/json",
        }

    def _request(
        self, method: str, endpoint: str, *, json_data: JsonObject | None = None
    ) -> JsonObject:
        url = f"{self.BASE}{endpoint}"
        headers = self._headers(method)

        if json_data is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            resp = self._client.request(method, url, headers=headers, json=json_data)
        else:
            resp = self._client.request(method, url, headers=headers)

        if resp.status_code == 401:
            raise SessionExpiredError("Cookie 已过期，请重新从浏览器获取", status_code=401)

        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise EduCoderAPIError(f"非 JSON 响应: {resp.text[:300]}") from exc

        if not isinstance(data, dict):
            raise EduCoderAPIError("JSON 响应不是对象")

        if data.get("status") == -102:
            raise SignatureError("签名验证失败，请检查 AK/SK 或时间戳")

        return data

    def _get(self, endpoint: str) -> JsonObject:
        return self._request("GET", endpoint)

    def _post(self, endpoint: str, json_data: JsonObject) -> JsonObject:
        return self._request("POST", endpoint, json_data=json_data)

    def get_courses(self, page: int = 1, limit: int = 20) -> list[Course]:
        data = self._get(
            f"/courses.json?page={page}&limit={limit}&order=mine&search=&zzud={self.zzud}"
        )
        return [Course.from_dict(course) for course in data.get("courses", [])]

    def get_homeworks(self, course_identifier: str | None = None) -> list[HomeworkCommon]:
        cid = course_identifier or self.course_identifier
        if not cid:
            raise ValueError("请先指定 course_identifier")
        data = self._get(
            f"/courses/{cid}/homework_commons.json"
            f"?limit=50&status=0&id={cid}&type=4&order=0&zzud={self.zzud}"
        )
        return [HomeworkCommon.from_dict(homework) for homework in data.get("homeworks", [])]

    def get_myshixun(self, myshixun_identifier: str | None = None) -> JsonObject:
        mid = myshixun_identifier or self.myshixun_identifier
        if not mid:
            raise ValueError("请先指定 myshixun_identifier")
        return self._get(f"/myshixuns/{mid}.json?zzud={self.zzud}")

    def get_task_detail(
        self, game_identifier: str | None = None, homework_common_id: int | None = None
    ) -> TaskDetail:
        gid = game_identifier or self.game_identifier
        hw_id = homework_common_id or self.homework_common_id
        if not gid:
            raise ValueError("请先指定 game_identifier")
        if not hw_id:
            raise ValueError("请先指定 homework_common_id")
        data = self._get(f"/tasks/{gid}.json?homework_common_id={hw_id}&zzud={self.zzud}")
        return TaskDetail.from_dict(data)

    def get_answer_code(
        self,
        code_path: str | None = None,
        game_identifier: str | None = None,
        homework_common_id: int | None = None,
    ) -> str:
        gid = game_identifier or self.game_identifier
        hw_id = homework_common_id or self.homework_common_id
        path = code_path
        if not gid:
            raise ValueError("请先指定 game_identifier")
        if not path:
            raise ValueError("请提供 code_path")
        if not hw_id:
            raise ValueError("请先指定 homework_common_id")

        path = path.rstrip("；;")
        data = self._get(
            f"/tasks/{gid}/rep_content.json"
            f"?path={path}&homework_common_id={hw_id}&exercise_id=&zzud={self.zzud}"
        )
        content_data = data.get("content", {})
        content = content_data.get("content", "") if isinstance(content_data, dict) else ""
        return base64.b64decode(content).decode("utf-8") if content else ""

    def save_code(
        self,
        code: str,
        *,
        code_path: str | None = None,
        game_id: int | None = None,
        challenge_id: int | None = None,
        user_id: int | None = None,
        homework_common_id: int | None = None,
    ) -> JsonObject:
        path = code_path
        gid = game_id
        cid = challenge_id
        uid = user_id
        hw_id = homework_common_id or self.homework_common_id
        mid = self.myshixun_identifier

        if not path or gid is None or cid is None or uid is None or hw_id is None or not mid:
            raise ValueError("缺少必要参数，请先调用 select_homework 加载上下文")

        path = path.rstrip("；;")
        body: JsonObject = {
            "path": path,
            "evaluate": 1,
            "content": code,
            "game_id": gid,
            "tab_type": 1,
            "homework_common_id": hw_id,
            "extras": {
                "challenge_id": cid,
                "homework_common_id": hw_id,
                "currentUserId": uid,
                "exercise_id": "",
                "question_id": "",
                "subject_id": "",
                "competition_entry_id": "",
            },
        }
        return self._post(f"/myshixuns/{mid}/update_file.json?zzud={self.zzud}", body)

    def game_build(
        self,
        sec_key: str,
        commit_id: str,
        *,
        shixun_environment_id: int | None = None,
        challenge_id: int | None = None,
        user_id: int | None = None,
        homework_common_id: int | None = None,
        game_identifier: str | None = None,
    ) -> JsonObject:
        gid = game_identifier or self.game_identifier
        sid = shixun_environment_id
        cid = challenge_id
        uid = user_id
        hw_id = homework_common_id or self.homework_common_id

        if not gid or sid is None or cid is None or uid is None or hw_id is None:
            raise ValueError("缺少必要参数，请先调用 select_homework 加载上下文")

        body: JsonObject = {
            "sec_key": sec_key,
            "resubmit": "",
            "first": 1,
            "content_modified": 0,
            "shixun_environment_id": sid,
            "tab_type": 1,
            "extras": {
                "challenge_id": cid,
                "commitID": commit_id,
                "homework_common_id": hw_id,
                "currentUserId": uid,
                "exercise_id": "",
                "question_id": "",
                "subject_id": "",
                "competition_entry_id": "",
            },
        }
        return self._post(f"/tasks/{gid}/game_build.json?zzud={self.zzud}", body)

    def select_course(self, name_or_id: str | int) -> Course:
        courses = self.get_courses()
        for course in courses:
            if isinstance(name_or_id, int) and course.id == name_or_id:
                self.course_identifier = course.identifier
                return course
            if isinstance(name_or_id, str) and (
                name_or_id in course.name or name_or_id == course.identifier
            ):
                self.course_identifier = course.identifier
                return course
        raise ValueError(f"未找到匹配的课堂: {name_or_id}")

    def select_homework(
        self, identifier: int | str, *, course_identifier: str | None = None
    ) -> HomeworkCommon:
        if course_identifier is not None:
            self.course_identifier = course_identifier
        homeworks = self.get_homeworks()
        target = None
        if isinstance(identifier, int):
            for homework in homeworks:
                if homework.homework_id == identifier:
                    target = homework
                    break
        else:
            for homework in homeworks:
                if identifier in homework.name:
                    target = homework
                    break

        if not target:
            raise ValueError(f"未找到匹配的实验: {identifier}")

        self.homework_common_id = target.homework_id
        self.shixun_identifier = target.shixun_identifier
        self.myshixun_identifier = target.myshixun_identifier

        if target.myshixun_identifier:
            myshixun_data = self.get_myshixun(target.myshixun_identifier)
            self.game_identifier = myshixun_data.get("game_identifier", "")

        return target

    def get_current_context(self) -> TaskDetail:
        if not self.game_identifier and self.myshixun_identifier:
            data = self.get_myshixun(self.myshixun_identifier)
            self.game_identifier = data.get("game_identifier", "")

        if not self.game_identifier:
            raise ValueError(
                "无法获取 game_identifier，该实验可能尚未开始。请先在 Web 页面打开该实验。"
            )

        return self.get_task_detail()

    def submit(self, code: str, *, wait: bool = True, poll_interval: float = 2.0) -> JsonObject:
        task = self.get_current_context()

        save_resp = self.save_code(
            code,
            code_path=task.challenge.clean_path,
            game_id=task.game.id,
            challenge_id=task.challenge.id,
            user_id=task.user.user_id,
            homework_common_id=task.homework_common_id,
        )

        content_data = save_resp.get("content", {})
        commit_id = content_data.get("commitID", "") if isinstance(content_data, dict) else ""
        sec_key = save_resp.get("sec_key", "")

        if not commit_id:
            raise EduCoderAPIError("保存代码失败: 未获取到 commitID")

        env_id = (
            task.shixun_environments[0].shixun_environment_id if task.shixun_environments else 0
        )
        self.game_build(
            sec_key,
            commit_id,
            shixun_environment_id=env_id,
            challenge_id=task.challenge.id,
            user_id=task.user.user_id,
            homework_common_id=task.homework_common_id,
        )

        if not wait:
            return {"task_detail": task, "passed": None, "test_sets": []}

        return self._poll_result(poll_interval)

    def _poll_result(self, interval: float = 2.0, timeout: int = 30) -> JsonObject:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(interval)
            result = self.get_task_detail()
            status = result.game.status
            if status == 2:
                return {
                    "task_detail": result,
                    "passed": True,
                    "test_sets": result.test_sets,
                }
            if status == 3:
                return {
                    "task_detail": result,
                    "passed": False,
                    "test_sets": result.test_sets,
                }
        raise EvaluationTimeoutError(f"评测未在 {timeout}s 内完成")

    def submit_all_levels(self, code: str) -> list[JsonObject]:
        results = []
        self.get_current_context()

        while True:
            result = self.submit(code)
            results.append(result)

            if not result["passed"]:
                break

            detail = result["task_detail"]
            if not detail.next_game:
                break
            self.game_identifier = detail.next_game

        return results
