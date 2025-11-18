import os
import glob
import datetime
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

SSI_DIR = BASE_DIR / "SSI"
SSI_GLOB = str(SSI_DIR / "excelDataList_*.xlsx")
TARGET_DAMS = ["소양강댐", "횡성댐", "충주댐"]
SAVE_DIR = SSI_DIR


def read_single_ssi_excel(path: str) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None)

    # 2) 댐 들어간 문자열 탐색
    dam_name = None
    max_row_search = min(6, raw.shape[0])
    max_col_search = min(6, raw.shape[1])
    for i in range(max_row_search):
        for j in range(max_col_search):
            val = raw.iat[i, j]
            if isinstance(val, str) and "댐" in val:
                dam_name = val.split(":")[0].strip()
                break
        if dam_name is not None:
            break

    header_row_idx = None
    for i in range(len(raw)):
        row_values = raw.iloc[i].astype(str)
        if any("일시" in v for v in row_values): # 일시 있는 행 인덱스 찾음
            header_row_idx = i
            break

    # 감지된 헤더 행을 컬럼명으로 사용함
    header = raw.iloc[header_row_idx].tolist()
    df = raw.iloc[header_row_idx + 1 :].copy()
    df.columns = header

    # 일시 데이터 찾기
    date_col_candidates = [c for c in df.columns if "일시" in str(c)]
    date_col = date_col_candidates[0]

    # 저수율 데이터 찾기
    storage_col_candidates = [c for c in df.columns if "저수율" in str(c)]
    storage_col = storage_col_candidates[0]

    # 필요한 애들만 정리
    out = df[[date_col, storage_col]].copy()
    out.rename(columns={date_col: "date", storage_col: "storage_rate"}, inplace=True)

    out["date"] = pd.to_datetime(out["date"])
    out["dam"] = dam_name

    return out


def main():
    file_list = glob.glob(SSI_GLOB)
    print("찾은 SSI 파일 수:", len(file_list))
    ssi_all_list = [read_single_ssi_excel(path) for path in file_list]

    ssi_all = pd.concat(ssi_all_list, ignore_index=True)
    ssi_all = ssi_all[ssi_all["dam"].isin(TARGET_DAMS)].copy()
    ssi_all["month"] = ssi_all["date"].dt.to_period("M").astype(str)

    # (dam, month)별 월평균 저수율(%)
    ssi_dam_month = (
        ssi_all
        .groupby(["dam", "month"], as_index=False)["storage_rate"]
        .mean()
        .rename(columns={"storage_rate": "SSI_dam_month"})
    )
    # month별 3댐 동일가중 평균 → SSI_global_raw
    ssi_global_month = (
        ssi_dam_month
        .groupby("month", as_index=False)["SSI_dam_month"]
        .mean()
        .rename(columns={"SSI_dam_month": "SSI_global_raw"})
    )

    # 결과 저장
    os.makedirs(SAVE_DIR, exist_ok=True)

    csv_path = SAVE_DIR / "SSI_monthly.csv"  # 저장 파일명
    ssi_global_month.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print("\nSSI 월별 지수 저장 완료", csv_path)

if __name__ == "__main__":
    main()
