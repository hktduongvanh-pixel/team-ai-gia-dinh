# Multi-Agent AI Team - Gia đình lớn (Phone Edition)
# Chạy 100% trên điện thoại qua Replit Mobile App + OpenRouter free models
# Inspired by @ezvibecode EverMind Team AI demo

import streamlit as st
import requests
import json
import os
from datetime import datetime

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Team AI Gia Đình",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OpenRouter free models (Nov 2026)
FREE_MODELS = {
    "Nemotron 3 Ultra (mạnh nhất)": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "Gemma 4 31B": "google/gemma-4-31b-it:free",
    "Gemma 4 26B A4B": "google/gemma-4-26b-a4b-it:free",
    "Nemotron 3.5 Super VL (vision)": "nvidia/nemotron-3.5-super-vl:free",
    "North Mini Code (code)": "cohere/north-mini-code:free",
    "Nemotron 3.5 Lightning": "nvidia/nemotron-3.5-lightning:free",
    "ERNIE 5.5 Flash": "baidu/ernie-5.5-flash-preview:free",
    "Free Router (random free)": "openrouter/free",
}

# ==================== ROLE PROMPTS ====================
ROLE_PROMPTS = {
    "planner": """Bạn là Planner / Điều phối trưởng (Project Manager) của Team AI Gia đình.
Nhiệm vụ: Phân tích yêu cầu người dùng, chia thành các task cụ thể, giao việc rõ ràng cho từng thành viên.
Luôn ưu tiên ràng buộc (thời gian, nguồn lực, mục tiêu).
Output dạng markdown rõ ràng:
- Các task chính
- Giao cho vai nào (Coder / Writer / Researcher / Designer / Analyst...)
- Thứ tự / song song
- Ghi chú quan trọng""",

    "coder": """Bạn là Coder Agent.
Chuyên viết code, kiến trúc, giải thích thuật toán.
Viết code sạch, có comment, ưu tiên Python hoặc HTML/JS đơn giản nếu phù hợp.
Nếu là web app, ưu tiên Streamlit hoặc single HTML.""",

    "writer": """Bạn là Writer Agent.
Viết nội dung rõ ràng, mạch lạc, đúng yêu cầu.
Ưu tiên ngắn gọn, có cấu trúc, dễ đọc.""",

    "researcher": """Bạn là Research Agent.
Tìm và tổng hợp thông tin có logic. Nêu rõ nguồn nếu có hoặc phần ước tính.
Không bịa đặt.""",

    "designer": """Bạn là Designer / Image Agent.
Đề xuất ý tưởng giao diện, mô tả hình ảnh, layout, màu sắc, UX.
Có thể viết prompt cho AI image nếu cần.""",

    "analyst": """Bạn là Analyst Agent.
Phân tích số liệu, logic, so sánh, đưa ra insight và khuyến nghị.""",

    "reviewer": """Bạn là Reviewer / Kiểm duyệt nghiêm ngặt.
Nhiệm vụ bắt buộc:
1. Kiểm tra toàn bộ kết quả có tuân thủ yêu cầu và ràng buộc không.
2. Nếu vượt giới hạn (thời gian, nguồn lực) → chỉ rõ và đề xuất cắt / dời.
3. Kiểm tra logic, thiếu sót, mâu thuẫn.
4. Tổng hợp thành bản cuối cùng mạch lạc, sẵn sàng dùng.
5. Nêu rõ phần nào cần sửa nếu có.
Luôn so với yêu cầu gốc + quy tắc team."""
}

# ==================== OPENROUTER CLIENT ====================
def call_openrouter(messages, model, api_key, temperature=0.7, max_tokens=2500):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://team-ai-family.streamlit.app",
        "X-Title": "Team AI Gia Dinh"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return content, usage
    except Exception as e:
        return f"Lỗi gọi API: {str(e)}", {}

# ==================== UI ====================
st.title("👨‍👩‍👧‍👦 Team AI Gia Đình Lớn")
st.caption("Multi-Agent Team • Tất cả các AI làm việc cùng nhau • Chạy 100% trên điện thoại")

