import streamlit as st
import pandas as pd
import plotly.express as px


# ==================================================
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="탐색 | 뇌졸중 예측 실습실",
    page_icon="🔎",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)

REQUIRED_COLUMNS = [
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


# ==================================================
# 2. 데이터 불러오기
# ==================================================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )

    df = df[REQUIRED_COLUMNS].copy()

    # 분석에 사용하는 열을 숫자형으로 변환
    numeric_columns = [
        "age",
        "avg_glucose_level",
        "bmi",
        "hypertension",
        "heart_disease",
        "stroke",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


try:
    df = load_data()
except Exception as error:
    st.error(f"데이터를 불러오지 못했습니다: {error}")
    st.info("인터넷 연결, CSV 주소, 열 이름을 확인해 주세요.")
    st.stop()


# ==================================================
# 3. 제목 및 안내
# ==================================================
st.title("🔎 데이터 탐색")

st.markdown(
    """
    뇌졸중 데이터의 분포와 변수 사이의 관계를 살펴봅니다.
    그래프와 표를 통해 나이, 혈당, 고혈압, 심장병,
    BMI 결측 여부, 흡연 상태를 탐색해 봅시다.
    """
)

st.caption(f"분석 데이터: {len(df):,}명")

st.divider()


# ==================================================
# 4. 나이와 평균 혈당의 히스토그램
# ==================================================
st.header("1. 나이와 평균 혈당의 분포")

st.markdown(
    """
    히스토그램은 값이 어느 구간에 많이 분포하는지 보여 줍니다.
    두 그래프에서 사람들의 나이와 평균 혈당 분포를 비교해 보세요.
    """
)

col_age, col_glucose = st.columns(2)

with col_age:
    age_data = df[["age"]].dropna()

    fig_age = px.histogram(
        age_data,
        x="age",
        nbins=30,
        title="나이의 분포",
        labels={"age": "나이", "count": "사람 수"},
        color_discrete_sequence=["#4C78A8"],
    )

    fig_age.update_layout(
        xaxis_title="나이",
        yaxis_title="사람 수",
        bargap=0.08,
    )

    st.plotly_chart(fig_age, use_container_width=True)
    st.caption(f"나이 값이 있는 사람: {len(age_data):,}명")

with col_glucose:
    glucose_data = df[["avg_glucose_level"]].dropna()

    fig_glucose = px.histogram(
        glucose_data,
        x="avg_glucose_level",
        nbins=30,
        title="평균 혈당의 분포",
        labels={
            "avg_glucose_level": "평균 혈당",
            "count": "사람 수",
        },
        color_discrete_sequence=["#F58518"],
    )

    fig_glucose.update_layout(
        xaxis_title="평균 혈당",
        yaxis_title="사람 수",
        bargap=0.08,
    )

    st.plotly_chart(fig_glucose, use_container_width=True)
    st.caption(
        f"평균 혈당 값이 있는 사람: {len(glucose_data):,}명"
    )


st.divider()


# ==================================================
# 5. 뇌졸중 경험 여부에 따른 상자그림과 평균
# ==================================================
st.header("2. 뇌졸중 경험 여부에 따른 비교")

st.markdown(
    """
    뇌졸중 경험 여부(`stroke`)에 따라 두 집단을 나눕니다.

    - `0`: 뇌졸중을 겪지 않은 사람
    - `1`: 뇌졸중을 겪은 사람

    상자그림은 각 집단의 값이 퍼져 있는 범위와 중앙값을 비교하는 데
    도움이 됩니다. 아래 표에는 각 집단의 평균도 함께 표시합니다.
    """
)

stroke_labels = {
    0: "뇌졸중 없음 (0)",
    1: "뇌졸중 있음 (1)",
}

stroke_df = df[df["stroke"].isin([0, 1])].copy()
stroke_df["뇌졸중 경험"] = stroke_df["stroke"].map(stroke_labels)

col_box_age, col_box_glucose = st.columns(2)

with col_box_age:
    box_age_data = stroke_df[
        ["뇌졸중 경험", "age"]
    ].dropna()

    fig_box_age = px.box(
        box_age_data,
        x="뇌졸중 경험",
        y="age",
        color="뇌졸중 경험",
        category_orders={
            "뇌졸중 경험": [
                "뇌졸중 없음 (0)",
                "뇌졸중 있음 (1)",
            ]
        },
        title="뇌졸중 경험별 나이",
        labels={
            "뇌졸중 경험": "집단",
            "age": "나이",
        },
        color_discrete_map={
            "뇌졸중 없음 (0)": "#4C78A8",
            "뇌졸중 있음 (1)": "#E45756",
        },
    )

    fig_box_age.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="나이",
    )

    st.plotly_chart(fig_box_age, use_container_width=True)

with col_box_glucose:
    box_glucose_data = stroke_df[
        ["뇌졸중 경험", "avg_glucose_level"]
    ].dropna()

    fig_box_glucose = px.box(
        box_glucose_data,
        x="뇌졸중 경험",
        y="avg_glucose_level",
        color="뇌졸중 경험",
        category_orders={
            "뇌졸중 경험": [
                "뇌졸중 없음 (0)",
                "뇌졸중 있음 (1)",
            ]
        },
        title="뇌졸중 경험별 평균 혈당",
        labels={
            "뇌졸중 경험": "집단",
            "avg_glucose_level": "평균 혈당",
        },
        color_discrete_map={
            "뇌졸중 없음 (0)": "#4C78A8",
            "뇌졸중 있음 (1)": "#E45756",
        },
    )

    fig_box_glucose.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="평균 혈당",
    )

    st.plotly_chart(fig_box_glucose, use_container_width=True)


