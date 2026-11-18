import json
import re

def main():
    with open('/tmp/gemini_chat_scrolled.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = [
        "# 📑 ประวัติการสนทนา Gemini: ฝึกงาน บริษัท อธีนา อินเทลลิเจนซ์ ซิสเต็มส์ จำกัด",
        "",
        "> **Session ID:** `c_4d89270bcb1c9137`  ",
        "> **แหล่งข้อมูล:** Google Gemini Web App  ",
        "> **สกัดข้อมูลโดย:** Form & API Interceptor (AI-Ready Prompt Extraction)",
        "",
        "---",
        ""
    ]

    for i, turn in enumerate(data):
        role = turn['role']
        text = turn['text']
        
        # Clean up UI prefixes
        if role == 'User':
            # Remove repeated text if any
            clean_text = text.replace("คุณบอกว่า", "").strip()
            # Often the user text is repeated twice in Gemini DOM
            parts = clean_text.split('\n\n')
            if len(parts) >= 2 and parts[0] == parts[1]:
                clean_text = parts[0]
            lines.append(f"### 👤 คุณ (User) - ข้อความที่ {i//2 + 1}")
            lines.append("")
            lines.append(f"> {clean_text}")
            lines.append("")
        else:
            clean_text = text.replace("Gemini บอกว่า", "").strip()
            lines.append(f"### 🤖 Gemini - คำตอบที่ {i//2 + 1}")
            lines.append("")
            lines.append(clean_text)
            lines.append("")
            lines.append("---")
            lines.append("")

    content = "\n".join(lines)
    filepath = "projects/form_api_interceptor/docs/gemini_chat_backup_c_4d89270bcb1c9137.md"
    with open(filepath, "w", encoding="utf-8") as out:
        out.write(content)
    print(f"Exported successfully to {filepath} ({len(content)} chars)")

if __name__ == "__main__":
    main()
