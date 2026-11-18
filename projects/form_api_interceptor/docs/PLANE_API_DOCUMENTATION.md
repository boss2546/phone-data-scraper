# 📘 Plane API Integration & Reference Manual (ฉบับสมบูรณ์)
> **เป้าหมาย:** เอกสารอ้างอิงและคู่มือการเชื่อมต่อ API ของระบบบริหารจัดการงาน **Plane (Community Edition)** สำหรับโปรเจกต์ `Joint Digital Service Platform (JDSP)`  
> **Host:** `https://devspace.mergesoft.cloud`  
> **API Version:** v1 (`/api/v1/`)  
> **อัปเดตล่าสุด:** พฤศจิกายน 2026 (โดย น้องมายมิ้น / Maymint 💖)

---

## 📑 สารบัญ (Table of Contents)
1. [ภาพรวมและระบบยืนยันตัวตน (Authentication & Overview)](#1-ภาพรวมและระบบยืนยันตัวตน-authentication--overview)
2. [ข้อมูลคงที่ประจำโปรเจกต์ JDSP (Constants & UUIDs)](#2-ข้อมูลคงที่ประจำโปรเจกต์-jdsp-constants--uuids)
   - [Workspace & Project IDs](#21-workspace--project-ids)
   - [สถานะงานทั้งหมด (Workflow States)](#22-สถานะงานทั้งหมด-workflow-states)
   - [ป้ายกำกับ (Issue Labels)](#23-ป้ายกำกับ-issue-labels)
   - [ระดับความสำคัญ (Priority Levels)](#24-ระดับความสำคัญ-priority-levels)
3. [รายการ Endpoints อ้างอิงแบบละเอียด (API Reference)](#3-รายการ-endpoints-อ้างอิงแบบละเอียด-api-reference)
   - [3.1 ตรวจสอบผู้ใช้งาน (User Profile)](#31-ตรวจสอบผู้ใช้งาน-user-profile)
   - [3.2 ข้อมูล Workspace & Project](#32-ข้อมูล-workspace--project)
   - [3.3 สถานะงานและป้ายกำกับ (States & Labels)](#33-สถานะงานและป้ายกำกับ-states--labels)
   - [3.4 รายชื่อสมาชิกในโปรเจกต์ (Members)](#34-รายชื่อสมาชิกในโปรเจกต์-members)
   - [3.5 การจัดการงาน (Issues CRUD)](#35-การจัดการงาน-issues-crud)
4. [โครงสร้าง JSON และ Schema (Request & Response Payloads)](#4-โครงสร้าง-json-และ-schema-request--response-payloads)
5. [ตัวอย่างโค้ดพร้อมใช้งาน (Code Implementations)](#5-ตัวอย่างโค้ดพร้อมใช้งาน-code-implementations)
   - [5.1 Python Client Class (Production-Ready)](#51-python-client-class-production-ready)
   - [5.2 คำสั่ง cURL สำหรับทดสอบใน Terminal](#52-คำสั่ง-curl-สำหรับทดสอบใน-terminal)
   - [5.3 Node.js / TypeScript Example](#53-nodejs--typescript-example)
6. [แนวทางปฏิบัติและข้อควรระวัง (Best Practices & Rate Limits)](#6-แนวทางปฏิบัติและข้อควรระวัง-best-practices--rate-limits)

---

## 1. ภาพรวมและระบบยืนยันตัวตน (Authentication & Overview)

ระบบ Plane แบ่งการเชื่อมต่อ API ออกเป็น 2 โหมด:
1. **Web Session Mode (`/api/`):** ใช้สำหรับหน้าเว็บเบราว์เซอร์ ต้องใช้ Cookie (`session-id`, `csrftoken`) ซึ่งมีอายุสั้นและหมดอายุได้
2. **API Token Mode (`/api/v1/`):** ใช้งานผ่าน Personal Access Token โดยตรง **ไม่หมดอายุ (Never Expires)** และไม่ต้องใช้ Cookie

### 🔑 วิธีการ Authentication ผ่าน Header
ทุก Request ที่ยิงเข้าสู่ `/api/v1/` จะต้องแนบ Header ต่อไปนี้:

```http
X-API-Key: plane_api_c4a70606fce34f789bf7ba09c253be2a
Content-Type: application/json
```

> ⚠️ **ข้อควรระวัง:** Endpoint ต้องขึ้นต้นด้วย `/api/v1/` เท่านั้น หากส่งไปยัง `/api/` ธรรมดาระบบจะไม่ยอมรับ `X-API-Key` และจะตอบกลับเป็น `401 Authentication credentials were not provided.`

---

## 2. ข้อมูลคงที่ประจำโปรเจกต์ JDSP (Constants & UUIDs)

### 2.1 Workspace & Project IDs
* **Base URL:** `https://devspace.mergesoft.cloud`
* **Workspace Slug:** `aiis`
* **Workspace ID:** `0ebe33a1-6741-4788-b899-ced8a06a764c`
* **Project Name:** `Joint Digital Service Platform`
* **Project Identifier (Prefix):** `JDSP`
* **Project ID:** `8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe`

---

### 2.2 สถานะงานทั้งหมด (Workflow States)
รายการ UUID ของแต่ละสถานะในโปรเจกต์ JDSP ที่ดึงมาจากระบบจริง:

| ชื่อสถานะ (State Name) | กลุ่ม (Group) | State UUID | คำอธิบาย |
| :--- | :--- | :--- | :--- |
| **Backlog** | `backlog` | `cb92c938-8c41-4d83-be57-e40cbd747fec` | งานที่เพิ่งสร้าง รอจัดคิว (Default) |
| **PM Review** | `backlog` | `18c704ce-24eb-4030-b528-3193ecbd3e46` | รอ PM ตรวจสอบ Requirement |
| **Ready for Development** | `unstarted` | `a0ee8fec-8941-4a58-b436-6f17d1ccb362` | พร้อมให้ Dev เริ่มพัฒนา |
| **Dev Todo** | `unstarted` | `5e7f9a4d-7c11-4595-a169-415ad98105ad` | รายการที่ Dev ต้องทำ |
| **In Development** | `started` | `d80de3de-2a56-4233-943a-d0629823d56a` | กำลังพัฒนาโปรแกรม |
| **Dev In Progress** | `started` | `b6362ac5-4256-47f8-9996-0cf0f5102e23` | Dev กำลังเขียนโค้ดแก้ไข |
| **Code Review** | `started` | `5479533e-556f-49f9-bc3c-ed7581caa47c` | ตรวจสอบ Source Code |
| **Dev Done** | `completed` | `c7e4ea87-988e-4ad6-9582-a80951f7d547` | Dev พัฒนาเสร็จสิ้น |
| **Ready for SIT** | `started` | `5dda9bd5-fad0-47c7-ad97-66fa47c18e75` | ส่งเข้าทดสอบ System Integration |
| **SIT Testing** | `started` | `1c6bc5ba-8ea0-4042-8836-3d61b110b6cb` | กำลังรันรอบทดสอบ SIT |
| **Ready for UAT** | `started` | `e11c72ae-7222-4000-8f80-ac489a918ee4` | ส่งมอบให้ผู้ใช้ตรวจรับงาน |
| **UAT Testing** | `started` | `f649a59b-db8f-4cf5-a79a-f87d3e6960a5` | ลูกค้า/ผู้ใช้กำลังทดสอบ UAT |
| **Ready for Production** | `started` | `efc696b1-0c15-4f3f-882c-3254241be6f5` | พร้อมขึ้นระบบจริง |
| **Done** | `completed` | `b0b74c6d-8ac7-4b0a-8b1b-28683e91c0b3` | งานเสร็จสมบูรณ์ปิดจ๊อบ |
| **Cancelled** | `cancelled` | `6770052a-9439-4c18-acda-842c3a19607b` | ยกเลิกรายการ |

---

### 2.3 ป้ายกำกับ (Issue Labels)
UUID สำหรับระบุ Label ให้กับแต่ละ Issue:

| ชื่อ Label | Label UUID | การนำไปใช้ |
| :--- | :--- | :--- |
| **Bug** | `e1e0b6f1-371d-4b89-ab5d-f75864a88d37` | ข้อผิดพลาดของระบบ |
| **Requirement** | `ef8ce9d0-7900-4e10-b306-ab560d4c58c9` | ความต้องการใหม่ (CR / Feature) |
| **Frontend** | `1db48be4-d864-444c-b4ca-8775aba10a84` | งานส่วนหน้าบ้าน (UI / Web) |
| **Backend** | `d101c238-85f3-433f-b1c7-bbdc109e146f` | งานส่วนหลังบ้าน (API / Database) |
| **DevOps** | `ef6220fb-33a2-49a5-a0cf-7980b6a2bcf3` | งานระบบ Server / Pipeline |
| **QA** | `a60fa5d7-aa72-46ba-936c-c8497de60937` | งานฝ่ายทดสอบคุณภาพ |
| **BA** | `af2eb93f-4cd6-4552-adf8-b3c1afb5b123` | งานฝ่ายวิเคราะห์ระบบ |
| **Blocked** | `d026f78c-854f-44de-a611-0944cec9c45e` | งานที่ติดบล็อกกิ้ง |

---

### 2.4 ระดับความสำคัญ (Priority Levels)
ค่าสตริงที่รองรับในฟิลด์ `priority`:
* `urgent` — ด่วนที่สุด (วิกฤติต้องแก้ทันที)
* `high` — สูง (ความสำคัญสูงสุดของงานทั่วไปตามนโยบายทีม)
* `medium` — ปานกลาง
* `low` — ต่ำ
* `none` — ไม่ระบุ

---

## 3. รายการ Endpoints อ้างอิงแบบละเอียด (API Reference)

### 3.1 ตรวจสอบผู้ใช้งาน (User Profile)
ใช้ตรวจสอบความถูกต้องของ API Token และดูข้อมูลโปรไฟล์เจ้าของ Token

* **Method:** `GET`
* **URL:** `/api/v1/users/me/`
* **Headers:** `X-API-Key: <TOKEN>`
* **Status Response:** `200 OK`
* **Response ตัวอย่าง:**
  ```json
  {
    "id": "c22765bc-6002-4ec1-9f89-3411779df217",
    "first_name": "Boss",
    "last_name": "",
    "email": "ratchanon.r@aiis-asia.com",
    "avatar": "",
    "avatar_url": null,
    "display_name": "ratchanon.r"
  }
  ```

---

### 3.2 ข้อมูล Workspace & Project

#### ดึงรายการโปรเจกต์ทั้งหมดใน Workspace
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/`
* **URL ตัวอย่าง:** `/api/v1/workspaces/aiis/projects/`
* **Status Response:** `200 OK`

---

### 3.3 สถานะงานและป้ายกำกับ (States & Labels)

#### ดึงรายการสถานะงาน (States)
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/states/`
* **URL ตัวอย่าง:** `/api/v1/workspaces/aiis/projects/8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe/states/`

#### ดึงรายการป้ายกำกับ (Labels)
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/labels/`

---

### 3.4 รายชื่อสมาชิกในโปรเจกต์ (Members)
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/members/`
* **Response โครงสร้าง:** รายการ Array ของข้อมูลสมาชิกแต่ละคน เพื่อนำ `id` ไปใช้กำหนดเป็นผู้รับผิดชอบ (`assignees`)

---

### 3.5 การจัดการงาน (Issues CRUD)

#### 1. ดึงรายการงานทั้งหมด (List Issues)
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/`
* **Query Parameters ที่รองรับ:**
  * `per_page`: จำนวนรายการต่อหน้า (เช่น `20`, `50`, `100`)
  * `cursor`: ตำแหน่ง Cursor สำหรับแบ่งหน้า (Pagination)
  * `state`: กรองเฉพาะ State ID ที่ต้องการ
  * `priority`: กรองตามระดับความสำคัญ (`high`, `medium`, `low`)
* **Status Response:** `200 OK`

#### 2. ดึงรายละเอียดของงานรายตัว (Get Single Issue)
* **Method:** `GET`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/{issue_id}/`
* **Status Response:** `200 OK`

#### 3. สร้างงานใหม่ (Create Issue)
* **Method:** `POST`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/`
* **Headers:**
  ```http
  X-API-Key: plane_api_c4a70606fce34f789bf7ba09c253be2a
  Content-Type: application/json
  ```
* **Status Response:** `201 Created`

#### 4. แก้ไขข้อมูลงาน (Update Issue)
* **Method:** `PATCH`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/{issue_id}/`
* **Status Response:** `200 OK`

#### 5. ลบงาน (Delete Issue)
* **Method:** `DELETE`
* **URL:** `/api/v1/workspaces/{workspace_slug}/projects/{project_id}/issues/{issue_id}/`
* **Status Response:** `204 No Content`

---

## 4. โครงสร้าง JSON และ Schema (Request & Response Payloads)

### 4.1 Schema สร้าง Issue (`POST /issues/`)

```json
{
  "name": "หัวข้อปัญหาหรือชื่องาน (จำเป็น)",
  "description_html": "<p>รายละเอียดของงาน สามารถใส่แท็ก HTML เช่น &lt;p&gt;, &lt;ul&gt;, &lt;strong&gt; ได้</p>",
  "priority": "high",
  "state": "cb92c938-8c41-4d83-be57-e40cbd747fec",
  "assignees": [
    "c22765bc-6002-4ec1-9f89-3411779df217"
  ],
  "labels": [
    "e1e0b6f1-371d-4b89-ab5d-f75864a88d37"
  ],
  "start_date": "2026-11-18",
  "target_date": "2026-11-25"
}
```

#### ตารางอธิบายฟิลด์ข้อมูล (Data Dictionary):
| ฟิลด์ (Field) | ชนิด (Type) | บังคับ (Required) | คำอธิบาย |
| :--- | :--- | :--- | :--- |
| `name` | string | ✅ บังคับ | หัวข้อของงาน (Title) |
| `description_html` | string (HTML) | ❌ ไม่บังคับ | รายละเอียดงานแบบจัดรูปแบบ HTML |
| `priority` | string (enum) | ❌ ไม่บังคับ | `urgent`, `high`, `medium`, `low`, `none` |
| `state` | string (UUID) | ❌ ไม่บังคับ | UUID ของสถานะ (เช่น Backlog) |
| `assignees` | array[UUID] | ❌ ไม่บังคับ | รายชื่อ User UUID ที่รับผิดชอบ |
| `labels` | array[UUID] | ❌ ไม่บังคับ | รายชื่อ Label UUID ที่ติดให้งานนี้ |
| `target_date` | string (YYYY-MM-DD) | ❌ ไม่บังคับ | กำหนดส่งงาน (Due date) |

---

### 4.2 Schema ผลลัพธ์เมื่อสร้างสำเร็จ (`201 Created`)

```json
{
  "id": "e89d81d2-a720-40ce-856f-870d0615951d",
  "sequence_id": 81,
  "name": "หัวข้องานตัวอย่าง",
  "description_html": "<p>รายละเอียดงาน</p>",
  "priority": "high",
  "state": "cb92c938-8c41-4d83-be57-e40cbd747fec",
  "project": "8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe",
  "workspace": "0ebe33a1-6741-4788-b899-ced8a06a764c",
  "created_at": "2026-11-18T01:10:00.000000Z",
  "updated_at": "2026-11-18T01:10:00.000000Z",
  "created_by": "c22765bc-6002-4ec1-9f89-3411779df217",
  "assignees": [],
  "labels": []
}
```

> 💡 **หมายเหตุสำคัญ:** รหัสงานจริง (เช่น `JDSP-81`) จะประกอบขึ้นจาก **Identifier ของโปรเจกต์ + `sequence_id`** ที่ระบบ Generate ให้โดยอัตโนมัติ

---

## 5. ตัวอย่างโค้ดพร้อมใช้งาน (Code Implementations)

### 5.1 Python Client Class (Production-Ready)
คลาส Python ที่เขียนครอบ API ไว้อย่างสมบูรณ์ พร้อมระบบ Retry และรองรับทั้งการอ่านและสร้าง Issue:

```python
import time
import requests
from typing import Dict, Any, List, Optional

class PlaneClient:
    """
    Client สำหรับเชื่อมต่อ Plane API v1 อย่างเป็นทางการ
    """
    def __init__(self, base_url: str, api_key: str, workspace_slug: str, project_id: str):
        self.base_url = base_url.rstrip("/")
        self.workspace_slug = workspace_slug
        self.project_id = project_id
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_profile(self) -> Dict[str, Any]:
        """ตรวจสอบความถูกต้องของ API Key และดึงข้อมูลโปรไฟล์"""
        url = f"{self.base_url}/api/v1/users/me/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_states(self) -> List[Dict[str, Any]]:
        """ดึงรายการสถานะงานทั้งหมดในโปรเจกต์"""
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/states/"
        res = self.session.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", data if isinstance(data, list) else [])

    def create_issue(
        self,
        name: str,
        description_html: str = "",
        priority: str = "high",
        state_id: Optional[str] = "cb92c938-8c41-4d83-be57-e40cbd747fec",
        label_ids: Optional[List[str]] = None,
        assignee_ids: Optional[List[str]] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        สร้าง Issue ใหม่พร้อมระบบป้องกันความผิดพลาด (Retry Mechanism)
        """
        url = f"{self.base_url}/api/v1/workspaces/{self.workspace_slug}/projects/{self.project_id}/issues/"
        payload = {
            "name": name,
            "description_html": description_html,
            "priority": priority,
            "state": state_id,
            "labels": label_ids or [],
            "assignees": assignee_ids or []
        }

        for attempt in range(1, retries + 1):
            try:
                res = self.session.post(url, json=payload, timeout=15)
                if res.status_code in [200, 201]:
                    return res.json()
                elif res.status_code == 429: # Rate limit
                    time.sleep(attempt * 2)
                    continue
                else:
                    res.raise_for_status()
            except requests.RequestException as e:
                if attempt == retries:
                    raise e
                time.sleep(1)

        raise RuntimeError("Failed to create issue after retries")


# --- ตัวอย่างการใช้งานจริง ---
if __name__ == "__main__":
    client = PlaneClient(
        base_url="https://devspace.mergesoft.cloud",
        api_key="plane_api_c4a70606fce34f789bf7ba09c253be2a",
        workspace_slug="aiis",
        project_id="8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe"
    )

    # 1. เช็คโปรไฟล์
    me = client.get_profile()
    print(f"เชื่อมต่อสำเร็จในชื่อ: {me['first_name']} ({me['email']})")

    # 2. ตัวอย่างการสร้างงาน
    # new_issue = client.create_issue(
    #     name="ทดสอบสร้างผ่าน API Client",
    #     description_html="<p>รายละเอียดงานตัวอย่าง</p>",
    #     priority="high"
    # )
    # print(f"สร้างสำเร็จ! Issue Sequence ID: {new_issue['sequence_id']}")
```

---

### 5.2 คำสั่ง cURL สำหรับทดสอบใน Terminal

#### ทดสอบดูโปรไฟล์ (Read-Only):
```bash
curl -X GET "https://devspace.mergesoft.cloud/api/v1/users/me/" \
  -H "X-API-Key: plane_api_c4a70606fce34f789bf7ba09c253be2a" \
  -H "Content-Type: application/json"
```

#### ทดสอบสร้าง Issue ใหม่:
```bash
curl -X POST "https://devspace.mergesoft.cloud/api/v1/workspaces/aiis/projects/8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe/issues/" \
  -H "X-API-Key: plane_api_c4a70606fce34f789bf7ba09c253be2a" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ทดสอบยิงผ่าน cURL",
    "description_html": "<p>รายละเอียดงานทดสอบ</p>",
    "priority": "high",
    "state": "cb92c938-8c41-4d83-be57-e40cbd747fec"
  }'
```

---

### 5.3 Node.js / TypeScript Example
```javascript
const API_KEY = "plane_api_c4a70606fce34f789bf7ba09c253be2a";
const BASE_URL = "https://devspace.mergesoft.cloud/api/v1";
const WORKSPACE = "aiis";
const PROJECT_ID = "8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe";

async function createIssue(title, descriptionHtml, priority = "high") {
  const url = `${BASE_URL}/workspaces/${WORKSPACE}/projects/${PROJECT_ID}/issues/`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: title,
      description_html: descriptionHtml,
      priority: priority,
      state: "cb92c938-8c41-4d83-be57-e40cbd747fec" // Backlog state
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  console.log(`สร้างสำเร็จ: JDSP-${data.sequence_id}`);
  return data;
}
```

---

## 6. แนวทางปฏิบัติและข้อควรระวัง (Best Practices & Rate Limits)

1. **การหน่วงเวลาเมื่อยิงแบบ Batch (Rate Limit Protection):**
   - ในการสร้างงานจำนวนมาก (เช่น นำเข้าจาก CSV 10–50 รายการ) **ต้องหน่วงเวลา (Delay) อย่างน้อย 1.5 – 2.0 วินาทีต่อ 1 Request**
   - เพื่อป้องกันไม่ให้ Proxy/Server ตัดการเชื่อมต่อ หรือคืนค่า `429 Too Many Requests`
2. **การล้างรหัสเดิมออกจากหัวข้อ (Title Normalization):**
   - ระบบ Plane จะมี Auto-Increment `sequence_id` (เช่น `JDSP-66`, `JDSP-67`) ให้อยู่แล้ว
   - **ห้าม** นำรหัสเก่า เช่น `BUG-001` หรือ `CR-002` ไปใส่ปะปนในชื่อหัวข้อ เพื่อไม่ให้เลขซ้ำซ้อน
3. **การรักษาความปลอดภัยของ Token:**
   - ห้าม Commit API Token ขึ้น Public Repository
   - ควรกำหนดในไฟล์ `.env` หรือ Environment Variables เช่น `PLANE_API_KEY=plane_api_...`
4. **การแปลงข้อความเป็น HTML ใน `description_html`:**
   - ควรห่อเนื้อหาด้วยแท็ก `<p>...</p>`
   - กรณีมีหลายบรรทัด ให้ใช้ `<br/>` หรือแยกย่อหน้า เพื่อให้แสดงผลบนการ์ดใน Plane อย่างสวยงาม
