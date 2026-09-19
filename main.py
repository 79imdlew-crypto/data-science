import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ---------------------------------------------------------
# 설정
# ---------------------------------------------------------
DAILY_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/"
    "kobis_daily.csv"
)
MOVIES_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/"
    "kobis_movies.csv"
)

st.set_page_config(
    page_title="영화 흥행 예측기",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 영화 흥행 예측기")
st.caption("KOBIS 영화별 데이터를 이용한 다중 선형회귀 예측")


# ---------------------------------------------------------
# 데이터 읽기
# ---------------------------------------------------------
@st.cache_data
def load_data():
    daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    movies = pd.read_csv(MOVIES_URL, encoding="utf-8")
    return daily, movies


try:
    daily, movies = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()


# ---------------------------------------------------------
# 컬럼 확인 및 이름 정리
# ---------------------------------------------------------
# 일별 데이터의 컬럼명이 사용자 설명처럼 한글일 수도 있고,
# 파일에 따라 영문 표기가 있을 가능성도 고려한다.
daily_column_map = {
    "날짜": "date",
    "순위": "rank",
    "영화코드": "movieCd",
    "영화명": "movieNm",
    "일관객": "daily_audi",
    "누적관객": "acc_audi",
    "스크린수": "screens",
    "상영횟수": "show_count",
}

for old, new in daily_column_map.items():
    if old in daily.columns:
        daily = daily.rename(columns={old: new})

required_daily = {"date", "movieCd"}
required_movies = {"movieCd", "total_audi"}

missing_daily = required_daily - set(daily.columns)
missing_movies = required_movies - set(movies.columns)

if missing_daily:
    st.error(f"일별 데이터에 필요한 열이 없습니다: {sorted(missing_daily)}")
    st.stop()

if missing_movies:
    st.error(f"영화별 데이터에 필요한 열이 없습니다: {sorted(missing_movies)}")
    st.stop()


# ---------------------------------------------------------
# 기준 기간
# ---------------------------------------------------------
date_numeric = pd.to_numeric(daily["date"], errors="coerce")
valid_dates = date_numeric.dropna()

if len(valid_dates) > 0:
    min_date = pd.to_datetime(
        valid_dates.astype(int).astype(str),
        format="%Y%m%d",
        errors="coerce",
    ).min()

    max_date = pd.to_datetime(
        valid_dates.astype(int).astype(str),
        format="%Y%m%d",
        errors="coerce",
    ).max()

    period_text = (
        f"{min_date.strftime('%Y-%m-%d')} ~ "
        f"{max_date.strftime('%Y-%m-%d')}"
    )
else:
    period_text = "기간을 확인할 수 없음"


# ---------------------------------------------------------
# 영화별 데이터 준비
# ---------------------------------------------------------
movies = movies.copy()

# 영화코드는 정렬을 위해 문자열로 통일
movies["movieCd"] = movies["movieCd"].astype(str).str.strip()

# 숫자로 처리해야 하는 주요 변수
numeric_candidates = [
    "first_scrn",
    "first_show",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10",
]

for col in numeric_candidates:
    if col in movies.columns:
        movies[col] = pd.to_numeric(movies[col], errors="coerce")

# 날짜형 변수는 모델에서 사용할 수 있도록 연/월/일 형태의 숫자로 변환
for col in ["openDt", "first_date"]:
    if col in movies.columns:
        parsed = pd.to_datetime(
            movies[col].astype(str),
            format="%Y%m%d",
            errors="coerce",
        )
        movies[f"{col}_year"] = parsed.dt.year
        movies[f"{col}_month"] = parsed.dt.month
        movies[f"{col}_day"] = parsed.dt.day

# ---------------------------------------------------------
# 영화별 표의 맨 위 행 그대로 표시
# ---------------------------------------------------------
st.subheader("영화별 데이터의 첫 번째 행")

# 원본 파일에서 읽은 행을 그대로 보여준다.
st.dataframe(
    movies.head(1),
    use_container_width=True,
)

st.info(f"일별 데이터 기준 기간: **{period_text}**")


# ---------------------------------------------------------
# 사용할 변수 선택
# ---------------------------------------------------------
st.subheader("예측 변수 선택")

# 목표변수와 식별용 컬럼은 예측변수 후보에서 제외
excluded = {
    "movieCd",
    "movieNm",
    "total_audi",
    "openDt",
    "first_date",
}

candidate_features = [
    col for col in movies.columns
    if col not in excluded
    and not col.endswith("_year")
    and not col.endswith("_month")
    and not col.endswith("_day")
]

# 날짜에서 만든 숫자 변수는 별도 후보로 포함
date_features = [
    col
    for col in movies.columns
    if col.endswith("_year")
    or col.endswith("_month")
    or col.endswith("_day")
]

candidate_features = candidate_features + date_features

# 실제 존재하는 컬럼만 사용
candidate_features = [
    col for col in candidate_features
    if col in movies.columns
]

if not candidate_features:
    st.error("선택할 수 있는 예측 변수가 없습니다.")
    st.stop()

# 기본적으로 전부 선택
selected_features = st.multiselect(
    "학습에 사용할 변수를 선택하세요.",
    options=candidate_features,
    default=candidate_features,
)

if not selected_features:
    st.warning("예측 변수를 하나 이상 선택하세요.")
    st.stop()


# ---------------------------------------------------------
# 영화코드 순 정렬
# ---------------------------------------------------------
model_df = movies.copy()

# 영화코드 순으로 정렬
model_df = model_df.sort_values(
    by="movieCd",
    kind="mergesort",
).reset_index(drop=True)

# 총 관객 수가 없는 영화는 학습/평가가 불가능하므로 제외하지 않고
# 우선 전체 영화 수를 기록한 뒤, target이 있는 행만 모델 계산에 사용한다.
all_movie_count = len(model_df)

model_df["total_audi"] = pd.to_numeric(
    model_df["total_audi"],
    errors="coerce",
)

model_df = model_df.dropna(
    subset=["total_audi"]
).reset_index(drop=True)


# ---------------------------------------------------------
# 10편마다 앞 3편 테스트 / 나머지 학습
# ---------------------------------------------------------
test_mask = np.zeros(len(model_df), dtype=bool)

for start in range(0, len(model_df), 10):
    end = min(start + 10, len(model_df))

    # 각 10편 묶음의 앞 3편
    test_mask[start:min(start + 3, end)] = True

test_df = model_df.loc[test_mask].copy()
train_df = model_df.loc[~test_mask].copy()

if len(train_df) == 0:
    st.error("학습에 사용할 영화가 없습니다.")
    st.stop()

if len(test_df) == 0:
    st.error("평가에 사용할 영화가 없습니다.")
    st.stop()


# ---------------------------------------------------------
# 전처리 + 다중 선형회귀
# ---------------------------------------------------------
X_train = train_df[selected_features]
y_train = train_df["total_audi"]

X_test = test_df[selected_features]
y_test = test_df["total_audi"]

numeric_features = [
    col for col in selected_features
    if pd.api.types.is_numeric_dtype(model_df[col])
]

categorical_features = [
    col for col in selected_features
    if col not in numeric_features
]

numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent",
            ),
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
        ),
    ]
)

