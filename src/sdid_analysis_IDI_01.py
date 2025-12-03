import numpy as np
import pandas as pd
from scipy.optimize import minimize
import os

try:
    import matplotlib
    matplotlib.use('Agg') 
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
except ImportError:
    print("오류: Matplotlib이 설치되어 있지 않거나 import에 실패함.")
    exit()

# --- 사용자 설정 영역 ---
TARGET_UNIT = '강릉'
FILE_PATH = "IDI_monthly_only01.csv"
TREATMENT_START_TIME = "202404"  # 정책 시행 시점 (YYYYMM)
OUTCOME_VAR = 'IDI'             # 분석 대상 결과 변수
FONT_PATH = "C:\\Users\\PC\\project\\kangwon-drought\\src\\LG_SMART_UI-REGULAR.TTF"
FONT_NAME = fm.FontProperties(fname=FONT_PATH).get_name()
# ----------------------------------------


class SDID:
    def __init__(self, df, unit_col, time_col, outcome_col, target_unit, t_start):
        self.df = df
        self.unit_col = unit_col
        self.time_col = time_col
        self.outcome_col = outcome_col
        self.target_unit = target_unit
        self.t_start = t_start
        self.unit_weights = None
        self.synthetic_outcome_corrected = None
        self.att = None
        
    def fit(self):
        # 데이터 피벗
        df_pivot = self.df.pivot(index=self.time_col, columns=self.unit_col, values=self.outcome_col).sort_index()
        all_units = df_pivot.columns.tolist()
        
        # 다중 대조군 자동 식별: 선택된 지역을 제외한 모든 지역
        control_units = [u for u in all_units if u != self.target_unit]
        
        pre_data = df_pivot[df_pivot.index < self.t_start]
        
        # 정책 시행 이전 처치 그룹 값과 대조군 값 추출
        Y_pre_target = pre_data[self.target_unit].values 
        Y_pre_control = df_pivot[control_units].loc[pre_data.index].values
        
        n_controls = len(control_units)
        if n_controls == 0:
             raise ValueError(f"'{self.target_unit}'을 제외하고 사용할 대조군 유닛이 데이터에 존재하지 않음.")
        
        # Unit Weights 최적화
        def loss_w(w):
            # Y_pre_control @ w는 다수의 대조군을 가중 결합한 가상의 추이(대조군). L2로 정규화
            diff = Y_pre_target - (Y_pre_control @ w)
            return np.sum(diff**2) + 1e-6 * np.sum(w**2) 

        # 제약조건: 가중치 합은 1, 모든 가중치는 0 이상
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1) for _ in range(n_controls)]
        w0 = np.ones(n_controls) / n_controls
        res = minimize(loss_w, w0, bounds=bounds, constraints=constraints, method='SLSQP')
        
        # 계산된 최적 가중치를 대조군 지역 이름과 함께 저장
        self.unit_weights = pd.Series(res.x, index=control_units) 
        self.df_pivot = df_pivot
        return self

    def estimate_att(self):
        if self.unit_weights is None:
             self.fit()
             
        # 전체 기간에 대한 대조군 결과 생성     
        Y_control_all = self.df_pivot[self.unit_weights.index].values
        # 정책이 없었을 경우의 가상의 결과
        synthetic_outcome = Y_control_all @ self.unit_weights.values
        
        real_outcome = self.df_pivot[self.target_unit].values
        time_index = self.df_pivot.index
        post_mask = time_index >= self.t_start
        
        # 정책 이전 기간의 실제 처치 값과 합성 추이 값의 평균 차이
        pre_gap = np.mean(real_outcome[~post_mask] - synthetic_outcome[~post_mask])
        # 보정된 합성 추이 값 (pre_gap를 bias 보정값으로 활용)
        self.synthetic_outcome_corrected = synthetic_outcome + pre_gap
        
        # 최종 ATT(정책 효과) 계산
        self.att = np.mean((real_outcome - self.synthetic_outcome_corrected)[post_mask])
        
        return self.att

    def plot_and_save(self):
        if self.att is None:
            self.estimate_att()
        plt.rc('font', family=FONT_NAME)
        plt.figure(figsize=(10, 6))
        
        plt.plot(self.df_pivot.index, self.df_pivot[self.target_unit], 
                 label=f'실제 처치군: {self.target_unit}', color='black', linewidth=2)
        
        plt.plot(self.df_pivot.index, self.synthetic_outcome_corrected, 
                 label='합성 대조군', color='red', linestyle='--', linewidth=2)
        
        plt.axvline(x=self.t_start, color='gray', linestyle=':', label=f'정책 시행 ({self.t_start})')
        
        plt.title(f"[SDID Analysis for {self.target_unit}] ATT = {self.att:.4f}")
        plt.xlabel("시각 (YYYYMM)")
        plt.ylabel(self.outcome_col)
        plt.ylim(-2,2)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        file_name = f"SDID_Analysis_{self.target_unit}.png"
        try:
            plt.savefig(file_name)
            print(f"그래프가 '{file_name}' 파일로 성공적으로 저장됨. 파일을 열어 확인.")
        except Exception as save_e:
            print(f"파일 저장 오류: {save_e}")

if __name__ == "__main__":
    if not os.path.exists(FILE_PATH):
        print(f"오류: 파일을 찾을 수 없음. {FILE_PATH}를 확인.")
    else:
        # 데이터 로드 및 전처리 (유효 지역 목록 추출)
        df_raw = pd.read_csv(FILE_PATH)
        
        # YYYYMM 형식의 time 컬럼 생성
        df_raw['month_str'] = df_raw['month_num'].astype(str).str.zfill(2)
        df_raw['time'] = df_raw['year'].astype(str) + df_raw['month_str']
        df_clean = df_raw[['region', 'time', OUTCOME_VAR]].copy()
        
        # 파일에 있는 모든 지역 목록 추출
        all_regions = sorted(df_clean['region'].unique().tolist())
        
        if TARGET_UNIT not in all_regions:
            print(f"오류: '{TARGET_UNIT}'은 파일에 존재하는 유효한 지역이 아님.")
            print(f"유효한 지역 목록: {all_regions}")
        elif len(all_regions) < 2:
            print("오류: 분석에는 최소 2개 이상의 지역 데이터가 필요.")
        else:
            print(f"==============================================")
            print(f"SDID 분석 시작: {TARGET_UNIT} (총 {len(all_regions) - 1}개 대조군 활용)")
            print(f"==============================================")
            
            try:
                # SDID 모델 실행
                sdid_model = SDID(
                    df_clean, 
                    unit_col='region', 
                    time_col='time', 
                    outcome_col=OUTCOME_VAR, 
                    target_unit=TARGET_UNIT, 
                    t_start=TREATMENT_START_TIME
                )
                
                att = sdid_model.estimate_att()
                
                print(f"**추정된 평균 처치 효과 (ATT) on {OUTCOME_VAR}: {att:.4f}**")
                print("\n가중치가 부여된 대조군 유닛 (0.1% 이상):")
                
                # 가중치 출력
                weights = sdid_model.unit_weights[sdid_model.unit_weights > 0.001].sort_values(ascending=False)
                print(weights if not weights.empty else "가중치 0.001 이상의 유의미한 대조군 없음.")
                
                # 그래프 저장 함수 호출
                sdid_model.plot_and_save()

            except Exception as e:
                print(f"{TARGET_UNIT} 분석 중 치명적인 오류 발생:")
                print("오류 내용:", e)