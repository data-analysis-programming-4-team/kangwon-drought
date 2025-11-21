import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# 파일 경로
INFRA_DIR = BASE_DIR / "Infra_idx"
EMER_CSV = INFRA_DIR / "emergency_water_raw.csv"

# 저장 파일 이름 및 csv 파일 이름
OUTPUT_EMER_STATIC = INFRA_DIR / "emergency_water_static_idx.csv"

# 다음 지역만 목표 지역으로 설정
# 실제 emergency_water_raw.csv 파일에는 7개 지역밖에 없지만 안전장치로 사용 (코드 통일)
TARGET_REGIONS = ["강릉시", "속초시", "인제군", "원주시", "춘천시", "홍천군", "철원군"]

# csv 파일 불러오기
df = pd.read_csv(EMER_CSV, encoding="utf-8-sig")

# 톤/일 한글 제거 및 혹시 모를 문자열 숫자로 변환 (안전장치)
df["용량_톤_일"] = (
    df["용량_톤_일"]
    .astype(str)
    .str.replace("톤/일", "", regex=False)
    .str.replace(",", "", regex=False)
    .apply(pd.to_numeric, errors="coerce")
)

# 시군구 필터링 (15줄 주석 -> 안전장치)
df = df[df["시군구"].isin(TARGET_REGIONS)].reset_index(drop=True)

# 정규화 함수 (min - max 방식) (모든 값이 같으면 0.5로 고정)
def normalize(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else pd.Series(0.5, index=s.index)

# 시군구 별로 각각 비상급수시설 개수, 총 용량, 평균 용량, 최대 용량, 최소 용량 집계
agg = (
    df.groupby("시군구")
    .agg(
        fac_count=("시설명", "count"),        # 비상급수시설 개수
        capacity_sum=("용량_톤_일", "sum"),   # 총 용량(톤/일)
        capacity_mean=("용량_톤_일", "mean"), # 평균 용량
        capacity_max=("용량_톤_일", "max"),   # 최대 용량
        capacity_min=("용량_톤_일", "min"),   # 최소 용량
    )
    .reset_index()
)

# 비상급수시설 개수, 총 용량, 평균 용량 표준화
agg["fac_count_norm"] = normalize(agg["fac_count"])
agg["capacity_sum_norm"] = normalize(agg["capacity_sum"])
agg["capacity_mean_norm"] = normalize(agg["capacity_mean"])

# emergency_water_idx 계산 (가중치 동일)
agg["emergency_water_idx"] = agg[
    ["fac_count_norm", "capacity_sum_norm", "capacity_mean_norm"]
].mean(axis=1)

# 컬럼 줄 순서 정리
cols_order = [
    "시군구",
    "fac_count_norm",
    "capacity_sum_norm",
    "capacity_mean_norm",
    "emergency_water_idx",
    "fac_count",
    "capacity_sum",
    "capacity_mean",
    "capacity_max",
    "capacity_min",
]
emer_static_idx = agg[cols_order].copy()

# csv 파일로 저장
emer_static_idx.to_csv(OUTPUT_EMER_STATIC, index=False, encoding="utf-8-sig")
print("비상급수 인프라 인덱스 저장 완료:", OUTPUT_EMER_STATIC)
