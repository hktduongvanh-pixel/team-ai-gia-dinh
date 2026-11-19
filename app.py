# Team AI Gia Đình - Modern Dark UI
import streamlit as st
import requests
from urllib.parse import quote

st.set_page_config(
    page_title="Team AI Gia Đình",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== MODERN DARK CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', system-ui, sans-serif; }
    
    .stApp {
        background: #0a0a0f;
        color: #e5e5e5;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 8rem;
        max-width: 800px;
    }
    
    /* Header đẹp hơn */
    h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ffffff 0%, #ff4d4d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    /* Chat bubbles hiện đại */
    .stChatMessage {
        background: #14141a;
        border: 1px solid #2a2a35;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    
    /* Ô nhập chat */
    .stChatInput > div {
        background: #14141a !important;
        border: 1px solid #2a2a35 !important;
        border-radius: 20px !important;
    }
    
    /* File uploader đẹp hơn */
    .stFileUploader {
        background: #14141a;
        border: 1px dashed #3a3a4a;
        border-radius: 14px;
        padding: 12px;
    }
    .stFileUploader label {
        color: #a0a0b0 !important;
    }
    
    /* Status */
    .status-working {
        background: #3a1f1f;
        color: #ff8a8a;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .status-done {
        background: #1f3a2a;
        color: #7dffb3;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0f0f14;
        border-right: 1px solid #22222a;
    }
    
    /* Nút */
    .stButton > button {
        background: #ff4d4d;
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
    }
    .stButton > button:hover {
        background: #ff3333;
    }
    
    /* Caption */
    .stCaption {
        color: #888 !important;
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
    try:
        if uploaded_file.type.startswith("text/") or uploaded_file.name.endswith((".txt", ".md", ".py", ".csv", ".json", ".html", ".js")):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.type.startswith("image/"):
            return f"[Hình ảnh: {uploaded_file.name}]"
        else:
            return f"[File: {uploaded_file.name}]"
    except:
        return f"[Không đọc được: {uploaded_file.name}]"

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
st.markdown("# 👨‍👩‍👧‍👦 Team AI<br>Gia Đình", unsafe_allow_html=True)
st.caption("Chat • Upload file • Tạo ảnh thật")

# File uploader
uploaded_files = st.file_uploader(
    "📎 Gửi file (kéo thả hoặc bấm chọn)",
    accept_multiple_files=True,
    type=["txt", "md", "py", "pdf", "jpg", "jpeg", "png", "csv", "json", "html", "js", "zip"]
)

file_context = ""
if uploaded_files:
    with st.expander(f"✅ Đã nhận {len(uploaded_files)} file", expanded=False):
        for f in uploaded_files:
            st.write(f"• {f.name}")
            file_context += f"\n\n--- {f.name} ---\n{extract_file_content(f)[:1500]}"

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
        st.error("⚠️ Chưa có OpenRouter API Key. Vào sidebar hoặc Secrets để thêm.")
        st.stop()

    full_prompt = prompt + (f"\n\nFile đính kèm:{file_context}" if file_context else "")

    st.session_state.messages.append({
        "role": "user",
        "content": prompt + (f"\n\n📎 {len(uploaded_files)} file" if uploaded_files else ""),
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
             {"role": "user", "content": f"Yêu cầu: {full_prompt}\n\nKết quả:\n{all_work}"}],
            selected_model, api_key
        )
        ph.markdown('<span class="status-done">✅ Reviewer xong</span>', unsafe_allow_html=True)
        st.markdown("### 🎯 Bản cuối")
        st.markdown(final)
    st.session_state.messages.append({"role": "assistant", "content": f"**✅ Reviewer**\n\n{final}", "avatar": "✅"})

    st.rerun()