# 두 집단의 평균값 표
mean_rows = []

for stroke_value, label in stroke_labels.items():
    group = stroke_df[stroke_df["stroke"] == stroke_value]

    mean_rows.append({
        "뇌졸중 경험": label,
        "사람 수": len(group),
        "평균 나이": group["age"].mean(),
        "평균 혈당": group["avg_glucose_level"].mean(),
    })

mean_table = pd.DataFrame(mean_rows)

mean_table["평균 나이"] = mean_table["평균 나이"].round(2)
mean_table["평균 혈당"] = mean_table["평균 혈당"].round(2)

st.subheader("집단별 평균값")

st.dataframe(
    mean_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "사람 수": st.column_config.NumberColumn(
            "사람 수",
            format="%d",
        ),
        "평균 나이": st.column_config.NumberColumn(
            "평균 나이",
            format="%.2f",
        ),
        "평균 혈당": st.column_config.NumberColumn(
            "평균 혈당",
            format="%.2f",
        ),
    },
)

st.caption(
    "평균은 해당 변수에 결측값이 없는 사람을 대상으로 계산합니다. "
    "상자그림도 해당 변수의 결측값을 제외합니다."
)


st.divider()


# ==================================================
# 6. 고혈압과 심장병에 따른 뇌졸중 비율
# ==================================================
st.header("3. 고혈압과 심장병에 따른 뇌졸중 비율")

st.markdown(
    """
    각 집단에서 `stroke = 1`인 사람의 비율을 비교합니다.
    막대 높이는 인원수가 아니라 **집단 안의 뇌졸중 비율(%)**을 뜻합니다.
    """
)


def calculate_stroke_rate(data, group_column, labels):
    """집단별 인원수와 뇌졸중 비율을 계산한다."""
    subset = data[
        data[group_column].isin([0, 1])
        & data["stroke"].isin([0, 1])
    ].copy()

    result = (
        subset.groupby(group_column, observed=True)
        .agg(
            사람수=("stroke", "size"),
            뇌졸중_인원=("stroke", "sum"),
            뇌졸중_비율=("stroke", "mean"),
        )
        .reset_index()
    )

    result["집단"] = result[group_column].map(labels)
    result["뇌졸중 비율(%)"] = result["뇌졸중_비율"] * 100

    return result


binary_labels = {
    0: "없음 (0)",
    1: "있음 (1)",
}

col_hyper, col_heart = st.columns(2)

with col_hyper:
    hyper_data = calculate_stroke_rate(
        df,
        "hypertension",
        binary_labels,
    )

    fig_hyper = px.bar(
        hyper_data,
        x="집단",
        y="뇌졸중 비율(%)",
        text=hyper_data["뇌졸중 비율(%)"].map(
            lambda value: f"{value:.2f}%"
        ),
        title="고혈압 여부에 따른 뇌졸중 비율",
        labels={
            "집단": "고혈압",
            "뇌졸중 비율(%)": "뇌졸중 비율(%)",
        },
        color="집단",
        category_orders={"집단": ["없음 (0)", "있음 (1)"]},
        color_discrete_map={
            "없음 (0)": "#4C78A8",
            "있음 (1)": "#E45756",
        },
        hover_data={
            "사람수": True,
            "뇌졸중_인원": True,
            "뇌졸중 비율(%)": ":.2f",
            "뇌졸중_비율": False,
        },
    )

    fig_hyper.update_traces(textposition="outside", cliponaxis=False)
    fig_hyper.update_layout(
        showlegend=False,
        xaxis_title="고혈압 여부",
        yaxis_title="뇌졸중 비율(%)",
        yaxis_ticksuffix="%",
    )

    st.plotly_chart(fig_hyper, use_container_width=True)

