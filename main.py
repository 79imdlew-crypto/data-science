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

    patterns = [
        r"\([^()]*\)",
        r"\[[^\[\]]*\]",
        r"\{[^{}]*\}",
        r"（[^（）]*）",
    ]

    # 중첩 괄호가 있어도 반복해서 제거
    for _ in range(10):
        previous = menu
        for pattern in patterns:
            menu = re.sub(pattern, "", menu)
        if menu == previous:
            break

    menu = re.sub(r"\s+", " ", menu).strip()
    return menu


def parse_menus(text):
    """세로줄로 메뉴를 분리하고 하루 안의 중복 메뉴를 제거한다."""
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
@st.cache_data
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

    # 메뉴가 하나도 없는 식단은 분석에서 제외
    df = df[df["메뉴목록"].map(bool)].reset_index(drop=True)

    return df


# ==================================================
# 4. 연관 규칙 계산
# ==================================================
@st.cache_data
def calculate_rules(menu_lists):
    total_days = len(menu_lists)

    if total_days == 0:
        return (
            pd.DataFrame(columns=DISPLAY_COLUMNS),
            0,
            {},
            {},
        )

    # 메뉴별 출현 일수
    menu_counts = {}

    # 함께 나온 메뉴 쌍별 일수
    pair_counts = {}

    for menus in menu_lists:
        menus = sorted(set(menus))

        for menu in menus:
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

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

    return rules_df, len(pair_counts), menu_counts, pair_counts


# ==================================================
# 5. 정렬 함수
# ==================================================
def sort_rules(df, sort_option):
    """숫자형 원본 열을 기준으로 내림차순 정렬한다."""
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

    return df.sort_values(
        by=columns,
        ascending=ascending,
        kind="mergesort",
    ).reset_index(drop=True)


# ==================================================
# 6. 화면 제목 및 데이터 불러오기
# ==================================================
st.title("🍱 급식 규칙 찾기")
st.write(
    "중식 메뉴가 같은 날 함께 등장하는 패턴과 "
    "한 번도 함께 나오지 않은 메뉴 짝을 분석합니다."
)

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("인터넷 연결, CSV 주소, CSV 열 이름을 확인해 주세요.")
    st.stop()

# 캐시 가능한 형태로 메뉴 목록 전달
menu_lists = tuple(
    tuple(menus) for menus in df["메뉴목록"]
)

rules_df, unique_pair_count, menu_counts, pair_counts = (
    calculate_rules(menu_lists)
)

all_menus = sorted(menu_counts.keys())
total_days = len(df)


# ==================================================
# 7. 요약 지표
# ==================================================
col1, col2, col3 = st.columns(3)

col1.metric("급식 일수", f"{total_days:,}일")
col2.metric("메뉴 종류 수", f"{len(all_menus):,}종")
col3.metric("함께 나온 메뉴 쌍 수", f"{unique_pair_count:,}쌍")

st.divider()


# ==================================================
# 8. 연관 규칙: 필터 및 정렬
# ==================================================
st.subheader("연관 규칙 탐색")

filter_col, sort_col = st.columns([2, 1])

with filter_col:
    selected_menu = st.selectbox(
        "좁혀 보기 - 메뉴 선택",
        options=["전체 메뉴"] + all_menus,
        index=0,
        help="조건 또는 결과에 선택한 메뉴가 포함된 규칙만 표시합니다.",
        key="rule_menu_filter",
    )

with sort_col:
    sort_option = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
        key="rule_sort_option",
    )

# 최소 동시 일수 슬라이더
min_together = st.slider(
    "최소 동시 일수",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="선택한 일수보다 적게 함께 나온 규칙은 표와 그래프에서 제외합니다.",
    key="min_together",
)

# 1) 최소 동시 일수 필터
filtered = rules_df[
    rules_df["동시"] >= min_together
].copy()

# 2) 메뉴 필터
if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()

# 3) 숫자형 데이터 상태에서 정렬
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

# 요청한 규칙 수 표시
st.write(
    f"**최소 동시 일수 {min_together}일 기준 · "
    f"남은 규칙: {len(filtered):,}개**"
)

# 표시용 문자열은 정렬이 끝난 뒤에만 생성
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

st.download_button(
    label="📥 현재 규칙 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="급식_연관규칙.csv",
    mime="text/csv",
)

st.divider()


