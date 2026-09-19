import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/data/"
    "kobis_movies.csv"
)

st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 영화 유형 나누기")


# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data
def load_data():
    columns = [
        "movieCd",
        "movieNm",
        "openDt",
        "genre",
        "nation",
        "first_scrn",
        "first_show",
        "first_date",
        "peak",
        "first_week_audi",
        "total_audi",
        "days_in_top10",
    ]

    df = pd.read_csv(DATA_URL, encoding="utf-8")
    return df[columns].copy()


df_original = load_data()
total_movies = len(df_original)


# ---------------------------------------------------------
# 분석용 변수 만들기
# ---------------------------------------------------------
df = df_original.copy()

numeric_columns = [
    "first_scrn",
    "first_week_audi",
    "total_audi",
    "days_in_top10",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# 스크린 수: 상용로그
df["스크린 수"] = df["first_scrn"].apply(
    lambda x: math.log10(x)
    if pd.notna(x) and x > 0
    else pd.NA
)

# 누적 관객: 상용로그
df["누적 관객"] = df["total_audi"].apply(
    lambda x: math.log10(x)
    if pd.notna(x) and x > 0
    else pd.NA
)

# 10위권 일수: 그대로 사용
df["10위권 일수"] = df["days_in_top10"]

# 롱런 지수: 누적 관객 / 첫 주 관객, 최대 20
df["롱런 지수"] = df.apply(
    lambda row: min(
        row["total_audi"] / row["first_week_audi"],
        20,
    )
    if (
        pd.notna(row["total_audi"])
        and pd.notna(row["first_week_audi"])
        and row["first_week_audi"] > 0
    )
    else pd.NA,
    axis=1,
)


feature_columns = [
    "스크린 수",
    "누적 관객",
    "10위권 일수",
    "롱런 지수",
]


# ---------------------------------------------------------
# 묶는 데 사용할 속성 선택
# ---------------------------------------------------------
selected_features = st.multiselect(
    "묶는 데 사용할 속성을 선택하세요. (2개 이상)",
    feature_columns,
    default=feature_columns,
)

if len(selected_features) < 2:
    st.warning("묶음을 만들려면 속성을 2개 이상 선택하세요.")
    st.stop()


# ---------------------------------------------------------
# 묶음 수 선택
# ---------------------------------------------------------
n_clusters = st.slider(
    "묶음 수",
    min_value=2,
    max_value=7,
    value=3,
    step=1,
)


# ---------------------------------------------------------
# 결측치 및 첫 주 관객 0인 영화 제거
# ---------------------------------------------------------
cluster_df = df.dropna(subset=selected_features).copy()

# 명시적으로 첫 주 관객이 0 이하인 영화 제거
cluster_df = cluster_df[
    cluster_df["first_week_audi"].notna()
    & (cluster_df["first_week_audi"] > 0)
].copy()


# 전체 편수 / 묶은 편수
st.write(
    f"전체 편수: **{total_movies:,}편**  |  "
    f"묶은 편수: **{len(cluster_df):,}편**"
)

if len(cluster_df) < n_clusters:
    st.error(
        f"현재 묶은 편수({len(cluster_df):,}편)가 "
        f"선택한 묶음 수({n_clusters}개)보다 적습니다."
    )
    st.stop()


# ---------------------------------------------------------
# 표준화
# ---------------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(cluster_df[selected_features])


# ---------------------------------------------------------
# 선택한 묶음 수로 K-means
# ---------------------------------------------------------
kmeans = KMeans(
    n_clusters=n_clusters,
    random_state=42,
    n_init=10,
)

cluster_df["cluster"] = kmeans.fit_predict(X_scaled)


# ---------------------------------------------------------
# 묶음별 누적 관객 평균 계산
# 누적 관객 평균이 큰 묶음부터 ㉮, ㉯, ㉰...
# ---------------------------------------------------------
cluster_mean_total = (
    cluster_df.groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
)


cluster_symbols = [
    "㉮",
    "㉯",
    "㉰",
    "㉱",
    "㉲",
    "㉳",
    "㉴",
]


cluster_to_symbol = {
    cluster_id: cluster_symbols[i]
    for i, cluster_id in enumerate(cluster_mean_total.index)
}

cluster_df["묶음"] = cluster_df["cluster"].map(cluster_to_symbol)

symbol_order = cluster_symbols[:n_clusters]


# ---------------------------------------------------------
# 2차원 산점도
# ---------------------------------------------------------
st.subheader("2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_axis = st.selectbox(
        "가로축 속성",
        feature_columns,
        index=0,
    )

with col2:
    y_axis = st.selectbox(
        "세로축 속성",
        feature_columns,
        index=1,
    )


fig_2d = px.scatter(
    cluster_df,
    x=x_axis,
    y=y_axis,
    color="묶음",
    hover_name="movieNm",
    hover_data={
        "묶음": True,
        x_axis: ":.2f",
        y_axis: ":.2f",
    },
    category_orders={
        "묶음": symbol_order,
    },
    labels={
        "movieNm": "영화 제목",
        "묶음": "묶음",
    },
)

fig_2d.update_traces(
    marker={
        "size": 7,
    }
)

st.plotly_chart(
    fig_2d,
    use_container_width=True,
)


# ---------------------------------------------------------
# 3차원 산점도
# ---------------------------------------------------------
st.subheader("3차원 산점도")

if len(selected_features) < 3:
    st.info(
        "묶는 데 사용할 속성을 3개 이상 선택하면 "
        "3차원 산점도를 볼 수 있습니다."
    )
else:
    col_x, col_y, col_z = st.columns(3)

    with col_x:
        x3 = st.selectbox(
            "X축 속성",
            selected_features,
            index=0,
            key="x3",
        )

    with col_y:
        y3 = st.selectbox(
            "Y축 속성",
            selected_features,
            index=1,
            key="y3",
        )

    with col_z:
        z3 = st.selectbox(
            "Z축 속성",
            selected_features,
            index=2,
            key="z3",
        )

    fig_3d = px.scatter_3d(
        cluster_df,
        x=x3,
        y=y3,
        z=z3,
        color="묶음",
        hover_name="movieNm",
        hover_data={
            "묶음": True,
            x3: ":.2f",
            y3: ":.2f",
            z3: ":.2f",
        },
        category_orders={
            "묶음": symbol_order,
        },
        labels={
            "movieNm": "영화 제목",
            "묶음": "묶음",
        },
    )

    fig_3d.update_traces(
        marker={
            "size": 3,
        }
    )

    fig_3d.update_layout(
        scene={
            "xaxis_title": x3,
            "yaxis_title": y3,
            "zaxis_title": z3,
        }
    )

    st.plotly_chart(
        fig_3d,
        use_container_width=True,
    )


# ---------------------------------------------------------
# 묶음별 요약 표
# ---------------------------------------------------------
st.subheader("묶음별 요약")

summary = (
    cluster_df.groupby("묶음")
    .agg(
        편수=("movieNm", "size"),
        스크린수_평균=("first_scrn", "mean"),
        누적관객_평균=("total_audi", "mean"),
        십위권일수_평균=("days_in_top10", "mean"),
        롱런지수_평균=("롱런 지수", "mean"),
    )
    .reindex(symbol_order)
    .reset_index()
)

summary.columns = [
    "묶음",
    "편수",
    "스크린 수 평균",
    "누적 관객 평균",
    "10위권 일수 평균",
    "롱런 지수 평균",
]

summary["편수"] = summary["편수"].astype(int)
summary["스크린 수 평균"] = summary["스크린 수 평균"].round(1)
summary["누적 관객 평균"] = (
    summary["누적 관객 평균"]
    .round(0)
    .astype("Int64")
)
summary["10위권 일수 평균"] = (
    summary["10위권 일수 평균"]
    .round(1)
)
summary["롱런 지수 평균"] = (
    summary["롱런 지수 평균"]
    .round(2)
)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# 묶음별 누적 관객 상위 5편
# ---------------------------------------------------------
st.subheader("묶음별 누적 관객 상위 5편")

top_movies = (
    cluster_df.sort_values(
        ["묶음", "total_audi"],
        ascending=[True, False],
    )
    .groupby("묶음", sort=False)
    .head(5)
)

for symbol in symbol_order:
    st.markdown(f"### {symbol}")

    movies = top_movies[
        top_movies["묶음"] == symbol
    ].sort_values(
        "total_audi",
        ascending=False,
    )

    for _, row in movies.iterrows():
        st.write(
            f"- {row['movieNm']} "
            f"({row['total_audi']:,.0f}명)"
        )


# ---------------------------------------------------------
# 묶음 수별 중심으로부터의 제곱거리 합
# ---------------------------------------------------------
st.subheader("묶음 수에 따른 중심으로부터의 제곱거리 합")

inertia_values = []

for k in range(1, 8):
    kmeans_for_elbow = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10,
    )

    kmeans_for_elbow.fit(X_scaled)

    inertia_values.append(
        kmeans_for_elbow.inertia_
    )


