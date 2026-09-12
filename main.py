import streamlit as st
import pandas as pd
import plotly.express as px


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_daily.csv"
)


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜 열을 실제 날짜 타입으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d",
    )

    # 숫자형 열 변환
    numeric_columns = [
        "순위",
        "영화코드",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


df = load_data()


# --------------------------------------------------
# 제목
# --------------------------------------------------
st.title("🎬 영화 데이터 그래프 도감 1 - 시간")

st.write(
    "영화별 일별 관객 변화를 시간의 흐름에 따라 살펴봅니다."
)


# ==================================================
# 그래프 1. 영화별 일관객 변화
# ==================================================
st.header("1. 영화별 일관객 변화")

movie_list = sorted(df["영화명"].dropna().unique())

selected_movie = st.selectbox(
    "영화를 선택하세요",
    movie_list,
)

movie_df = (
    df[df["영화명"] == selected_movie]
    .sort_values("날짜")
    .copy()
)

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"「{selected_movie}」 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객",
    },
)

fig1.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>일관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig1.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수",
)

st.plotly_chart(
    fig1,
    use_container_width=True,
)

st.info(
    "이 그래프로 알 수 있는 것: "
    "영화의 일별 관객 수가 시간의 흐름에 따라 어떻게 변하는지 확인할 수 있습니다."
)


# ==================================================
# 그래프 2. 일관객 합계가 가장 큰 영화 5편
# ==================================================
st.header("2. 일관객 합계가 가장 큰 영화 5편")

top5_movies = (
    df.groupby("영화명", as_index=False)["일관객"]
    .sum()
    .sort_values("일관객", ascending=False)
    .head(5)["영화명"]
    .tolist()
)

top5_df = (
    df[df["영화명"].isin(top5_movies)]
    .sort_values(["날짜", "영화명"])
    .copy()
)

fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계 상위 5편의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객",
        "영화명": "영화",
    },
)

fig2.update_traces(
    hovertemplate=(
        "영화: %{fullData.name}"
        "<br>날짜: %{x|%Y-%m-%d}"
        "<br>일관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig2.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    legend_title="영화",
    legend=dict(
        itemclick="toggle",
        itemdoubleclick="toggleothers",
    ),
)

st.plotly_chart(
    fig2,
    use_container_width=True,
)

st.info(
    "이 그래프로 알 수 있는 것: "
    "전체 기간 동안 관객을 많이 모은 영화 5편의 흥행 추이를 서로 비교할 수 있습니다."
)


# ==================================================
# 그래프 3. 날짜별 전체 10위권 일관객 합계
# ==================================================
st.header("3. 날짜별 전체 10위권 일관객 합계")

daily_total = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
    .rename(columns={"일관객": "일관객합계"})
)

top3_days = (
    daily_total
    .nlargest(3, "일관객합계")
    .sort_values("날짜")
)

fig3 = px.area(
    daily_total,
    x="날짜",
    y="일관객합계",
    title="날짜별 10위권 일관객 합계",
    labels={
        "날짜": "날짜",
        "일관객합계": "10위권 일관객 합계",
    },
)

fig3.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>10위권 일관객 합계: %{y:,}명"
        "<extra></extra>"
    )
)

for _, row in top3_days.iterrows():
    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객합계"],
        text=row["날짜"].strftime("%Y-%m-%d"),
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor="#d62728",
        ax=0,
        ay=-45,
        font=dict(
            color="#d62728",
            size=12,
        ),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="#d62728",
        borderwidth=1,
    )

fig3.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="10위권 일관객 합계",
)

st.plotly_chart(
    fig3,
    use_container_width=True,
)

st.info(
    "이 그래프로 알 수 있는 것: "
    "날짜별 영화관 전체 흥행 규모의 변화와 관객이 가장 많이 몰린 날을 한눈에 볼 수 있습니다."
)


# ==================================================
# 그래프 4. 영화별 기간 누적 일관객 TOP 10
# ==================================================
st.header("4. 영화별 기간 누적 일관객 TOP 10")

# 영화별 기간 전체 일관객 합계
movie_total = (
    df.groupby("영화명")
    .agg(
        일관객합계=("일관객", "sum"),
        top10_일수=("날짜", "nunique"),
    )
    .reset_index()
)

# 관객 합계 기준 TOP 10
top10_movies = (
    movie_total
    .sort_values("일관객합계", ascending=False)
    .head(10)
    .sort_values("일관객합계", ascending=True)
)

fig4 = px.bar(
    top10_movies,
    x="일관객합계",
    y="영화명",
    orientation="h",
    title="영화별 기간 누적 일관객 TOP 10",
    labels={
        "일관객합계": "기간 누적 일관객",
        "영화명": "영화",
    },
)

fig4.update_traces(
    marker_color="#4C78A8",
    customdata=top10_movies[["top10_일수"]].to_numpy(),
    hovertemplate=(
        "영화: %{y}"
        "<br>기간 누적 일관객: %{x:,}명"
        "<br>10위권에 든 날수: %{customdata[0]}일"
        "<extra></extra>"
    ),
)

fig4.update_layout(
    xaxis_title="기간 누적 일관객",
    yaxis_title="영화",
    yaxis=dict(
        categoryorder="array",
        categoryarray=top10_movies["영화명"].tolist(),
    ),
)

st.plotly_chart(
    fig4,
    use_container_width=True,
)

st.info(
    "이 그래프로 알 수 있는 것: "
    "이 기간 동안 가장 많은 관객을 모은 영화와 10위권에 머문 기간을 함께 비교할 수 있습니다."
)


# ==================================================
# 그래프 5. 앞으로 추가할 공간
# ==================================================
st.header("5. 다음 그래프")

st.write(
    "추가 그래프를 위한 공간입니다."
)

st.info(
    "이 그래프로 알 수 있는 것: "
    "여기에 다섯 번째 그래프에서 발견할 수 있는 내용을 적습니다."
)