# ==================================================
# 9. 향상도 상위 10개 그래프
# ==================================================
st.subheader("📊 향상도 상위 10개 규칙")

st.caption(
    "최소 동시 일수 및 위 메뉴 필터를 적용한 결과 중 "
    "향상도가 높은 규칙을 표시합니다."
)

if filtered.empty:
    st.info("조건에 맞는 규칙이 없습니다. 슬라이더나 메뉴를 바꿔 보세요.")
else:
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

    # 큰 향상도가 위에 표시되도록 축 순서를 지정
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


st.divider()


# ==================================================
# 10. 함께 나온 적 없는 짝
# ==================================================
st.subheader("🚫 함께 나온 적 없는 짝")

st.write(
    "선택한 메뉴와 같은 날 한 번도 함께 나오지 않았지만, "
    "각각 10일 이상 등장한 메뉴를 찾아봅니다."
)

# 위의 '좁혀 보기'와 별개의 메뉴 선택 상자
target_menu = st.selectbox(
    "비교할 기준 메뉴 선택",
    options=all_menus,
    index=0 if all_menus else None,
    help="위의 연관 규칙 메뉴 필터와 독립적으로 작동합니다.",
    key="never_together_menu",
)

if target_menu:
    target_days = menu_counts[target_menu]

    # 함께 나온 적이 있는 메뉴는 제외
    cooccurring_menus = set()

    for (a, b), count in pair_counts.items():
        if count > 0:
            if a == target_menu:
                cooccurring_menus.add(b)
            elif b == target_menu:
                cooccurring_menus.add(a)

    # 10일 이상 등장했고 기준 메뉴와 동시 출현이 없는 메뉴
    never_together = []

    for menu, days in menu_counts.items():
        if menu == target_menu:
            continue

        if days < 10:
            continue

        if menu in cooccurring_menus:
            continue

        never_together.append({
            "메뉴": menu,
            "나온 날": days,
        })

    never_df = pd.DataFrame(
        never_together,
        columns=["메뉴", "나온 날"],
    )

    if not never_df.empty:
        never_df = never_df.sort_values(
            by=["나온 날", "메뉴"],
            ascending=[False, True],
            kind="mergesort",
        ).reset_index(drop=True)

    # 선택 메뉴의 출현 일수와 후보 개수를 표시
    metric_col1, metric_col2 = st.columns(2)

    metric_col1.metric(
        f"'{target_menu}'이(가) 나온 날",
        f"{target_days:,}일",
    )

    metric_col2.metric(
        "함께 나온 적 없는 메뉴",
        f"{len(never_df):,}종",
    )

    if never_df.empty:
        st.info(
            "조건에 맞는 메뉴가 없습니다. "
            "선택 메뉴를 바꿔 보세요."
        )
    else:
        st.caption(
            "조건: 같은 날 동시 출현 0회, 해당 메뉴 출현 10일 이상. "
            "나온 날이 많은 순서로 정렬했습니다."
        )

        st.dataframe(
            never_df,
            use_container_width=True,
            hide_index=True,
            height=350,
        )

        st.download_button(
            label="📥 함께 나온 적 없는 짝 CSV 다운로드",
            data=never_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="함께_나온_적_없는_메뉴.csv",
            mime="text/csv",
            key="download_never_together",
        )


# ==================================================
# 11. 지표 설명
# ==================================================
with st.expander("지표와 계산 방법"):
    st.markdown(
        """
        - **동시:** 조건 메뉴와 결과 메뉴가 함께 나온 날짜 수
        - **지지도:** 함께 나온 날짜 수 ÷ 전체 급식 일수
        - **신뢰도:** 함께 나온 날짜 수 ÷ 조건 메뉴 출현 일수
        - **향상도:** 신뢰도 ÷ 결과 메뉴 출현 비율
        - **향상도 > 1:** 독립적으로 등장할 때보다 함께 나오는 경향이 강함
        - **향상도 = 1:** 독립적인 출현과 같은 수준
        - **향상도 < 1:** 독립적으로 등장할 때보다 함께 나오는 경향이 약함

        연관 규칙은 A → B와 B → A를 별도로 표시합니다.
        최소 동시 일수는 두 방향 규칙에 동일하게 적용됩니다.

        '함께 나온 적 없는 짝'에서는 같은 날 함께 등장한 횟수가
        0인 메뉴만 표시합니다. 각 메뉴의 출현 일수는
        최소 10일이어야 합니다.
        """
    )


