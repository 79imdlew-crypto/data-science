import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# 페이지 설정
# ============================================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide",
)

st.title("영화 데이터 그래프 도감 1 - 시간")


# ============================================================
# 데이터 불러오기 및 전처리
# ============================================================

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_daily.csv"
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜: YYYYMMDD → 실제 날짜 타입
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
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


df = load_data()


# ============================================================
# 그래프 1. 영화별 일관객 변화
# ============================================================

st.header("1. 영화별 일관객 변화")

movie_list = sorted(df["영화명"].dropna().unique())

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list,
)

movie_df = (
    df[df["영화명"] == selected_movie]
    .sort_values("날짜")
    .copy()
)

fig = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"〈{selected_movie}〉의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수",
    },
)

fig.update_traces(
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}"
        "<br>관객수: %{y:,}명"
        "<extra></extra>"
    )
)

fig.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수",
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것**")
st.text_input(
    "그래프 해석 문구를 입력하세요.",
    placeholder="예: 이 영화의 개봉 이후 날짜별 관객수 변화를 볼 수 있다.",
    key="graph1_description",
)


# ============================================================
# 그래프 2. 기간 전체 일관객 합계 TOP 5
# ============================================================

st.header("2. 기간 전체 일관객 합계 TOP 5")

# 영화별 기간 전체 일관객 합계 계산
top5_movies = (
    df.groupby("영화명", as_index=False)["일관객"]
    .sum()
    .sort_values("일관객", ascending=False)
    .head(5)["영화명"]
    .tolist()
)

# TOP 5 영화의 날짜별 일관객 데이터
top5_df = (
    df[df["영화명"].isin(top5_movies)]
    .groupby(["날짜", "영화명"], as_index=False)["일관객"]
    .sum()
    .sort_values(["날짜", "영화명"])
)

fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    title="기간 전체 일관객 합계가 가장 큰 5편의 날짜별 일관객",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수",
        "영화명": "영화",
    },
)

fig2.update_traces(
    hovertemplate=(
        "영화: %{fullData.name}"
        "<br>날짜: %{x|%Y-%m-%d}"
        "<br>관객수: %{y:,}명"
        "<extra></extra>"
    )
)

fig2.update_layout(
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    legend_title="영화",
)

st.plotly_chart(
    fig2,
    use_container_width=True,
)

st.markdown("**이 그래프로 알 수 있는 것**")
st.text_input(
    "그래프 해석 문구를 입력하세요.",
    placeholder="예: 기간 전체에서 관객을 가장 많이 모은 영화 5편의 일별 흥행 추이를 비교할 수 있다.",
    key="graph2_description",
)


# ============================================================
# 그래프 3. 날짜별 10위권 일관객 합계
# ============================================================

st.header("3. 날짜별 10위권 일관객 합계")

# 날짜별로 그날의 10위권 영화 일관객 합계 계산
daily_audience = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

# 일관객 합계가 가장 큰 날 3일
top3_days = (
    daily_audience
    .nlargest(3, "일관객")
    .sort_values("날짜")
)

# 영역 그래프
fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=daily_audience["날짜"],
        y=daily_audience["일관객"],
        mode="lines",
        fill="tozeroy",
        line=dict(
            color="#4C78A8",
            width=2,
        ),
        fillcolor="rgba(76, 120, 168, 0.25)",
        hovertemplate=(
            "날짜: %{x|%Y-%m-%d}"
            "<br>10위권 일관객 합계: %{y:,}명"
            "<extra></extra>"
        ),
        name="10위권 일관객 합계",
    )
)

# 상위 3일을 그래프 위에 표시
for _, row in top3_days.iterrows():
    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객"],
        text=(
            f"{row['날짜'].strftime('%Y-%m-%d')}"
            f"<br>{row['일관객']:,}명"
        ),
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor="#D62728",
        ax=0,
        ay=-50,
        bgcolor="white",
        bordercolor="#D62728",
        borderwidth=1,
        font=dict(
            color="#D62728",
            size=12,
        ),
    )

fig3.update_layout(
    title="날짜별 10위권 일관객 합계",
    xaxis_title="날짜",
    yaxis_title="10위권 일관객 합계",
    hovermode="x unified",
    showlegend=False,
)

st.plotly_chart(
    fig3,
    use_container_width=True,
)

st.markdown("**이 그래프로 알 수 있는 것**")
st.text_input(
    "그래프 해석 문구를 입력하세요.",
    placeholder="예: 날짜별로 전체 영화 시장의 관객 규모가 어떻게 변했는지 볼 수 있다.",
    key="graph3_description",
)


# ============================================================
# 그래프 4. 앞으로 추가할 영역
# ============================================================

st.header("4. 다음 그래프")

st.info("앞으로 새로운 그래프를 추가할 영역입니다.")

