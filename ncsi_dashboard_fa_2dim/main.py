import streamlit as st
import json
import pandas as pd
import os
from streamlit_folium import folium_static
import folium
import plotly.express as px
import datetime # For displaying last updated time

# --- Configuration Constants ---
NCSI_DASHBOARD_TITLE = "글로벌 사이버 보안 지수 (NCSI) 대시보드"
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "ncsi_top20.json")
NCSI_URL = "https://ncsi.ega.ee/ncsi-index/?order=rank" # Moved from crawler for info display

# --- Import Crawler Function ---
try:
    from crawler import crawl_ncsi
except ImportError:
    st.error("오류: 'crawler.py' 파일을 찾을 수 없습니다. 'main.py'와 같은 디렉토리에 있는지 확인해주세요.")
    st.stop() # Stop the app if crawler cannot be imported

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title=NCSI_DASHBOARD_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://ncsi.ega.ee/ncsi-index/?order=rank',
        'Report a bug': "mailto:your_email@example.com", # Replace with your email
        'About': f"# {NCSI_DASHBOARD_TITLE}\n"
                 "이 대시보드는 National Cyber Security Index (NCSI) 데이터를 기반으로 합니다.\n"
                 "**개발자:** [Your Name or Organization Name]" # Replace with your name/org
    }
)

