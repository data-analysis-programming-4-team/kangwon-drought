import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# 파일 경로
INFRA_DIR = BASE_DIR / "Infra_idx"
PIPE_CSV = INFRA_DIR / "old_pipe_ratio.csv"

# 저장 파일 이름 및 csv 파일 이름
OUTPUT_PIPE_STATIC = INFRA_DIR / "pipe_static_idx.csv"

# 다음 지역만 목표 지역으로 설정
# 실제 old_pipe_ratio.csv 파일에는 7개 지역밖에 없지만 안전장치로 사용 (코드 통일)
TARGET_REGIONS = ["강릉시", "속초시", "인제군", "원주시", "춘천시", "홍천군", "철원군"]

# csv 파일 불러오기
df = pd.read_csv(PIPE_CSV, encoding="utf-8-sig")

# csv 파일안의 숫자를 문자열로 변환
for col in ["total_pipe_km", "old_pipe_km", "old_ratio"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "")
        .apply(pd.to_numeric, errors="coerce")
    )

# 2024년도 것만 사용
df = df[df["year"] == 2024].copy()

# 다른 인프라 데이터와 이름 통일
region_map = {
    "강릉": "강릉시",
    "속초": "속초시",
    "원주": "원주시",
    "춘천": "춘천시",
    "홍천": "홍천군",
    "철원": "철원군",
    "인제": "인제군",
}
df["region"] = df["region"].map(region_map)

#지역 필터링 (15줄 주석 -> 안전 장치)
df = df[df["region"].isin(TARGET_REGIONS)].reset_index(drop=True)

# 정규화 함수 (min - max 방식) (모든 값이 같으면 0.5로 고정)
def normalize(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else pd.Series(0.5, index=s.index)

# old ratio 다시 계산 (정확도 올리기)
df["old_ratio"] = (df["old_pipe_km"] / df["total_pipe_km"]) * 100.0

# 각 총배관길이, 노후된배관 길이, 노후관비율 정규화
df["pipe_total_norm"] = normalize(df["total_pipe_km"])
df["pipe_old_norm"] = normalize(df["old_pipe_km"])
df["old_pipe_ratio_norm"] = normalize(df["old_ratio"])

# pipe_index 계산 
df["pipe_index"] = df[
    ["pipe_total_norm", "pipe_old_norm", "old_pipe_ratio_norm"]
].mean(axis=1)

# 컬럼 줄 순서 정리
cols_order = [
    "region",
    "pipe_total_norm",
    "pipe_old_norm",
    "old_pipe_ratio_norm",
    "pipe_index",
    "total_pipe_km",
    "old_pipe_km",
    "old_ratio",
]
pipe_static_idx = df[cols_order].copy()

# csv 파일로 저장
pipe_static_idx.to_csv(OUTPUT_PIPE_STATIC, index=False, encoding="utf-8-sig")
print("관로노후도 인프라 인덱스 저장 완료:", OUTPUT_PIPE_STATIC)