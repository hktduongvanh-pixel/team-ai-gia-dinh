# Team AI Gia Đình - Light Theme (nền trắng chữ đen)
import streamlit as st
import requests
from urllib.parse import quote
import io

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

    .stApp {
        background: #ffffff;
        color: #1a1a1a;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 8rem;
        max-width: 820px;
    }

    h1 {
        font-size: 1.9rem;
        font-weight: 700;
        color: #111111 !important;
        margin-bottom: 0.3rem;
    }

    .stCaption, .stMarkdown p, .stMarkdown li, .stMarkdown {
        color: #222222 !important;
    }

    /* Chat bubble */
    .stChatMessage {
        background: #f7f7f8;
        border: 1px solid #e0e0e0;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #1a1a1a;
    }

    /* Chat input */
    .stChatInput > div {
        background: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 22px !important;
    }
    .stChatInput input {
        color: #111111 !important;
    }

    /* File uploader */
    .stFileUploader {
        background: #f9f9f9;
        border: 2px dashed #bbbbbb;
        border-radius: 14px;
        padding: 14px;
    }
    .stFileUploader label, .stFileUploader span {
        color: #333333 !important;
        font-weight: 500;
    }

    /* Status */
    .status-working {
        background: #fff3cd;
        color: #856404;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .status-done {
        background: #d4edda;
        color: #155724;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    section[data-testid="stSidebar"] * {
        color: #1a1a1a !important;
    }

    /* Button */
    .stButton > button {
        background: #dc3545;
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: #c82333;
    }

    .streamlit-expanderHeader {
        color: #111111 !important;
        background: #f7f7f8;
    }
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
    "planner": """Bạn là Planner của Team AI Gia đình. Phân tích yêu cầu và chia việc rõ ràng. Nếu cần tạo ảnh thì giao Designer. Output markdown.""",
    "coder": """Bạn là Coder. Viết code sạch, có comment.""",
    "writer": """Bạn là Writer. Viết nội dung mạch lạc, chuyên nghiệp.""",
    "designer": """Bạn là Designer. Nếu yêu cầu tạo ảnh, viết 1-3 prompt tiếng Anh đẹp. Mỗi prompt bắt đầu bằng "PROMPT: " trên một dòng.""",
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
    """Đọc nội dung file, hỗ trợ text + cố gắng đọc docx"""
    try:
        name = uploaded_file.name.lower()
        data = uploaded_file.getvalue()

        # Text files
        if uploaded_file.type.startswith("text/") or name.endswith((".txt", ".md", ".py", ".csv", ".json", ".html", ".js", ".css", ".xml", ".log", ".rtf")):
            return data.decode("utf-8", errors="ignore")

        # DOCX (basic extraction without extra library)
        if name.endswith(".docx"):
            try:
                import zipfile
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    if "word/document.xml" in z.namelist():
                        xml_content = z.read("word/document.xml").decode("utf-8", errors="ignore")
                        # Simple strip tags
                        import re
                        text = re.sub(r'<[^>]+>', ' ', xml_content)
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text[:5000] if text else "[DOCX: không trích xuất được text]"
            except:
                pass
            return f"[File DOCX: {uploaded_file.name} - cần xử lý thêm]"

        # DOC (old format) - không đọc được dễ dàng
        if name.endswith(".doc"):
            return f"[File .doc cũ: {uploaded_file.name} - vui lòng chuyển sang .docx hoặc .txt để đọc tốt hơn]"

        # Image
        if uploaded_file.type.startswith("image/"):
            return f"[Hình ảnh: {uploaded_file.name}]"

        # PDF hoặc khác
        return f"[File: {uploaded_file.name} ({uploaded_file.type or 'unknown'})]"
    except Exception as e:
        return f"[Không đọc được {uploaded_file.name}: {str(e)}]"

def generate_image(prompt: str):
    clean = quote(prompt.strip()[:500])
    return f"https://image.pollinations.ai/prompt/{clean}?width=1024&height=1024&nologo=true&model=flux"

def extract_prompts(text: str):
    return [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().upper().startswith("PROMPT:")]

# ==================== SESSION ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")
    try:
        default_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except:
        default_key = ""
    api_key = st.text_input("OpenRouter API Key", type="password", value=default_key)
    model_choice = st.selectbox("Model", list(FREE_MODELS.keys()), index=0)
    selected_model = FREE_MODELS[model_choice]
    st.divider()
    if st.button("🗑️ Xóa chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ==================== MAIN ====================
st.markdown("# 👨‍👩‍👧‍👦 Team AI Gia Đình")
st.caption("Chat • Upload file • Tạo ảnh thật")

uploaded_files = st.file_uploader(
    "📎 Gửi file (kéo thả hoặc bấm Upload)",
    accept_multiple_files=True,
    type=None
)

file_context = ""
if uploaded_files:
    with st.expander(f"✅ Đã nhận {len(uploaded_files)} file", expanded=True):
        for f in uploaded_files:
            st.write(f"**{f.name}** — {f.type or 'unknown'}")
            file_context += f"\n\n--- {f.name} ---\n{extract_file_content(f)[:3000]}"

# Lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
        st.markdown(msg["content"])
        if msg.get("images"):
            for img in msg["images"]:
                st.image(img, use_container_width=True)

# Chat input
if prompt := st.chat_input("Nhập yêu cầu..."):
    if not api_key.strip():
        st.error("⚠️ Chưa có OpenRouter API Key. Mở sidebar hoặc thêm vào Secrets.")
        st.stop()

    full_prompt = prompt + (f"\n\nFile đính kèm:{file_context}" if file_context else "")

    st.session_state.messages.append({
        "role": "user",
        "content": prompt + (f"\n\n📎 {len(uploaded_files)} file đính kèm" if uploaded_files else ""),
        "avatar": "👤"
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if uploaded_files:
            st.caption(f"📎 {len(uploaded_files)} file đính kèm")

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
                 {"role": "user", "content": f"Yêu cầu: {full_prompt}\n\nKế hoạch: {plan}"}],
                selected_model, api_key
            )
            ph.markdown(f'<span class="status-done">✅ {name} xong</span>', unsafe_allow_html=True)
            st.markdown(result)

            if key == "designer":
                prompts = extract_prompts(result)
                if prompts:
                    st.markdown("**🖼️ Ảnh được tạo:**")
                    for p in prompts[:3]:
                        url = generate_image(p)
                        st.image(url, caption=p[:120], use_container_width=True)
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
             {"role": "user", "content": f"Yêu cầu: {full_prompt}\n\nKết quả:\n{all_work}"}],
            selected_model, api_key
        )
        ph.markdown('<span class="status-done">✅ Reviewer xong</span>', unsafe_allow_html=True)
        st.markdown("### 🎯 Bản tổng hợp cuối")
        st.markdown(final)
    st.session_state.messages.append({"role": "assistant", "content": f"**✅ Reviewer**\n\n{final}", "avatar": "✅"})

    st.rerun()
