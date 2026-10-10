import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# ==================================================
# 1. 기본 설정
# ==================================================
st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide",
)

CSV_URL = (
    "https://raw.githubusercontent.com/teacher188-netizen/"
    "2026-datascience/refs/heads/main/dorim_meals.csv"
)

REQUIRED_COLUMNS = ["날짜", "식사", "메뉴"]
DISPLAY_COLUMNS = ["조건", "결과", "동시", "지지도", "신뢰도", "향상도"]


# ==================================================
# 2. 메뉴 전처리
# ==================================================
def clean_menu(menu):
    """메뉴 이름에서 괄호와 괄호 안의 내용을 제거한다."""
    menu = str(menu)

    # 소괄호, 대괄호, 중괄호 및 전각 소괄호
    patterns = [
        r"\([^()]*\)",
        r"\[[^\[\]]*\]",
        r"\{[^{}]*\}",
        r"（[^（）]*）",
    ]

    # 중첩 괄호가 있더라도 반복해서 제거
    for _ in range(10):
        previous = menu
        for pattern in patterns:
            menu = re.sub(pattern, "", menu)
        if menu == previous:
            break

    menu = re.sub(r"\s+", " ", menu).strip()
    return menu


def parse_menus(text):
    """세로줄로 분리하고 중복 메뉴를 제거한다."""
    if pd.isna(text):
        return []

    menus = [
        clean_menu(item)
        for item in str(text).split("|")
    ]

    return sorted(set(menu for menu in menus if menu))


# ==================================================
# 3. CSV 불러오기
# ==================================================
@st.cache_data(show_spinner="급식 데이터를 불러오는 중...")
def load_data():
    df = pd.read_csv(CSV_URL, encoding="utf-8")
    df.columns = df.columns.astype(str).str.strip()

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            "CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing))
        )

    df = df[REQUIRED_COLUMNS].copy()
    df["메뉴목록"] = df["메뉴"].apply(parse_menus)

    # 메뉴가 없는 식단은 제외
    df = df[df["메뉴목록"].map(bool)].reset_index(drop=True)

    # CSV의 한 행을 하루의 장바구니 하나로 취급
    return df


# ==================================================
# 4. 연관 규칙 계산
# ==================================================
@st.cache_data
def calculate_rules(menu_lists):
    total_days = len(menu_lists)

    if total_days == 0:
        return pd.DataFrame(columns=DISPLAY_COLUMNS), 0, 0

    # 메뉴별 출현 일수
    menu_counts = {}

    # 같은 날 함께 나온 메뉴 쌍별 일수
    pair_counts = {}

    for menus in menu_lists:
        # 메뉴 목록은 이미 하루 안에서 중복 제거됨
        for menu in menus:
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

        for a, b in combinations(sorted(set(menus)), 2):
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
            "동시": int(together),
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
            "동시": int(together),
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift_ba,
        })

    rules_df = pd.DataFrame(rules, columns=DISPLAY_COLUMNS)

    return rules_df, len(pair_counts), len(menu_counts)


# ==================================================
# 5. 정렬 함수
# ==================================================
def sort_rules(df, sort_option):
    """
    숫자형 원본 열을 기준으로 내림차순 정렬한다.
    표시용 문자열로 변환하기 전에 반드시 호출한다.
    """
    sort_config = {
        "향상도 순": (
            ["향상도", "신뢰도", "동시", "조건", "결과"],
            [False, False, False, True, True],
        ),
        "신뢰도 순": (
            ["신뢰도", "향상도", "동시", "조건", "결과"],
            [False, False, False, True, True],
        ),
        "동시 순": (
            ["동시", "향상도", "신뢰도", "조건", "결과"],
            [False, False, False, True, True],
        ),
    }

    columns, ascending = sort_config[sort_option]

    result = df.sort_values(
        by=columns,
        ascending=ascending,
        kind="mergesort",
    ).reset_index(drop=True)

    return result


# ==================================================
# 6. 화면
# ==================================================
st.title("🍱 급식 규칙 찾기")
st.write(
    "중식 메뉴가 같은 날 함께 등장하는 패턴을 분석하고 "
    "메뉴 사이의 연관 규칙을 찾아봅니다."
)

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("인터넷 연결, CSV 주소, CSV의 열 이름을 확인해 주세요.")
    st.stop()

rules_df, unique_pair_count, menu_count = calculate_rules(
    tuple(tuple(menus) for menus in df["메뉴목록"])
)

# 요약 지표
col1, col2, col3 = st.columns(3)

col1.metric("급식 일수", f"{len(df):,}일")
col2.metric("메뉴 종류 수", f"{menu_count:,}종")
col3.metric("함께 나온 메뉴 쌍 수", f"{unique_pair_count:,}쌍")

