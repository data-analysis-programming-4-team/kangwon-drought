from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# 파일 위치 , 출력 파일 위치 및 csv 파일 이름
INFRA_DIR = BASE_DIR / "Infra_idx"
OUTPUT_STATIC = INFRA_DIR / "water_budget_static_idx.csv"

# 다음 지역만 목표 지역으로 설정
# 실제 csv 파일에는 7개 지역밖에 없지만 안전장치로 사용 (코드 통일) 
TARGET_REGIONS = ["강릉시", "속초시", "인제군", "원주시", "춘천시", "홍천군", "철원군"]

# 7개의 지역 매핑
REGION_FILE_MAP = {
    "강릉시": "2024_기능별_회계별_세출예산_강릉.csv",
    "속초시": "2024_기능별_회계별_세출예산_속초.csv",
    "원주시": "2024_기능별_회계별_세출예산_원주.csv",
    "춘천시": "2024_기능별_회계별_세출예산_춘천.csv",
    "홍천군": "2024_기능별_회계별_세출예산_홍천.csv",
    "철원군": "2024_기능별_회계별_세출예산_철원.csv",
    "인제군": "2024_기능별_회계별_세출예산_인제.csv",
}

# 정규화 함수 (min - max 방식) (모든 값이 같으면 0.5로 고정)
def normalize(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else pd.Series(0.5, index=s.index)

# csv 를 불러오는 함수
def load_csv(csv_file: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_file, encoding="utf-8-sig")

    # 분야-부문 문자열 정리 (따옴표, 공백 제거)
    df["분야-부문"] = (
        df["분야-부문"]
        .astype(str)
        .str.replace('"', "", regex=False)
        .str.strip()
    )

    # 문자형 데이터를 숫자형 데이터로 변환 ("분야-부문" 컬럼 제외 모두 숫자형 데이터)
    num_cols = [c for c in df.columns if c != "분야-부문"]
    for col in num_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .apply(pd.to_numeric, errors="coerce")
        )

    return df

# 전체 예산과 상하수도예산을 튜플로 반환하는 함수
def extract_budget(df: pd.DataFrame, name: str):
    # "분야-부문" 제외 컬럼 리스트
    num_cols = [c for c in df.columns if c != "분야-부문"]

    # 전체 예산을 구하는 코드 (합계 series의 첫번째 열은 "계")
    total_row = df[df["분야-부문"].str.contains("합계", na=False)]
    total_budget = float(total_row.iloc[0][num_cols[0]])

    # 상하수도 예산을 구하는 코드 (상하수도 series의 첫번째 열은 "계")
    water_mask = df["분야-부문"].str.contains("상하수도", na=False)
    water_budget = float(df.loc[water_mask, num_cols[0]].sum())

    return total_budget, water_budget

def main():
    # 데이터프레임을 만들기 위한 지역별 계산 결과를 저장하는 딕셔너리
    records = []

    # 지역별 상수도예산비중 계산
    for region, filename in REGION_FILE_MAP.items():
        # 파일 경로 생성
        file_path = INFRA_DIR / filename

        # 파일이 경로에 없으면 오류
        if not file_path.exists():
            print(f"[경고] 파일 없음 → {file_path}")
            continue
        
        # 파일 및 지역별 전체 예산과 상하수도 예산 불러오기
        df = load_csv(file_path)
        total, water = extract_budget(df, filename)

        # 상수도 예산 비중 계산
        ratio = water / total

        # 딕셔너리에 지역, 상하수도 예산, 총 예산, 상수도예산비중 저장
        records.append({
            "region": region,
            "water_budget": water,
            "total_budget": total,
            "water_budget_ratio": ratio,
        })

    # 상수도예산비중 데이터 프레임 생성
    df_ratio = pd.DataFrame(records)

    # # 시군구 필터링 (11줄 주석 -> 안전장치)
    df_ratio = df_ratio[df_ratio["region"].isin(TARGET_REGIONS)]

    # 상수도예산비중 정규화
    df_ratio["water_budget_ratio_norm"] = normalize(df_ratio["water_budget_ratio"])
    df_ratio["water_budget_static_idx"] = df_ratio["water_budget_ratio_norm"]

    # 컬럼 줄 순서 정리
    cols = [
        "region",
        "water_budget_static_idx",
        "water_budget_ratio_norm",
        "water_budget_ratio",
        "water_budget",
        "total_budget",
    ]

    # csv 파일로 저장
    df_ratio[cols].to_csv(OUTPUT_STATIC, index=False, encoding="utf-8-sig")
    print("상수도 예산 비중 static index 저장 완료", OUTPUT_STATIC)


if __name__ == "__main__":
    main()