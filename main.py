import streamlit as st
import pandas as pd


# ==========================================
# 1. 페이지 등록 및 사이드바 메뉴
# ==========================================
home_page = st.Page(
    "main.py",
    title="데이터 소개",
    icon="🏠",
    default=True,
)

explore_page = st.Page(
    "pages/1_탐색.py",
    title="탐색",
    icon="🔎",
)

page = st.navigation(
    [home_page, explore_page],
    position="sidebar",
    expanded=True,
)

# 페이지 공통 설정
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 선택된 페이지 실행
# 아래 코드는 반드시 페이지 본문보다 먼저 실행해야 합니다.
# 단, 홈페이지 내용은 아래에서 실행하므로 별도 함수로 구성합니다.


# ==========================================
# 2. 데이터 주소 및 열 이름
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
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    missing_columns = [
        column for column in COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )

    return df[COLUMNS].copy()


# ==========================================
# 4. 값의 종류 요약
# ==========================================
def get_value_types(series):
    unique_values = series.dropna().unique()

    if pd.api.types.is_numeric_dtype(series):
        if len(unique_values) <= 10:
            try:
                values = sorted(unique_values.tolist())
            except TypeError:
                values = unique_values.tolist()

            return ", ".join(str(value) for value in values)

        return f"수치형 ({len(unique_values):,}개 고유값)"

    values = sorted(str(value) for value in unique_values)

    if len(values) <= 10:
        return ", ".join(values)

    return f"문자형 ({len(values):,}개 고유값)"


# ==========================================
# 5. 데이터 소개 화면
# ==========================================
def show_home():
    st.title("🧠 뇌졸중 예측 실습실")

    st.markdown(
        """
        뇌졸중 예측 실습실에 오신 것을 환영합니다!

        이 앱에서는 사람들의 건강 정보와 생활 습관이 담긴 데이터를
        살펴보고, 데이터 분석과 뇌졸중 예측을 위한 기초를 학습합니다.

        왼쪽 사이드바의 **탐색** 메뉴를 선택하면 그래프와 표를 통해
        데이터의 특징을 자세히 살펴볼 수 있습니다.
        """
    )

    st.divider()

    try:
        df = load_data()
    except Exception as error:
        st.error(f"데이터를 불러오지 못했습니다: {error}")
        st.info("인터넷 연결, CSV 주소, 열 이름을 확인해 주세요.")
        st.stop()

    # 요약 카드
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

    st.subheader("📊 데이터 한눈에 보기")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("전체 사람 수", f"{total_people:,}명")
    col2.metric("열 개수", f"{total_columns:,}개")
    col3.metric("stroke가 1인 사람 수", f"{stroke_count:,}명")
    col4.metric("stroke가 1인 비율", f"{stroke_rate:.2f}%")

    st.caption(
        "stroke가 1인 비율은 전체 행 중 stroke 값이 1인 행의 비율입니다."
    )

    st.divider()

    # 열 설명 표
    st.subheader("📋 열 이름과 데이터 정보")

    st.markdown(
        """
        **우리말 뜻** 열을 클릭해 교재에 나온 설명을 입력하세요.
        나머지 열은 수정할 수 없습니다.
        """
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

    edited_column_info = st.data_editor(
        column_info,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["열 이름", "값의 종류", "빈 값 개수"],
        column_config={
            "열 이름": st.column_config.TextColumn("열 이름"),
            "우리말 뜻": st.column_config.TextColumn(
                "우리말 뜻",
                help="셀을 클릭해 뜻을 입력하거나 수정하세요.",
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
        data=edited_column_info.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="열_설명.csv",
        mime="text/csv",
    )

    st.caption(
        "수정 내용은 현재 앱 세션에 유지됩니다. "
        "다운로드한 CSV 파일로 별도 보관할 수 있습니다."
    )

    st.divider()

    # 원본 데이터 미리 보기
    st.subheader("🔎 원본 데이터 미리 보기")

    st.dataframe(
        df.head(5),
        use_container_width=True,
        hide_index=True,
    )

    st.caption("원본 데이터의 처음 다섯 행입니다.")

    st.divider()

    # 데이터 출처
    st.subheader("📚 데이터 출처")

    st.text_area(
        "데이터 출처 및 참고 자료",
        value="",
        placeholder="교재의 데이터 출처와 참고 문헌을 입력하세요.",
        height=120,
        key="data_source",
    )

    st.caption(
        "데이터 파일: "
        "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
    )


# ==========================================
# 6. 선택된 페이지 실행
# ==========================================
if page == home_page:
    show_home()
else:
    page.run()
