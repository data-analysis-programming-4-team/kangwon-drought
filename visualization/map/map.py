
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

# 한글 폰트 설정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# 파일 경로
shp_path = r"TN_SIGNGU_BNDRY.shp"
idi_csv_path = r"IDI_monthly_only (1).csv"

# SHP 읽기
full_gdf = gpd.read_file(shp_path, encoding="euc-kr")

# 시군구 이름 컬럼 자동 탐색
if "SIG_KOR_NM" in full_gdf.columns:
    name_col = "SIG_KOR_NM"
elif "ADMD_NM" in full_gdf.columns:
    name_col = "ADMD_NM"
elif "ADZONE_NM" in full_gdf.columns:
    name_col = "ADZONE_NM"
else:
    raise ValueError("시군구 이름 컬럼을 찾을 수 없습니다.")

# 강원도 지역만 선택
sido_col = None
for c in full_gdf.columns:
    if "CTP" in c and "KOR" in c:
        sido_col = c
        break

gangwon_names = ["강원도", "강원특별자치도"]

if sido_col:
    gw_gdf = full_gdf[full_gdf[sido_col].isin(gangwon_names)].copy()
else:
    gw_list = ["강릉","춘천","원주","속초","삼척","동해","태백",
               "홍천","인제","철원","영월","평창","정선","횡성",
               "화천","양구","양양","고성"]
    gw_gdf = full_gdf[
        full_gdf[name_col].str.replace("시","").str.replace("군","").isin(gw_list)
    ].copy()

# IDI 데이터 읽기
df = pd.read_csv(idi_csv_path)

if "IDI" in df.columns:
    idi_col = "IDI"
else:
    candidate_cols = [
        c for c in df.columns
        if "IDI" in c.upper() and "INFRA" not in c.upper()
    ]
    if not candidate_cols:
        raise ValueError("순수 IDI 컬럼을 찾을 수 없습니다.")
    idi_col = candidate_cols[0]

# 특정 월 선택
target_month = "2025-09"
idi_month = df[df["month"] == target_month].copy()

mapping = {
    "강릉": "강릉시",
    "속초": "속초시",
    "원주": "원주시",
    "춘천": "춘천시",
    "인제": "인제군",
    "철원": "철원군",
    "홍천": "홍천군",
}
idi_month["sgg_name"] = idi_month["region"].map(mapping)

# 지도 데이터와 병합
merged = gw_gdf.merge(
    idi_month[["sgg_name", idi_col]],
    how="left",
    left_on=name_col,
    right_on="sgg_name",
)

# 고성 남쪽 떨어진 조각 등 제거
union_geom = unary_union(merged.geometry)
if isinstance(union_geom, MultiPolygon):
    main_poly = max(union_geom.geoms, key=lambda g: g.area)
else:
    main_poly = union_geom

merged["geometry"] = merged.geometry.intersection(main_poly)

# 지도 시각화
fig, ax = plt.subplots(figsize=(8, 9))

vmin = -1.31
vmax = 0.85

merged.plot(
    column=idi_col,
    ax=ax,
    cmap="RdYlBu",
    linewidth=0.0,
    edgecolor="none",
    legend=True,
    vmin=vmin,
    vmax=vmax,
    missing_kwds={
        "color": "lightgrey",
        "edgecolor": "none",
        "label": "데이터 없음",
    },
)

# 지역 이름 1번만 표시
label_gdf = merged.dropna(subset=[idi_col]).dissolve(by=name_col, as_index=False)

for _, row in label_gdf.iterrows():
    x = row.geometry.centroid.x
    y = row.geometry.centroid.y
    txt = row[name_col].replace("시", "").replace("군", "")
    ax.text(x, y, txt, ha="center", va="center", fontsize=9, color="black")

ax.set_title(f"강원도 {idi_col} 지도 ({target_month})", fontsize=16)
ax.axis("off")

plt.tight_layout()
plt.show()
