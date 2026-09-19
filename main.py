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
RECENT_YEARS = 20


# ----------------------------------------
# 데이터 불러오기
# ----------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"]).copy()
    df["연도"] = df["날짜"].dt.year

    return df


# ----------------------------------------
# 연도별 데이터 계산
# ----------------------------------------
@st.cache_data
def make_yearly_data(df):
    # 2025년까지의 데이터만 사용
    df = df[df["연도"] <= LAST_DATA_YEAR].copy()

    yearly = (
        df.groupby("연도")
        .agg(
            관측일수=("평균기온", "count"),
            평균기온=("평균기온", "mean"),
        )
        .reset_index()
    )

    # 관측일수가 300일 이상인 해만 사용
    yearly = yearly[
        yearly["관측일수"] >= MIN_OBSERVATIONS
    ].copy()

    # 1908년부터 지난 연수
    yearly["지난연수"] = yearly["연도"] - BASE_YEAR

    return yearly.sort_values("연도").reset_index(drop=True)


df = load_data()
yearly = make_yearly_data(df)

if len(yearly) < 2:
    st.error("회귀 직선을 계산할 수 있는 연도 데이터가 충분하지 않습니다.")
    st.stop()


# ----------------------------------------
# 회귀 계산 함수
# ----------------------------------------
def calculate_regression(data):
    x = data["지난연수"].to_numpy()
    y = data["평균기온"].to_numpy()

    slope, intercept = np.polyfit(x, y, 1)
    correlation = data["지난연수"].corr(data["평균기온"])

    # 1년당 기온 변화량 → 100년당 기온 변화량
    slope_per_100_years = slope * 100

    return slope, intercept, correlation, slope_per_100_years


# 전체 기간 회귀
overall_slope, overall_intercept, overall_corr, overall_100 = (
    calculate_regression(yearly)
)


# ----------------------------------------
# 최근 20년 데이터
# ----------------------------------------
overall_end_year = yearly["연도"].max()
recent_start_year = overall_end_year - RECENT_YEARS + 1

recent = yearly[
    (yearly["연도"] >= recent_start_year)
    & (yearly["연도"] <= overall_end_year)
].copy()

# 최근 20년 중 실제 데이터가 2개 이상일 때 회귀
if len(recent) >= 2:
    recent_slope, recent_intercept, recent_corr, recent_100 = (
        calculate_regression(recent)
    )
else:
    recent_slope = np.nan
    recent_intercept = np.nan
    recent_corr = np.nan
    recent_100 = np.nan


# ----------------------------------------
# 예측 함수
# ----------------------------------------
def predict_temperature(year):
    elapsed_years = year - BASE_YEAR
    return overall_slope * elapsed_years + overall_intercept


# ----------------------------------------
# 화면
# ----------------------------------------
st.title("🌡️ 기온 예측기")

st.markdown(
    """
서울의 일별 평균기온을 이용해 연평균기온을 계산하고,
연도와 평균기온의 선형 회귀를 이용해 미래 기온을 예측합니다.
"""
)

st.info(
    f"분석 기준: {LAST_DATA_YEAR}년까지의 데이터 중 "
    f"관측일수가 {MIN_OBSERVATIONS}일 이상인 연도만 사용"
)


# ----------------------------------------
# 100년당 상승폭 — 크게 표시
# ----------------------------------------
st.subheader("📈 100년에 몇 °C 오르는가?")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="전체 기간의 100년당 기온 변화",
        value=f"{overall_100:+.2f} °C / 100년",
        border=True,
    )

with col2:
    if np.isnan(recent_100):
        st.metric(
            label=f"최근 {RECENT_YEARS}년의 100년당 기온 변화",
            value="계산 불가",
            border=True,
        )
    else:
        st.metric(
            label=f"최근 {RECENT_YEARS}년의 100년당 기온 변화",
            value=f"{recent_100:+.2f} °C / 100년",
            border=True,
        )


# ----------------------------------------
# 전체 기간 vs 최근 20년 비교
# ----------------------------------------
st.subheader("전체 기간과 최근 20년의 기울기 비교")

comparison = pd.DataFrame(
    {
        "구간": [
            "전체 기간",
            f"최근 {RECENT_YEARS}년",
        ],
        "시작 연도": [
            int(yearly["연도"].min()),
            int(recent["연도"].min()) if len(recent) else None,
        ],
        "끝 연도": [
            int(yearly["연도"].max()),
            int(recent["연도"].max()) if len(recent) else None,
        ],
        "사용 연도 수": [
            len(yearly),
            len(recent),
        ],
        "100년당 변화": [
            f"{overall_100:+.2f} °C",
            f"{recent_100:+.2f} °C"
            if not np.isnan(recent_100)
            else "계산 불가",
        ],
        "상관계수": [
            f"{overall_corr:.3f}",
            f"{recent_corr:.3f}"
            if not np.isnan(recent_corr)
            else "계산 불가",
        ],
    }
)

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True,
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
# 기존 회귀 정보
# ----------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "회귀에 사용한 연도 수",
        f"{len(yearly)}개",
    )

with col2:
    st.metric(
        "시작 연도",
        f"{yearly['연도'].min()}년",
    )

with col3:
    st.metric(
        "끝 연도",
        f"{yearly['연도'].max()}년",
    )

with col4:
    st.metric(
        "전체 기간 상관계수",
        f"{overall_corr:.3f}",
    )


# ----------------------------------------
# 그래프
# ----------------------------------------
line_years = np.arange(1900, 2101)
line_temperatures = np.array(
    [predict_temperature(year) for year in line_years]
)

fig = go.Figure()

# 실제 연평균기온
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

# 전체 기간 회귀 직선
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_temperatures,
        mode="lines",
        name="전체 기간 회귀 직선",
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

# 선택한 연도의 예측값
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
    title="서울 연평균기온과 전체 기간 선형 회귀",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    xaxis=dict(
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
# 회귀식
# ----------------------------------------
st.subheader("전체 기간 회귀식")

st.code(
    f"평균기온 = {overall_slope:.6f} × (연도 - {BASE_YEAR}) "
    f"+ {overall_intercept:.6f}"
)

st.caption(
    f"전체 회귀는 {yearly['연도'].min()}~{yearly['연도'].max()}년의 "
    f"연평균기온을 사용했습니다. "
    f"기울기 {overall_slope:.6f} °C/년을 100배하여 "
    f"100년당 {overall_100:+.2f} °C로 표시합니다."
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
