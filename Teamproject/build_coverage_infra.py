from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent  
INFRA_DIR = BASE_DIR / "Infra_idx"
INPUT_CSV = INFRA_DIR / "상수도_보급현황.csv"

OUTPUT_TIMESERIES = INFRA_DIR / "coverage_rate_timeseries.csv"
OUTPUT_STATIC = INFRA_DIR / "coverage_static_idx.csv"
TARGET_REGIONS = ["강릉시", "속초시", "인제군", "원주시", "춘천시", "홍천군", "철원군"]

df_raw = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

# 첫번쨰 행은 데이터이름 행
meta_row = df_raw.iloc[0]

# 실제 데이터 값들 존재
df = df_raw.iloc[1:].reset_index(drop=True).copy()
df = df.rename(columns={"시군별": "region"})

# 멀티인덱스 컬럼 생성 (year, metric)
new_cols = []
for col in df_raw.columns:
    if col == "시군별":
        new_cols.append(("", "region"))
    else:
        base_year = col.split(".")[0]      
        metric = meta_row[col]              
        new_cols.append((str(base_year), str(metric)))

multi_cols = pd.MultiIndex.from_tuples(new_cols, names=["year", "metric"])

df_multi = df.copy()
df_multi.columns = multi_cols
df_multi = df_multi.rename(columns={("", "region"): ("", "region")})

# 년별 보급률 시계열 추출
records = []

for year in sorted({y for (y, m) in df_multi.columns if y not in ["", None]}):
    col_key = (year, "보급률 (%)")
    if col_key not in df_multi.columns:
        continue

    tmp = df_multi[[("", "region"), col_key]].copy()
    tmp.columns = ["region", "coverage_rate"]
    tmp["year"] = int(year)

    # 숫자형 변환
    tmp["coverage_rate"] = pd.to_numeric(tmp["coverage_rate"], errors="coerce")

    records.append(tmp[["region", "year", "coverage_rate"]])

coverage_ts = pd.concat(records, ignore_index=True)
coverage_ts = coverage_ts[coverage_ts["region"].isin(TARGET_REGIONS)].reset_index(drop=True) #기준 7개지역

# 최신 기준 인프라 인덱스 생성
latest_year = coverage_ts["year"].max()
coverage_static = coverage_ts[coverage_ts["year"] == latest_year].copy()
coverage_static = coverage_static.sort_values("region").reset_index(drop=True)

# 보급 취약지수 = 100 - 보급률
coverage_static["coverage_vulnerability"] = 100 - coverage_static["coverage_rate"]

# csv 저장
coverage_ts.to_csv(OUTPUT_TIMESERIES, index=False, encoding="utf-8-sig")
coverage_static.to_csv(OUTPUT_STATIC, index=False, encoding="utf-8-sig")
print("상수도보급률 인프라 인덱스 저장", OUTPUT_STATIC)
