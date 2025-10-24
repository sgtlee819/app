import streamlit as st
from openai import OpenAI
from datetime import datetime
import random
from pathlib import Path
import yaml
import traceback

st.set_page_config(page_title="달 & 태양계 통합 챗봇", page_icon="🌙", layout="wide")

# 날짜 정보만 표시
date_str = datetime.now().strftime("%Y-%m-%d")

# ==== 1. prompt.yaml 로드 ====
DEFAULT_PROMPTS = {
    "moon": {
        "system": "너는 '달박사 루나'야. 초등 4학년 눈높이, 3~4문장, 쉬운 말로 답해.",
        "guardrails": "달과 직접 관련 없는 질문이면 달/관측/우주와 연결해 부드럽게 유도."
    },
    "solar": {
        "system": "너는 '코스모스'라는 태양계 안내자야. 밝고 친근히, 쉬운 말, 3~4문장 답변.",
        "guardrails": "태양계/별/행성 주제와 관련 없으면 주제와 연결해 유도."
    }
}
prompts = DEFAULT_PROMPTS.copy()
try:
    p = Path(__file__).with_name("prompt.yaml")
    if p.exists():
        with p.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            for k in prompts:
                if k in loaded and loaded[k]:
                    prompts[k].update(loaded[k])
except Exception:
    st.warning("prompt.yaml 로딩 실패 (기본 프롬프트만 적용)")
    with st.expander("자세히"):
        st.code(traceback.format_exc())

# ==== 2. OpenAI 클라이언트 ====
client = None
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except Exception:
    st.warning("OpenAI 키/클라이언트 없음: 데모 답변만 출력됩니다.")

MODEL_NAME = "gpt-4o-mini"

# ==== 3. 챗봇별 칭찬, 빠른질문, 관련키워드 ====
moon_praises = [
    "와, 정말 똑똑하네! 🌟", "좋은 질문이야! 👍", "너무 멋진 생각이야! 💡", "대단한걸? 🤩", "정말 잘하고 있어! 👏"
]
solar_compliments = [
    "정말 멋진 생각이야! 🌟", "너는 작은 우주 과학자 같아! 🚀","굉장히 좋은 질문이네! 🌞", "우주 탐험가가 될 자격이 있어! 🛰️"
]

moon_keywords = [
    "달", "moon", "lunar", "월식", "일식", "음력",
    "보름달", "반달", "초승달", "상현달", "하현달",
    "달탐사", "아폴로", "달의 바다", "달표면", "달토끼"
]
def is_moon_related(text):
    return any(keyword in text.lower() for keyword in moon_keywords)

def random_praise(lst): return random.choice(lst)

def shorten_answer(text, max_sentences=4):
    sentences = text.replace("\n", " ").split(".")
    short_text = ".".join(sentences[:max_sentences]).strip()
    if not short_text.endswith("."):
        short_text += "."
    return short_text

moon_quick = {
    "🌙 오늘의 달": "오늘 달은 어떤 모양이에요? 언제 볼 수 있나요?",
    "📖 달 이야기": "달에 관한 재미있는 전설을 들려주세요",
    "🔍 관찰 방법": "달을 관찰할 때 무엇을 보면 좋을까요?",
    "❓ 달 퀴즈": "달에 관한 퀴즈를 내주세요",
    "🌗 달 모양 변화": "달의 모양은 왜 바뀌나요?",
    "🏔️ 달 표면": "달의 표면에는 뭐가 있나요?",
    "📅 음력과 달": "음력과 달의 모양은 어떤 관계가 있나요?",
    "⚠️ 안전 수칙": "밤에 달을 관찰할 때 주의할 점은 뭐예요?",
    "👩‍🚀 달 탐사 이야기": "사람이 달에 다녀온 적이 있나요?",
    "🔭 낮에도 보이는 달": "달은 낮에도 보이나요?",
    "🌍 달과 지구의 차이": "달과 지구는 뭐가 달라요?",
    "✍️ 관찰 일기 쓰는 법": "달 관찰 일기는 어떻게 써야 해요?",
}
solar_quick = {
    "☀️ 태양": "태양은 어떤 별이야?",
    "🪐 행성 순서": "태양계의 행성 순서를 알려줘",
    "🌍 지구 특징": "지구는 다른 행성과 뭐가 달라?",
    "🪐 목성": "목성에 대해서 알려줘",
    "🪐 토성 고리": "토성의 고리는 어떻게 생겼어?",
    "🌕 위성": "위성은 무엇이고 어떤 종류가 있어?",
    "☄️ 혜성": "혜성은 어디서 오는 거야?",
    "⭐ 별": "별은 어떻게 태어나?",
    "🔭 관측 방법": "별이나 행성을 관찰하려면 어떻게 해야 해?",
    "❓ 우주 퀴즈": "우주에 관한 퀴즈를 하나 내줘",
}

