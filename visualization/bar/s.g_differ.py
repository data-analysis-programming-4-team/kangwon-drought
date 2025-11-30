import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# 1 CSV 불러오기

infra = pd.read_csv("infra_index.csv")
idi_m = pd.read_csv("IDI_monthly_only (1).csv")
hum = pd.read_csv("humidity_monthly.csv")
clim = pd.read_csv("climate_indices.csv")
idi_result = pd.read_csv("2023_2025_IDI_result.csv")

# 2. 2025년 9월 데이터만 필터링
target_year = 2025
target_month = 9

# ---- SPI, WUI, SSI ----
idi_spi_sel = idi_result[
    (idi_result["year"] == target_year) &
    (idi_result["month_num"] == target_month)
][["region", "year", "month_num",
   "SPI_raw", "WUI_raw", "SSI_global_raw"]].copy()

# ---- IDI, IDI_with_infra ----
idi_sel = idi_m[
    (idi_m["year"] == target_year) &
    (idi_m["month_num"] == target_month)
][["region", "year", "month_num", "IDI", "IDI_with_infra"]].copy()

# ---- 습도 ----
hum2 = hum.copy()
hum2["year"] = hum2["ym"].str[:4].astype(int)
hum2["month_num"] = hum2["ym"].str[5:7].astype(int)
hum_sel = hum2[
    (hum2["year"] == target_year) &
    (hum2["month_num"] == target_month)
][["region", "year", "month_num", "mean_humidity"]].copy()

# ---- 기온 ----
clim2 = clim.rename(columns={"지역명": "region", "년월": "ym", "평균기온": "mean_temp"}).copy()
clim2["year"] = clim2["ym"].str[:4].astype(int)
clim2["month_num"] = clim2["ym"].str[5:7].astype(int)
clim_sel = clim2[
    (clim2["year"] == target_year) &
    (clim2["month_num"] == target_month)
][["region", "year", "month_num", "mean_temp"]].copy()

# 3. 지표들 병합 (region, year, month_num 기준)
merged = idi_spi_sel.merge(
    idi_sel,
    on=["region", "year", "month_num"],
    how="left"
)

merged = merged.merge(
    hum_sel,
    on=["region", "year", "month_num"],
    how="left"
)

merged = merged.merge(
    clim_sel,
    on=["region", "year", "month_num"],
    how="left"
)

# 4. 인프라 데이터 붙이기 (region 이름 매핑)
region_map = {
    "강릉": "강릉시",
    "속초": "속초시",
    "원주": "원주시",
    "춘천": "춘천시",
    "인제": "인제군",
    "철원": "철원군",
    "홍천": "홍천군",
}

merged["region_full"] = merged["region"].map(region_map)

merged2 = merged.merge(
    infra,
    left_on="region_full",
    right_on="region",
    how="left",
    suffixes=("", "_infra")
)

# 5. 12개 변수 선택
vars12 = [
    "SPI_raw",
    "WUI_raw",
    "SSI_global_raw",
    "coverage_rate_norm",
    "pipe_index",
    "emergency_water_idx",
    "water_budget_static_idx",
    "water_resilience_index",
    "mean_humidity",
    "mean_temp",
    "IDI",
    "IDI_with_infra"
]

# NaN 제거
df_2025_09 = merged2[["region"] + vars12].dropna().copy()

# 6. 0~1 정규화 (강원도 전체 시·군 기준)
df_norm = df_2025_09.copy()

for col in vars12:
    col_min = df_norm[col].min()
    col_max = df_norm[col].max()
    if col_max - col_min == 0:
        # 분산이 0인 경우(예: SSI가 전 지역 동일) → 중간값 0.5로 세팅
        df_norm[col + "_norm"] = 0.5
    else:
        df_norm[col + "_norm"] = (df_norm[col] - col_min) / (col_max - col_min)

norm_cols = [c + "_norm" for c in vars12]

# 7. 속초 vs 강릉만 추출
target_regions = ["속초", "강릉"]   # idi_result 기준 지역명이 이 형식일 것임
df_pair = df_norm[df_norm["region"].isin(target_regions)].set_index("region")

radar_df = df_pair[norm_cols].copy()
radar_df.index.name = "region"

# 변수 라벨
label_map = {
    "SPI_raw_norm": "SPI",
    "WUI_raw_norm": "WUI",
    "SSI_global_raw_norm": "SSI",
    "coverage_rate_norm_norm": "상수도 보급률",
    "pipe_index_norm": "관로노후도",
    "emergency_water_idx_norm": "비상급수시설",
    "water_budget_static_idx_norm": "상수도 예산비중",
    "water_resilience_index_norm": "정수지/배수지 용량",
    "mean_humidity_norm": "습도",
    "mean_temp_norm": "기온",
    "IDI_norm": "IDI",
    "IDI_with_infra_norm": "IDI_infra",
}

labels = [label_map[c] for c in norm_cols]

# 9. 차이 막대 그래프
sc_vals = radar_df.loc["속초"]
gn_vals = radar_df.loc["강릉"]

diff = sc_vals - gn_vals  # 속초 - 강릉

diff_df = pd.DataFrame({
    "variable": labels,
    "diff": diff.values
})

# 속초/강릉 구분 컬럼 생성
diff_df["region_color"] = diff_df["diff"].apply(lambda x: "속초" if x > 0 else "강릉")

# 색상 맵
color_map = {
    "속초": "steelblue",
    "강릉": "indianred"
}

plt.figure(figsize=(10, 6))

ax = sns.barplot(
    data=diff_df,
    x="diff",
    y="variable",
    hue="region_color",       # hue로 그룹 분리
    palette=color_map,        # 그룹별 색상 지정
    dodge=False,              # 막대 겹침 없음
    legend=False              # 범례 숨김
)

# 기준선
plt.axvline(0, color="black", linewidth=1)

plt.title("강릉 - 속초 (정규화 지표 차이, 2025년 9월)", fontsize=15, pad=15)
plt.xlabel("차이 (강릉 - 속초, 0~1 스케일)")
plt.ylabel("지표")

plt.tight_layout()
plt.show()
