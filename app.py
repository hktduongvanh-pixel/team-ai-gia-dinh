# Team AI Gia Đình Lớn - Premium Edition
# Chat UI chuyên nghiệp + Upload mọi loại file + Trạng thái agent realtime

import streamlit as st
import requests
import json
import os
from datetime import datetime
import base64

st.set_page_config(
    page_title="Team AI Gia Đình • Premium",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== PREMIUM CSS ====================
st.markdown("""
<style>
    /* Premium Dark Theme */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #e0e0e0;
    }
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1100px;
    }
    
    /* Chat bubbles */
    .stChatMessage {
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 12px;
    }
    .stChatMessage[data-testid="stChatMessage"] {
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    /* Status badges */
    .status-working {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        animation: pulse 1.5s infinite;
    }
    .status-done {
        background: linear-gradient(90deg, #00b894, #00cec9);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    
    /* Premium buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Header */
    h1 {
        background: linear-gradient(90deg, #a29bfe, #fd79a8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# ==================== MODELS & PROMPTS ====================
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

ROLE_PROMPTS = {
    "planner": """Bạn là Planner / Điều phối trưởng của Team AI Gia đình Premium.
Phân tích yêu cầu + file đính kèm (nếu có), chia task rõ ràng cho từng agent.
Output markdown:
- Các task chính
- Giao cho vai nào
- Thứ tự thực hiện
- Ghi chú quan trọng""",

    "coder": """Bạn là Coder Agent Premium.
Viết code sạch, có comment, ưu tiên Python/Streamlit/HTML nếu phù hợp.""",

    "writer": """Bạn là Writer Agent Premium.
Viết nội dung mạch lạc, chuyên nghiệp, đúng yêu cầu.""",

    "researcher": """Bạn là Research Agent Premium.
Tổng hợp thông tin logic, rõ ràng. Không bịa đặt.""",

    "designer": """Bạn là Designer Agent Premium.
Đề xuất ý tưởng giao diện, layout, UX, mô tả hình ảnh.""",

    "analyst": """Bạn là Analyst Agent Premium.
Phân tích, so sánh, đưa insight và khuyến nghị.""",

    "reviewer": """Bạn là Reviewer Premium.
Kiểm tra toàn bộ kết quả, sửa lỗi logic, tổng hợp bản cuối cùng hoàn chỉnh và sẵn sàng dùng."""
}

AGENT_INFO = {
    "planner": ("🎯", "Planner", "Đang điều phối & chia việc"),
    "coder": ("💻", "Coder", "Đang viết code"),
    "writer": ("✍️", "Writer", "Đang viết nội dung"),
    "researcher": ("🔍", "Researcher", "Đang nghiên cứu"),
    "designer": ("🎨", "Designer", "Đang thiết kế"),
    "analyst": ("📊", "Analyst", "Đang phân tích"),
    "reviewer": ("✅", "Reviewer", "Đang kiểm duyệt & tổng hợp"),
}

# ==================== API ====================
def call_openrouter(messages, model, api_key, temperature=0.7, max_tokens=2000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://team-ai-gia-dinh.streamlit.app",
        "X-Title": "Team AI Gia Dinh Premium"
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

def extract_file_content(uploaded_file):
    """Trích xuất nội dung text từ file (txt, md, py, csv...)"""
    try:
        if uploaded_file.type.startswith("text/") or uploaded_file.name.endswith((".txt", ".md", ".py", ".csv", ".json", ".html")):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.type.startswith("image/"):
            return f"[Hình ảnh: {uploaded_file.name}]"
        else:
            return f"[File: {uploaded_file.name} - loại {uploaded_file.type}]"
    except:
        return f"[Không đọc được file: {uploaded_file.name}]"

# ==================== SESSION ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {}

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình Premium")
    try:
        default_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except:
        default_key = ""
    
    api_key = st.text_input("OpenRouter API Key", type="password", value=default_key)
    model_choice = st.selectbox("Model", list(FREE_MODELS.keys()), index=0)
    selected_model = FREE_MODELS[model_choice]
    
    st.divider()
    st.markdown("### 📜 Quy tắc Team")
    team_rules = st.text_area("Nội quy", value="Ưu tiên chất lượng • Tuân thủ yêu cầu gốc • Reviewer tổng hợp bản cuối hoàn chỉnh", height=100)
    
    st.info("💡 Free: ~50 request/ngày • Mỗi lần chạy team ≈ 4-5 request")

# ==================== MAIN UI ====================
st.title("👨‍👩‍👧‍👦 Team AI Gia Đình Premium")
st.caption("Chat chuyên nghiệp • Upload mọi loại file • Xem agent đang làm việc realtime")

# File uploader
uploaded_files = st.file_uploader(
    "📎 Gửi file (hỗ trợ: txt, md, py, pdf, jpg, png, csv, json...)",
    accept_multiple_files=True,
    type=["txt", "md", "py", "pdf", "jpg", "jpeg", "png", "csv", "json", "html", "docx"]
)

file_context = ""
if uploaded_files:
    st.success(f"✅ Đã nhận {len(uploaded_files)} file")
    for f in uploaded_files:
        content = extract_file_content(f)
        file_context += f"\n\n--- File: {f.name} ---\n{content[:3000]}"  # giới hạn để tránh quá dài

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Nhập yêu cầu cho Team AI..."):
    if not api_key:
        st.error("Vui lòng nhập OpenRouter API Key ở sidebar!")
        st.stop()
    
    # User message
    full_prompt = prompt
    if file_context:
        full_prompt += f"\n\n**File đính kèm:**{file_context}"
    
    st.session_state.messages.append({
        "role": "user",
        "content": prompt + (f"\n\n📎 {len(uploaded_files)} file đính kèm" if uploaded_files else ""),
        "avatar": "👤"
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if uploaded_files:
            st.caption(f"📎 Đính kèm {len(uploaded_files)} file")

    # ========== RUN TEAM ==========
    with st.spinner("Team đang khởi động..."):
        # 1. Planner
        with st.chat_message("assistant", avatar="🎯"):
            status_placeholder = st.empty()
            status_placeholder.markdown('<span class="status-working">⏳ Planner đang điều phối...</span>', unsafe_allow_html=True)
            
            planner_msg = [
                {"role": "system", "content": ROLE_PROMPTS["planner"] + "\n\nQuy tắc:\n" + team_rules},
                {"role": "user", "content": full_prompt}
            ]
            plan, _ = call_openrouter(planner_msg, selected_model, api_key)
            status_placeholder.markdown('<span class="status-done">✅ Planner đã chia việc</span>', unsafe_allow_html=True)
            st.markdown(plan)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**🎯 Planner**\n\n{plan}",
            "avatar": "🎯"
        })

        # 2. Workers (chọn 2-3 agent chính)
        workers = ["coder", "writer", "researcher"]
        worker_results = {}
        
        for agent_key in workers:
            emoji, name, status_text = AGENT_INFO[agent_key]
            with st.chat_message("assistant", avatar=emoji):
                status_placeholder = st.empty()
                status_placeholder.markdown(f'<span class="status-working">⏳ {name} {status_text}...</span>', unsafe_allow_html=True)
                
                worker_msg = [
                    {"role": "system", "content": ROLE_PROMPTS[agent_key]},
                    {"role": "user", "content": f"Yêu cầu gốc:\n{full_prompt}\n\nKế hoạch từ Planner:\n{plan}\n\nHãy thực hiện phần việc của bạn."}
                ]
                result, _ = call_openrouter(worker_msg, selected_model, api_key)
                worker_results[agent_key] = result
                
                status_placeholder.markdown(f'<span class="status-done">✅ {name} đã hoàn thành</span>', unsafe_allow_html=True)
                st.markdown(result)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**{emoji} {name}**\n\n{result}",
                "avatar": emoji
            })

        # 3. Reviewer
        with st.chat_message("assistant", avatar="✅"):
            status_placeholder = st.empty()
            status_placeholder.markdown('<span class="status-working">⏳ Reviewer đang kiểm duyệt & tổng hợp...</span>', unsafe_allow_html=True)
            
            all_work = "\n\n".join([f"### {AGENT_INFO[k][1]}\n{v}" for k, v in worker_results.items()])
            reviewer_msg = [
                {"role": "system", "content": ROLE_PROMPTS["reviewer"]},
                {"role": "user", "content": f"Yêu cầu gốc:\n{full_prompt}\n\nKế hoạch:\n{plan}\n\nKết quả các agent:\n{all_work}\n\nHãy tổng hợp bản cuối hoàn chỉnh."}
            ]
            final, _ = call_openrouter(reviewer_msg, selected_model, api_key)
            
            status_placeholder.markdown('<span class="status-done">✅ Reviewer hoàn tất</span>', unsafe_allow_html=True)
            st.markdown("### 🎯 Bản tổng hợp cuối cùng")
            st.markdown(final)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**✅ Reviewer - Bản cuối**\n\n{final}",
            "avatar": "✅"
        })

    st.success("Team AI đã hoàn thành yêu cầu!")
    st.rerun()

# Clear chat
if st.sidebar.button("🗑️ Xóa lịch sử chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()
