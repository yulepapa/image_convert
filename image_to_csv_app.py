import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import colorsys
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

def rgb_to_hex(r, g, b):
    """RGB 값을 HEX 색상 코드로 변환"""
    return f"#{r:02x}{g:02x}{b:02x}"

def get_color_name(r, g, b):
    """RGB 값을 기반으로 대략적인 색상 이름 분류"""
    # 그레이스케일 체크
    if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
        if r < 50:
            return "Black"
        elif r < 100:
            return "DarkGray"
        elif r < 150:
            return "Gray"
        elif r < 200:
            return "LightGray"
        else:
            return "White"
    
    # 색상 분류
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = h * 360
    s = s * 100
    v = v * 100
    
    if s < 20:  # 채도가 낮으면 무채색
        if v < 30:
            return "Black"
        elif v < 60:
            return "Gray"
        else:
            return "LightGray"
    
    # 색조에 따른 분류
    if h < 15 or h >= 345:
        return "Red"
    elif h < 45:
        return "Orange"
    elif h < 75:
        return "Yellow"
    elif h < 150:
        return "Green"
    elif h < 210:
        return "Cyan"
    elif h < 270:
        return "Blue"
    elif h < 315:
        return "Purple"
    else:
        return "Pink"

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
                'brightness': int(brightness),
                'brightness_inverted': 255 - int(brightness)
            })
    
    return pd.DataFrame(data_list)

def process_image_color(image, target_width, target_height):
    """이미지를 색상 CSV로 변환"""
    # 크기 조정 (RGB 모드 유지)
    img_resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    if img_resized.mode != 'RGB':
        img_resized = img_resized.convert('RGB')
    
    # RGB 배열과 그레이스케일 배열 생성
    img_array_rgb = np.array(img_resized)
    img_gray = img_resized.convert('L')
    img_array_gray = np.array(img_gray)
    
    # 데이터 변환
    data_list = []
    for y in range(img_array_rgb.shape[0]):
        for x in range(img_array_rgb.shape[1]):
            # RGB 값 추출
            r, g, b = img_array_rgb[y, x]
            brightness = img_array_gray[y, x]
            
            # HSV 변환
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            h = h * 360
            s = s * 100
            v = v * 100
            
            # HEX 색상 코드
            hex_color = rgb_to_hex(r, g, b)
            color_name = get_color_name(r, g, b)
            
            data_list.append({
                'x': x + 1,
                'y': y + 1,
                'brightness': int(brightness),
                'brightness_inverted': 255 - int(brightness),
                'r': int(r),
                'g': int(g),
                'b': int(b),
                'hex_color': hex_color,
                'hue': round(h, 1),
                'saturation': round(s, 1),
                'value': round(v, 1),
                'color_name': color_name
            })
    
    return pd.DataFrame(data_list)

def create_optimized_version(df, brightness_threshold, saturation_threshold=0, color_mode=False):
    """최적화 버전 생성"""
    if color_mode:
        # 색상 모드 최적화 (채도도 고려)
        df_optimized = df[
            (df['brightness'] >= brightness_threshold) & 
            (df['brightness'] <= 255 - brightness_threshold) &
            (df['saturation'] >= saturation_threshold)
        ].copy()
    else:
        # 흑백 모드 최적화
        df_optimized = df[
            (df['brightness'] >= brightness_threshold) & 
            (df['brightness'] <= 255 - brightness_threshold)
        ].copy()
    
    return df_optimized

def get_download_link(df, filename):
    """DataFrame을 CSV로 다운로드할 수 있는 링크 생성"""
    csv = df.to_csv(index=False, encoding='utf-8')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 {filename} 다운로드</a>'
    return href