transformers = []

if numeric_features:
    transformers.append(
        (
            "numeric",
            numeric_pipeline,
            numeric_features,
        )
    )

if categorical_features:
    transformers.append(
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        )
    )

preprocessor = ColumnTransformer(
    transformers=transformers,
    remainder="drop",
)

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regression", LinearRegression()),
    ]
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

# 실제 관객 수는 음수가 될 수 없으므로
# 평가용 예측값 자체도 음수이면 0으로 제한한다.
pred = np.maximum(pred, 0)


# ---------------------------------------------------------
# 평가 지표
# ---------------------------------------------------------
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))

# MAPE는 실제값이 0인 경우를 제외
nonzero = y_test.to_numpy() != 0

if nonzero.any():
    mape = (
        np.mean(
            np.abs(
                (
                    y_test.to_numpy()[nonzero]
                    - pred[nonzero]
                )
                / y_test.to_numpy()[nonzero]
            )
        )
        * 100
    )
else:
    mape = np.nan


# ---------------------------------------------------------
# 화면 요약
# ---------------------------------------------------------
st.subheader("학습 및 평가 결과")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "학습에 사용한 영화",
    f"{len(train_df):,}편",
)

col2.metric(
    "평가한 영화",
    f"{len(test_df):,}편",
)

col3.metric(
    "R²",
    f"{r2:.4f}",
)

col4.metric(
    "MAE",
    f"{mae:,.0f}명",
)

st.write(
    f"**기준 기간:** {period_text}  \n"
    f"**전체 영화:** {all_movie_count:,}편  \n"
    f"**학습 영화:** {len(train_df):,}편  \n"
    f"**평가 영화:** {len(test_df):,}편  \n"
    f"**RMSE:** {rmse:,.0f}명  ·  "
    f"**MAPE:** {mape:.2f}%"
    if not np.isnan(mape)
    else
    f"**기준 기간:** {period_text}  \n"
    f"**전체 영화:** {all_movie_count:,}편  \n"
    f"**학습 영화:** {len(train_df):,}편  \n"
    f"**평가 영화:** {len(test_df):,}편  \n"
    f"**RMSE:** {rmse:,.0f}명  ·  **MAPE:** 계산 불가"
)


