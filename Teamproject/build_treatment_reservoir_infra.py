from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INFRA_DIR = BASE_DIR / "Infra_idx"
COVERAGE_CSV = INFRA_DIR / "상수도_보급현황.csv"
RESERVOIR_CSV = INFRA_DIR / "kangwon_reservoir_capacity.csv"

OUTPUT_STATIC = INFRA_DIR / "water_resilience_static_idx.csv"

TARGET_REGIONS = ["강릉시", "속초시", "인제군", "원주시", "춘천시", "홍천군", "철원군"]
raw_cov = pd.read_csv(COVERAGE_CSV, encoding="utf-8-sig")

# 메타: 컬럼명을 추출
meta = raw_cov.iloc[0]
df_cov = raw_cov.iloc[1:].copy()
df_cov = df_cov.rename(columns={"시군별": "region"})

# 각 지역에 대해, 연도와 지표를 넣음
new_cols = []
for col in raw_cov.columns:
    if col == "시군별":
        new_cols.append(("", "region"))
    else:
        # 데이터자료에서 원하는 년도 값만 추출
        year = col.split(".")[0]
        metric = meta[col]
        new_cols.append((str(year), str(metric)))

df_cov.columns = pd.MultiIndex.from_tuples(new_cols)

# 최신연도 데이터만 사용
LATEST_YEAR = "2023"

pop_col_name = "급수인구 (명)"
supply_col_name = "급수량 (㎥/일)"
capacity_col_name = "시설용량 (㎥/일)"

# 필요한 것만
cols_to_fetch = [
    ("", "region"),
    (LATEST_YEAR, pop_col_name),
    (LATEST_YEAR, supply_col_name),
    (LATEST_YEAR, capacity_col_name)
]

cov_2023 = df_cov[cols_to_fetch].copy()
cov_2023.columns = ["region", "population", "daily_supply", "treatment_capacity"] # 컬럼명 부여

# 콤마로 나뉜 숫자 , 제거
for col in ["population", "daily_supply", "treatment_capacity"]:
    cov_2023[col] = (
        cov_2023[col]
        .astype(str)
        .str.replace(",", "")
        .apply(pd.to_numeric, errors="coerce")
    )

# 1인당 처리용량 계산
cov_2023["capacity_per_capita"] = cov_2023["treatment_capacity"] / cov_2023["population"]

# 필요한 데이터 불러오기
df_res = pd.read_csv(RESERVOIR_CSV, encoding="utf-8-sig")
df_res = df_res.rename(columns={
    "region": "region",
    "capacity_m3_per_day": "reservoir_capacity"
})

# 콤마 제거 및 숫자 변환
df_res["reservoir_capacity"] = (
    df_res["reservoir_capacity"]
    .astype(str)
    .str.replace(",", "")
    .apply(pd.to_numeric, errors="coerce")
)

# 데이터 합침
merged_df = cov_2023.merge(df_res[["region", "reservoir_capacity"]], on="region", how="left")

 # 저수일류
merged_df["storage_days"] = merged_df["reservoir_capacity"] / merged_df["daily_supply"] # 배수지 용량 / 일평균 급수량

#인덱스 정규화
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

merged_df["treatment_resilience"] = normalize(merged_df["capacity_per_capita"])
merged_df["reservoir_resilience"] = normalize(merged_df["storage_days"])
merged_df["water_resilience_index"] = merged_df[
    ["treatment_resilience", "reservoir_resilience"]
].mean(axis=1)

final_df = merged_df[merged_df["region"].isin(TARGET_REGIONS)].reset_index(drop=True)

cols_order = [
    "region", 
    "treatment_resilience", 
    "reservoir_resilience", 
    "water_resilience_index",
    "capacity_per_capita",
    "storage_days",
    "treatment_capacity",
    "reservoir_capacity"
]
final_df = final_df[cols_order]

final_df.to_csv(OUTPUT_STATIC, index=False, encoding="utf-8-sig")
print(f"급수 인프라 인덱스 파일 저장 {OUTPUT_STATIC}")
print(final_df)