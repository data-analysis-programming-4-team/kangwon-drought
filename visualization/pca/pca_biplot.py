
import matplotlib.pyplot as plt

from pca import (
    set_korean_font,
    load_merge,
    pca_start,
)

def pca_biplot():
    #폰트
    set_korean_font()

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
        "IDI_with_infra": "IDI.infra",
    }

    # data load, pca 수행
    df = load_merge()
    pca, pca_df, features = pca_start(df)


    loadings_2d = pca.components_[0:2, :].T   # (변수 개수, 2)

    # 화살표 길이 스케일 조정
    x_max = pca_df["PC1"].abs().max()
    y_max = pca_df["PC2"].abs().max()
    arrow_scale = 1.1 * min(x_max, y_max)

    for i, feat in enumerate(features):
        x_vec = loadings_2d[i, 0] * arrow_scale
        y_vec = loadings_2d[i, 1] * arrow_scale

        # 화살표(원점 → 변수 방향)
        plt.arrow(0, 0, x_vec, y_vec,
                width=0.01, head_width=0.08, head_length=0.1,
                length_includes_head=True, alpha=0.8)

        #화살표 끝부분에 변수명 표시
        label = varname_ko.get(feat, feat)
        plt.text(x_vec * 1.05, y_vec * 1.05, label,
                fontsize=9, ha="center", va="center")

    plt.axhline(0, color="grey", linewidth=0.8)
    plt.axvline(0, color="grey", linewidth=0.8)
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.legend(title="지역", loc="best")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    pca_biplot()