with st.sidebar:
    st.header("⚙️ Cấu hình")
    # Ưu tiên secrets (Streamlit Cloud / Replit) rồi mới đến input
    default_key = ""
    try:
        default_key = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    except Exception:
        default_key = os.getenv("OPENROUTER_API_KEY", "")
    
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=default_key,
        help="Lấy free key tại openrouter.ai. Trên Streamlit Cloud dùng Secrets."
    )
    model_choice = st.selectbox("Model mặc định cho cả team", list(FREE_MODELS.keys()), index=0)
    selected_model = FREE_MODELS[model_choice]
    
    st.divider()
    st.subheader("Quy tắc team (Rules)")
    default_rules = """- Ưu tiên chất lượng và đúng yêu cầu gốc
- Nếu có giới hạn thời gian / nguồn lực → tuân thủ nghiêm
- Reviewer phải kiểm tra đầy đủ và tổng hợp bản cuối
- Các agent có thể làm song song hoặc tuần tự tùy Planner quyết định"""
    team_rules = st.text_area("Nội quy / ràng buộc", value=default_rules, height=150)
    
    st.info("Giới hạn free: ~50 request/ngày. Một lần chạy team tốn 3-5 request.")

# Team roster
st.subheader("🏢 Thành viên Team AI")
cols = st.columns(4)
members = [
    ("🎯 Planner", "Điều phối / Chia việc"),
    ("💻 Coder", "Viết code / Kiến trúc"),
    ("✍️ Writer", "Nội dung / Văn bản"),
    ("🔍 Researcher", "Nghiên cứu / Tổng hợp"),
    ("🎨 Designer", "Giao diện / Hình ảnh"),
    ("📊 Analyst", "Phân tích / Insight"),
    ("✅ Reviewer", "Kiểm duyệt / Tổng hợp"),
    ("🤖 Tất cả", "Làm việc cùng nhau")
]
for i, (name, desc) in enumerate(members):
    with cols[i % 4]:
        st.info(f"**{name}**\n{desc}")

# Main
tab1, tab2 = st.tabs(["🚀 Chạy Team", "📋 Hướng dẫn"])

