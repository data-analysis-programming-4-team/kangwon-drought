from pathlib import Path
import pandas as pd

# 파일 경로
BASE_DIR = Path(__file__).resolve().parent
INFRA_DIR = BASE_DIR / "Infra_idx"

# 5개의 인프라 데이터 파일 경로
PIPE_STATIC     = INFRA_DIR / "pipe_static_idx.csv"
EMER_STATIC     = INFRA_DIR / "emergency_water_static_idx.csv"
RES_STATIC      = INFRA_DIR / "water_resilience_static_idx.csv"
COV_STATIC      = INFRA_DIR / "coverage_static_idx.csv"
BUDGET_STATIC   = INFRA_DIR / "water_budget_static_idx.csv"

# infra_index 결과 저장 폴더 및 파일 이름 
OUTPUT_INFRA    = INFRA_DIR / "infra_index.csv"

# 정규화 함수 (min - max 방식) (모든 값이 같으면 0.5로 고정)
def normalize(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else pd.Series(0.5, index=s.index)

def main():
    # 5개의 인프라 데이터 파일 불러오기
    pipe   = pd.read_csv(PIPE_STATIC, encoding="utf-8-sig")
    emer   = pd.read_csv(EMER_STATIC, encoding="utf-8-sig")
    res    = pd.read_csv(RES_STATIC, encoding="utf-8-sig")
    cov    = pd.read_csv(COV_STATIC, encoding="utf-8-sig")
    budget = pd.read_csv(BUDGET_STATIC, encoding="utf-8-sig")

    # emergency 파일 컬럼 명 region으로 통일
    emer = emer.rename(columns={"시군구": "region"})

    # 필요한 주요 정규화 값 뽑아내기
    pipe_index = pipe[["region", "pipe_index"]].copy()
    emer_index = emer[["region", "emergency_water_idx"]].copy()
    res_index  = res[["region", "water_resilience_index"]].copy()
    budget_index = budget[["region", "water_budget_static_idx"]].copy()

    # 보급률 정규화 후 값 뽑아내기
    if "coverage_rate_norm" not in cov.columns:
        cov["coverage_rate_norm"] = normalize(cov["coverage_rate"])
    cov_index = cov[["region", "coverage_rate_norm"]].copy()

    # 지역을 기준으로 merge
    merged = (
        pipe_index
        .merge(emer_index,   on="region", how="inner")
        .merge(res_index,    on="region", how="inner")
        .merge(cov_index,    on="region", how="inner")
        .merge(budget_index, on="region", how="inner")
    )

    # 높을 수록 취약한 관로노후도 부호 반대로 바꾸기
    merged["pipe_index"] = 1 - merged["pipe_index"]

    # 부호 맞춘 지표들 모으기
    index_cols = [
        "pipe_index",
        "emergency_water_idx",
        "water_resilience_index",
        "coverage_rate_norm",
        "water_budget_static_idx",
    ]

    # 인프라 인덱스들 평균내기
    merged["infra_index"] = merged[index_cols].mean(axis=1)

    # 컬럼 줄 순서 정리
    cols_order = [
        "region",
        "infra_index",
        "pipe_index",
        "emergency_water_idx",
        "water_resilience_index",
        "coverage_rate_norm",
        "water_budget_static_idx",
    ]
    merged = merged[cols_order].sort_values("infra_index", ascending=False).reset_index(drop=True)

    # csv 파일로 저장
    merged.to_csv(OUTPUT_INFRA, index=False, encoding="utf-8-sig")
    print(" 인프라 인덱스 저장 완료:", OUTPUT_INFRA)
    print(merged)

if __name__ == "__main__":
    main()