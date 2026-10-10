import streamlit as st
import pandas as pd


# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
)

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
# 2. 데이터 불러오기
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    # 열 이름 확인
    missing_columns = [
        column for column in COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )

    # 지정된 열 순서 유지
    df = df[COLUMNS].copy()

    return df


# ==========================================
# 3. 앱 제목
# ==========================================
st.title("🧠 뇌졸중 예측 실습실")

st.markdown(
    """
    이 실습실에서는 사람들의 건강 정보와 생활 습관이 담긴
    데이터를 살펴봅니다.

    먼저 데이터의 크기와 각 열의 의미, 빈 값의 분포를 확인해 봅시다.
    """
)

st.divider()


# ==========================================
# 4. 데이터 불러오기 및 오류 처리
# ==========================================
try:
    df = load_data()

except Exception as error:
    st.error(f"데이터를 불러오지 못했습니다: {error}")
    st.info(
        "인터넷 연결과 CSV 주소, 파일의 열 이름을 확인해 주세요."
    )
    st.stop()


# ==========================================
# 5. 요약 숫자 카드 네 개
# ==========================================
total_people = len(df)
total_columns = len(df.columns)

stroke_count = int(
    (pd.to_numeric(df["stroke"], errors="coerce") == 1).sum()
)

stroke_rate = (
    stroke_count / total_people * 100
    if total_people > 0
    else 0
)

st.subheader("📊 데이터 한눈에 보기")

card1, card2, card3, card4 = st.columns(4)

card1.metric(
    label="전체 사람 수",
    value=f"{total_people:,}명",
)

card2.metric(
    label="열 개수",
    value=f"{total_columns:,}개",
)

card3.metric(
    label="stroke가 1인 사람 수",
    value=f"{stroke_count:,}명",
)

card4.metric(
    label="stroke가 1인 비율",
    value=f"{stroke_rate:.2f}%",
)

st.caption(
    "stroke가 1인 비율은 전체 행 중 stroke 값이 1인 행의 비율입니다."
)

st.divider()


# ==========================================
# 6. 열 이름과 데이터 정보 표
# ==========================================
st.subheader("📋 열 이름과 데이터 정보")

st.markdown(
    """
    각 열에 어떤 정보가 들어 있는지 살펴보세요.
    **우리말 뜻** 칸은 교재를 참고해 직접 채울 수 있도록 비워 두었습니다.
    """
)

# 값의 종류를 확인하는 함수
def get_value_types(series):
    unique_values = series.dropna().unique()

    # 수치형 열
    if pd.api.types.is_numeric_dtype(series):
        if len(unique_values) <= 10:
            values = sorted(unique_values.tolist())
            return ", ".join(str(value) for value in values)

        return f"수치형 ({len(unique_values):,}개 고유값)"

    # 문자형 열
    values = sorted(str(value) for value in unique_values)

    if len(values) <= 10:
        return ", ".join(values)

    return f"문자형 ({len(values):,}개 고유값)"


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

st.dataframe(
    column_info,
    use_container_width=True,
    hide_index=True,
    height=470,
    column_config={
        "열 이름": st.column_config.TextColumn(
            "열 이름",
            help="CSV에 저장된 원래 열 이름",
        ),
        "우리말 뜻": st.column_config.TextColumn(
            "우리말 뜻",
            help="교재를 참고해 직접 작성할 수 있는 빈 칸",
        ),
        "값의 종류": st.column_config.TextColumn(
            "값의 종류",
        ),
        "빈 값 개수": st.column_config.NumberColumn(
            "빈 값 개수",
            format="%d",
        ),
    },
)

st.caption(
    "빈 값 개수는 pandas에서 결측값으로 인식한 셀의 수입니다. "
    "값의 종류는 실제 데이터에 나타나는 값 또는 고유값 개수를 나타냅니다."
)

st.divider()


# ==========================================
# 7. 원본 데이터 첫 다섯 행
# ==========================================
st.subheader("🔎 원본 데이터 미리 보기")

st.markdown(
    "데이터가 실제로 어떻게 기록되어 있는지 첫 다섯 행을 확인합니다."
)

st.dataframe(
    df.head(5),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "원본의 처음 다섯 행을 표시합니다. "
    "이 화면에서는 결측값을 임의로 채우거나 행을 삭제하지 않습니다."
)

st.divider()


# ==========================================
# 8. 데이터 출처
# ==========================================
st.subheader("📚 데이터 출처")

st.markdown(
    "교재에 제시된 데이터 출처와 설명을 아래에 기록하세요."
)

source_text = st.text_area(
    "데이터 출처 및 참고 자료",
    value="",
    placeholder="교재를 참고해 데이터 출처, 제공 기관, 참고 문헌 등을 입력하세요.",
    height=120,
    key="data_source",
)

st.caption(
    "데이터 파일: "
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
)