with tab1:
    st.subheader("Giao việc cho Team AI Gia đình")
    user_task = st.text_area(
        "Yêu cầu / Mục tiêu (bất kỳ)",
        placeholder="Ví dụ: Lên kế hoạch xây dựng website bán hàng online, viết landing page, thiết kế giao diện, nghiên cứu đối thủ...",
        height=120
    )
    
    col1, col2 = st.columns(2)
    with col1:
        run_btn = st.button("▶️ Chạy Team Agent", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.rerun()

    if run_btn and user_task.strip():
        if not api_key:
            st.error("Vui lòng nhập OpenRouter API Key ở sidebar!")
            st.stop()
        
        logs = []
        progress = st.progress(0)
        status = st.empty()
        
        # Visual workflow
        st.markdown("### 🔄 Luồng làm việc")
        flow_cols = st.columns(3)
        with flow_cols[0]:
            st.success("**01. Giao việc**\nPlanner chia task")
        with flow_cols[1]:
            st.info("**02. Xử lý**\nWorkers thực hiện")
        with flow_cols[2]:
            st.warning("**03. Kết quả**\nReviewer kiểm duyệt")
        
        # Step 1: Planner
        status.info("1️⃣ Planner đang chia việc...")
        planner_msg = [
            {"role": "system", "content": ROLE_PROMPTS["planner"] + "\n\nQuy tắc team:\n" + team_rules},
            {"role": "user", "content": f"Yêu cầu: {user_task}"}
        ]
        plan_result, plan_usage = call_openrouter(planner_msg, selected_model, api_key)
        logs.append(("Planner (Điều phối)", plan_result, plan_usage))
        progress.progress(20)
        
        # Step 2: Workers (Coder + Writer + Researcher as example)
        status.info("2️⃣ Workers đang thực hiện (Coder + Writer + Researcher)...")
        worker_system = ROLE_PROMPTS["coder"] + "\n" + ROLE_PROMPTS["writer"] + "\n" + ROLE_PROMPTS["researcher"]
        worker_msg = [
            {"role": "system", "content": worker_system},
            {"role": "user", "content": f"Kế hoạch từ Planner:\n{plan_result}\n\nThực hiện phần việc phù hợp. Quy tắc:\n{team_rules}\nYêu cầu gốc: {user_task}"}
        ]
        worker_result, worker_usage = call_openrouter(worker_msg, selected_model, api_key)
        logs.append(("Workers (Coder/Writer/Researcher)", worker_result, worker_usage))
        progress.progress(55)
        
        # Optional extra worker
        status.info("2️⃣b Designer đang đóng góp ý tưởng...")
        designer_msg = [
            {"role": "system", "content": ROLE_PROMPTS["designer"]},
            {"role": "user", "content": f"Dựa trên kế hoạch và yêu cầu:\n{user_task}\nKế hoạch:\n{plan_result}\nĐưa ý tưởng thiết kế / giao diện phù hợp."}
        ]
        designer_result, designer_usage = call_openrouter(designer_msg, selected_model, api_key)
        logs.append(("Designer", designer_result, designer_usage))
        progress.progress(75)
        
        # Step 3: Reviewer
        status.info("3️⃣ Reviewer đang kiểm duyệt và tổng hợp...")
        reviewer_msg = [
            {"role": "system", "content": ROLE_PROMPTS["reviewer"]},
            {"role": "user", "content": f"""Yêu cầu gốc: {user_task}
Quy tắc: {team_rules}

Kế hoạch Planner:
{plan_result}

Kết quả Workers:
{worker_result}

Ý tưởng Designer:
{designer_result}

Hãy kiểm duyệt nghiêm ngặt, đề xuất chỉnh sửa nếu cần, rồi tổng hợp bản cuối cùng hoàn chỉnh."""}
        ]
        review_result, review_usage = call_openrouter(reviewer_msg, selected_model, api_key)
        logs.append(("Reviewer (Kiểm duyệt)", review_result, review_usage))
        progress.progress(100)
        status.success("✅ Team hoàn thành!")
        
        # Display results
        st.divider()
        st.subheader("📊 Kết quả từng bước")
        
        for role, content, usage in logs:
            with st.expander(f"**{role}**", expanded=(role.startswith("Reviewer"))):
                st.markdown(content)
                if usage:
                    st.caption(f"Tokens: in={usage.get('prompt_tokens', '?')} • out={usage.get('completion_tokens', '?')}")
        
        st.subheader("🎯 Bản tổng hợp cuối từ Reviewer")
        st.success(review_result)

with tab2:
    st.markdown("""
### Cách build & chạy 100% trên iPhone

1. **Cài app Replit** từ App Store.
2. Tạo project mới → chọn Python / dùng template Streamlit.
3. Copy toàn bộ code `app.py` này vào file chính.
4. Tạo file `requirements.txt` với nội dung:
   ```
   streamlit
   requests
   ```
5. Vào **Secrets** → thêm `OPENROUTER_API_KEY` = key của bạn (lấy free tại openrouter.ai).
6. Chạy app (Run) → Deploy để có link public.
7. Mở link trên Safari → **Add to Home Screen** → dùng như app PWA full màn hình.

### Models free tốt nhất hiện tại
- `nvidia/nemotron-3-ultra-550b-a55b:free` — mạnh nhất
- `google/gemma-4-31b-it:free`
- `cohere/north-mini-code:free` — tốt cho code

### Giới hạn
Free tier: khoảng 50 request/ngày (tăng lên 1000 sau khi nạp $10 một lần).
Một vòng Team tốn 4 request.

### Mở rộng sau này
Thêm nhiều Worker song song thật sự, lưu history, visual canvas (React Flow), hoặc chuyển sang Flet/Gradio nếu muốn native hơn.
    """)

st.divider()
st.caption(f"Team AI Gia Đình • {datetime.now().strftime('%Y-%m-%d')} • Inspired by @ezvibecode EverMind")
