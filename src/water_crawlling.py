import requests
import json
import pandas as pd
from datetime import datetime
import os

# ----사용자 설정----
OUTPUT_FILENAME = "water_usage.csv"
TARGET_AREA_CODE = "GWD"  # 강원도 지역 코드
TARGET_DATE = "20241130" # 조회 기준일 (YYYYMMDD)
URL = "https://www.wamis.go.kr/wks/wks_agrwaa_lst_data.do"
# --------------------

def crawl_wamis_data(area_code, target_date, output_filename):
    payload = {
        'page': '1', 
        'rows': '100', 
        'sort': 'yymmdd',
        'order': 'desc',
        'srchAreaCd': area_code,
        'yymmdd': target_date
    }
    # HTTP 요청 헤더 설정
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' 
    }
    print(f"서버에 데이터 요청- (지역 코드: {area_code}, 기준일: {target_date})")
    
    try:
        # POST 요청 실행
        response = requests.post(URL, data=payload, headers=headers)
        response.raise_for_status() # http 오류 발생 시 예외 발생

        data = response.json()
        records = [row['cell'] for row in data['rows']]

        df = pd.DataFrame(records)
        
        # 컬럼 이름 지정 
        df.columns = [
            '기준일', '시도', '시군구', '지점번호', '지점명', '구분', 
            '용수량(천m3)', '유입량(천m3)', '유출량(천m3)', '저수량(천m3)', '저수율(%)', '비고'
        ]
        
        # 불필요한 첫 번째 행 제거
        df = df.iloc[1:].reset_index(drop=True)
        
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"데이터를 '{output_filename}' 파일로 저장.")
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 오류 발생: {e}")
    except json.JSONDecodeError:
        print("JSON 디코딩 오류")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    crawl_wamis_data(
        area_code=TARGET_AREA_CODE, 
        target_date=TARGET_DATE, 
        output_filename=OUTPUT_FILENAME

    )
