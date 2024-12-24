import streamlit as st
import google.generativeai as genai
from PIL import Image

# Gemini API 설정
genai.configure(api_key="AIzaSyBLnHPdemSV1rmwPDkOd7KkL-UT9-B8mWk") # 실제 API 키로 바꿔주세요!
model = genai.GenerativeModel("gemini-2.0-flash-exp")

st.set_page_config(
    page_title="tool-assistant", page_icon="", layout="centered"
)
st.title("Tool-assistant")
st.markdown("Chat with Tool-assistant AI powered by Gemini")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

def generate_streaming_response(message, image=None):
    try:
        if image:
            response = model.generate_content([message, image], stream=True)
        else:
            response = model.generate_content(message, stream=True)
        response_container = st.empty()
        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
            response_container.markdown(full_response + "▌")
        response_container.markdown(full_response)
        return full_response
    except Exception as e:
        error_message = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
        st.error(error_message)
        return error_message

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message:
            st.image(message["image"])
        st.markdown(message["content"])

# 채팅 히스토리와 입력 필드 사이에 공간 만들기
st.markdown("<br>", unsafe_allow_html=True)

# 파일 업로더와 채팅 입력 통합
uploaded_file = st.file_uploader(
    "", type=['png', 'jpg', 'jpeg'], accept_multiple_files=False
)

current_image = None
if uploaded_file:
    current_image = Image.open(uploaded_file)
    st.image(current_image, width=200)

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    user_message = {"role": "user", "content": prompt}
    if current_image:
        user_message["image"] = current_image
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        if current_image:
            st.image(current_image)
        st.markdown(prompt)

    # AI 응답 생성 및 표시
    with st.chat_message("assistant"):
        response = generate_streaming_response(prompt, current_image if current_image else None)
        st.session_state.messages.append({"role": "assistant", "content": response})

# 사이드바에 대화 초기화 버튼 추가
with st.sidebar:
    if st.button("대화 지우기", type="primary"):
        st.session_state.messages = []
        st.rerun()
