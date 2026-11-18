"""
Plane API Client (v1) - Official Python Module for Form & API Interceptor
Target: https://devspace.mergesoft.cloud (Plane Community Edition v1.4.3)
"""

import time
import requests
from typing import Dict, Any, List, Optional


class PlaneClient:
    """
    Official Plane API v1 Client supporting Personal Access Token (X-API-Key).
    """

    DEFAULT_BASE_URL = "https://devspace.mergesoft.cloud"
    DEFAULT_WORKSPACE = "aiis"
    DEFAULT_PROJECT_ID = "8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe" # Joint Digital Service Platform (JDSP)

    # Common State UUIDs
    STATE_BACKLOG = "cb92c938-8c41-4d83-be57-e40cbd747fec"
    STATE_PM_REVIEW = "18c704ce-24eb-4030-b528-3193ecbd3e46"
    STATE_READY_FOR_DEV = "a0ee8fec-8941-4a58-b436-6f17d1ccb362"
    STATE_DEV_TODO = "5e7f9a4d-7c11-4595-a169-415ad98105ad"
    STATE_DEV_IN_PROGRESS = "b6362ac5-4256-47f8-9996-0cf0f5102e23"
    STATE_CODE_REVIEW = "5479533e-556f-49f9-bc3c-ed7581caa47c"
    STATE_DEV_DONE = "c7e4ea87-988e-4ad6-9582-a80951f7d547"
    STATE_READY_FOR_SIT = "5dda9bd5-fad0-47c7-ad97-66fa47c18e75"
    STATE_SIT_TESTING = "1c6bc5ba-8ea0-4042-8836-3d61b110b6cb"
    STATE_READY_FOR_UAT = "e11c72ae-7222-4000-8f80-ac489a918ee4"
    STATE_UAT_TESTING = "f649a59b-db8f-4cf5-a79a-f87d3e6960a5"
    STATE_READY_FOR_PROD = "efc696b1-0c15-4f3f-882c-3254241be6f5"
    STATE_DONE = "b0b74c6d-8ac7-4b0a-8b1b-28683e91c0b3"
    STATE_CANCELLED = "6770052a-9439-4c18-acda-842c3a19607b"

    def __init__(
        self,
        api_key: str = "plane_api_c4a70606fce34f789bf7ba09c253be2a",
        base_url: str = DEFAULT_BASE_URL,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID
    ):
        self.base_url = base_url.rstrip("/")
        self.workspace_slug = workspace_slug
        self.project_id = project_id
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_current_user(self) -> Dict[str, Any]:
        """ดึงข้อมูลโปรไฟล์ของผู้ใช้งานปัจจุบัน"""
        url = f"{self.base_url}/api/v1/users/me/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_projects(self) -> List[Dict[str, Any]]:
        """ดึงรายการโปรเจกต์ทั้งหมดใน Workspace"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", data if isinstance(data, list) else [])

    def get_states(self) -> List[Dict[str, Any]]:
        """ดึงรายการสถานะงาน (States) ทั้งหมดในโปรเจกต์"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/states/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", data if isinstance(data, list) else [])

    def get_labels(self) -> List[Dict[str, Any]]:
        """ดึงรายการป้ายกำกับ (Labels) ทั้งหมดในโปรเจกต์"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/labels/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", data if isinstance(data, list) else [])

    def get_members(self) -> List[Dict[str, Any]]:
        """ดึงรายชื่อสมาชิกในโปรเจกต์"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/members/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        return res.json() if isinstance(res.json(), list) else res.json().get("results", [])

    def list_issues(self, per_page: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        """ดึงรายการงาน (Issues) ในโปรเจกต์"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/issues/"
        params = {"per_page": per_page}
        if cursor:
            params["cursor"] = cursor
        res = self.session.get(url, params=params, timeout=15)
        res.raise_for_status()
        return res.json()

    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """ดึงข้อมูล Issue รายการเดียวตาม UUID"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/issues/{issue_id}/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def create_issue(
        self,
        name: str,
        description_html: str = "",
        priority: str = "high",
        state_id: Optional[str] = STATE_BACKLOG,
        label_ids: Optional[List[str]] = None,
        assignee_ids: Optional[List[str]] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        สร้าง Issue ใหม่ลงในโปรเจกต์ พร้อมระบบหน่วงเวลาและ Retry
        """
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/issues/"
        payload = {
            "name": name,
            "description_html": description_html,
            "priority": priority,
            "state": state_id or self.STATE_BACKLOG,
            "labels": label_ids or [],
            "assignees": assignee_ids or []
        }

        for attempt in range(1, retries + 1):
            try:
                res = self.session.post(url, json=payload, timeout=15)
                if res.status_code in (200, 201):
                    return res.json()
                elif res.status_code == 429:
                    time.sleep(attempt * 2)
                    continue
                else:
                    res.raise_for_status()
            except requests.RequestException as e:
                if attempt == retries:
                    raise e
                time.sleep(1.5)

        raise RuntimeError("Failed to create issue after retries")


if __name__ == "__main__":
    client = PlaneClient()
    user = client.get_current_user()
    print(f"✅ PlaneClient Connected: {user.get('display_name')} ({user.get('email')})")
