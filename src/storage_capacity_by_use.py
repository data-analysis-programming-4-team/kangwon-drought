import numpy as np
import pandas as pd
from scipy.optimize import minimize
import os

try:
    import matplotlib
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
except ImportError:
    print("오류: Matplotlib이 설치되어 있지 않거나 import에 실패함.")
    exit()

# ----파일 경로 설정----
FILE_PATH_WATER = "water_usage.csv"
FILE_PATH_STORAGE = "storage_capacity.csv"
# ---------------------

# 그래프 출력 후 storage_capacity_by_use.png파일 저장
def plot_storage_capacity_by_use(categories, data):
    plt.figure(figsize=(10, 6))
    plt.title('Storage Capacity by Use')
    plt.xlabel('region')
    plt.bar(categories, data, color=['skyblue'], width=0.6, align='center', edgecolor='black')
    plt.savefig('storage_capacity_by_use.png')

if __name__ == "__main__":
    if not os.path.exists(FILE_PATH_WATER):
        print(f"오류: 파일을 찾을 수 없음. {FILE_PATH_WATER}를 확인.")
    elif not os.path.exists(FILE_PATH_STORAGE):
        print(f"오류: 파일을 찾을 수 없음. {FILE_PATH_STORAGE}를 확인.")
    else:
        df_water = pd.read_csv(FILE_PATH_WATER)
        df_storage = pd.read_csv(FILE_PATH_STORAGE)
        categories = ['gangneung', 'sokcho']
        data = []
        # 시의 물 : total_water = 생활용수 + 농업용수
        gangneung_total_water_2022 = int(df_water.iloc[0,2]) + int(df_water.iloc[0,6])
        gangneung_total_water_2021 = int(df_water.iloc[1,2]) + int(df_water.iloc[1,6])
        sokcho_total_water_2022 = int(df_water.iloc[2,2]) + int(df_water.iloc[2,6])
        sokcho_total_water_2021 = int(df_water.iloc[3,2]) + int(df_water.iloc[3,6])
        
        gangneung_capacity = int(df_storage.iloc[0,5])
        sokcho_capacity = int(df_storage.iloc[2,5])

        # 식 : 해당 시의 저수지 용량 / 해당 시의 용수 사용량
        gangneung_final = gangneung_capacity / ((gangneung_total_water_2022 + gangneung_total_water_2021) / 2)
        sokcho_final = sokcho_capacity / ((sokcho_total_water_2022 + sokcho_total_water_2021) / 2)
        
        data.append(gangneung_final)
        data.append(sokcho_final)
        plot_storage_capacity_by_use(categories, data)