with col_heart:
    heart_data = calculate_stroke_rate(
        df,
        "heart_disease",
        binary_labels,
    )

    fig_heart = px.bar(
        heart_data,
        x="집단",
        y="뇌졸중 비율(%)",
        text=heart_data["뇌졸중 비율(%)"].map(
            lambda value: f"{value:.2f}%"
        ),
        title="심장병 여부에 따른 뇌졸중 비율",
        labels={
            "집단": "심장병",
            "뇌졸중 비율(%)": "뇌졸중 비율(%)",
        },
        color="집단",
        category_orders={"집단": ["없음 (0)", "있음 (1)"]},
        color_discrete_map={
            "없음 (0)": "#4C78A8",
            "있음 (1)": "#E45756",
        },
        hover_data={
            "사람수": True,
            "뇌졸중_인원": True,
            "뇌졸중 비율(%)": ":.2f",
            "뇌졸중_비율": False,
        },
    )

    fig_heart.update_traces(textposition="outside", cliponaxis=False)
    fig_heart.update_layout(
        showlegend=False,
        xaxis_title="심장병 여부",
        yaxis_title="뇌졸중 비율(%)",
        yaxis_ticksuffix="%",
    )

    st.plotly_chart(fig_heart, use_container_width=True)


st.caption(
    "비율은 각 집단에서 뇌졸중 여부가 확인된 사람을 기준으로 계산합니다. "
    "집단별 사람 수도 막대 위에 마우스를 올려 확인할 수 있습니다."
)


st.divider()


# ==================================================
# 7. BMI 결측자와 전체의 뇌졸중 비율 비교
# ==================================================
st.header("4. BMI 빈 값과 뇌졸중 비율")

st.markdown(
    """
    BMI가 비어 있는 사람만 별도로 모아 그 집단의 뇌졸중 비율을 계산하고,
    전체 데이터의 비율과 나란히 비교합니다.
    """
)

bmi_missing_df = df[df["bmi"].isna()].copy()

valid_stroke_all = df[df["stroke"].isin([0, 1])]
valid_stroke_missing_bmi = bmi_missing_df[
    bmi_missing_df["stroke"].isin([0, 1])
]


def summarize_stroke_rate(data, group_name):
    count = len(data)

    if count == 0:
        stroke_count = 0
        rate = None
    else:
        stroke_count = int((data["stroke"] == 1).sum())
        rate = stroke_count / count * 100

    return {
        "대상": group_name,
        "사람 수": count,
        "뇌졸중 인원": stroke_count,
        "뇌졸중 비율(%)": rate,
    }


bmi_comparison = pd.DataFrame([
    summarize_stroke_rate(
        valid_stroke_missing_bmi,
        "BMI가 비어 있는 사람",
    ),
    summarize_stroke_rate(
        valid_stroke_all,
        "전체 사람",
    ),
])

bmi_comparison["뇌졸중 비율(%)"] = (
    bmi_comparison["뇌졸중 비율(%)"].round(2)
)

st.metric(
    "BMI가 비어 있는 사람 수",
    f"{len(bmi_missing_df):,}명",
)

st.dataframe(
    bmi_comparison,
    use_container_width=True,
    hide_index=True,
    column_config={
        "사람 수": st.column_config.NumberColumn(
            "사람 수",
            format="%d",
        ),
        "뇌졸중 인원": st.column_config.NumberColumn(
            "뇌졸중 인원",
            format="%d",
        ),
        "뇌졸중 비율(%)": st.column_config.NumberColumn(
            "뇌졸중 비율(%)",
            format="%.2f%%",
        ),
    },
)

st.caption(
    "뇌졸중 비율은 stroke가 0 또는 1로 확인되는 행을 기준으로 계산합니다. "
    "BMI 결측자 수와 비율 계산에 사용된 사람 수는 "
    "stroke 값이 비어 있는 경우 서로 다를 수 있습니다."
)


st.divider()


# ==================================================
# 8. 흡연 상태별 사람 수
# ==================================================
st.header("5. 흡연 상태별 사람 수")

st.markdown(
    """
    흡연 상태(`smoking_status`)의 값마다 해당하는 사람 수를 집계합니다.
    흡연 상태가 비어 있는 사람도 별도로 표시합니다.
    """
)

smoking_data = df["smoking_status"].fillna("빈 값")
smoking_counts = (
    smoking_data.value_counts(dropna=False)
    .rename_axis("흡연 상태")
    .reset_index(name="사람 수")
)

# 보기 편하게 사람 수가 많은 순서로 정렬
smoking_counts = smoking_counts.sort_values(
    by=["사람 수", "흡연 상태"],
    ascending=[False, True],
    kind="mergesort",
).reset_index(drop=True)

st.dataframe(
    smoking_counts,
    use_container_width=True,
    hide_index=True,
    column_config={
        "사람 수": st.column_config.NumberColumn(
            "사람 수",
            format="%d",
        ),
    },
)

st.caption(
    "빈 값은 smoking_status가 결측인 행을 뜻합니다."
)

