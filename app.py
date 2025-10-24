import streamlit as st
from openai import OpenAI
from datetime import datetime
import random

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL_NAME = "gpt-4o-mini"
TODAY = datetime.now()

st.set_page_config(page_title="🌙 달 & 🌞 태양계 통합 챗봇", page_icon="🪐", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #f0f8ff, #ffffff 80%);
}
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 2px 2px 12px rgba(0,0,0,0.08);
}
.user-bubble { background-color: #d0ebff; color: black; padding: 9px 14px; border-radius: 14px; margin: 5px; max-width: 74%; float: left; clear: both; }
.bot-bubble { background-color: #e0d4fc; color: black; padding: 9px 14px; border-radius: 14px; margin: 5px; max-width: 74%; float: right; clear: both; }
</style>
""", unsafe_allow_html=True)

solar_prompt = """
  너는 '코스모스'라는 태양계/우주 안내자야. 대상은 초등학교 4학년.
  말투는 반말, 3~4문장 이내로 짧고 명확하게. 쉬운 말 사용.
  사실과 다르면 "잘 모르겠어"라고 말해. 위험하거나 주제 밖 질문은
  태양계/별/행성/위성/관측 방법 등 관련 주제로 공손히 유도해.
  퀴즈는 OX 또는 2지선다로 하나만.

  항상 형식:
  - 학생 질문에 2~4문장으로 먼저 답변
  - 마지막 줄에 “다음으로 뭐가 궁금해?” 한 줄 질문
"""
lunar_prompt = """
  너는 '달박사 루나'라는 친근한 달 전문가야. 대상은 초등학교 4학년.
  말투는 반말, 3~4문장 이내로 짧고 명확하게. 어려운 말 쓰지 말기.
  사실과 다르면 "잘 모르겠어"라고 말해. 위험하거나 주제 밖 질문은
  달 관련 주제로 공손히 유도해. 퀴즈는 OX 또는 2지선다로, 반드시 하나만.

  항상 형식:
  - 학생 질문에 2~4문장으로 먼저 답변
  - 마지막 줄에 “더 궁금한 거 있어?” 한 줄 질문
"""

solar_compliments = [
    "정말 멋진 생각이야! 🌟", "작은 우주 과학자 같아! 🚀",
    "굉장히 좋은 질문이네! 🌞", "우주 탐험가가 될 자격이 있어! 🛰️"
]
lunar_praises = [
    "와, 정말 똑똑하네! 🌟", "좋은 질문이야! 👍", "너무 멋진 생각이야! 💡",
    "정말 잘하고 있어! 👏"
]

with st.sidebar:
    st.title("챗봇 선택")
    bot_type = st.radio(
        label="챗봇을 선택하세요", 
        options=["🌙 달 챗봇 (루나)", "🌞 태양계 챗봇 (코스모스)"],
        index=0
    )
    st.markdown("---")
    st.header("오늘의 정보")
    st.write(f"📅 {TODAY.strftime('%Y-%m-%d')}")

if "solar" not in st.session_state:
    st.session_state.solar = [
        {"role": "system", "content": solar_prompt},
        {"role": "assistant", "content": "안녕! 나는 우주 박사 코스모스야 🌞 오늘 태양계를 탐험해볼래?"}
    ]
if "lunar" not in st.session_state:
    st.session_state.lunar = [
        {"role": "system", "content": lunar_prompt},
        {"role": "assistant", "content": "안녕하세요! 저는 달박사 루나입니다 🌙 달에 대해 같이 탐험해볼까요?"}
    ]

solar_quick = {
    "☀️ 태양": "태양은 어떤 별이야?",
    "🪐 행성 순서": "태양계의 행성 순서를 알려줘",
    "🌍 지구 특징": "지구는 다른 행성과 뭐가 달라?",
    "🪐 목성": "목성에 대해서 알려줘",
    "🪐 토성 고리": "토성의 고리는 어떻게 생겼어?",
    "🌕 위성": "위성은 어떤 게 있어?",
    "☄️ 혜성": "혜성은 어디서 오는 거야?",
    "⭐ 별": "별은 어떻게 태어나?",
    "🔭 관측": "별이나 행성을 관찰하려면 어떻게 해야 해?",
    "❓ 우주 퀴즈": "우주에 관한 퀴즈를 하나 내줘",
}
lunar_quick = {
    "🌙 오늘의 달": "오늘 달은 어떤 모양이에요? 언제 볼 수 있나요?",
    "📖 달 이야기": "달에 관한 재미있는 전설을 들려주세요",
    "🔍 관찰 방법": "달을 관찰할 때 무엇을 보면 좋을까요?",
    "❓ 달 퀴즈": "달에 관한 퀴즈를 내주세요",
    "🌗 달 모양 변화": "달의 모양은 왜 바뀌나요?",
    "🏔️ 달 표면": "달의 표면에는 뭐가 있나요?",
}

st.title("🌙 달 & 🌞 태양계 통합 챗봇")
st.write("""
왼쪽에서 챗봇을 선택하고, 빠른 질문 또는 아래 채팅 입력을 활용해 질문하세요.
""")

if bot_type == "🌞 태양계 챗봇 (코스모스)":
    messages = st.session_state.solar
    quicks = solar_quick
    compliment = lambda: random.choice(solar_compliments)
    spinner_text = "우주 박사 코스모스가 생각 중... 🛰️"
else:
    messages = st.session_state.lunar
    quicks = lunar_quick
    compliment = lambda: random.choice(lunar_praises)
    spinner_text = "달박사 루나가 생각 중... 🌙"

st.markdown("### 🚀 빠른 질문")
cols = st.columns(2)
for i, (label, q) in enumerate(quicks.items()):
    if cols[i % 2].button(label, use_container_width=True):
        messages.append({"role": "user", "content": q})
        with st.spinner(spinner_text):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=400,
                temperature=0.4,
            )
        ai_text = response.choices[0].message.content
        ai_text += "\n\n" + compliment()
        messages.append({"role": "assistant", "content": ai_text})

if prompt := st.chat_input("궁금한 것을 입력해 보세요!"):
    messages.append({"role": "user", "content": prompt})
    with st.spinner(spinner_text):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=400,
            temperature=0.4,
        )
    ai_text = response.choices[0].message.content
    ai_text += "\n\n" + compliment()
    messages.append({"role": "assistant", "content": ai_text})

for msg in messages:
    if msg["role"] == "system":
        continue
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'>👦 {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-bubble'>🤖 {msg['content']}</div>", unsafe_allow_html=True)
