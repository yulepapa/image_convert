import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import io
import base64
import zipfile
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="📸 이미지 → CSV 변환기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
/* 드래그앤드롭 영역 크게 만들기 */
.uploadedFile {
    border: 3px dashed #cccccc !important;
    border-radius: 10px !important;
    padding: 2rem !important;
    text-align: center !important;
    background-color: #fafafa !important;
    min-height: 200px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* 파일 업로드 후 빛나는 효과 */
.uploadedFile.success {
    border: 3px solid #00ff00 !important;
    background-color: #f0fff0 !important;
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.3) !important;
    animation: glow 2s ease-in-out infinite alternate !important;
}

@keyframes glow {
    from { box-shadow: 0 0 10px rgba(0, 255, 0, 0.3); }
    to { box-shadow: 0 0 30px rgba(0, 255, 0, 0.6); }
}

/* 사이드바 전체 레이아웃 개선 */
div[data-testid="stSidebar"] {
    padding-top: 1rem !important;
}

/* 크기 조절 버튼 스타일 */
.stButton button {
    width: 100% !important;
    height: 40px !important;
    border-radius: 8px !important;
    border: none !important;
    font-size: 1.2rem !important;
    font-weight: bold !important;
    transition: all 0.3s ease !important;
}

/* + 버튼 스타일 */
.stButton button:contains("➕") {
    background: linear-gradient(135deg, #4CAF50, #45a049) !important;
    color: white !important;
}

/* - 버튼 스타일 */
.stButton button:contains("➖") {
    background: linear-gradient(135deg, #f44336, #d32f2f) !important;
    color: white !important;
}

/* 버튼 hover 효과 */
.stButton button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}

/* number_input 스타일 개선 */
.stNumberInput > div > div > input {
    text-align: center !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    background: linear-gradient(90deg, #f8f9fa, #e9ecef) !important;
    border: 2px solid #dee2e6 !important;
    border-radius: 6px !important;
}

/* 크기 설정 섹션 스타일 */
div[data-testid="stSidebar"] .stMarkdown h4 {
    color: #2c3e50 !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

def process_image_grayscale(image, target_width, target_height):
    """이미지를 흑백 CSV로 변환"""
    # 크기 조정
    img_resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # 그레이스케일 변환
    img_gray = img_resized.convert('L')
    img_array = np.array(img_gray)
    
    # 데이터 변환
    data_list = []
    for y in range(img_array.shape[0]):
        for x in range(img_array.shape[1]):
            brightness = img_array[y, x]
            data_list.append({
                'x': x + 1,
                'y': y + 1,
                'brightness': int(brightness)
            })
    
    return pd.DataFrame(data_list)

def get_download_link(df, filename):
    """DataFrame을 CSV로 다운로드할 수 있는 링크 생성"""
    csv = df.to_csv(index=False, encoding='utf-8')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="text-decoration: none; background: linear-gradient(90deg, #4CAF50, #45a049); color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold; display: inline-block; margin: 5px;">📥 {filename} 다운로드</a>'
    return href

# 메인 앱
def main():
    # 헤더
    st.title("📸 이미지 → CSV 변환기")
    st.markdown("### 💎 Tableau 바차트 포트레이트용 데이터 생성기")
    st.markdown("---")
    
    # 사이드바 설정 (제목 제거)
    
    # 파일 업로드
    
    # 이미지 업로드
    uploaded_file = st.sidebar.file_uploader(
        "",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="지원 형식: PNG, JPG, JPEG, BMP, TIFF (최대 200MB)",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # 이미지 로드
        image = Image.open(uploaded_file)
        original_width, original_height = image.size
        
        # 이미지 정보 표시
        st.sidebar.info(f"📏 원본 크기: {original_width} × {original_height}")
        
        # 크기 설정
        st.sidebar.markdown("### 📐 출력 크기 설정")
        
        # Session state 초기화
        if 'width' not in st.session_state:
            st.session_state.width = 90
        if 'height' not in st.session_state:
            st.session_state.height = 72
        
        # 가로 크기 설정
        st.sidebar.markdown("**가로 (Width)**")
        col_minus1, col_input1, col_plus1 = st.sidebar.columns([1, 2, 1])
        with col_minus1:
            if st.button("➖", key="width_minus", help="가로 크기 -1"):
                if st.session_state.width > 10:
                    st.session_state.width -= 1
                    st.rerun()
        with col_input1:
            new_width = st.number_input("크기", min_value=10, max_value=500, value=st.session_state.width, step=1, key="width_input", label_visibility="collapsed")
            if new_width != st.session_state.width:
                st.session_state.width = new_width
        with col_plus1:
            if st.button("➕", key="width_plus", help="가로 크기 +1"):
                if st.session_state.width < 500:
                    st.session_state.width += 1
                    st.rerun()
        
        # 세로 크기 설정
        st.sidebar.markdown("**세로 (Height)**")
        col_minus2, col_input2, col_plus2 = st.sidebar.columns([1, 2, 1])
        with col_minus2:
            if st.button("➖", key="height_minus", help="세로 크기 -1"):
                if st.session_state.height > 10:
                    st.session_state.height -= 1
                    st.rerun()
        with col_input2:
            new_height = st.number_input("크기", min_value=10, max_value=500, value=st.session_state.height, step=1, key="height_input", label_visibility="collapsed")
            if new_height != st.session_state.height:
                st.session_state.height = new_height
        with col_plus2:
            if st.button("➕", key="height_plus", help="세로 크기 +1"):
                if st.session_state.height < 500:
                    st.session_state.height += 1
                    st.rerun()
        
        # 현재 값을 변수에 저장
        target_width = st.session_state.width
        target_height = st.session_state.height
        
        total_pixels = target_width * target_height
        st.sidebar.info(f"🔢 총 픽셀 수: {total_pixels:,}개")
        
        # 파일명 설정
        st.sidebar.markdown("### 📝 파일명 설정")
        base_filename = st.sidebar.text_input("기본 파일명", value="converted_image", help="확장자 없이 입력")
        
        # 변환 실행 버튼 (크고 눈에 띄게)
        st.sidebar.markdown("---")
        if st.sidebar.button("🚀 CSV 변환 시작", type="primary", use_container_width=True):
            # 메인 컨텐츠 영역
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📷 원본 이미지")
                st.image(image, caption=f"원본: {original_width}×{original_height}", use_column_width=True)
                
                # 리사이즈된 이미지 미리보기
                preview_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                st.subheader("🔍 변환될 크기 미리보기")
                st.image(preview_image, caption=f"변환 후: {target_width}×{target_height}", use_column_width=True)
            
            with col2:
                st.subheader("📊 변환 결과")
                
                # 진행 상황 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 변환 실행
                status_text.text("🔄 이미지 처리 중...")
                progress_bar.progress(30)
                
                try:
                    # 흑백 변환만 수행
                    df_full = process_image_grayscale(image, target_width, target_height)
                    
                    progress_bar.progress(70)
                    status_text.text("📈 데이터 분석 중...")
                    
                    # 데이터 통계
                    st.success(f"✅ 흑백 변환 완료!")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("총 픽셀 수", f"{len(df_full):,}")
                        st.metric("컬럼 수", len(df_full.columns))
                    with col_b:
                        st.metric("밝기 범위", f"{df_full['brightness'].min()}~{df_full['brightness'].max()}")
                        avg_brightness = df_full['brightness'].mean()
                        st.metric("평균 밝기", f"{avg_brightness:.1f}")
                    
                    progress_bar.progress(90)
                    
                    # 데이터 미리보기
                    st.subheader("📋 데이터 미리보기")
                    st.dataframe(df_full.head(10), use_container_width=True)
                    
                    # 밝기 분포 히스토그램
                    st.subheader("📊 밝기 분포")
                    brightness_counts = df_full['brightness'].value_counts().sort_index()
                    st.bar_chart(brightness_counts)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 변환 완료!")
                    
                    # 다운로드 파일 준비
                    output_filename = f"{base_filename}_{target_width}x{target_height}.csv"
                    
                    # 다운로드 섹션
                    st.subheader("📥 파일 다운로드")
                    
                    file_size = len(df_full.to_csv(index=False, encoding='utf-8').encode()) / 1024  # KB
                    st.markdown(f"**{output_filename}** ({len(df_full):,}행, {file_size:.1f}KB)")
                    st.markdown(get_download_link(df_full, output_filename), unsafe_allow_html=True)
                    
                    # Tableau 사용법 팁
                    st.subheader("💡 Tableau 사용법 팁")
                    st.info("""
                    **⚫ Tableau에서 바차트 포트레이트 만들기:**
                    1. **열**: x (연속형)
                    2. **행**: y (연속형)
                    3. **마크**: Bar
                    4. **크기**: brightness
                    5. **색상**: brightness (연속형)
                    6. **Y축 뒤집기** 필수! (축 편집 → "축 순서 바꾸기")
                    
                    🎨 **꿀팁**: 색상을 "흑백"으로 설정하면 더욱 사실적인 포트레이트!
                    """)
                
                except Exception as e:
                    st.error(f"❌ 변환 중 오류 발생: {str(e)}")
                    progress_bar.progress(0)
                    status_text.text("❌ 변환 실패")
    
    else:
        # 이미지가 업로드되지 않은 경우
        st.markdown('<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin: 2rem 0;"><h2>📸 이미지를 업로드해주세요</h2></div>', unsafe_allow_html=True)
        
        # 사용법 안내
        st.markdown("""
        ## 📋 사용법
        
        1. **이미지 업로드** → 사이드바에서 파일 선택
        2. **크기 설정** → 가로×세로 픽셀 수 조정
        3. **파일명 설정** → CSV 파일 이름 입력
        4. **변환 시작** → 버튼 클릭하여 변환
        5. **다운로드** → 생성된 CSV 파일 다운로드
        
        ## 💎 CSV 데이터 구조
        
        - **x**: 가로 좌표 (1~width)
        - **y**: 세로 좌표 (1~height)  
        - **brightness**: 밝기값 (0~255, 0=검정, 255=흰색)
        
        ## 🎯 Tableau 활용
        
        - **열**: x (연속형)
        - **행**: y (연속형)
        - **마크**: Bar
        - **크기**: brightness
        - **Y축 뒤집기** 필수!
        """)

if __name__ == "__main__":
    main() 