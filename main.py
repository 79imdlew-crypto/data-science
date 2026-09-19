import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ----------------------------------------
# 기본 설정
# ----------------------------------------
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)

BASE_YEAR = 1908
LAST_DATA_YEAR = 2025
MIN_OBSERVATIONS = 300


# ----------------------------------------
# 데이터 불러오기
# ----------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 필요한 숫자 열을 숫자형으로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 날짜 또는 평균기온이 없는 행 제거
    df = df.dropna(subset=["날짜", "평균기온"]).copy()

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    return df


# ----------------------------------------
# 연도별 데이터 계산
# ----------------------------------------
@st.cache_data
def make_yearly_data(df):
    # 2025년까지의 데이터만 사용
    df = df[df["연도"] <= LAST_DATA_YEAR].copy()

    # 연도별 관측일 수와 평균기온 계산
    yearly = (
        df.groupby("연도")
        .agg(
            관측일수=("평균기온", "count"),
            평균기온=("평균기온", "mean"),
        )
        .reset_index()
    )

    # 관측일이 300일 이상인 해만 사용
    yearly = yearly[yearly["관측일수"] >= MIN_OBSERVATIONS].copy()

    # 회귀의 독립 변수: 1908년부터 지난 연수
    yearly["지난연수"] = yearly["연도"] - BASE_YEAR

    return yearly.sort_values("연도").reset_index(drop=True)


df = load_data()
yearly = make_yearly_data(df)


# ----------------------------------------
# 회귀 계산
# ----------------------------------------
if len(yearly) < 2:
    st.error("회귀 직선을 계산할 수 있는 연도 데이터가 충분하지 않습니다.")
    st.stop()

x = yearly["지난연수"].to_numpy()
y = yearly["평균기온"].to_numpy()

# y = slope * x + intercept
slope, intercept = np.polyfit(x, y, 1)

# 상관계수
correlation = yearly["지난연수"].corr(yearly["평균기온"])


def predict_temperature(year):
    """주어진 연도의 회귀 예상 평균기온."""
    elapsed_years = year - BASE_YEAR
    return slope * elapsed_years + intercept


# ----------------------------------------
# 화면
# ----------------------------------------
st.title("🌡️ 기온 예측기")

st.markdown(
    """
서울의 일별 평균기온 데이터를 이용해 연평균기온을 계산하고,
연도와 평균기온의 선형 회귀를 이용해 기온을 예측합니다.
"""
)

# 데이터 기준 안내
st.info(
    f"분석 기준: 2025년까지의 데이터 중 관측일수가 "
    f"{MIN_OBSERVATIONS}일 이상인 연도만 사용"
)

# ----------------------------------------
# 슬라이더
# ----------------------------------------
selected_year = st.slider(
    "예측할 연도를 선택하세요",
    min_value=1900,
    max_value=2100,
    value=2025,
    step=1,
    format="%d년",
)

predicted_temp = predict_temperature(selected_year)

st.metric(
    label=f"{selected_year}년 예상 평균기온",
    value=f"{predicted_temp:.2f} °C",
)

# ----------------------------------------
# 회귀 정보
# ----------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("회귀에 사용한 연도 수", f"{len(yearly)}개")

with col2:
    st.metric("시작 연도", f"{yearly['연도'].min()}년")

with col3:
    st.metric("끝 연도", f"{yearly['연도'].max()}년")

with col4:
    st.metric("상관계수", f"{correlation:.3f}")


# ----------------------------------------
# 산점도 + 회귀 직선
# ----------------------------------------

# 그래프에서는 1900~2100년까지 회귀선을 표시
line_years = np.arange(1900, 2101)
line_temperatures = np.array(
    [predict_temperature(year) for year in line_years]
)

fig = go.Figure()

# 실제 연평균기온 산점도
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["평균기온"],
        mode="markers",
        name="실제 연평균기온",
        marker=dict(
            size=7,
            color="#1f77b4",
            opacity=0.8,
        ),
        customdata=yearly["관측일수"],
        hovertemplate=(
            "<b>%{x}년</b><br>"
            "평균기온: %{y:.2f} °C<br>"
            "관측일수: %{customdata}일"
            "<extra></extra>"
        ),
    )
)

# 회귀 직선
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_temperatures,
        mode="lines",
        name="회귀 직선",
        line=dict(
            color="#e74c3c",
            width=3,
        ),
        hovertemplate=(
            "<b>%{x}년</b><br>"
            "예상 평균기온: %{y:.2f} °C"
            "<extra></extra>"
        ),
    )
)

# 선택한 연도의 예측값 표시
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name=f"{selected_year}년 예측",
        marker=dict(
            size=14,
            color="#2ca02c",
            line=dict(
                color="white",
                width=2,
            ),
        ),
        hovertemplate=(
            f"<b>{selected_year}년</b><br>"
            f"예상 평균기온: {predicted_temp:.2f} °C"
            "<extra></extra>"
        ),
    )
)

fig.update_layout(
    title="서울 연평균기온과 선형 회귀",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    xaxis=dict(
        # 가로축에 연도를 그대로 표시
        tickmode="linear",
        dtick=10,
        range=[1900, 2100],
    ),
    hovermode="closest",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
    height=600,
)

st.plotly_chart(fig, width="stretch")


# ----------------------------------------
# 회귀식 및 데이터 설명
# ----------------------------------------
st.subheader("회귀식")

st.code(
    f"평균기온 = {slope:.6f} × (연도 - {BASE_YEAR}) + {intercept:.6f}"
)

st.caption(
    f"독립 변수는 '{BASE_YEAR}년부터 지난 연수'이며, "
    f"{yearly['연도'].min()}~{yearly['연도'].max()}년의 "
    f"연평균기온을 이용해 회귀 직선을 계산했습니다."
)

# ----------------------------------------
# 사용된 연도별 데이터
# ----------------------------------------
with st.expander("회귀에 사용된 연도별 데이터 보기"):
    display_df = yearly.copy()
    display_df["평균기온"] = display_df["평균기온"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
