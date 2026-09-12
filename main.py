
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"


# ---------------------------------
# 페이지 설정
# ---------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide",
)


# ---------------------------------
# 데이터 불러오기
# ---------------------------------
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
    df["first_scrn"] = pd.to_numeric(
        df["first_scrn"],
        errors="coerce",
    )

    df["total_audi"] = pd.to_numeric(
        df["total_audi"],
        errors="coerce",
    )

    return df


df = load_data()


# ---------------------------------
# 제목
# ---------------------------------
st.title("영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 "
    f"해당 기간에 개봉한 {len(df):,}편의 데이터를 살펴봅니다."
)


# =================================
# 그래프 1. 장르별 영화 편수
# =================================
st.header("1. 장르별 영화 편수")

genre_counts = (
    df["genre_first"]
    .value_counts()
    .rename_axis("장르")
    .reset_index(name="영화 편수")
)

fig1 = px.pie(
    genre_counts,
    names="장르",
    values="영화 편수",
    hole=0.55,
    title="장르별 영화 편수",
)

fig1.update_traces(
    textinfo="percent",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "영화 편수: %{value}편<br>"
        "비율: %{percent}<extra></extra>"
    ),
)

fig1.update_layout(
    showlegend=True,
    legend_title_text="장르",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(
    fig1,
    use_container_width=True,
)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    "여기에 장르별 영화 편수의 분포에서 발견한 특징을 한 문장으로 적어 보세요."
)


# =================================
# 그래프 2. 장르별 영화 트리맵
# =================================
st.header("2. 장르 안에 들어 있는 영화")

treemap_df = (
    df[
        [
            "genre_first",
            "movieNm",
            "total_audi",
        ]
    ]
    .dropna(subset=["total_audi"])
    .copy()
)

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

st.plotly_chart(
    fig2,
    use_container_width=True,
)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    "여기에 장르별로 어떤 영화가 큰 관객을 모았는지 한 문장으로 적어 보세요."
)


# =================================
# 그래프 3. 총 관객 히스토그램
# =================================
st.header("3. 총 관객 분포")

hist_df = (
    df[
        [
            "movieNm",
            "total_audi",
        ]
    ]
    .dropna(subset=["total_audi"])
    .copy()
)

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

st.plotly_chart(
    fig3,
    use_container_width=True,
)


# ---------------------------------
# 히스토그램에서 알 수 있는 내용 계산
# ---------------------------------
counts, bin_edges = np.histogram(
    hist_df["total_audi"],
    bins=20,
)

max_bin_index = counts.argmax()

bin_start = bin_edges[max_bin_index]
bin_end = bin_edges[max_bin_index + 1]

# 가장 관객이 많은 영화
top_movie = hist_df.loc[
    hist_df["total_audi"].idxmax()
]

top_movie_name = top_movie["movieNm"]
top_movie_audience = int(top_movie["total_audi"])


st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    f"대부분의 영화는 총 관객 약 "
    f"{bin_start:,.0f}명~{bin_end:,.0f}명 구간에 몰려 있으며, "
    f"가장 관객이 많은 영화는 **{top_movie_name}**으로 "
    f"총 관객은 **{top_movie_audience:,}명**입니다."
)


# =================================
# 그래프 4. 개봉일 스크린수와 총 관객
# =================================
st.header("4. 개봉일 스크린수와 총 관객의 관계")

scatter_df = (
    df[
        [
            "movieNm",
            "genre_first",
            "first_scrn",
            "total_audi",
        ]
    ]
    .dropna(
        subset=[
            "first_scrn",
            "total_audi",
        ]
    )
    .copy()
)

fig4 = px.scatter(
    scatter_df,
    x="first_scrn",
    y="total_audi",
    color="genre_first",
    hover_name="movieNm",
    title="개봉일 스크린수와 총 관객",
    labels={
        "first_scrn": "개봉일 스크린수",
        "total_audi": "총 관객",
        "genre_first": "장르",
    },
)

fig4.update_traces(
    marker=dict(
        size=9,
        opacity=0.75,
    ),
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "개봉일 스크린수: %{x:,.0f}개<br>"
        "총 관객: %{y:,.0f}명"
        "<extra></extra>"
    ),
)

fig4.update_layout(
    xaxis_title="개봉일 스크린수",
    yaxis_title="총 관객",
    legend_title_text="장르",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(
    fig4,
    use_container_width=True,
)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    "여기에 개봉일 스크린수와 총 관객 사이의 관계에서 발견한 특징을 한 문장으로 적어 보세요."
)


# =================================
# 그래프 5. 장르별 총 관객 상자 그림
# =================================
st.header("5. 장르별 총 관객 분포")

# 장르별 영화 편수가 10편 이상인 장르만 선택
genre_movie_counts = df["genre_first"].value_counts()

selected_genres = genre_movie_counts[
    genre_movie_counts >= 10
].index.tolist()

box_df = (
    df[
        [
            "genre_first",
            "movieNm",
            "total_audi",
        ]
    ]
    .dropna(subset=["total_audi"])
    .copy()
)

box_df = box_df[
    box_df["genre_first"].isin(selected_genres)
]


fig5 = px.box(
    box_df,
    x="genre_first",
    y="total_audi",
    points="outliers",
    hover_name="movieNm",
    title="영화가 10편 이상인 장르의 총 관객 분포",
    labels={
        "genre_first": "장르",
        "total_audi": "총 관객",
    },
)

fig5.update_traces(
    marker=dict(
        size=8,
        opacity=0.8,
    ),
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "총 관객: %{y:,.0f}명"
        "<extra></extra>"
    ),
)

fig5.update_layout(
    xaxis_title="장르",
    yaxis_title="총 관객",
    margin=dict(t=60, b=20, l=20, r=20),
)

st.plotly_chart(
    fig5,
    use_container_width=True,
)

st.markdown("---")

st.subheader("이 그래프로 알 수 있는 것")

st.info(
    "여기에 장르별 총 관객의 중앙값과 분포, 그리고 유난히 관객이 많은 영화의 특징을 한 문장으로 적어 보세요."
)

)
