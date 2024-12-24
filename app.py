import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF for PDF handling

# Gemini API 설정
genai.configure(api_key="AIzaSyBLnHPdemSV1rmwPDkOd7KkL-UT9-B8mWk")
model = genai.GenerativeModel("gemini-2.0-flash-exp")

st.set_page_config(
    page_title="Tool use assistant", page_icon="", layout="centered"
)

# 사이드바에 파일 업로더 추가
with st.sidebar:
    st.title("파일 업로드")
    uploaded_file = st.file_uploader(
        "이미지 또는 PDF 파일을 업로드하세요",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        accept_multiple_files=False
    )
    if st.button("대화 지우기", type="primary"):
        st.session_state.messages = []
        st.rerun()

st.title("Tool use Assistant AI Chating power by Gemini")
st.markdown("Chat with Tool use AI")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

def process_uploaded_file(uploaded_file):
    """파일 처리 함수: 이미지 또는 PDF를 처리하여 이미지 리스트 반환"""
    if uploaded_file is None:
        return None, None
    
    file_type = uploaded_file.type
    if file_type.startswith('image'):
        return Image.open(uploaded_file), 'image'
    elif file_type == 'application/pdf':
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        images = []
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap()
            img_bytes = pix.tobytes()
            img = Image.frombytes("RGB", [pix.width, pix.height], img_bytes)
            images.append(img)
        pdf_document.close()
        return images, 'pdf'
    return None, None

def generate_streaming_response(message, uploaded_content=None, content_type=None):
    try:
        if uploaded_content:
            if content_type == 'image':
                response = model.generate_content([message, uploaded_content], stream=True)
            elif content_type == 'pdf':
                # PDF의 경우 첫 페이지 이미지만 사용
                response = model.generate_content([message, uploaded_content[0]], stream=True)
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
        if "content_type" in message:
            if message["content_type"] == 'image':
                st.image(message["file_content"])
            elif message["content_type"] == 'pdf':
                st.write("PDF 파일 첨부됨")
                for i, img in enumerate(message["file_content"]):
                    st.image(img, caption=f"PDF 페이지 {i+1}")
        st.markdown(message["content"])

# 채팅 히스토리와 입력 필드 사이에 공간 만들기
st.markdown("<br>", unsafe_allow_html=True)

# 업로드된 파일 처리
current_content = None
content_type = None
if uploaded_file:
    current_content, content_type = process_uploaded_file(uploaded_file)
    if content_type == 'image':
        st.image(current_content, width=200)
    elif content_type == 'pdf':
        st.write("업로드된 PDF:")
        for i, img in enumerate(current_content):
            st.image(img, caption=f"페이지 {i+1}", width=200)

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    user_message = {"role": "user", "content": prompt}
    if current_content:
        user_message["file_content"] = current_content
        user_message["content_type"] = content_type
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        if current_content:
            if content_type == 'image':
                st.image(current_content)
            elif content_type == 'pdf':
                for i, img in enumerate(current_content):
                    st.image(img, caption=f"PDF 페이지 {i+1}")
        st.markdown(prompt)

    # AI 응답 생성 및 표시
    with st.chat_message("assistant"):
        response = generate_streaming_response(prompt, current_content, content_type)
        st.session_state.messages.append({"role": "assistant", "content": response})
