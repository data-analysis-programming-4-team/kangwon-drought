import pandas as pd
import os
import io
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "Infra_idx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "climate_indices_23_25.csv"

API_KEY = "---" # 본인의 API 키 
START_YM = "202301"
END_YM = "202510"

STATIONS = {
    90: '속초',
    95: '철원',
    101: '춘천',
    105: '강릉',
    114: '원주',
    211: '인제',
    212: '홍천'
}

def get_kma_data(category, stn_id, region_name):
    url = f"https://apihub.kma.go.kr/api/typ01/url/{category}.php" # 데이터 받아올 주소
    params = {
        "tm1": START_YM,
        "tm2": END_YM,
        "stn_id": stn_id,
        "help": 1,     
        "disp": 1, 
        "authKey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        # api 연결확인 용
        if response.status_code != 200:
            print("API 연결 안됨 ")
            return None
        
        lines = response.text.splitlines()
        valid_lines = []
        
        for line in lines: # 데이터 형태를 보고 필요한 데이터 처리
            if "YY" in line and "MM" in line and "AVG" in line:
                valid_lines.append(line)
            elif not line.strip().startswith("#") and len(line.strip()) > 0:
                valid_lines.append(line)
                
        # 제대로 크롤링 됐는지 
        if not valid_lines:
            print("유효한 데이터가 없음")
            return None

        # CSV 파일로 변환 후 판다스로 읽기
        csv_buffer = io.StringIO("\n".join(valid_lines))
        
        # 공백으로 구분된 데이터 읽기
        df = pd.read_csv(csv_buffer, sep="\s+")
        
        # 컬럼명 정리 (혹시 모를 공백 제거)
        df.columns = [c.upper() for c in df.columns]
        
        # 평균기온, 평균 습도 월별 데이터 찾기 
        target_col = None
        for col in df.columns:
            if "AVG" in col: 
                target_col = col
                break
        # 컬럼 목록에 찾으려는 데이터 없을 경우 대비용
        if target_col is None:
            print(f"컬럼 목록 {df.columns}에 [{region_name}] AVG 컬럼 없음 ")
            return None
            
        # 필요한 데이터 포맷팅
        df['YY'] = df['YY'].astype(str)
        df['MM'] = df['MM'].astype(str).str.zfill(2)
        df['date'] = df['YY'] + "-" + df['MM']
        
        df['region'] = region_name
        df['value'] = pd.to_numeric(df[target_col], errors='coerce') # 숫자로 변환, 에러시 NaN
        
        return df[['date', 'region', 'value']]

    except Exception as e:
        print(f"[{region_name}] 처리 중 에러 발생: {e}")
        return None

final_data = []

for stn_id, region in STATIONS.items():    
    # 기온
    df_temp = get_kma_data("sts_ta", stn_id, region)
    
    # 습도
    df_humid = get_kma_data("sts_rhm", stn_id, region)
    
    if df_temp is not None and df_humid is not None:
        # 데이터 병합 
        df_temp = df_temp.rename(columns={'value': 'avg_temp'})  # 기온 df
        df_humid = df_humid.rename(columns={'value': 'avg_humid'})  # 습도 df
        merged = pd.merge(df_temp, df_humid, on=['date', 'region'], how='inner') #데이터병합방법
        final_data.append(merged)
    else: 
        print(f"{region} 데이터 수집 안됨 데이터 누락됨") # 데이터 없는 경우 확인 용

if final_data:
    final_df = pd.concat(final_data, ignore_index=True)
    final_df = final_df.sort_values(by=['region', 'date'])
    final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print("\n데이터 수집 완료")
    print(final_df.head())
else:
    print("\n데이터 수집 실패")