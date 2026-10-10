import streamlit as st
import pandas as pd


# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# 2. 데이터 주소와 열 이름
# ==========================================
DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)

COLUMNS = [
    "id",
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "ever_married",
    "work_type",
    "Residence_type",
    "avg_glucose_level",
    "bmi",
    "smoking_status",
    "stroke",
]


# ==========================================
# 3. 데이터 불러오기
# ==========================================
@st.cache_datafrom pathlib import Path

import pandas as pd
import streamlit as st


# ==========================================
# 1. 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# 2. 프로젝트 경로
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / "pages"

EXPLORE_PAGE_PATH = PAGES_DIR / "1_탐색.py"
MODEL_PAGE_PATH = PAGES_DIR / "2_분류_모델.py"


# ==========================================
# 3. 데이터 주소와 열 이름
# ==========================================
DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)

COLUMNS = [
    "id",
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "ever_married",
    "work_type",
    "Residence_type",
    "avg_glucose_level",
    "bmi",
    "smoking_status",
    "stroke",
]


# ==========================================
# 4. 데이터 불러오기
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    missing_columns = [
        column
        for column in COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )

    return df[COLUMNS].copy()


# ==========================================
# 5. 값의 종류 요약
# ==========================================
def get_value_types(series):
    values = series.dropna().unique()

    if pd.api.types.is_numeric_dtype(series):
        if len(values) <= 10:
            try:
                values = sorted(values.tolist())
            except TypeError:
                values = values.tolist()

            return ", ".join(str(value) for value in values)

        return f"수치형 ({len(values):,}개 고유값)"

    values = sorted(str(value) for value in values)

    if len(values) <= 10:
        return ", ".join(values)

    return f"문자형 ({len(values):,}개 고유값)"


# ==========================================
# 6. 데이터 소개 화면
# ==========================================
def show_home():
    st.title("🧠 뇌졸중 예측 실습실")

    st.markdown(
        """
        사람들의 건강 정보와 생활 습관이 담긴 데이터를 살펴보고,
        데이터 분석과 뇌졸중 예측을 위한 기초를 학습합니다.

        왼쪽 사이드바에서 **탐색** 또는 **분류 모델**을 선택하세요.
        """
    )

    try:
        df = load_data()
    except Exception as error:
        st.error(f"데이터를 불러오지 못했습니다: {error}")
        st.stop()

    # --------------------------------------
    # 요약 카드
    # --------------------------------------
    st.divider()
    st.subheader("📊 데이터 한눈에 보기")

    total_people = len(df)
    total_columns = len(df.columns)

    stroke_values = pd.to_numeric(
        df["stroke"],
        errors="coerce",
    )

    stroke_count = int((stroke_values == 1).sum())

    stroke_rate = (
        stroke_count / total_people * 100
        if total_people > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("전체 사람 수", f"{total_people:,}명")
    col2.metric("열 개수", f"{total_columns:,}개")
    col3.metric("stroke가 1인 사람 수", f"{stroke_count:,}명")
    col4.metric("stroke가 1인 비율", f"{stroke_rate:.2f}%")

    st.caption(
        "stroke가 1인 비율은 전체 행 중 뇌졸중으로 기록된 사람의 비율입니다."
    )

    # --------------------------------------
    # 열 설명 표
    # --------------------------------------
    st.divider()
    st.subheader("📋 열 이름과 데이터 정보")

    st.write(
        "우리말 뜻 열을 클릭해 교재의 설명을 입력하거나 수정하세요."
    )

    column_info = pd.DataFrame({
        "열 이름": df.columns,
        "우리말 뜻": ["" for _ in df.columns],
        "값의 종류": [
            get_value_types(df[column])
            for column in df.columns
        ],
        "빈 값 개수": [
            int(df[column].isna().sum())
            for column in df.columns
        ],
    })

    edited_info = st.data_editor(
        column_info,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=[
            "열 이름",
            "값의 종류",
            "빈 값 개수",
        ],
        column_config={
            "열 이름": st.column_config.TextColumn("열 이름"),
            "우리말 뜻": st.column_config.TextColumn(
                "우리말 뜻",
                help="교재를 참고해 우리말 뜻을 입력하세요.",
            ),
            "값의 종류": st.column_config.TextColumn("값의 종류"),
            "빈 값 개수": st.column_config.NumberColumn(
                "빈 값 개수",
                format="%d",
            ),
        },
        key="column_info_editor",
    )

    st.download_button(
        label="📥 수정한 열 설명 다운로드",
        data=edited_info.to_csv(
            index=False,
        ).encode("utf-8-sig"),
        file_name="열_설명.csv",
        mime="text/csv",
    )

    st.caption(
        "수정한 열 설명은 CSV 파일로 내려받아 보관할 수 있습니다."
    )

    # --------------------------------------
    # 원본 데이터 미리 보기
    # --------------------------------------
    st.divider()
    st.subheader("🔎 원본 데이터 미리 보기")

    st.dataframe(
        df.head(5),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------
    # 데이터 출처
    # --------------------------------------
    st.divider()
    st.subheader("📚 데이터 출처")

    st.text_area(
        "데이터 출처 및 참고 자료",
        placeholder="교재에 나온 출처와 참고 문헌을 입력하세요.",
        height=120,
        key="data_source",
    )

    st.caption(f"데이터 파일 주소: {DATA_URL}")


# ==========================================
# 7. 페이지 파일 확인
# ==========================================
missing_pages = []

if not EXPLORE_PAGE_PATH.is_file():
    missing_pages.append("pages/1_탐색.py")

if not MODEL_PAGE_PATH.is_file():
    missing_pages.append("pages/2_분류_모델.py")

if missing_pages:
    st.error("페이지 파일을 찾을 수 없습니다.")
    st.write("다음 파일을 확인해 주세요:")

    for missing_page in missing_pages:
        st.code(missing_page)

    st.info(
        "GitHub 저장소에서 파일 이름과 대소문자, "
        "폴더 위치를 확인한 뒤 다시 배포하세요."
    )
    st.stop()


# ==========================================
# 8. 사이드바 메뉴 등록
# ==========================================
home_page = st.Page(
    show_home,
    title="데이터 소개",
    icon="🏠",
    default=True,
)

explore_page = st.Page(
    str(EXPLORE_PAGE_PATH),
    title="탐색",
    icon="🔎",
)

model_page = st.Page(
    str(MODEL_PAGE_PATH),
    title="분류 모델",
    icon="🌳",
)

navigation = st.navigation(
    {
        "실습 메뉴": [
            home_page,
            explore_page,
            model_page,
        ]
    },
    position="sidebar",
    expanded=True,
)

navigation.run()