# --- Custom CSS for a cleaner look (Optional) ---
st.markdown("""
<style>
    /* General Text Styling */
    h1 {
        color: #2F80ED; /* A nice blue */
    }
    h2, h3, h4 {
        color: #333333;
    }
    p, li {
        font-size: 16px;
    }

    /* Streamlit specific adjustments */
    .stApp {
        background-color: #f8f9fa; /* Light grey background */
    }
    .stSidebar {
        background-color: #e9ecef; /* Slightly darker grey for sidebar */
        padding-top: 2rem;
    }
    .css-1d391kg { /* Target for main content padding - adjust if needed */
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        border: 1px solid #2F80ED;
        background-color: #2F80ED;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .stButton>button:hover {
        background-color: #256bbd;
        border-color: #256bbd;
    }
    .stRadio > label {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .stSlider label {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .stMetric {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    .stMetric > div > div:first-child { /* Metric label */
        font-size: 1.1rem;
        color: #555555;
    }
    .stMetric > div > div:last-child { /* Metric value */
        font-size: 2.5rem;
        font-weight: bold;
        color: #2F80ED;
    }
    /* Hide the default Streamlit footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Data Loading and Caching ---
@st.cache_data(ttl=datetime.timedelta(hours=6)) # Cache for 6 hours, then re-run to check for fresh data
def load_and_process_data():
    """Loads NCSI data from JSON, attempts crawling if not found, and returns a DataFrame."""
    if not os.path.exists(OUTPUT_FILE):
        st.warning("데이터 파일이 없습니다. 초기 데이터를 크롤링합니다. 이 과정은 몇 초 소요될 수 있습니다.")
        with st.spinner("초기 데이터 크롤링 중..."):
            crawl_ncsi()
        if not os.path.exists(OUTPUT_FILE):
            st.error("초기 데이터 크롤링에 실패했습니다. 'crawler.py'를 직접 실행하거나 웹사이트 구조 변경 여부를 확인하세요.")
            return pd.DataFrame()

    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        # Ensure numeric types
        df['security_index'] = pd.to_numeric(df['security_index'], errors='coerce')
        df['digital_level'] = pd.to_numeric(df['digital_level'], errors='coerce')
        df['difference'] = pd.to_numeric(df['difference'], errors='coerce') # Ensure difference is numeric
        return df
    except json.JSONDecodeError:
        st.error(f"데이터 파일을 읽는 중 오류가 발생했습니다: {OUTPUT_FILE}. 파일 내용이 올바른 JSON 형식이 아닐 수 있습니다.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 및 처리 중 예상치 못한 오류가 발생했습니다: {e}")
        return pd.DataFrame()

df = load_and_process_data()

# --- Sidebar Content ---
st.sidebar.header("📊 대시보드 메뉴")

# Crawl Button (always at the top of sidebar for easy access)
if st.sidebar.button("🔄 최신 데이터 크롤링"):
    st.cache_data.clear() # Clear cache so new data is loaded
    with st.spinner("최신 데이터를 크롤링하는 중입니다... 잠시만 기다려 주세요."):
        crawled_data = crawl_ncsi() # Call the imported crawling function
    if crawled_data:
        st.sidebar.success("✅ 데이터 크롤링 및 업데이트 완료! 페이지를 새로고침합니다.")
        st.rerun() # Rerun the app to load new data
    else:
        st.sidebar.error("❌ 데이터 크롤링에 실패했습니다. 콘솔 로그를 확인하세요.")

# Display last updated time if file exists
if os.path.exists(OUTPUT_FILE):
    last_modified_timestamp = os.path.getmtime(OUTPUT_FILE)
    last_modified_datetime = datetime.datetime.fromtimestamp(last_modified_timestamp)
    st.sidebar.info(f"최종 데이터 업데이트: {last_modified_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.sidebar.info("데이터 파일이 없습니다. '최신 데이터 크롤링' 버튼을 눌러주세요.")


# Page Navigation Radio Buttons
page_selection = st.sidebar.radio(
    "페이지 선택:",
    ("🚀 대시보드 개요", "🔍 국가별 상세 분석", "🗺️ 글로벌 지도 시각화", "📈 심층 통계 및 차트"),
    index=0 # Default to the first page
)

# Global Filters (apply across all pages)
st.sidebar.markdown("---")
st.sidebar.header("⚙️ 데이터 필터링")
filtered_df = pd.DataFrame() # Initialize filtered_df

if not df.empty:
    min_rank, max_rank = int(df['rank'].min()), int(df['rank'].max())
    rank_range = st.sidebar.slider(
        "순위 범위 선택",
        min_value=min_rank,
        max_value=max_rank,
        value=(min_rank, max_rank),
        help="표시할 국가의 NCSI 순위 범위를 조정합니다."
    )
    filtered_df = df[(df['rank'] >= rank_range[0]) & (df['rank'] <= rank_range[1])]

    sort_column = st.sidebar.selectbox(
        "정렬 기준",
        ['rank', 'country', 'security_index', 'digital_level', 'difference'],
        index=0,
        help="데이터 테이블과 차트를 정렬할 기준을 선택합니다."
    )
    sort_order = st.sidebar.radio(
        "정렬 순서",
        ('오름차순', '내림차순'),
        index=0,
        horizontal=True, # Display radio buttons horizontally
        help="선택된 정렬 기준에 대한 순서를 결정합니다."
    )

    if sort_order == '내림차순':
        filtered_df = filtered_df.sort_values(by=sort_column, ascending=False)
    else:
        filtered_df = filtered_df.sort_values(by=sort_column, ascending=True)
else:
    st.info("데이터 로드 중 문제가 발생했거나 데이터 파일이 비어 있습니다. '최신 데이터 크롤링'을 시도해주세요.")


# --- Main Content Area based on Sidebar Selection ---
if page_selection == "🚀 대시보드 개요":
    st.header("✨ NCSI 대시보드 개요")
    st.markdown("이 페이지에서는 NCSI(National Cyber Security Index) 데이터의 **전반적인 흐름과 상위 국가들의 주요 통계**를 한눈에 볼 수 있습니다.")

    if not filtered_df.empty:
        st.subheader("📊 주요 지표 요약")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="총 국가 수", value=f"{len(filtered_df)}개국")
        with col2:
            st.metric(label="평균 사이버 보안 지수", value=f"{filtered_df['security_index'].mean():.2f}점")
        with col3:
            st.metric(label="평균 디지털 생활 수준", value=f"{filtered_df['digital_level'].mean():.2f}점")

        st.subheader("📋 NCSI 순위 테이블")
        st.markdown("현재 필터링 및 정렬 조건에 따른 **국가별 사이버 보안 지수 현황**입니다.")
        st.dataframe(filtered_df, use_container_width=True, height=400) # Fixed height for scrollability

        with st.expander("👉 데이터 컬럼 설명 보기"):
            st.markdown("""
            * **rank**: NCSI 순위 (낮을수록 좋음)
            * **country**: 국가명
            * **security_index**: 사이버 보안 지수 (높을수록 좋음)
            * **digital_level**: 디지털 생활 수준 지수 (높을수록 좋음)
            * **difference**: 사이버 보안 지수 - 디지털 생활 수준 지수 (양수면 보안이 앞서고, 음수면 디지털화가 앞섬)
            * **latitude**, **longitude**: 해당 국가의 지도상 위도 및 경도
            """)
    else:
        st.warning("표시할 데이터가 없습니다. 필터 조건을 변경하거나 '최신 데이터 크롤링' 버튼을 눌러 데이터를 업데이트하세요.")

elif page_selection == "🔍 국가별 상세 분석":
    st.header("🔍 국가별 상세 분석")
    st.markdown("여기서는 **선택된 국가의 NCSI 상세 지표**를 집중적으로 살펴볼 수 있습니다.")

    if not filtered_df.empty:
        selected_country = st.selectbox(
            "상세 정보를 볼 국가를 선택하세요:",
            filtered_df['country'].tolist(),
            help="드롭다운 메뉴에서 원하는 국가를 선택하여 상세 지표를 확인합니다."
        )
        if selected_country:
            country_data = filtered_df[filtered_df['country'] == selected_country].iloc[0]

            st.subheader(f"🌐 {country_data['country']}의 NCSI 상세 지표")
            col_detail1, col_detail2, col_detail3 = st.columns(3)
            with col_detail1:
                st.metric(label="✅ NCSI 순위", value=country_data['rank'])
            with col_detail2:
                st.metric(label="🛡️ 사이버 보안 지수", value=country_data['security_index'])
            with col_detail3:
                st.metric(label="💻 디지털 생활 수준", value=country_data['digital_level'])

            # Add an expander for "Difference" explanation or other derived metrics
            with st.expander("💡 격차(Difference) 상세 설명"):
                st.markdown(
                    f"**격차 (사이버 보안 지수 - 디지털 생활 수준):** `{country_data['difference']:.2f}`\n\n"
                    "이 지표는 국가의 사이버 보안 능력과 디지털 인프라 및 서비스 사용 수준 간의 균형을 나타냅니다.\n"
                    "- **양수**: 사이버 보안 능력이 디지털 생활 수준보다 더 높습니다. (보안 우위)\n"
                    "- **음수**: 디지털 생활 수준이 사이버 보안 능력보다 더 높습니다. (디지털화 우위, 보안 강화 필요성 시사)\n"
                    "- **0에 가까움**: 두 지표 간의 균형이 잘 이루어져 있습니다."
                )

            st.markdown("---")
            st.info(f"**{country_data['country']}**는 현재 사이버 보안 및 디지털화 영역에서 흥미로운 위치에 있습니다. 추가적인 분석을 통해 이 국가의 강점과 개선점을 파악할 수 있습니다.")
    else:
        st.warning("표시할 국가 데이터가 없습니다. 필터 조건을 변경하거나 '최신 데이터 크롤링' 버튼을 눌러 데이터를 업데이트하세요.")


elif page_selection == "🗺️ 글로벌 지도 시각화":
    st.header("🗺️ 글로벌 사이버 보안 지수 지도")
    st.markdown("세계 지도에서 각 국가의 **상대적인 위치와 NCSI 지표**를 시각적으로 확인합니다.")

    if not filtered_df.empty:
        if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
            # Drop rows with NaN coordinates for cleaner map
            map_df = filtered_df.dropna(subset=['latitude', 'longitude'])

            if not map_df.empty:
                center_lat = map_df['latitude'].mean()
                center_lon = map_df['longitude'].mean()
                zoom_start = 2 # General global view

                # Adjust zoom if only a few countries are selected
                if len(map_df) == 1:
                    zoom_start = 6
                elif len(map_df) <= 5:
                    zoom_start = 4

                m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, control_scale=True)

                for idx, row in map_df.iterrows():
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=f"<b>순위:</b> {row['rank']}<br>"
                              f"<b>국가:</b> {row['country']}<br>"
                              f"<b>사이버 보안 지수:</b> {row['security_index']:.2f}<br>"
                              f"<b>디지털 생활 수준:</b> {row['digital_level']:.2f}<br>"
                              f"<b>격차:</b> {row['difference']:.2f}",
                        tooltip=f"{row['country']} (Rank: {row['rank']})",
                        icon=folium.Icon(color="blue", icon="shield", prefix='fa') # Use Font Awesome shield icon
                    ).add_to(m)

                st.markdown("**💡 팁**: 지도 마커를 클릭하면 국가별 상세 정보 팝업이 나타납니다. 지도를 확대/축소하여 더 자세히 탐색해보세요.")
                folium_static(m, width=950, height=600) # Larger map for better view
            else:
                st.warning("선택된 국가 중 지도에 표시할 유효한 위도/경도 데이터가 없습니다.")
        else:
            st.error("데이터에 위도/경도 정보가 누락되어 지도 시각화를 할 수 없습니다. `crawler.py` 설정을 확인해주세요.")
    else:
        st.warning("표시할 지도 데이터가 없습니다. 필터 조건을 변경하거나 '최신 데이터 크롤링' 버튼을 눌러 데이터를 업데이트하세요.")


elif page_selection == "📈 심층 통계 및 차트":
    st.header("📈 NCSI 심층 통계 및 차트")
    st.markdown("선택된 국가들의 NCSI 데이터를 다양한 차트와 통계를 통해 **심층적으로 분석**합니다.")

    if not filtered_df.empty:
        # Layout with columns for charts
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("사이버 보안 지수 vs. 디지털 생활 수준")
            st.bar_chart(filtered_df.set_index('country')[['security_index', 'digital_level']])
            st.markdown("각 국가의 사이버 보안 지수와 디지털 생활 수준을 직접 비교합니다.")

        with chart_col2:
            st.subheader("사이버 보안 지수 분포 (히스토그램)")
            fig_hist_security = px.histogram(
                filtered_df,
                x='security_index',
                nbins=10,
                title='사이버 보안 지수 빈도 분포',
                labels={'security_index': '사이버 보안 지수'},
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            st.plotly_chart(fig_hist_security, use_container_width=True)
            st.markdown("국가들의 사이버 보안 지수 점수가 어떤 범위에 주로 분포하는지 보여줍니다.")

        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            st.subheader("디지털 생활 수준 분포 (히스토그램)")
            fig_hist_digital = px.histogram(
                filtered_df,
                x='digital_level',
                nbins=10,
                title='디지털 생활 수준 빈도 분포',
                labels={'digital_level': '디지털 생활 수준'},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_hist_digital, use_container_width=True)
            st.markdown("국가들의 디지털 생활 수준 점수가 어떤 범위에 주로 분포하는지 보여줍니다.")

        with chart_col4:
            st.subheader("보안 지수와 디지털 수준 간의 관계 (산점도)")
            fig_scatter = px.scatter(
                filtered_df,
                x='digital_level',
                y='security_index',
                size='security_index',
                color='country',
                hover_name='country',
                log_x=False,
                size_max=60,
                title='디지털 생활 수준 대비 사이버 보안 지수',
                labels={'digital_level': '디지털 생활 수준', 'security_index': '사이버 보안 지수'},
                template='plotly_white' # Cleaner Plotly theme
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.markdown("국가의 디지털화 수준이 높을수록 사이버 보안 지수도 높은 경향이 있는지 파악합니다.")

        # Optional: Correlation matrix/heatmap if you have more numeric features
        # st.subheader("상관관계 분석 (선택 사항)")
        # st.write("사이버 보안 지수와 다른 지표 간의 상관관계를 보여줍니다.")
        # if 'security_index' in filtered_df.columns and 'digital_level' in filtered_df.columns:
        #     correlation = filtered_df[['security_index', 'digital_level']].corr()
        #     st.dataframe(correlation)


    else:
        st.warning("표시할 차트 데이터가 없습니다. 필터 조건을 변경하거나 '최신 데이터 크롤링' 버튼을 눌러 데이터를 업데이트하세요.")

st.markdown("---")
st.markdown(f"데이터 출처: [National Cyber Security Index (NCSI)]({NCSI_URL})")
st.markdown("© 2025 [Your Name or Organization Name]. All rights reserved.") # Update year and name