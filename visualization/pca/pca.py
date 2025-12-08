import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import platform

def set_korean_font():
    if platform.system() == 'Darwin':      # macOS
        plt.rc('font', family='AppleGothic')
    elif platform.system() == 'Windows':   # Windows
        plt.rc('font', family='Malgun Gothic') 
    else:                                  # Linux / Colab
        plt.rc('font', family='NanumGothic')
    plt.rcParams['axes.unicode_minus'] = False

def load_merge():
    idi = pd.read_csv("IDI_monthly_only.csv")              # region, month, IDI, IDI_with_infra
    climate = pd.read_csv("climate_indices.csv")           # 지역명, 년월, 평균기온
    humid = pd.read_csv("humidity_monthly.csv")            # region, ym, mean_humidity
    infra = pd.read_csv("infra_index.csv")                

    climate = climate.rename(columns={
        "지역명": "region",
        "년월": "month",
        "평균기온": "mean_temp"
    })

    humid = humid.rename(columns={
        "ym": "month"
    })

    # 지역명 통일
    name_map = {
        "강릉": "강릉시",
        "속초": "속초시",
        "원주": "원주시",
        "춘천": "춘천시",
        "홍천": "홍천군",
        "철원": "철원군",
        "인제": "인제군",
    }
    idi["region_std"] = idi["region"].map(name_map)
    climate["region_std"] = climate["region"].map(name_map)
    humid["region_std"] = humid["region"].map(name_map)
    infra["region_std"] = infra["region"] 

    # 머지 (IDI + 기온 + 습도 + 인프라)
    df = (
        idi
        .merge(climate[["region_std", "month", "mean_temp"]],
            on=["region_std", "month"], how="left")
        .merge(humid[["region_std", "month", "mean_humidity"]],
            on=["region_std", "month"], how="left")
        .merge(infra[["region_std", "infra_index", "pipe_index",
                    "emergency_water_idx", "water_resilience_index",
                    "coverage_rate_norm", "water_budget_static_idx"]],
            on="region_std", how="left")
    )

    return df

    #print(df.head())


def pca_start(df):

    # pca 사용할 변수
    features = [
        "infra_index",
        "pipe_index",
        "emergency_water_idx",
        "water_resilience_index",
        "coverage_rate_norm",
        "water_budget_static_idx",
        "mean_temp",
        "mean_humidity",
        "IDI",
        "IDI_with_infra",
    ]

    X = df[features].dropna()  #결측 제거
    print("PCA 대상 행 수:", len(X))

    #표준화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)


    #pca
    pca = PCA(n_components=len(features))
    pca_result = pca.fit_transform(X_scaled)

    # 결과 DataFrame으로 정리
    pca_df = pd.DataFrame(
        pca_result,
        columns=[f"PC{i+1}" for i in range(len(features))]
    )

    # 메타 정보
    valid_idx = X.index
    meta = df.loc[valid_idx, ["region", "month", "region_std"]].reset_index(drop=True)
    pca_df = pd.concat([meta, pca_df], axis=1)

    pca_df.to_csv("PCA_result_panel.csv", index=False)
    
    return pca, pca_df, features

# 설명분산 그래프

def plot_explained_variance(pca):
    n_comp = len(pca.explained_variance_ratio_)
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, n_comp + 1), pca.explained_variance_ratio_, marker="o")
    plt.xlabel("Principal Component")
    plt.ylabel("Explained Variance Ratio")
    plt.title("설명 분산 비율 그래프")
    plt.grid(True)
    plt.show()
    
def plot_loadings(pca, features):
    
    varname_ko = {
        "infra_index": "인프라 지수",
        "pipe_index": "관로노후도",
        "emergency_water_idx": "비상급수시설",
        "water_resilience_index": "정수지/배수지 용량",
        "coverage_rate_norm": "상수도 보급률",
        "water_budget_static_idx": "상수도 예산비중",
        "mean_temp": "기온",
        "mean_humidity": "습도",
        "IDI": "IDI",
        "IDI_with_infra": "IDI.infra"
    }

    loadings = pd.DataFrame(
        pca.components_.T,
        index=features,
        columns=[f"PC{i+1}" for i in range(len(features))]
    )

    loadings_ko = loadings.copy()
    loadings_ko.index = [varname_ko[v] for v in loadings.index]

    plt.figure(figsize=(10,6))
    sns.heatmap(loadings_ko.iloc[:, :3], annot=True, cmap="coolwarm")
    plt.title("PCA 변수 기여도 (PC1~PC3)")
    plt.show()

    #PC1 vs PC2 지역별 산점도
def plot_pc_scatter(pca_df):
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=pca_df, x="PC1", y="PC2", hue="region_std")
    plt.title("PCA (PC1 vs PC2)")
    plt.grid(True)
    plt.show()

#총 10개 변수 중 PC1~PC3가 전체 변동의 약 81%를 설명한다.
#따라서 PC1~PC3만으로도 대부분의 패턴을 요약할 수 있다.

if __name__ == "__main__":
    set_korean_font()

    df = load_merge()

    pca, pca_df, features = pca_start(df)

    plot_explained_variance(pca)
    plot_loadings(pca, features)
    plot_pc_scatter(pca_df)