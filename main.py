import pandas as pd
import streamlit as st
import plotly.express as px
from sklearn.cluster import KMeans
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

    # 필요한 열만 사용
    df = df[columns].copy()

    # 숫자형으로 변환
    numeric_columns = [
        "first_scrn",
        "first_week_audi",
        "total_audi",
        "days_in_top10",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df_original = load_data()
total_movies = len(df_original)


# ---------------------------------------------------------
# 클러스터링용 변수 생성
# ---------------------------------------------------------
df = df_original.copy()

# 0 이하의 값은 로그 변환이 불가능하므로 결측 처리
df.loc[df["first_scrn"] <= 0, "first_scrn"] = pd.NA
df.loc[df["total_audi"] <= 0, "total_audi"] = pd.NA

# 로그 변환
df["스크린 수"] = df["first_scrn"].apply(
    lambda x: __import__("math").log10(x) if pd.notna(x) else pd.NA
)

df["누적 관객"] = df["total_audi"].apply(
    lambda x: __import__("math").log10(x) if pd.notna(x) else pd.NA
)

# 10위권 일수는 그대로
df["10위권 일수"] = df["days_in_top10"]

# 롱런 지수
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

original_feature_columns = {
    "스크린 수": "first_scrn",
    "누적 관객": "total_audi",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "롱런 지수",
}


# ---------------------------------------------------------
# 속성 선택
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
# 결측치 제거
# ---------------------------------------------------------
cluster_df = df.dropna(subset=selected_features).copy()

# 전체 편수 / 묶은 편수
st.write(
    f"전체 편수: **{total_movies:,}편**  |  "
    f"묶은 편수: **{len(cluster_df):,}편**"
)

if len(cluster_df) < 3:
    st.error("세 묶음으로 나누려면 유효한 영화가 최소 3편 필요합니다.")
    st.stop()


# ---------------------------------------------------------
# 표준화 + K-means
# ---------------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(cluster_df[selected_features])

kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10,
)

cluster_df["cluster"] = kmeans.fit_predict(X_scaled)


# ---------------------------------------------------------
# 묶음 번호 재지정
# 누적 관객 평균이 큰 묶음부터 ㉮, ㉯, ㉰
# ---------------------------------------------------------
cluster_mean_total = (
    cluster_df.groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
)

cluster_labels = ["㉮", "㉯", "㉰"]

cluster_to_label = {
    cluster_id: cluster_labels[i]
    for i, cluster_id in enumerate(cluster_mean_total.index)
}

cluster_df["묶음"] = cluster_df["cluster"].map(cluster_to_label)


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
        index=1 if len(feature_columns) > 1 else 0,
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
        "묶음": ["㉮", "㉯", "㉰"]
    },
    labels={
        "movieNm": "영화 제목",
        "묶음": "묶음",
    },
)

fig_2d.update_traces(marker={"size": 7})

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
    c1, c2, c3 = st.columns(3)

    with c1:
        x3 = st.selectbox(
            "X축 속성",
            selected_features,
            index=0,
            key="x3",
        )

    with c2:
        y3 = st.selectbox(
            "Y축 속성",
            selected_features,
            index=1 if len(selected_features) > 1 else 0,
            key="y3",
        )

    with c3:
        z3 = st.selectbox(
            "Z축 속성",
            selected_features,
            index=2 if len(selected_features) > 2 else 0,
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
            "묶음": ["㉮", "㉯", "㉰"]
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
    .reindex(["㉮", "㉯", "㉰"])
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

# 원래 단위로 보기 좋게 표시
summary["편수"] = summary["편수"].astype(int)
summary["스크린 수 평균"] = summary["스크린 수 평균"].round(1)
summary["누적 관객 평균"] = summary["누적 관객 평균"].round(0).astype("Int64")
summary["10위권 일수 평균"] = summary["10위권 일수 평균"].round(1)
summary["롱런 지수 평균"] = summary["롱런 지수 평균"].round(2)

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
    .groupby("묶음")
    .head(5)
)

for label in ["㉮", "㉯", "㉰"]:
    st.markdown(f"### {label}")

    movies = top_movies[top_movies["묶음"] == label]

    if movies.empty:
        st.write("해당 묶음에 영화가 없습니다.")
    else:
        for _, row in movies.iterrows():
            st.write(
                f"- {row['movieNm']} "
                f"({row['total_audi']:,.0f}명)"
            )