st.divider()

# ==================================================
# 7. 메뉴 필터 및 정렬
# ==================================================
st.subheader("연관 규칙 탐색")

all_menus = sorted({
    menu
    for menus in df["메뉴목록"]
    for menu in menus
})

filter_col, sort_col = st.columns([2, 1])

with filter_col:
    selected_menu = st.selectbox(
        "메뉴 선택",
        options=["전체 메뉴"] + all_menus,
        index=0,
        help="조건 또는 결과에 선택한 메뉴가 포함된 규칙을 표시합니다.",
    )

with sort_col:
    sort_option = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
    )

# 1) 원본 숫자 데이터에서 메뉴 필터 적용
filtered = rules_df.copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()

# 2) 숫자형 열로 정렬
filtered = sort_rules(filtered, sort_option)

sort_descriptions = {
    "향상도 순": "향상도가 높은 규칙부터 표시합니다.",
    "신뢰도 순": "조건 메뉴가 등장했을 때 결과 메뉴도 등장하는 비율이 높은 순서입니다.",
    "동시 순": "두 메뉴가 함께 등장한 날짜가 많은 순서입니다.",
}

st.caption(
    f"정렬 기준: {sort_option} · 내림차순 · "
    f"{sort_descriptions[sort_option]}"
)
st.write(f"검색 결과: {len(filtered):,}개 규칙")

# 3) 정렬이 끝난 다음에만 표시 형식 지정
display_df = filtered.copy()

if not display_df.empty:
    display_df["지지도"] = display_df["지지도"].map(
        lambda value: f"{value:.2%}"
    )
    display_df["신뢰도"] = display_df["신뢰도"].map(
        lambda value: f"{value:.2%}"
    )
    display_df["향상도"] = display_df["향상도"].map(
        lambda value: f"{value:.3f}"
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=430,
)

# CSV 다운로드는 표시용 문자열이 아닌 숫자 원본을 사용
st.download_button(
    label="📥 현재 규칙 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="급식_연관규칙.csv",
    mime="text/csv",
)

st.divider()

# ==================================================
# 8. 향상도 상위 10개 그래프
# ==================================================
st.subheader("📊 향상도 상위 10개 규칙")

st.caption(
    "현재 메뉴 필터를 적용한 결과에서 향상도가 높은 규칙을 표시합니다. "
    "정렬 기준을 변경해도 그래프는 향상도 기준 상위 10개를 유지합니다."
)

if filtered.empty:
    st.info("표시할 규칙이 없습니다. 다른 메뉴를 선택해 주세요.")
else:
    # 그래프는 표의 정렬 기준과 관계없이 향상도 상위 10개
    top10 = (
        filtered.sort_values(
            by=["향상도", "신뢰도", "동시", "조건", "결과"],
            ascending=[False, False, False, True, True],
            kind="mergesort",
        )
        .head(10)
        .copy()
    )

    top10["규칙"] = top10["조건"] + " → " + top10["결과"]

    # 그래프에서는 작은 향상도가 위쪽, 큰 향상도가 아래쪽
    # 으로 배치되어 막대 길이 비교가 쉽도록 정렬
    plot_df = top10.sort_values(
        "향상도",
        ascending=True,
        kind="mergesort",
    )

    fig = px.bar(
        plot_df,
        x="향상도",
        y="규칙",
        orientation="h",
        text=plot_df["향상도"].map(lambda value: f"{value:.3f}"),
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
            "규칙": "조건 → 결과",
        },
        title="향상도 상위 10개",
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title="향상도",
        yaxis_title="",
        yaxis=dict(automargin=True),
        margin=dict(l=20, r=75, t=60, b=35),
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# 9. 지표 설명
# ==================================================
with st.expander("지표와 정렬 기준 설명"):
    st.markdown(
        """
        - **동시:** 조건과 결과 메뉴가 같은 날 함께 나온 횟수
        - **지지도:** 함께 나온 날짜 수 ÷ 전체 급식 일수
        - **신뢰도:** 함께 나온 날짜 수 ÷ 조건 메뉴 출현 일수
        - **향상도:** 신뢰도 ÷ 결과 메뉴 출현 비율
        - **향상도 > 1:** 두 메뉴가 독립적일 때보다 함께 나오는 경향이 강함
        - **향상도 = 1:** 독립적인 출현과 같은 수준
        - **향상도 < 1:** 독립적인 출현보다 함께 나오는 경향이 약함

        정렬은 선택한 지표를 가장 먼저 비교합니다.
        값이 같으면 다른 지표와 메뉴 이름으로 순서를 결정합니다.
        """
    )


