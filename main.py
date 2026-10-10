import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide",
)

CSV_URL = (
    "https://raw.githubusercontent.com/teacher188-netizen/"
    "2026-datascience/refs/heads/main/dorim_meals.csv"
)

COLUMNS = ["날짜", "식사", "메뉴"]
TABLE_COLUMNS = [
    "조건", "결과", "동시", "지지도", "신뢰도", "향상도"
]


# --------------------------------------------------
# 데이터 불러오기 및 전처리
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL, encoding="utf-8")

    # 열 이름의 앞뒤 공백 제거
    df.columns = df.columns.astype(str).str.strip()

    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV에 필요한 열이 없습니다: {', '.join(sorted(missing))}"
        )

    df = df[COLUMNS].copy()
    df["메뉴"] = df["메뉴"].fillna("").astype(str)

    # 괄호와 괄호 안의 내용을 제거한다.
    # 예: 김치찌개(돼지고기) -> 김치찌개
    def clean_menu(menu):
        menu = re.sub(r"\([^()]*\)", "", menu)
        menu = re.sub(r"\[[^\[\]]*\]", "", menu)
        menu = re.sub(r"\（[^（）]*\）", "", menu)
        menu = re.sub(r"\s+", " ", menu).strip()
        return menu

    def parse_menu(text):
        menus = [
            clean_menu(item)
            for item in text.split("|")
        ]
        # 빈 메뉴 제거 및 하루 안의 중복 메뉴 제거
        return sorted(set(menu for menu in menus if menu))

    df["메뉴목록"] = df["메뉴"].apply(parse_menu)

    # 메뉴가 하나도 없는 식단은 분석에서 제외
    df = df[df["메뉴목록"].map(bool)].reset_index(drop=True)

    return df


# --------------------------------------------------
# 연관 규칙 계산
# --------------------------------------------------
def make_rules(df):
    total_days = len(df)

    if total_days == 0:
        return pd.DataFrame(columns=TABLE_COLUMNS), 0

    # 각 메뉴가 등장한 날짜 수
    menu_counts = {}
    pair_counts = {}

    for menus in df["메뉴목록"]:
        for menu in menus:
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

        # 각 날짜에서 서로 다른 메뉴의 모든 조합을 계산
        for a, b in combinations(menus, 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    rules = []

    for (a, b), together in pair_counts.items():
        support = together / total_days

        # A -> B
        confidence_ab = together / menu_counts[a]
        lift_ab = confidence_ab / (menu_counts[b] / total_days)

        rules.append({
            "조건": a,
            "결과": b,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ab,
            "향상도": lift_ab,
        })

        # B -> A
        confidence_ba = together / menu_counts[b]
        lift_ba = confidence_ba / (menu_counts[a] / total_days)

        rules.append({
            "조건": b,
            "결과": a,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift_ba,
        })

    rules_df = pd.DataFrame(rules, columns=TABLE_COLUMNS)

    # 같은 방향 규칙의 향상도와 신뢰도는 동일한 메뉴 출현
    # 빈도에 따라 결정된다. 동률이면 메뉴 이름으로 정렬한다.
    if not rules_df.empty:
        rules_df = rules_df.sort_values(
            ["향상도", "신뢰도", "동시", "조건", "결과"],
            ascending=[False, False, False, True, True],
            kind="mergesort",
        ).reset_index(drop=True)

    # 방향을 구분하지 않는 메뉴 쌍의 수
    unique_pair_count = len(pair_counts)

    return rules_df, unique_pair_count


# --------------------------------------------------
# 앱 화면
# --------------------------------------------------
st.title("🍱 급식 규칙 찾기")
st.caption(
    "우리 학교 중식 데이터에서 함께 등장하는 메뉴와 "
    "메뉴 간 연관 규칙을 찾아봅니다."
)

try:
    df = load_data()
except Exception as e:
    st.error(f"CSV를 불러오지 못했습니다: {e}")
    st.info("인터넷 연결과 CSV 주소, 열 이름을 확인해 주세요.")
    st.stop()

rules_df, unique_pair_count = make_rules(df)

menu_set = sorted({
    menu
    for menus in df["메뉴목록"]
    for menu in menus
})

# 요약 지표
m1, m2, m3 = st.columns(3)
m1.metric("급식 일수", f"{len(df):,}일")
m2.metric("메뉴 종류 수", f"{len(menu_set):,}종")
m3.metric("함께 나온 메뉴 쌍 수", f"{unique_pair_count:,}쌍")

st.divider()

# 필터와 정렬
st.subheader("연관 규칙 탐색")

left, right = st.columns([2, 1])

with left:
    selected_menu = st.selectbox(
        "메뉴 선택",
        options=["전체 메뉴"] + menu_set,
        index=0,
        help="조건 또는 결과에 선택한 메뉴가 포함된 규칙을 표시합니다.",
    )

with right:
    sort_option = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
    )

