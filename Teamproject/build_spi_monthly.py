import os
import glob
import datetime
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

SPI_DIR = BASE_DIR / "SPI"
SPI_CONFIG = {
    "SPI_FILE_GLOB": str(SPI_DIR / "CLM_SPI_DD_*.csv"),
    "DATE_COL": "일시",      
    "STATION_COL": "지점명", 
    "VALUE_COL": "SPI3", # SPI6도 있긴함
}


def read_many_csv(path_glob: str, encoding: str = "cp949") -> pd.DataFrame:
    file_list = glob.glob(path_glob)
    if not file_list:
        raise FileNotFoundError(f"No SPI files matched: {path_glob}")

    dfs = [pd.read_csv(file, encoding=encoding) for file in file_list]
    return pd.concat(dfs, ignore_index=True)


def main():
    date_col = SPI_CONFIG["DATE_COL"]       
    station_col = SPI_CONFIG["STATION_COL"] 
    val_col = SPI_CONFIG["VALUE_COL"]       

    spi_raw = read_many_csv(SPI_CONFIG["SPI_FILE_GLOB"])

    spi = spi_raw.copy()
    spi[date_col] = pd.to_datetime(spi[date_col])
    spi["month"] = spi[date_col].dt.to_period("M").astype(str)
    spi["region"] = spi[station_col]
    spi[val_col] = pd.to_numeric(spi[val_col], errors="coerce")

    spi_monthly = (
        spi
        .groupby(["region", "month"], as_index=False)[val_col]
        .mean()
        .rename(columns={val_col: "SPI_raw"})
    )

    spi_monthly["year"] = spi_monthly["month"].str.slice(0, 4).astype(int)
    spi_monthly["month_num"] = spi_monthly["month"].str.slice(5, 7).astype(int)
    spi_monthly = spi_monthly[["region", "month", "SPI_raw", "year", "month_num"]]
    spi_monthly["SPI_raw"] = spi_monthly["SPI_raw"].round(3)

    SAVE_DIR = SPI_DIR
    os.makedirs(SAVE_DIR, exist_ok=True)

    csv_path = SAVE_DIR / "SPI_monthly.csv"
    spi_monthly.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print("SPI 월평균 지수 저장 완료", csv_path)

if __name__ == "__main__":
    main()
