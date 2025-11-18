import numpy as np
import pandas as pd
import glob
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
WUI_DIR = BASE_DIR / "WUI"
WUI_FILE_GLOB = str(WUI_DIR / "WUI_Gangwon_*.csv")
SAVE_DIR = WUI_DIR
SAVE_FILENAME = "WUI_monthly.csv"
VALID_REGIONS = ["강릉", "속초", "원주", "춘천", "홍천", "인제", "철원"]

def load_wui_files(path_glob: str) -> pd.DataFrame:
    files = glob.glob(path_glob)

    dfs = []
    for file in files:
        df = pd.read_csv(file, encoding="utf-8-sig")
        df["source_file"] = Path(file).name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def main():
    wui_raw = load_wui_files(WUI_FILE_GLOB)

    region_col = wui_raw.columns[2]
    wui_raw["region"] = (
        wui_raw[region_col]
        .astype(str)
        .str.replace("강원특별자치도 ", "", regex=False)
        .str.replace("강원도 ", "", regex=False)
        .str.replace("시", "", regex=False)
        .str.replace("군", "", regex=False)
    )

    wui_filtered = wui_raw[wui_raw["region"].isin(VALID_REGIONS)].copy()

    year_col = wui_filtered.columns[1]
    value_col = wui_filtered.select_dtypes(include=["number"]).columns[-1]

    rows = []
    for _, row in wui_filtered.iterrows():
        region = row["region"]
        year = int(row[year_col])
        val = float(row[value_col])

        for m in range(1, 13):
            rows.append(
                {
                    "region": region,
                    "year": year,
                    "month_num": m,
                    "month": f"{year}-{m:02d}",
                    "WUI_raw": val,
                }
            )

    wui_monthly = pd.DataFrame(rows).sort_values(
        ["region", "year", "month_num"]
    ).reset_index(drop=True)

    wui_yearly = (
        wui_monthly.groupby(["region", "year"], as_index=False)["WUI_raw"]
        .mean()
        .sort_values(["region", "year"])
    )

    # 선형추세 예측: 21-23 을 이용한 24,25 데이터 값 생성
    pred_rows = []
    for region, g in wui_yearly.groupby("region"):
        hist = g[g["year"].isin([2021, 2022, 2023])]
        if len(hist) < 2:
            continue

        x = hist["year"].astype(float).values
        y = hist["WUI_raw"].astype(float).values

        m, b = np.polyfit(x, y, 1)

        for y_year in [2024, 2025]:
            y_hat = m * y_year + b
            y_hat_round = round(y_hat, 1)
            pred_rows.append(
                {
                    "region": region,
                    "year": y_year,
                    "WUI_raw": y_hat_round,
                }
            )

    wui_yearly_future = pd.DataFrame(pred_rows).sort_values(["region", "year"])

    future_monthly_rows = []
    for _, row in wui_yearly_future.iterrows():
        region = row["region"]
        year = int(row["year"])
        val = float(row["WUI_raw"])

        for m in range(1, 13): # 24,25 예측값 월별로 확장
            future_monthly_rows.append(
                {
                    "region": region,
                    "year": year,
                    "month": f"{year}-{m:02d}",
                    "month_num": m,
                    "WUI_raw": val,
                }
            )
    wui_future_monthly = pd.DataFrame(future_monthly_rows)

    # 기존의 데이터에들에 24, 25년도 결합
    wui_full = pd.concat([wui_monthly, wui_future_monthly], ignore_index=True)
    wui_full = wui_full.sort_values(
        ["region", "year", "month_num"]
    ).reset_index(drop=True)

    # 2023~2025만 남기기
    wui_full_filtered = wui_full[wui_full["year"] >= 2023].reset_index(drop=True)

    os.makedirs(SAVE_DIR, exist_ok=True)
    csv_path = SAVE_DIR / SAVE_FILENAME
    wui_full_filtered.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("WUI 월별 지수 저장 완료", csv_path)

if __name__ == "__main__":
    main()
