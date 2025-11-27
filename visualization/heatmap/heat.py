import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ===== 한글 폰트 =====
plt.rcParams["font.family"] = "Malgun Gothic"   # 지금 잘 나오는 폰트 그대로
plt.rcParams["axes.unicode_minus"] = False

# ===== 1. 데이터 불러오기 =====
csv_path = r"IDI_monthly_only (1).csv"  # 경로/이름 맞게 수정
df = pd.read_csv(csv_path)

print("컬럼 확인:", df.columns)

# ===== 2. 히트맵에 사용할 컬럼 이름 =====
idi_col = "IDI_with_infra" # IDI 보고싶으면 IDI로 바꾸기
print("사용할 지표 컬럼:", idi_col)

# ===== 3. month / region 정리 =====
# month가 '2023-01' 같은 문자열이라고 가정
# 정렬된 월 순서 만들기
month_order = sorted(df["month"].unique())

# region 순서는 알파벳/가나다 순으로
region_order = sorted(df["region"].unique())

# ===== 4. 피벗 테이블 만들기 (행=지역, 열=월) =====
pivot = df.pivot_table(
    index="region",
    columns="month",
    values=idi_col
)

# 순서 정렬
pivot = pivot.loc[region_order, month_order]

# ===== 5. 히트맵 그리기 =====
fig, ax = plt.subplots(figsize=(len(month_order) * 0.8, len(region_order) * 0.6))

# 낮을수록 빨강, 높을수록 파랑 유지 → 'RdYlBu'
im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlBu")

# 축 라벨 (월 / 지역)
ax.set_xticks(np.arange(len(month_order)))
ax.set_yticks(np.arange(len(region_order)))

ax.set_xticklabels(month_order, rotation=45, ha="right")
ax.set_yticklabels(region_order)

ax.set_xlabel("2023-01 ~ 2025-10")
ax.set_ylabel("지역")
ax.set_title("IDI_with_infra 월별 히트맵")

# 컬러바
cbar = fig.colorbar(im, ax=ax)
cbar.set_label(idi_col)

# ===== 6. 값 숫자도 함께 표기하고 싶으면 (선택) =====
for i in range(len(region_order)):
    for j in range(len(month_order)):
        val = pivot.values[i, j]
        if pd.notna(val):
            ax.text(
                j, i, f"{val:.2f}",
                ha="center", va="center",
                fontsize=7, color="black"
            )

plt.tight_layout()
plt.show()