# 바로 앞 값 대비 감소량
decrease_values = [None]

for i in range(1, len(inertia_values)):
    decrease_values.append(
        inertia_values[i - 1]
        - inertia_values[i]
    )


# ---------------------------------------------------------
# 꺾은선 그래프
# ---------------------------------------------------------
fig_elbow = go.Figure()

fig_elbow.add_trace(
    go.Scatter(
        x=list(range(1, 8)),
        y=inertia_values,
        mode="lines+markers",
        name="제곱거리 합",
        line={
            "width": 3,
        },
        marker={
            "size": 8,
        },
        hovertemplate=(
            "묶음 수: %{x}<br>"
            "제곱거리 합: %{y:.2f}"
            "<extra></extra>"
        ),
    )
)

# 현재 선택한 묶음 수에 세로선
fig_elbow.add_vline(
    x=n_clusters,
    line_width=2,
    line_dash="dash",
    line_color="red",
    annotation_text=f"현재 {n_clusters}개",
    annotation_position="top",
)

fig_elbow.update_layout(
    xaxis_title="묶음 수",
    yaxis_title="중심으로부터의 제곱거리 합",
    xaxis={
        "tickmode": "linear",
        "dtick": 1,
    },
    hovermode="x unified",
)

st.plotly_chart(
    fig_elbow,
    use_container_width=True,
)


