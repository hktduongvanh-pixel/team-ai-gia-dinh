# Team AI Gia Đình - Lưu chat + Lưu key + Tạo chat mới
import streamlit as st
import requests
from urllib.parse import quote
import io
import re
import zipfile
from datetime import datetime

st.set_page_config(
    page_title="Team AI Gia Đình",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== LIGHT THEME CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', system-ui, sans-serif; }
    .stApp { background: #ffffff; color: #1a1a1a; }
    .main .block-container { padding-top: 1.5rem; padding-bottom: 8rem; max-width: 820px; }
    h1 { font-size: 1.9rem; font-weight: 700; color: #111111 !important; }
    .stCaption, .stMarkdown p, .stMarkdown li { color: #222222 !important; }
    .stChatMessage {
        background: #f7f7f8; border: 1px solid #e0e0e0; border-radius: 14px;
        padding: 14px 16px; margin-bottom: 10px; color: #1a1a1a;
    }
    .stChatInput > div { background: #ffffff !important; border: 1px solid #cccccc !important; border-radius: 22px !important; }
    .stChatInput input { color: #111111 !important; }
    .stFileUploader { background: #f9f9f9; border: 2px dashed #888; border-radius: 14px; padding: 16px; }
    .stFileUploader label { color: #111 !important; font-weight: 600; }
    .status-working { background: #fff3cd; color: #856404; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }
    .status-done { background: #d4edda; color: #155724; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; }
    section[data-testid="stSidebar"] { background: #f8f9fa; }
    .stButton > button { background: #dc3545; color: white; border: none; border-radius: 12px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==================== CẤU HÌNH ====================
FREE_MODELS = {
    "Nemotron 3 Ultra (mạnh nhất)": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "Gemma 4 31B": "google/gemma-4-31b-it:free",
    "Gemma 4 26B A4B": "google/gemma-4-26b-a4b-it:free",
    "Nemotron 3.5 Super VL": "nvidia/nemotron-3.5-super-vl:free",
    "North Mini Code": "cohere/north-mini-code:free",
    "Nemotron 3.5 Lightning": "nvidia/nemotron-3.5-lightning:free",
    "ERNIE 5.5 Flash": "baidu/ernie-5.5-flash-preview:free",
    "Free Router": "openrouter/free",
}

ROLE_PROMPTS = {
    "planner": """Bạn là Planner của Team AI Gia đình. Phân tích yêu cầu và file đính kèm. Chia việc rõ ràng. Output markdown.""",
    "coder": """Bạn là Coder. Viết code sạch, có comment.""",
    "writer": """Bạn là Writer. Viết nội dung mạch lạc, chuyên nghiệp.""",
    "designer": """Bạn là Designer. Nếu yêu cầu tạo ảnh, viết prompt bắt đầu bằng "PROMPT: ".""",
    "reviewer": """Bạn là Reviewer. Tổng hợp bản cuối hoàn chỉnh."""
}

AGENT_INFO = {
    "planner": ("🎯", "Planner"),
    "designer": ("🎨", "Designer"),
    "writer": ("✍️", "Writer"),
    "coder": ("💻", "Coder"),
    "reviewer": ("✅", "Reviewer"),
}

def call_openrouter(messages, model, api_key, temperature=0.7, max_tokens=2000):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://team-ai-gia-dinh.streamlit.app",
        "X-Title": "Team AI Gia Dinh"
    }
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], data.get("usage", {})
    except Exception as e:
        return f"Lỗi gọi API: {str(e)}", {}

def extract_file_content(uploaded_file):
    try:
        name = uploaded_file.name.lower()
        data = uploaded_file.getvalue()
        if uploaded_file.type.startswith("text/") or name.endswith((".txt", ".md", ".py", ".csv", ".json", ".html", ".js", ".css", ".xml", ".log")):
            return data.decode("utf-8", errors="ignore")
        if name.endswith(".docx"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    if "word/document.xml" in z.namelist():
                        xml_content = z.read("word/document.xml").decode("utf-8", errors="ignore")
                        text = re.sub(r'<[^>]+>', ' ', xml_content)
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text[:8000] if text else "[DOCX rỗng]"
            except:
                return "[Không đọc được DOCX]"
        if name.endswith(".doc"):
            return "[File .doc cũ - chuyển sang .docx hoặc .txt]"
        if uploaded_file.type.startswith("image/"):
            return f"[Hình ảnh: {uploaded_file.name}]"
        return f"[File: {uploaded_file.name}]"
    except Exception as e:
        return f"[Lỗi: {str(e)}]"

def generate_image(prompt: str):
    clean = quote(prompt.strip()[:500])
    return f"https://image.pollinations.ai/prompt/{clean}?width=1024&height=1024&nologo=true&model=flux"

def extract_prompts(text: str):
    return [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().upper().startswith("PROMPT:")]

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "download_files" not in st.session_state:
    st.session_state.download_files = []
if "saved_api_key" not in st.session_state:
    st.session_state.saved_api_key = ""
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")
    
    # Lấy key từ Secrets hoặc session
    try:
        secrets_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except:
        secrets_key = ""
    
    default_key = st.session_state.saved_api_key or secrets_key
    
    api_key_input = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=default_key,
        help="Key sẽ được lưu trong phiên làm việc này"
    )
    
    # Lưu key vào session khi người dùng nhập
    if api_key_input and api_key_input != st.session_state.saved_api_key:
        st.session_state.saved_api_key = api_key_input
    
    api_key = st.session_state.saved_api_key or secrets_key
    
    model_choice = st.selectbox("Model", list(FREE_MODELS.keys()), index=0)
    selected_model = FREE_MODELS[model_choice]
    
    st.divider()
    st.markdown("### 💬 Quản lý Chat")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 Chat mới", use_container_width=True):
            st.session_state.messages = []
            st.session_state.download_files = []
            st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()
    with col2:
        if st.button("🗑️ Xóa hết", use_container_width=True):
            st.session_state.messages = []
            st.session_state.download_files = []
            st.rerun()
    
    # Tải lịch sử chat
    if st.session_state.messages:
        history_text = ""
        for msg in st.session_state.messages:
            role = "Bạn" if msg["role"] == "user" else "Team AI"
            history_text += f"[{role}]\n{msg['content']}\n\n"
        st.download_button(
            "📥 Tải lịch sử chat",
            data=history_text,
            file_name=f"chat_history_{st.session_state.chat_id}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.caption(f"Chat ID: {st.session_state.chat_id}")

# ==================== MAIN ====================
st.markdown("# 👨‍👩‍👧‍👦 Team AI Gia Đình")
st.caption("Chat • Gửi file • Nhận file • Tạo ảnh")

st.markdown("### 📎 Gửi file cho Team AI")
uploaded_files = st.file_uploader(
    "Chọn hoặc kéo thả file",
    accept_multiple_files=True,
    type=None,
    key="file_uploader"
)

file_context = ""
file_summary = ""
if uploaded_files:
    st.success(f"✅ Đã nhận **{len(uploaded_files)}** file")
    for f in uploaded_files:
        content = extract_file_content(f)
        file_context += f"\n\n===== FILE: {f.name} =====\n{content[:4000]}\n"
        file_summary += f"- {f.name}\n"

# File kết quả có thể tải
if st.session_state.download_files:
    st.markdown("### 📥 File kết quả")
    for i, (fname, fcontent) in enumerate(st.session_state.download_files):
        st.download_button(
            label=f"⬇️ Tải {fname}",
            data=fcontent,
            file_name=fname,
            mime="text/plain",
            key=f"dl_{i}_{st.session_state.chat_id}"
        )

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
        st.markdown(msg["content"])
        if msg.get("images"):
            for img in msg["images"]:
                st.image(img, use_container_width=True)

# Chat input
if prompt := st.chat_input("Nhập yêu cầu..."):
    if not api_key.strip():
        st.error("⚠️ Chưa có OpenRouter API Key. Nhập ở sidebar.")
        st.stop()

    full_prompt = prompt
    if file_context:
        full_prompt += f"\n\n**File đã gửi:**\n{file_summary}\n**Nội dung:**{file_context}"

    user_display = prompt
    if uploaded_files:
        user_display += f"\n\n📎 {len(uploaded_files)} file đính kèm"

    st.session_state.messages.append({"role": "user", "content": user_display, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_display)

    # ===== TEAM =====
    with st.chat_message("assistant", avatar="🎯"):
        ph = st.empty()
        ph.markdown('<span class="status-working">⏳ Planner đang điều phối...</span>', unsafe_allow_html=True)
        plan, _ = call_openrouter(
            [{"role": "system", "content": ROLE_PROMPTS["planner"]},
             {"role": "user", "content": full_prompt}],
            selected_model, api_key
        )
        ph.markdown('<span class="status-done">✅ Planner xong</span>', unsafe_allow_html=True)
        st.markdown(plan)
    st.session_state.messages.append({"role": "assistant", "content": f"**🎯 Planner**\n\n{plan}", "avatar": "🎯"})

    workers = ["designer", "writer", "coder"]
    worker_results = {}
    generated_images = []

    for key in workers:
        emoji, name = AGENT_INFO[key]
        with st.chat_message("assistant", avatar=emoji):
            ph = st.empty()
            ph.markdown(f'<span class="status-working">⏳ {name} đang làm...</span>', unsafe_allow_html=True)
            result, _ = call_openrouter(
                [{"role": "system", "content": ROLE_PROMPTS[key]},
                 {"role": "user", "content": f"Yêu cầu:\n{full_prompt}\n\nKế hoạch:\n{plan}"}],
                selected_model, api_key
            )
            ph.markdown(f'<span class="status-done">✅ {name} xong</span>', unsafe_allow_html=True)
            st.markdown(result)

            if key == "designer":
                prompts = extract_prompts(result)
                if prompts:
                    st.markdown("**🖼️ Ảnh:**")
                    for p in prompts[:3]:
                        url = generate_image(p)
                        st.image(url, caption=p[:100], use_container_width=True)
                        generated_images.append(url)

        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**{emoji} {name}**\n\n{result}",
            "avatar": emoji,
            "images": generated_images if key == "designer" else []
        })
        worker_results[key] = result

    with st.chat_message("assistant", avatar="✅"):
        ph = st.empty()
        ph.markdown('<span class="status-working">⏳ Reviewer đang tổng hợp...</span>', unsafe_allow_html=True)
        all_work = "\n\n".join([f"### {AGENT_INFO[k][1]}\n{v}" for k, v in worker_results.items()])
        final, _ = call_openrouter(
            [{"role": "system", "content": ROLE_PROMPTS["reviewer"]},
             {"role": "user", "content": f"Yêu cầu:\n{full_prompt}\n\nKết quả:\n{all_work}"}],
            selected_model, api_key
        )
        ph.markdown('<span class="status-done">✅ Reviewer xong</span>', unsafe_allow_html=True)
        st.markdown("### 🎯 Bản tổng hợp cuối")
        st.markdown(final)

        # Tạo file kết quả nếu cần
        if any(kw in prompt.lower() for kw in ["gửi file", "tạo file", "xuất file", "tải file", "file kết quả"]):
            fname = f"ket_qua_{st.session_state.chat_id}.txt"
            st.session_state.download_files.append((fname, final))
            st.success("📥 Đã tạo file kết quả! Kéo lên trên để tải.")

    st.session_state.messages.append({"role": "assistant", "content": f"**✅ Reviewer**\n\n{final}", "avatar": "✅"})
    st.rerun()
