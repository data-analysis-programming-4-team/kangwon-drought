import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

#한글 폰트 (윈도우)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
#1 파일 경로
shp_path = r"TN_SIGNGU_BNDRY.shp"
idi_csv_path = r"2023_2025_IDI_result.csv"

#2. 시군구 경계 SHP 읽기
full_gdf = gpd.read_file(shp_path, encoding="euc-kr")

# 시군구 이름 컬럼 찾기
if "SIG_KOR_NM" in full_gdf.columns:
    name_col = "SIG_KOR_NM"
elif "ADMD_NM" in full_gdf.columns:
    name_col = "ADMD_NM"
elif "ADZONE_NM" in full_gdf.columns:
    name_col = "ADZONE_NM"
else:
    raise ValueError("시군구 이름 컬럼을 직접 지정해야 합니다.")

# 시도 컬럼 찾기 (강원도만 필터용)
sido_col = None
for c in full_gdf.columns:
    if "CTP" in c and "KOR" in c:
        sido_col = c
        break

gangwon_names = ["강원도", "강원특별자치도"]

if sido_col:
    gw_gdf = full_gdf[full_gdf[sido_col].isin(gangwon_names)].copy()
else:
    gw_candidates = ["강릉", "춘천", "원주", "속초", "삼척", "동해", "태백",
                     "홍천", "인제", "철원", "영월", "평창", "정선", "횡성",
                     "화천", "양구", "양양", "고성"]
    gw_gdf = full_gdf[
        full_gdf[name_col].str.replace("시","").str.replace("군","").isin(gw_candidates)
    ].copy()

#3 IDI 불러오기
idi_df = pd.read_csv(idi_csv_path)

# 4 특정 월 선택
target_month = "2025-09"
idi_month = idi_df[idi_df["month"] == target_month].copy()

# region → 시군구 이름 매핑
region_to_sgg = {
    "강릉": "강릉시",
    "속초": "속초시",
    "원주": "원주시",
    "춘천": "춘천시",
    "인제": "인제군",
    "철원": "철원군",
    "홍천": "홍천군",
}
idi_month["sgg_name"] = idi_month["region"].map(region_to_sgg)

merged = gw_gdf.merge(
    idi_month[["sgg_name", "IDI"]],
    how="left",
    left_on=name_col,
    right_on="sgg_name",
)

union_geom = unary_union(merged.geometry)
if isinstance(union_geom, MultiPolygon):
    main_poly = max(union_geom.geoms, key=lambda g: g.area)
else:
    main_poly = union_geom

# 각 시군구 geometry를 본토와 교차시켜서, 본토에 속하는 부분만 남김
merged["geometry"] = merged.geometry.intersection(main_poly)

# 시각화
fig, ax = plt.subplots(figsize=(8, 9))

# 색: IDI 낮음=빨강, 높음=파랑
merged.plot(
    column="IDI",
    ax=ax,
    cmap="RdYlBu",
    linewidth=0.0,        # 경계선 제거
    edgecolor="none",
    legend=True,
    missing_kwds={
        "color": "lightgrey",
        "edgecolor": "none",
        "hatch": None,
        "label": "IDI 데이터 없음",
    },
)

# 지역 이름은 시군/군당 딱 1번만 표시
# 같은 시군이 여러 폴리곤으로 나뉘어 있어도 하나로 합쳐서(해상도용) 중심점 계산
label_gdf = merged.dropna(subset=["IDI"]).dissolve(by=name_col, as_index=False)

for _, row in label_gdf.iterrows():
    x = row.geometry.centroid.x
    y = row.geometry.centroid.y
    label = str(row[name_col]).replace("시", "").replace("군", "")
    ax.text(
        x, y, label,
        ha="center", va="center",
        fontsize=9,
        color="black",
    )

ax.set_title(f"강원도 IDI 지도 ({target_month})", fontsize=16)
ax.axis("off")

plt.tight_layout()
plt.show()
