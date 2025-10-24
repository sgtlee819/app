# app.py
import streamlit as st
from pathlib import Path
import traceback

st.set_page_config(page_title="달 & 태양계 통합 챗봇", page_icon="🌙", layout="wide")

# 0) 화면 상단 히어로 영역
st.markdown(
    """
    <style>
      .hero {padding: 24px 8px 0 8px;}
      .hero h1 {font-size: 40px; margin: 0 0 8px 0;}
      .hero p {color: #cbd5e1; margin: 0 0 16px 0;}
    </style>
    <div class="hero">
      <h1>🌙 달 & 🪐 태양계 통합 챗봇</h1>
      <p>챗봇에 오신 것을 환영합니다!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# 1) prompt.yaml 읽기 (없으면 기본값 사용, 에러 시에도 계속 진행)
PROMPTS = {
    "moon": {"system": "너는 '달박사 루나'야. 초등 4학년 눈높이, 3~4문장, 쉬운 말로 답해."},
    "solar": {"system": "너는 '우주네비'야. 태양계/행성/위성 주제, 3~4문장, 쉬운 말로 답해."},
    "guardrails": {
        "refuse_unrelated": "달/태양계와 직접 관련 없는 질문이면 주제와 연결되게 부드럽게 유도해."
    },
}

try:
    import yaml
    p = Path(__file__).with_name("prompt.yaml")
    if p.exists():
        with p.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            for k in PROMPTS.keys():
                if k in loaded:
                    PROMPTS[k].update(loaded[k] or {})
except Exception as e:
    st.warning("`prompt.yaml`을 읽는 중 문제가 있었지만, 기본 프롬프트로 계속 진행합니다.")
    with st.expander("프롬프트 로딩 경고 자세히 보기"):
        st.code("".join(traceback.format_exc()))

# 2) OpenAI 클라이언트 (없어도 UI는 뜸)
client = None
model_name = "gpt-4o-mini"
try:
    from openai import OpenAI
    # Streamlit Cloud에서는 secrets, 로컬은 secrets.toml 사용
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        st.info("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 답변은 예시/에코로 동작합니다.")
except Exception:
    st.info("⚠️ OpenAI 클라이언트를 초기화하지 못했습니다. (패키지/키 미설정)")

# 3) 세션 상태 안전 초기화
for key, default in {
    "page": "달 챗봇",
    "moon_history": [],
    "solar_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 4) 사이드바 라우팅 (항상 표시)
with st.sidebar:
    page = st.radio("🔭 모드 선택", ["달 챗봇", "태양계 챗봇"], index=0 if st.session_state["page"]=="달 챗봇" else 1)
    if page != st.session_state["page"]:
        st.session_state["page"] = page
        st.rerun()

# 5) 공통 보조 함수
def call_llm(messages, sys_prompt):
    """API 키 없으면 예시로 동작, 있으면 실제 호출"""
    # 시스템 프롬프트 prepend
    msgs = [{"role":"system", "content": sys_prompt}] + messages
    if client is None:
        # 데모용 응답
        user_last = next((m["content"] for m in reversed(messages) if m["role"]=="user"), "질문")
        return f"(데모 응답) '{user_last}'에 대해 간단히 설명해 줄게! 아직 API 키가 없어 예시로 답했어. 😉"
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=msgs,
            temperature=0.3,
            max_tokens=400,
        )
        return resp.choices[0].message.content
    except Exception:
        st.error("모델 호출 중 오류가 발생했어요. 아래 로그를 확인해 주세요.")
        st.code("".join(traceback.format_exc()))
        return None

def render_chat(history_key, sys_prompt, quick_questions):
    """공통 채팅 UI: 히스토리 표시 + 빠른 질문 + 입력"""
    # 빠른 질문 버튼
    st.markdown("#### 🚀 빠른 질문")
    cols = st.columns(4)
    for i, (label, question) in enumerate(quick_questions.items()):
        if cols[i % 4].button(label, use_container_width=True):
            st.session_state[history_key].append({"role":"user", "content":question})

    st.divider()

    # 히스토리 출력
    for msg in st.session_state[history_key]:
        avatar = "🌙" if msg["role"]=="assistant" else "👩‍🎓"
        with st.chat_message("assistant" if msg["role"]=="assistant" else "user", avatar=avatar):
            st.write(msg["content"])

    # 입력창
    user_text = st.chat_input("무엇이 궁금한가요?")
    if user_text:
        st.session_state[history_key].append({"role":"user", "content":user_text})

    # 새 질문이 있으면 답변 생성
    if st.session_state[history_key] and st.session_state[history_key][-1]["role"]=="user":
        # 가드레일: 주제 유도
        guard = PROMPTS["guardrails"]["refuse_unrelated"]
        # LLM 호출
        answer = call_llm(st.session_state[history_key][-6:], sys_prompt + "\n\n" + guard)
        if answer:
            st.session_state[history_key].append({"role":"assistant", "content":answer})
            with st.chat_message("assistant", avatar="🌙"):
                st.write(answer)

# 6) 페이지 별 렌더
if st.session_state["page"] == "달 챗봇":
    st.subheader("🌙 달 챗봇 (달박사 루나)")
    moon_quick = {
        "🌗 달의 위상": "달의 모양이 왜 매일 달라져?",
        "🔭 관찰 팁": "초등학생이 달을 관찰할 때 뭐가 중요해?",
        "📖 전설 하나": "달과 관련된 전설 한 가지만 들려줘.",
        "🛡️ 안전 수칙": "밤에 달 관찰할 때 주의할 점 3가지를 알려줘.",
    }
    render_chat("moon_history", PROMPTS["moon"]["system"], moon_quick)
else:
    st.subheader("🪐 태양계 챗봇 (우주네비)")
    solar_quick = {
        "☀️ 태양": "태양은 어떤 별이야? 크기와 역할은?",
        "🪐 행성 순서": "수~해 행성 순서를 외우는 쉬운 방법 알려줘.",
        "🌍 지구 특징": "지구가 다른 행성과 다른 점 3가지!",
        "🛰️ 위성": "위성은 뭐야? 자연위성과 인공위성 차이도!",
    }
    render_chat("solar_history", PROMPTS["solar"]["system"], solar_quick)
