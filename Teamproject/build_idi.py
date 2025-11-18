import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# 파일 경로
SPI_PATH = BASE_DIR / "SPI" / "SPI_monthly.csv"
SSI_PATH = BASE_DIR / "SSI" / "SSI_monthly.csv"
WUI_PATH = BASE_DIR / "WUI" / "WUI_monthly.csv"

# IDI 결과 저장 폴더 및 파일 이름
IDI_DIR = BASE_DIR / "IDI"
PANEL_FILENAME = "IDI_monthly_panel.csv"
ONLY_FILENAME = "IDI_monthly_only.csv"


# CSV를 불러오는 함수
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")

# Z-SCORE 표준화 함수 (( 변수 - 평균 )/ 표준편차))
def zscore(series: pd.Series) -> pd.Series:
    return (series - series.mean()) / (series.std() + 1e-8)


def main():

    # SCV에서 데이터 불러오기
    spi = load_csv(SPI_PATH)
    ssi = load_csv(SSI_PATH)
    wui = load_csv(WUI_PATH)

    #SSI 값에 year, month_num 만들기
    ssi["year"] = ssi["month"].str.slice(0, 4).astype(int)
    ssi["month_num"] = ssi["month"].str.slice(5, 7).astype(int)

    # SPI 와 WUI 합치기 (지역단위 O)
    df = spi.merge(
        wui[["region", "year", "month_num", "WUI_raw"]],
        on=["region", "year", "month_num"],
        how="inner"
    )

    print("SPI + WUI 병합 후:", df.shape)

    # SSI 합치기 (지역단위 X)
    df = df.merge(
        ssi[["year", "month_num", "SSI_global_raw"]],
        on=["year", "month_num"],
        how="left"
    )

    # Z-SCORE 표준화
    df["SPI_z"] = zscore(df["SPI_raw"])
    df["WUI_z"] = zscore(df["WUI_raw"])
    df["SSI_z"] = zscore(df["SSI_global_raw"])

    # IDI 산출 (가중치는 모두 1/3으로 동일)
    df["IDI"] = (df["SPI_z"] + df["WUI_z"] + df["SSI_z"]) / 3

    # IDI 결과 저장 폴더 생성
    os.makedirs(IDI_DIR, exist_ok=True)

    # 전체 패널 CSV 저장
    panel_path = IDI_DIR / PANEL_FILENAME
    df.to_csv(panel_path, index=False, encoding="utf-8-sig")

    # IDI 값만 저장하는 CSV 생성
    idi_only = df[["region", "year", "month_num", "month", "IDI"]].copy()
    idi_only_path = IDI_DIR / ONLY_FILENAME
    idi_only.to_csv(idi_only_path, index=False, encoding="utf-8-sig")

    #완료 메세지
    print("전체 패널 CSV 저장 완료", panel_path)
    print("IDI only 값 CSV 저장 완료", idi_only_path)

if __name__ == "__main__":
    main()