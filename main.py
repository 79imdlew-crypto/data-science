
import re
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="학교 급식 찾아보기", page_icon="🍱", layout="wide")

API_KEY = "a002a61cc69e4a22a41f9c0b840f1341"
SCHOOL_URL = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

SCHOOLS = ["도림고등학교", "아라고등학교", "논현고등학교"]


def neis_get(url, params):
    params = {
        "KEY": API_KEY,
        "Type": "json",
        **params,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600)
def find_school(school_name):
    data = neis_get(
        SCHOOL_URL,
        {"SCHUL_NM": school_name, "pIndex": 1, "pSize": 5},
    )
    if "schoolInfo" not in data or len(data["schoolInfo"]) < 2:
        return None

    rows = data["schoolInfo"][1].get("row", [])
    # 정확히 일치하는 학교명을 우선 사용
    exact = [r for r in rows if r.get("SCHUL_NM") == school_name]
    row = exact[0] if exact else (rows[0] if rows else None)
    return row


@st.cache_data(ttl=1800)
def get_meals(atpt_code, school_code, from_ymd, to_ymd):
    data = neis_get(
        MEAL_URL,
        {
            "ATPT_OFCDC_SC_CODE": atpt_code,
            "SD_SCHUL_CODE": school_code,
            "MMEAL_SC_CODE": "2",
            "MLSV_FROM_YMD": from_ymd,
            "MLSV_TO_YMD": to_ymd,
            "pSize": 1000,
            "pIndex": 1,
        },
    )
    if "mealServiceDietInfo" not in data or len(data["mealServiceDietInfo"]) < 2:
        return pd.DataFrame()

    rows = data["mealServiceDietInfo"][1].get("row", [])
    return pd.DataFrame(rows)


def parse_number(value):
    if pd.isna(value):
        return None
    text = str(value).replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def parse_protein(cal_info):
    # NEIS CAL_INFO는 보통 "탄수화물(g) 단백질(g) 지방(g) ... 칼로리(kcal)" 형식.
    # 표준 표기에서 단백질 뒤 숫자를 추출한다.
    if pd.isna(cal_info):
        return None
    text = str(cal_info)
    match = re.search(r"단백질\s*\(?g\)?\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)", text, re.I)
    if match:
        return float(match.group(1))

    # 일부 응답은 "단백질 : 00.0g"처럼 표기될 수 있다.
    match = re.search(r"단백질[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*g", text, re.I)
    return float(match.group(1)) if match else None


def has_dessert(menu):
    if pd.isna(menu):
        return False
    # 메뉴명에 후식/디저트 성격의 항목이 있는지 간단히 판별
    keywords = [
        "후식", "과일", "요구르트", "요거트", "주스", "음료", "푸딩",
        "아이스크림", "젤리", "떡", "케이크", "쿠키", "빵", "마카롱",
        "파이", "초코", "바나나", "사과", "배", "귤", "오렌지",
        "포도", "수박", "참외", "키위", "딸기", "복숭아", "멜론",
    ]
    menu_lower = str(menu).lower()
    return any(k.lower() in menu_lower for k in keywords)


@st.cache_data(ttl=1800)
def load_school_data():
    today = date.today()
    six_months_ago = today - timedelta(days=183)
    from_ymd = six_months_ago.strftime("%Y%m%d")
    to_ymd = today.strftime("%Y%m%d")

    result = {}
    for name in SCHOOLS:
        info = find_school(name)
        if not info:
            result[name] = {"info": None, "meals": pd.DataFrame()}
            continue

        meals = get_meals(
            info["ATPT_OFCDC_SC_CODE"],
            info["SD_SCHUL_CODE"],
            from_ymd,
            to_ymd,
        )
        if not meals.empty:
            meals["date"] = pd.to_datetime(meals["MLSV_YMD"], format="%Y%m%d", errors="coerce")
            meals["calories"] = meals["CAL_INFO"].apply(parse_number)
            meals["protein"] = meals["CAL_INFO"].apply(parse_protein)
            meals["dessert"] = meals["DDISH_NM"].apply(has_dessert)
        result[name] = {"info": info, "meals": meals}

    return result, six_months_ago, today


st.title("🍱 학교 급식 찾아보기")
st.caption("나이스 교육정보 개방 포털의 중식 데이터를 이용합니다.")

try:
    data, start_date, end_date = load_school_data()
except requests.RequestException as e:
    st.error(f"나이스 API 요청 중 오류가 발생했습니다: {e}")
    st.stop()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

st.info(
    f"조회 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} "
    "(한국 시간 기준 오늘을 끝 날짜로 사용)"
)

tabs = st.tabs(SCHOOLS)

for tab, school_name in zip(tabs, SCHOOLS):
    with tab:
        school = data[school_name]
        info = school["info"]
        df = school["meals"]

        if not info:
            st.warning("학교 기본정보를 찾지 못했습니다.")
            continue

        st.subheader(school_name)
        st.write(
            f"교육청: {info.get('ATPT_OFCDC_SC_CODE', '-')} · "
            f"지역: {info.get('LCTN_SC_NM', '-')}"
        )

        if df.empty:
            st.warning("조회 기간에 중식 데이터가 없습니다. (NEIS의 INFO-200일 수 있습니다.)")
            continue

        # 월별 평균
        monthly = (
            df.dropna(subset=["date"])
            .assign(month=lambda x: x["date"].dt.to_period("M").astype(str))
            .groupby("month", as_index=False)
            .agg(
                평균칼로리=("calories", "mean"),
                평균단백질=("protein", "mean"),
                후식제공일수=("dessert", "sum"),
            )
        )

        st.markdown("### 한달 평균 칼로리")
        if monthly["평균칼로리"].notna().any():
            chart_cal = monthly.set_index("month")[["평균칼로리"]]
            st.line_chart(chart_cal, y="평균칼로리")
        else:
            st.warning("칼로리 값이 없어 그래프를 만들 수 없습니다.")

        st.markdown("### 한달 평균 단백질 함유량")
        if monthly["평균단백질"].notna().any():
            chart_protein = monthly.set_index("month")[["평균단백질"]]
            st.line_chart(chart_protein, y="평균단백질")
        else:
            st.warning(
                "현재 응답의 CAL_INFO에서 단백질 수치를 확인하지 못했습니다. "
                "나이스 응답 형식이 다른 경우 파싱 규칙을 조정해야 합니다."
            )

        st.markdown("### 후식 여부")
        dessert_days = int(df["dessert"].sum())
        total_days = len(df)
        if dessert_days > 0:
            st.success(f"후식으로 판단되는 메뉴가 나온 날이 있습니다. ({dessert_days}/{total_days}일)")
        else:
            st.info("조회된 메뉴에서 후식으로 판단되는 항목을 찾지 못했습니다.")

        with st.expander("급식 원본 데이터 보기"):
            show_cols = [c for c in ["MLSV_YMD", "DDISH_NM", "CAL_INFO"] if c in df.columns]
            st.dataframe(df[show_cols], use_container_width=True)