# ==== 4. 세션 상태 초기화 ====
for key, default in {
    "tab": "달 챗봇",
    "moon_history": [],
    "solar_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ==== 5. 스타일 ====
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to bottom, #f0f8ff, #ffffff 80%);
}
.user-bubble { background-color: #d0ebff; color: black; padding: 9px 14px; border-radius: 14px; margin: 5px; max-width: 74%; float: left; clear: both; }
.bot-bubble { background-color: #e0d4fc; color: black; padding: 9px 14px; border-radius: 14px; margin: 5px; max-width: 74%; float: right; clear: both; }
.info-box {
    background: #f9fbfe;
    border-radius: 13px;
    border: 1px solid #e9eff6;
    padding: 14px 18px;
    margin-bottom: 16px;
    margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

# ==== 6. 상단 타이틀 & 안내 ====
st.markdown(
    f"""
    <div class="hero">
      <h1>🌙 달 & 🪐 태양계 통합 챗봇</h1>
      <p>탭에서 챗봇 선택!  빠른 질문, 채팅 입력으로 질문해보세요.</p>
    </div>""",
    unsafe_allow_html=True,
)

# ==== 7. 탭 UI로 챗봇 전환 (학년/이름/반 UI 완전 제거) ====
tabs = st.tabs(["🌙 달 챗봇 (루나)", "🌞 태양계 챗봇 (코스모스)"])
tabmap = {
    "🌙 달 챗봇 (루나)": {
        "key": "moon_history",
        "sys": prompts["moon"]["system"] + "\n\n" + prompts["moon"]["guardrails"],
        "quicks": moon_quick,
        "praise": moon_praises,
        "check_topic": is_moon_related,
        "spinner": "달박사 루나가 생각 중... 🌙",
    },
    "🌞 태양계 챗봇 (코스모스)": {
        "key": "solar_history",
        "sys": prompts["solar"]["system"] + "\n\n" + prompts["solar"]["guardrails"],
        "quicks": solar_quick,
        "praise": solar_compliments,
        "check_topic": lambda x: True,
        "spinner": "코스모스가 생각 중... 🛰️",
    },
}

# ==== 8. 각 챗봇별 메인 로직 ====
for i, tab in enumerate(tabs):
    conf = list(tabmap.values())[i]
    with tab:
        st.markdown(
            f"""<div class='info-box'>
            <b>🗓️ 오늘의 정보</b><br>
            날짜 : {date_str}
            </div>""",
            unsafe_allow_html=True,
        )

        history_key = conf["key"]
        if not st.session_state[history_key]:
            st.session_state[history_key] = [{"role": "assistant", "content": "안녕하세요! 무엇이든 물어보세요!"}]

        st.markdown("#### 🚀 빠른 질문")
        cols = st.columns(4)
        for idx, (label, question) in enumerate(conf["quicks"].items()):
            if cols[idx % 4].button(label, use_container_width=True, key=history_key + "_btn_" + str(idx)):
                st.session_state[history_key].append({"role": "user", "content": question})

        # 대화 출력
        for msg in st.session_state[history_key]:
            if msg["role"] == "system":
                continue
            avatar = "🌙" if i == 0 else "🪐"
            who = "assistant" if msg["role"] == "assistant" else "user"
            st.markdown(
                f"<div class='{'bot-bubble' if who=='assistant' else 'user-bubble'}'>{avatar} {msg['content']}</div>",
                unsafe_allow_html=True,
            )

        user_text = st.chat_input("궁금한 걸 입력해 보세요!", key=history_key + "_input")
        if user_text:
            if i == 0 and not conf["check_topic"](user_text):
                st.session_state[history_key].append({
                    "role": "assistant",
                    "content": "이 질문은 달과 직접 관련이 없는 것 같아요 🌙 달에 대해 궁금한 걸 물어보는 건 어때요?"
                })
            else:
                st.session_state[history_key].append({"role": "user", "content": user_text})

        if st.session_state[history_key] and st.session_state[history_key][-1]["role"] == "user":
            with st.spinner(conf["spinner"]):
                messages = st.session_state[history_key][-8:]
                sys_prompt = conf["sys"]
                messages_for_llm = [{"role": "system", "content": sys_prompt}] + messages
                if client:
                    try:
                        resp = client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=messages_for_llm,
                            max_tokens=400,
                            temperature=0.45,
                        )
                        ai_text = resp.choices[0].message.content
                    except Exception:
                        ai_text = "(API 호출 오류, 답변 생성 실패)"
                else:
                    ai_text = f"(데모 응답) '{messages[-1]['content']}'에 대해 간단히 설명해 줄게!"
                # 답변 다듬기 & 칭찬 추가
                if i == 0:
                    ai_text = shorten_answer(ai_text, 4) + "\n\n" + random_praise(conf["praise"])
                else:
                    ai_text = ai_text.strip() + "\n\n" + random_praise(conf["praise"])
                st.session_state[history_key].append({"role": "assistant", "content": ai_text})
                st.markdown(
                    f"<div class='bot-bubble'>{'🌙' if i==0 else '🪐'} {ai_text}</div>",
                    unsafe_allow_html=True,
                )