def create_zip_download(files_dict):
    """여러 CSV 파일을 ZIP으로 묶어서 다운로드"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, df in files_dict.items():
            csv_data = df.to_csv(index=False, encoding='utf-8')
            zip_file.writestr(filename, csv_data)
    
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="converted_csvs.zip">📦 모든 파일 ZIP 다운로드</a>'
    return href

# 메인 앱
def main():
    # 헤더
    st.title("📸 이미지 → CSV 변환기")
    st.markdown("### Tableau 바차트 포트레이트용 데이터 생성기")
    st.markdown("---")
    
    # 사이드바 설정
    st.sidebar.title("⚙️ 변환 설정")
    
    # 이미지 업로드
    uploaded_file = st.sidebar.file_uploader(
        "📁 이미지 파일 선택",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="지원 형식: PNG, JPG, JPEG, BMP, TIFF"
    )
    
    if uploaded_file is not None:
        # 이미지 로드
        image = Image.open(uploaded_file)
        original_width, original_height = image.size
        
        # 이미지 정보 표시
        st.sidebar.success(f"✅ 이미지 로드 완료!")
        st.sidebar.info(f"📏 원본 크기: {original_width} × {original_height}")
        
        # 크기 설정
        st.sidebar.subheader("📐 출력 크기 설정")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            target_width = st.number_input("가로 (Width)", min_value=10, max_value=500, value=90, step=1)
        with col2:
            target_height = st.number_input("세로 (Height)", min_value=10, max_value=500, value=72, step=1)
        
        total_pixels = target_width * target_height
        st.sidebar.info(f"🔢 총 픽셀 수: {total_pixels:,}개")
        
        # 변환 옵션
        st.sidebar.subheader("🎨 변환 옵션")
        
        color_mode = st.sidebar.checkbox("🌈 색상 정보 포함", value=True, help="체크하면 RGB, HSV, HEX 색상 정보 포함")
        
        # 최적화 설정
        st.sidebar.subheader("⚡ 최적화 설정")
        enable_optimization = st.sidebar.checkbox("🚀 최적화 버전 생성", value=True, help="Tableau 성능 향상을 위한 최적화")
        
        if enable_optimization:
            brightness_threshold = st.sidebar.slider("밝기 임계값", 0, 100, 30, 5, help="이 값 이상/이하의 밝기만 포함")
            if color_mode:
                saturation_threshold = st.sidebar.slider("채도 임계값 (%)", 0, 50, 5, 1, help="이 값 이상의 채도만 포함")
            else:
                saturation_threshold = 0
        
        # 파일명 설정
        st.sidebar.subheader("📝 파일명 설정")
        base_filename = st.sidebar.text_input("기본 파일명", value="converted_image", help="확장자 없이 입력")
        
        # 변환 실행 버튼
        if st.sidebar.button("🚀 변환 시작", type="primary"):
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
                progress_bar.progress(25)
                
                try:
                    if color_mode:
                        df_full = process_image_color(image, target_width, target_height)
                        mode_text = "색상"
                        columns_count = len(df_full.columns)
                    else:
                        df_full = process_image_grayscale(image, target_width, target_height)
                        mode_text = "흑백"
                        columns_count = len(df_full.columns)
                    
                    progress_bar.progress(50)
                    status_text.text("📈 데이터 분석 중...")
                    
                    # 데이터 통계
                    st.success(f"✅ {mode_text} 변환 완료!")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("총 픽셀 수", f"{len(df_full):,}")
                        st.metric("컬럼 수", columns_count)
                    with col_b:
                        st.metric("밝기 범위", f"{df_full['brightness'].min()}~{df_full['brightness'].max()}")
                        if color_mode:
                            unique_colors = df_full['color_name'].nunique()
                            st.metric("색상 종류", unique_colors)
                    
                    progress_bar.progress(75)
                    
                    # 데이터 미리보기
                    st.subheader("📋 데이터 미리보기")
                    st.dataframe(df_full.head(10), use_container_width=True)
                    
                    # 색상 분포 (색상 모드인 경우)
                    if color_mode:
                        st.subheader("🎨 색상 분포")
                        color_dist = df_full['color_name'].value_counts()
                        st.bar_chart(color_dist)
                    
                    progress_bar.progress(90)
                    status_text.text("📁 파일 준비 중...")
                    
                    # 다운로드 파일 준비
                    files_to_download = {}
                    
                    # 전체 버전
                    full_filename = f"{base_filename}_{target_width}x{target_height}.csv"
                    files_to_download[full_filename] = df_full
                    
                    # 최적화 버전
                    if enable_optimization:
                        df_optimized = create_optimized_version(
                            df_full, brightness_threshold, saturation_threshold, color_mode
                        )
                        optimized_filename = f"{base_filename}_{target_width}x{target_height}_optimized.csv"
                        files_to_download[optimized_filename] = df_optimized
                        
                        st.info(f"🚀 최적화: {len(df_full):,}개 → {len(df_optimized):,}개 픽셀 ({len(df_optimized)/len(df_full)*100:.1f}%)")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 변환 완료!")
                    
                    # 다운로드 섹션
                    st.subheader("📥 파일 다운로드")
                    
                    # 개별 파일 다운로드
                    for filename, df in files_to_download.items():
                        file_size = len(df.to_csv(index=False, encoding='utf-8').encode()) / 1024  # KB
                        st.markdown(
                            f"**{filename}** ({len(df):,}행, {file_size:.1f}KB)"
                        )
                        st.markdown(get_download_link(df, filename), unsafe_allow_html=True)
                        st.markdown("---")
                    
                    # ZIP 다운로드 (여러 파일이 있는 경우)
                    if len(files_to_download) > 1:
                        st.markdown("### 📦 전체 다운로드")
                        st.markdown(create_zip_download(files_to_download), unsafe_allow_html=True)
                    
                    # Tableau 사용법 팁
                    st.subheader("💡 Tableau 사용법 팁")
                    if color_mode:
                        st.info("""
                        🌈 **색상 모드 Tableau 활용:**
                        1. **열**: x (연속형)
                        2. **행**: y (연속형) 
                        3. **마크**: Bar 또는 Square
                        4. **크기**: brightness_inverted
                        5. **색상**: hex_color (HEX 값 사용)
                        6. **Y축 뒤집기** 필수!
                        """)
                    else:
                        st.info("""
                        ⚫ **흑백 모드 Tableau 활용:**
                        1. **열**: x (연속형)
                        2. **행**: y (연속형)
                        3. **마크**: Bar
                        4. **크기**: brightness_inverted
                        5. **색상**: brightness (연속형)
                        6. **Y축 뒤집기** 필수!
                        """)
                
                except Exception as e:
                    st.error(f"❌ 변환 중 오류 발생: {str(e)}")
                    progress_bar.progress(0)
                    status_text.text("❌ 변환 실패")
    
    else:
        # 이미지가 업로드되지 않은 경우
        st.info("👈 왼쪽 사이드바에서 이미지를 업로드해주세요!")
        
        # 사용법 안내
        st.markdown("""
        ## 🔥 사용법
        
        1. **📁 이미지 업로드**: 왼쪽 사이드바에서 PNG, JPG 등의 이미지 파일 선택
        2. **📐 크기 설정**: 원하는 가로×세로 픽셀 수 입력 (예: 90×72)
        3. **🎨 모드 선택**: 
           - ✅ 색상 정보 포함: RGB, HSV, HEX 색상 데이터 추가 (추천!)
           - ❌ 흑백만: 밝기 정보만 포함
        4. **⚡ 최적화**: Tableau 성능 향상을 위한 데이터 필터링
        5. **🚀 변환 시작**: 버튼 클릭하여 CSV 파일 생성
        6. **📥 다운로드**: 생성된 CSV 파일들 다운로드
        
        ## 🎯 특징
        
        - **🌈 실제 색상 재현**: HEX 색상 코드로 원본 이미지 색상 완벽 복원
        - **⚡ Tableau 최적화**: 성능을 위한 불필요한 픽셀 자동 제거
        - **📊 다양한 형식**: 흑백/색상 모드, 전체/최적화 버전 동시 생성
        - **🔍 실시간 미리보기**: 변환 전 결과 미리 확인
        - **📁 편리한 다운로드**: 개별 또는 ZIP 파일로 한번에 다운로드
        
        ## 💡 권장 설정
        
        - **크기**: 90×72 (6,480픽셀) - 품질과 성능의 균형
        - **모드**: 색상 정보 포함 ✅ - 더 생생한 결과
        - **최적화**: 활성화 ✅ - Tableau 성능 향상
        """)

if __name__ == "__main__":
    main() 