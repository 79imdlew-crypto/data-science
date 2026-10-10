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
    st.info("인터넷 연결과 CSV 주소, 파일의 열 이름을 확인해 주세요.")
    st.stop()


# ==========================================
# 5. 요약 숫자 카드 네 개
# ==========================================
total_people = len(df)
total_columns = len(df.columns)

stroke_values = pd.to_numeric(
    df["stroke"], errors="coerce"
)
stroke_count = int((stroke_values == 1).sum())

stroke_rate = (
    stroke_count / total_people * 100
    if total_people > 0
    else 0
)

st.subheader("📊 데이터 한눈에 보기")

card1, card2, card3, card4 = st.columns(4)

card1.metric("전체 사람 수", f"{total_people:,}명")
card2.metric("열 개수", f"{total_columns:,}개")
card3.metric("stroke가 1인 사람 수", f"{stroke_count:,}명")
card4.metric("stroke가 1인 비율", f"{stroke_rate:.2f}%")

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
    **우리말 뜻** 열의 셀을 클릭해 내용을 직접 입력하거나 수정하세요.
    다른 열은 편집할 수 없도록 설정되어 있습니다.
    """
)


def get_value_types(series):
    """실제 데이터에 나타나는 값의 종류를 설명한다."""
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

# 우리말 뜻을 편집할 수 있는 표
edited_column_info = st.data_editor(
    column_info,
    use_container_width=True,
    hide_index=True,
    height=470,
    num_rows="fixed",
    disabled=["열 이름", "값의 종류", "빈 값 개수"],
    column_config={
        "열 이름": st.column_config.TextColumn(
            "열 이름",
            help="CSV에 저장된 원래 열 이름",
        ),
        "우리말 뜻": st.column_config.TextColumn(
            "우리말 뜻",
            help="셀을 클릭해 우리말 뜻을 입력하거나 수정하세요.",
            default="",
        ),
        "값의 종류": st.column_config.TextColumn(
            "값의 종류",
        ),
        "빈 값 개수": st.column_config.NumberColumn(
            "빈 값 개수",
            format="%d",
        ),
    },
    key="column_info_editor",
)

st.caption(
    "표에서 수정한 내용은 현재 앱 세션에 반영됩니다. "
    "CSV 원본 데이터 자체는 변경되지 않습니다."
)

# 수정한 우리말 뜻을 별도 CSV로 다운로드할 수 있도록 제공
st.download_button(
    label="📥 수정한 열 설명 다운로드",
    data=edited_column_info.to_csv(
        index=False
    ).encode("utf-8-sig"),
    file_name="열_설명.csv",
    mime="text/csv",
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
    "결측값을 임의로 채우거나 행을 삭제하지 않습니다."
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
    placeholder=(
        "교재를 참고해 데이터 출처, 제공 기관, "
        "참고 문헌 등을 입력하세요."
    ),
    height=120,
    key="data_source",
)

st.caption(
    "데이터 파일: "
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
)


