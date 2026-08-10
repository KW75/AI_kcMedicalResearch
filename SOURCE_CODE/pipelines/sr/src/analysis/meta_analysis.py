import numpy as np
import pandas as pd
from scipy import stats

class MetaAnalyzer:
    def run(self, data: pd.DataFrame, effect_measure: str = "OR") -> dict:
        df       = data.copy().reset_index(drop=True)
        is_ratio = effect_measure in ("OR","RR")
        if is_ratio:
            df["yi"]  = np.log(df["effect_estimate"].astype(float))
            df["se_i"]= (np.log(df["ci_upper"].astype(float)) -
                         np.log(df["ci_lower"].astype(float))) / (2*1.96)
        else:
            df["yi"]  = df["effect_estimate"].astype(float)
            df["se_i"]= (df["ci_upper"].astype(float) -
                         df["ci_lower"].astype(float)) / (2*1.96)
        df["vi"] = df["se_i"]**2
        wi       = 1.0/df["vi"].values
        fe_theta = np.sum(wi*df["yi"].values)/np.sum(wi)
        k   = len(df)
        Q   = float(np.sum(wi*(df["yi"].values-fe_theta)**2))
        df_ = k-1
        Q_p = float(1-stats.chi2.cdf(Q,df_))
        c   = float(np.sum(wi)-np.sum(wi**2)/np.sum(wi))
        tau2= max(0.0,(Q-df_)/c)
        wi_re    = 1.0/(df["vi"].values+tau2)
        theta_re = np.sum(wi_re*df["yi"].values)/np.sum(wi_re)
        se_re    = np.sqrt(1.0/np.sum(wi_re))
        ci_lo    = theta_re-1.96*se_re
        ci_hi    = theta_re+1.96*se_re
        z    = theta_re/se_re
        pval = float(2*(1-stats.norm.cdf(abs(z))))
        I2   = float(max(0.0,(Q-df_)/Q*100)) if Q>0 else 0.0
        if is_ratio:
            pooled,ci_low,ci_high = float(np.exp(theta_re)),float(np.exp(ci_lo)),float(np.exp(ci_hi))
        else:
            pooled,ci_low,ci_high = float(theta_re),float(ci_lo),float(ci_hi)
        df["weight_pct"] = (wi_re/np.sum(wi_re))*100
        return {"pooled_effect":pooled,"se":float(se_re),"ci_lower":ci_low,
                "ci_upper":ci_high,"z_score":float(z),"p_value":pval,
                "tau2":float(tau2),"Q":Q,"df":df_,"Q_p":Q_p,"I2":I2,
                "k":k,"effect_measure":effect_measure,"study_effects":df}
