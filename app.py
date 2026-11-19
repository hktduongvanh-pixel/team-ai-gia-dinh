# Team AI Gia Đình Lớn - Premium (Giao diện sạch + Tạo ảnh + Upload file)
import streamlit as st
import requests
from urllib.parse import quote

st.set_page_config(
    page_title="Team AI Gia Đình",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS SẠCH, DỄ NHÌN ====================
st.markdown("""
<style>
    .stApp {
        background: #0f1117;
        color: #e6e6e6;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 6rem;
        max-width: 900px;
    }
    .stChatMessage {
        background: #1a1d27;
        border-radius: 14px;
        border: 1px solid #2a2e3a;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .stChatInput {
        background: #1a1d27;
        border-radius: 20px;
        border: 1px solid #2a2e3a;
    }
    .status-working {
        background: #3a2a2a;
        color: #ff9f9f;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-done {
        background: #1e3a2f;
        color: #7dcea0;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .stButton > button {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background: #4338ca;
    }
    h1 {
        color: #f0f0f0;
        font-weight: 700;
        font-size: 1.6rem;
    }
    section[data-testid="stSidebar"] {
        background: #161922;
        border-right: 1px solid #2a2e3a;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CẤU HÌNH ====================
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
    "planner": """Bạn là Planner / Điều phối trưởng của Team AI Gia đình.
Phân tích yêu cầu và chia task rõ ràng cho từng agent.
Nếu yêu cầu tạo ảnh thì giao việc cho Designer.
Output dạng markdown rõ ràng.""",

    "coder": """Bạn là Coder Agent. Viết code sạch, có comment.""",
    "writer": """Bạn là Writer Agent. Viết nội dung mạch lạc, chuyên nghiệp.""",
    "researcher": """Bạn là Research Agent. Tổng hợp thông tin logic, không bịa đặt.""",
    "designer": """Bạn là Designer Agent.
Nếu yêu cầu tạo ảnh, hãy viết 1-3 prompt cực đẹp (tiếng Anh).
Mỗi prompt trên một dòng và bắt đầu bằng "PROMPT: ".
Ví dụ:
PROMPT: A cinematic photorealistic portrait of a young Vietnamese girl in ao dai, golden hour, 8k
PROMPT: ...""",
    "reviewer": """Bạn là Reviewer. Tổng hợp bản cuối hoàn chỉnh, mạch lạc."""
}

AGENT_INFO = {
    "planner": ("🎯", "Planner"),
    "coder": ("💻", "Coder"),
    "writer": ("✍️", "Writer"),
    "researcher": ("🔍", "Researcher"),
    "designer": ("🎨", "Designer"),
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
        if uploaded_file.type.startswith("text/") or uploaded_file.name.endswith((".txt", ".md", ".py", ".csv", ".json", ".html")):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.type.startswith("image/"):
            return f"[Hình ảnh: {uploaded_file.name}]"
        else:
            return f"[File: {uploaded_file.name}]"
    except:
        return f"[Không đọc được file: {uploaded_file.name}]"

def generate_image(prompt: str):
    clean_prompt = quote(prompt.strip()[:500])
    return f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&nologo=true&model=flux"

def extract_prompts(text: str):
    prompts = []
    for line in text.splitlines():
        if line.strip().upper().startswith("PROMPT:"):
            prompts.append(line.split(":", 1)[1].strip())
    return prompts

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
    st.info("💡 Tạo ảnh dùng Pollinations (miễn phí)")

# ==================== MAIN ====================
st.title("👨‍👩‍👧‍👦 Team AI Gia Đình")
st.caption("Chat + Upload file + Tạo ảnh thật")

uploaded_files = st.file_uploader(
    "📎 Gửi file (txt, md, py, pdf, ảnh, csv, json...)",
    accept_multiple_files=True,
    type=["txt", "md", "py", "pdf", "jpg", "jpeg", "png", "csv", "json", "html"]
)

file_context = ""
if uploaded_files:
    st.success(f"✅ Đã nhận {len(uploaded_files)} file")
    for f in uploaded_files:
        file_context += f"\n\n--- {f.name} ---\n{extract_file_content(f)[:2000]}"

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "👤")):
        st.markdown(msg["content"])
        if msg.get("images"):
            for img_url in msg["images"]:
                st.image(img_url, use_container_width=True)

# Ô nhập chat
if prompt := st.chat_input("Nhập yêu cầu cho Team AI..."):
    if not api_key:
        st.error("Vui lòng nhập OpenRouter API Key ở sidebar!")
        st.stop()

    full_prompt = prompt + (f"\n\nFile đính kèm:{file_context}" if file_context else "")

    # Lưu tin nhắn người dùng
    st.session_state.messages.append({
        "role": "user",
        "content": prompt + (f"\n\n📎 {len(uploaded_files)} file đính kèm" if uploaded_files else ""),
        "avatar": "👤"
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if uploaded_files:
            st.caption(f"📎 {len(uploaded_files)} file đính kèm")

    # ===== CHẠY TEAM =====
    # 1. Planner
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

    # 2. Các agent
    workers = ["designer", "writer", "coder"]
    worker_results = {}
    generated_images = []

    for agent_key in workers:
        emoji, name = AGENT_INFO[agent_key]
        with st.chat_message("assistant", avatar=emoji):
            ph = st.empty()
            ph.markdown(f'<span class="status-working">⏳ {name} đang làm việc...</span>', unsafe_allow_html=True)
            result, _ = call_openrouter(
                [{"role": "system", "content": ROLE_PROMPTS[agent_key]},
                 {"role": "user", "content": f"Yêu cầu: {full_prompt}\n\nKế hoạch: {plan}\n\nThực hiện phần của bạn."}],
                selected_model, api_key
            )
            ph.markdown(f'<span class="status-done">✅ {name} xong</span>', unsafe_allow_html=True)
            st.markdown(result)

            if agent_key == "designer":
                prompts = extract_prompts(result)
                if prompts:
                    st.markdown("**🖼️ Ảnh được tạo:**")
                    for p in prompts[:3]:
                        img_url = generate_image(p)
                        st.image(img_url, caption=p[:120], use_container_width=True)
                        generated_images.append(img_url)

        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**{emoji} {name}**\n\n{result}",
            "avatar": emoji,
            "images": generated_images if agent_key == "designer" else []
        })
        worker_results[agent_key] = result

    # 3. Reviewer
    with st.chat_message("assistant", avatar="✅"):
        ph = st.empty()
        ph.markdown('<span class="status-working">⏳ Reviewer đang tổng hợp...</span>', unsafe_allow_html=True)
        all_work = "\n\n".join([f"### {AGENT_INFO[k][1]}\n{v}" for k, v in worker_results.items()])
        final, _ = call_openrouter(
            [{"role": "system", "content": ROLE_PROMPTS["reviewer"]},
             {"role": "user", "content": f"Yêu cầu: {full_prompt}\n\nKết quả các agent:\n{all_work}\n\nTổng hợp bản cuối."}],
            selected_model, api_key
        )
        ph.markdown('<span class="status-done">✅ Reviewer xong</span>', unsafe_allow_html=True)
        st.markdown("### 🎯 Bản tổng hợp cuối")
        st.markdown(final)
    st.session_state.messages.append({"role": "assistant", "content": f"**✅ Reviewer**\n\n{final}", "avatar": "✅"})

    st.success("Hoàn thành!")
    st.rerun()

# Nút xóa chat
if st.sidebar.button("🗑️ Xóa lịch sử chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()
