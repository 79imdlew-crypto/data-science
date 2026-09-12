import re

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"


st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 장르가 여러 개이면 첫 번째 장르만 사용
    def first_genre(value):
        if pd.isna(value) or str(value).strip() == "":
            return "미분류"

        # 기본 데이터의 장르 구분자는 |이지만,
        # 일부 데이터에 /가 사용된 경우도 있어 함께 처리
        genre = re.split(r"[|]", str(value))[0].strip()

        return genre if genre else "미분류"

    df["genre_first"] = df["genre"].apply(first_genre)

    return df


# -----------------------------
# 데이터 불러오기
# -----------------------------
df = load_data()


# -----------------------------
# 제목
# -----------------------------
st.title("영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 "
    f"{len(df):,}편의 데이터를 살펴봅니다."
)


# -----------------------------
# 그래프 1. 장르별 영화 편수
# -----------------------------
st.header("1. 장르별 영화 편수")

genre_counts = (
    df["genre_first"]
    .value_counts()
    .rename_axis("장르")
    .reset_index(name="영화 편수")
)

fig = px.pie(
    genre_counts,
    names="장르",
    values="영화 편수",
    hole=0.55,
    title="장르별 영화 편수",
)

fig.update_traces(
    textinfo="percent",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "영화 편수: %{value}편<br>"
        "비율: %{percent}<extra></extra>"
    ),
)

fig.update_layout(
    showlegend=True,
    legend_title_text="장르",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")
st.info(
    "여기에 장르별 영화 편수의 분포에서 발견한 특징을 한 문장으로 적어 보세요."
)