# ---------------------------------------------------------
# 평가 결과 표
# ---------------------------------------------------------
result_df = test_df[
    ["movieCd"] +
    ([c for c in ["movieNm"] if c in test_df.columns])
].copy()

result_df["실제 총 관객 수"] = y_test.to_numpy()
result_df["예측 총 관객 수"] = pred
result_df["절대 오차"] = np.abs(
    result_df["실제 총 관객 수"]
    - result_df["예측 총 관객 수"]
)

result_df["오차율(%)"] = np.where(
    result_df["실제 총 관객 수"] != 0,
    result_df["절대 오차"]
    / result_df["실제 총 관객 수"]
    * 100,
    np.nan,
)

result_df = result_df.sort_values(
    "movieCd",
    kind="mergesort",
).reset_index(drop=True)

st.subheader("테스트 영화별 실제값 / 예측값")

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# 1,000명 미만 예측 영화
# ---------------------------------------------------------
low_prediction_mask = pred < 1000
low_prediction_count = int(low_prediction_mask.sum())

st.write(
    f"**예측 총 관객 수가 1,000명보다 작은 영화: "
    f"{low_prediction_count}편**"
)


# ---------------------------------------------------------
# Plotly 산점도
# ---------------------------------------------------------
st.subheader("실제 관객 수 vs 예측 관객 수")

actual = np.asarray(y_test, dtype=float)
predicted = np.asarray(pred, dtype=float)

# 로그축에서는 0 이하를 표시할 수 없으므로
# 실제값/예측값이 1명 미만인 경우 1명으로 처리한다.
actual_plot = np.maximum(actual, 1)
pred_plot = np.maximum(predicted, 1)

# 요구사항:
# 예측값이 1,000명보다 작으면 그래프 바닥(1,000)에 붙인다.
pred_plot_floor = np.maximum(pred_plot, 1000)

# 대각선의 범위
axis_min = max(
    1,
    min(actual_plot.min(), pred_plot_floor.min()),
)

axis_max = max(
    actual_plot.max(),
    pred_plot_floor.max(),
)

fig = go.Figure()

# 실제값-예측값 점
fig.add_trace(
    go.Scatter(
        x=actual_plot,
        y=pred_plot_floor,
        mode="markers",
        marker=dict(
            size=9,
            color="#1f77b4",
            opacity=0.75,
        ),
        text=(
            result_df["movieNm"]
            if "movieNm" in result_df.columns
            else result_df["movieCd"]
        ),
        customdata=np.column_stack(
            [
                result_df["movieCd"].to_numpy(),
                actual,
                predicted,
                result_df["절대 오차"].to_numpy(),
            ]
        ),
        hovertemplate=(
            "영화코드: %{customdata[0]}<br>"
            "영화명: %{text}<br>"
            "실제: %{customdata[1]:,.0f}명<br>"
            "예측: %{customdata[2]:,.0f}명<br>"
            "절대 오차: %{customdata[3]:,.0f}명"
            "<extra></extra>"
        ),
        name="테스트 영화",
    )
)

# y = x 대각선
fig.add_trace(
    go.Scatter(
        x=[axis_min, axis_max],
        y=[axis_min, axis_max],
        mode="lines",
        line=dict(
            color="red",
            dash="dash",
            width=2,
        ),
        name="실제값 = 예측값",
    )
)

fig.update_layout(
    xaxis=dict(
        title="실제 총 관객 수",
        type="log",
        range=[
            np.log10(axis_min),
            np.log10(axis_max),
        ],
    ),
    yaxis=dict(
        title="예측 총 관객 수",
        type="log",
        range=[
            np.log10(max(1, min(1000, axis_min))),
            np.log10(axis_max),
        ],
    ),
    height=650,
    hovermode="closest",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ---------------------------------------------------------
# 선택 변수 / 데이터 분할 정보
# ---------------------------------------------------------
with st.expander("모델에 사용한 변수와 데이터 분할 규칙"):
    st.write("**선택한 예측 변수**")
    st.write(selected_features)

    st.write(
        "**데이터 분할:** 영화코드를 오름차순 정렬한 뒤 "
        "10편마다 앞 3편을 테스트용으로 사용하고, "
        "나머지를 학습용으로 사용했습니다."
    )

    st.write(
        f"학습: {len(train_df):,}편 / "
        f"테스트: {len(test_df):,}편"
    )