filtered = rules_df.copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ]

sort_columns = {
    "향상도 순": ["향상도", "신뢰도", "동시", "조건", "결과"],
    "신뢰도 순": ["신뢰도", "향상도", "동시", "조건", "결과"],
    "동시 순": ["동시", "향상도", "신뢰도", "조건", "결과"],
}

filtered = filtered.sort_values(
    sort_columns[sort_option],
    ascending=[False, False, False, True, True],
    kind="mergesort",
).reset_index(drop=True)

# 표 위에 결과 수 표시
st.write(f"**검색 결과: {len(filtered):,}개 규칙**")

# 표 출력
display_df = filtered.copy()

if not display_df.empty:
    display_df["지지도"] = display_df["지지도"].map(
        lambda x: f"{x:.2%}"
    )
    display_df["신뢰도"] = display_df["신뢰도"].map(
        lambda x: f"{x:.2%}"
    )
    display_df["향상도"] = display_df["향상도"].map(
        lambda x: f"{x:.3f}"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=420,
)

# 표 다운로드
st.download_button(
    "📥 현재 규칙 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="급식_연관규칙.csv",
    mime="text/csv",
)

st.divider()

# --------------------------------------------------
# 향상도 상위 10개 가로 막대그래프
# --------------------------------------------------
st.subheader("📊 향상도 상위 10개 규칙")

st.caption(
    "향상도가 높을수록 두 메뉴가 독립적일 때보다 "
    "함께 등장하는 연관성이 강합니다. "
    "같은 메뉴 쌍의 양방향 규칙은 각각 표시될 수 있습니다."
)

if filtered.empty:
    st.info("표시할 규칙이 없습니다. 다른 메뉴를 선택해 보세요.")
else:
    top10 = (
        filtered.nlargest(10, "향상도")
        .copy()
        .sort_values("향상도", ascending=True)
    )

    top10["규칙"] = (
        top10["조건"] + " → " + top10["결과"]
    )

    fig = px.bar(
        top10,
        x="향상도",
        y="규칙",
        orientation="h",
        text=top10["향상도"].map(lambda x: f"{x:.3f}"),
        hover_data={
            "조건": True,
            "결과": True,
            "동시": True,
            "지지도": ":.2%",
            "신뢰도": ":.2%",
            "향상도": ":.3f",
            "규칙": False,
        },
        labels={
            "향상도": "향상도 (Lift)",
            "규칙": "연관 규칙",
        },
        title="향상도 기준 상위 10개",
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )
    fig.update_layout(
        yaxis_title="",
        xaxis_title="향상도",
        yaxis=dict(automargin=True),
        margin=dict(l=20, r=80, t=60, b=30),
    )

    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 분석 안내
# --------------------------------------------------
with st.expander("지표 계산 방법"):
    st.markdown(
        """
        - **동시:** 조건 메뉴와 결과 메뉴가 함께 나온 날짜 수
        - **지지도:** 동시 출현 날짜 수 / 전체 급식 일수
        - **신뢰도:** 동시 출현 날짜 수 / 조건 메뉴 출현 날짜 수
        - **향상도:** 신뢰도 / 결과 메뉴 출현 비율
        - **향상도 > 1:** 독립적인 출현보다 함께 등장하는 경향이 강함
        - **향상도 = 1:** 두 메뉴의 출현이 독립적인 경우와 같음
        - **향상도 < 1:** 두 메뉴가 함께 등장하는 경향이 약함
        """
    )


