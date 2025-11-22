import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#한글 폰트
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 불러오기
df = pd.read_csv("merged_2025_09_by_region.csv")

# ====== 평균기온/평균습도 컬럼 자동 rename 처리 ======
if "mean_temp" not in df.columns and "평균기온" in df.columns:
    df = df.rename(columns={"평균기온": "mean_temp"})
if "mean_humidity" not in df.columns and "평균습도" in df.columns:
    df = df.rename(columns={"평균습도": "mean_humidity"})

# 8개 변수 정의
vars8 = [
    "IDI",
    "coverage_rate",
    "water_resilience_index",
    "emergency_water_idx",
    "water_budget_ratio_norm",
    "pipe_index",
    "mean_temp",
    "mean_humidity"
]

# 한글 라벨
korean = {
    "IDI": "IDI",
    "coverage_rate": "상수도 보급률",
    "water_resilience_index": "물 회복력 지수",
    "emergency_water_idx": "비상급수시설 지수",
    "water_budget_ratio_norm": "상수도 예산비중",
    "pipe_index": "관로 노후도 지수",
    "mean_temp": "평균기온",
    "mean_humidity": "평균습도"
}


# min-max 정규화 + 범위 압축 0.2~1.0
scaled = df.copy()
for v in vars8:
    mn, mx = df[v].min(), df[v].max()
    if mn == mx:
        scaled[v] = 0.6
    else:
        scaled[v] = 0.2 + 0.8 * (df[v] - mn) / (mx - mn)

# 시(市) 4곳만 선택
regions = ["강릉", "속초", "원주", "춘천"]

plt.figure(figsize=(10, 8))

angles = np.linspace(0, 2*np.pi, len(vars8), endpoint=False).tolist()
angles += angles[:1]

colors = plt.cm.tab10(np.linspace(0, 1, len(regions)))

#방사형 레이더 차트 그리기
for region, color in zip(regions, colors):
    row = scaled[scaled["region"] == region].iloc[0]
    values = row[vars8].tolist()
    values += values[:1]

    plt.polar(angles, values, marker='o', color=color, label=region)
    plt.fill(angles, values, alpha=0.15, color=color)

#축 라벨
ticks = [korean[v] for v in vars8]
plt.xticks(angles[:-1], ticks, fontsize=10)

plt.legend(
    title="시 지역",
    loc="center left",
    bbox_to_anchor=(1.15, 0.5),
    fontsize=10
)

plt.title("2025년 9월 강원도 내 4개 도시 방사형 차트", fontsize=15)
plt.tight_layout()
plt.show()
