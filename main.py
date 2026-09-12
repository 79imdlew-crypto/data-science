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

        genre = re.split(r"[|]", str(value))[0].strip()
        return genre if genre else "미분류"

    df["genre_first"] = df["genre"].apply(first_genre)

    # 숫자형 데이터로 변환
    df["total_audi"] = pd.to_numeric(df["total_audi"], errors="coerce")

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


# -----------------------------
# 그래프 2. 장르별 영화 트리맵
# -----------------------------
st.header("2. 장르 안에 들어 있는 영화")

treemap_df = df[
    ["genre_first", "movieNm", "total_audi"]
].dropna(subset=["total_audi"]).copy()

fig2 = px.treemap(
    treemap_df,
    path=["genre_first", "movieNm"],
    values="total_audi",
    title="장르별 영화와 총 관객",
)

fig2.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "총 관객: %{value:,.0f}명"
        "<extra></extra>"
    ),
)

fig2.update_layout(
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")
st.info(
    "여기에 장르별로 어떤 영화가 큰 관객을 모았는지 한 문장으로 적어 보세요."
)


# -----------------------------
# 그래프 3. 총 관객 히스토그램
# -----------------------------
st.header("3. 총 관객 분포")

hist_df = df.dropna(subset=["total_audi"]).copy()

fig3 = px.histogram(
    hist_df,
    x="total_audi",
    nbins=20,
    title="영화별 총 관객 분포",
    labels={
        "total_audi": "총 관객",
        "count": "영화 편수",
    },
)

fig3.update_traces(
    hovertemplate=(
        "총 관객 구간: %{x}<br>"
        "영화 편수: %{y}편"
        "<extra></extra>"
    )
)

fig3.update_layout(
    xaxis_title="총 관객",
    yaxis_title="영화 편수",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(fig3, use_container_width=True)


# -----------------------------
# 히스토그램에서 알 수 있는 것 계산
# -----------------------------

# 가장 많은 영화가 들어 있는 구간 계산
counts, bin_edges = pd.np.histogram(
    hist_df["total_audi"],
    bins=20,
)

max_bin_index = counts.argmax()

bin_start = bin_edges[max_bin_index]
bin_end = bin_edges[max_bin_index + 1]

# 가장 관객이 많은 영화
top_movie = hist_df.loc[hist_df["total_audi"].idxmax()]
top_movie_name = top_movie["movieNm"]
top_movie_audience = int(top_movie["total_audi"])


st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    f"대부분의 영화는 총 관객 약 {bin_start:,.0f}명~{bin_end:,.0f}명 구간에 "
    f"몰려 있으며, 가장 관객이 많은 영화는 **{top_movie_name}**으로 "
    f"총 관객은 **{top_movie_audience:,}명**입니다."
)
