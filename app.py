import random
from datetime import datetime
import yaml
import streamlit as st
from openai import OpenAI

# ----------------- 기본 설정 -----------------
st.set_page_config(page_title="🌙 달 & 🌞 태양계 통합 챗봇", page_icon="🪐", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
TODAY = datetime.now()
MODEL_NAME = "gpt-4o-mini"

# ----------------- 프롬프트 로드 -----------------
@st.cache_resource(show_spinner=False)
def load_prompts():
    with open("prompt.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
PROMPTS = load_prompts()

def build_system_prompt(bot_mode: str) -> str:
    return PROMPTS["moon_bot"] if bot_mode == "moon" else PROMPTS["solar_bot"]

# ----------------- 칭찬 한 줄 -----------------
COMPLIMENTS = [
    "정말 멋진 생각이야! 🌟",
    "작은 우주 과학자 같아! 🚀",
    "굉장히 좋은 질문이네! 🌞",
    "우주 탐험가가 될 자격이 있어! 🛰️",
]
def random_compliment(): return random.choice(COMPLIMENTS)

# ----------------- 빠른 질문 -----------------
MOON_BUTTONS = {
    "🌙 오늘의 달": "오늘 달은 어떤 모양이야? 언제 볼 수 있을까?",
    "🧭 달 모양 변화": "달의 모양은 왜 바뀌어?",
    "🏔️ 달 표면": "달의 바다는 뭐야? 표면은 어떻게 생겼어?",
    "🔭 관측 방법": "달을 관찰할 때 어떻게 하면 좋아?",
    "🧩 달 퀴즈": "달에 관한 OX 퀴즈 하나만 내줘",
}
SOLAR_BUTTONS = {
    "☀️ 태양": "태양은 어떤 별이야?",
    "🪐 행성 순서": "태양계의 행성 순서를 알려줘",
    "💍 토성 고리": "토성의 고리는 어떻게 생겼어?",
    "⭐ 별": "별은 어떻게 태어나?",
    "❓ 우주 퀴즈": "우주에 관한 OX 퀴즈 하나만 내줘",
}

# ----------------- 세션 상태 -----------------
def ensure_state():
    if "bot" not in st.session_state:
        st.session_state.bot = "moon"
    if "moon_history" not in st.session_state:
        st.session_state.moon_history = []
    if "solar_history" not in st.session_state:
        st.session_state.solar_history = []
ensure_state()

# ----------------- 스타일 -----------------
def apply_style(bot_mode: str):
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-radius: 16px;
        padding-top: 8px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.10);
    }
    section[data-testid="stSidebar"] .stRadio > label { display:none; }
    section[data-testid="stSidebar"] .stRadio div[role='radiogroup'] {
        display:flex; gap:8px; flex-direction:column;
    }
    section[data-testid="stSidebar"] .stRadio div[role='radio'] {
        border-radius:10px; padding:10px 12px; cursor:pointer;
        border:1px solid #e5e7eb; background:#f8fafc; font-weight:600;
    }
    section[data-testid="stSidebar"] .stRadio div[aria-checked="true"] {
        border-color:#3B82F6; background:linear-gradient(90deg,#3b82f6,#60a5fa);
        color:#fff;
    }
    .user-bubble { padding:10px 14px; border-radius:16px; max-width:80%; float:left; clear:both; margin:6px 0; }
    .bot-bubble  { padding:10px 14px; border-radius:16px; max-width:80%; float:right; clear:both; margin:6px 0; }
    </style>
    """, unsafe_allow_html=True)

    if bot_mode == "moon":
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #0f1226 0%, #1a1f3b 100%);
            color:#eef1ff;
        }
        .user-bubble { background:#22315e; color:#fff; }
        .bot-bubble  { background:#4b3f8a; color:#fff; }
        </style>
        """, unsafe_allow_html=True)