# ---------------------------------------------------------
# 묶음 수별 제곱거리 합 및 감소량 표
# ---------------------------------------------------------
elbow_table = pd.DataFrame(
    {
        "묶음 수": list(range(1, 8)),
        "중심으로부터의 제곱거리 합": inertia_values,
        "바로 앞 값 대비 감소량": decrease_values,
    }
)

elbow_table[
    "중심으로부터의 제곱거리 합"
] = elbow_table[
    "중심으로부터의 제곱거리 합"
].round(2)

elbow_table[
    "바로 앞 값 대비 감소량"
] = elbow_table[
    "바로 앞 값 대비 감소량"
].round(2)

st.dataframe(
    elbow_table,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# 선택한 묶음 수의 실루엣 점수
# ---------------------------------------------------------
if n_clusters >= 2 and len(cluster_df) > n_clusters:
    silhouette = silhouette_score(
        X_scaled,
        cluster_df["cluster"],
    )

    st.write(
        f"현재 묶음 수 **{n_clusters}개**의 "
        f"실루엣 점수: **{silhouette:.3f}** "
        f"(범위 -1~1, 1에 가까울수록 묶음이 뚜렷함)"
    )
else:
    st.write(
        f"현재 묶음 수 **{n_clusters}개**의 "
        "실루엣 점수를 계산할 수 없습니다."
    )



