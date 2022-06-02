from itertools import count
from cv2 import sort
import pandas as pd
import numpy as np
import cmath

def pretreat(old_model,new_model,gold_std):
    """
    This function only detects whether input is suitable for the following function.
    The code in the 'improveProb' function of R package 'Hmisc' and
    'reclassification' function of R package 'PredictABEL' are referred:
    
    https://github.com/harrelfe/Hmisc/edit/master/R/rcorrp.cens.s    started from line 67
    
    https://github.com/cran/PredictABEL/blob/master/R/PredictABEL.R  started from line 1316
   
    Args:
        old_model (_type_): old_model is an array of probability generated by new model.
        new_model (_type_): new_model is an array of probability generated by existing model.
        gold_std (_type_): real status collected.
    Note:
        this progress automaticlly delete NA
    """    
    try:
        dic={"old_model":old_model,
             "new_model":new_model,
             "gold_std":gold_std}
        df = pd.DataFrame(dic)
        df = df.dropna(how='any',axis=0)
        df = df.sort_values(by = "gold_std",ascending = True)  
        y  = df["gold_std"].astype('int')
        n  = len(y)
        u  = y.unique()
    except:
        print("input format is wrong")
        
    else:
        print("input format is corret")
        if len(u) != 2 or u[0] != 0 or u[1] != 1:
            print("gold_std must have two values: 0 and 1")
        else:
            if  max(df["old_model"])<1 and min(df["old_model"])>0 and max(df["new_model"])<1 and min(df["new_model"])>0:
                print("inputs are within suitable range")
                return(df,n)
            else:
                print('old_model and new_model must be between 0 and 1')            


def nri_cal(df,n):
    """
    The following articles are referred:
    
    1.Pencina MJ, D'Agostino RB Sr, Steyerberg EW. Extensions of net reclassification
    improvement calculations to measure usefulness of new biomarkers.
    Stat Med. 2011 Jan 15;30(1):11-21.
    doi: 10.1002/sim.4085. Epub 2010 Nov 5. PMID: 21204120; PMCID: PMC3341973.
    
    2.Kerr KF, Wang Z, Janes H, McClelland RL, Psaty BM, Pepe MS. Net reclassification
    indices for evaluating risk prediction instruments: a critical review. Epidemiology.
    2014 Jan;25(1):114-21. doi: 10.1097/EDE.0000000000000018. PMID: 24240655; PMCID: PMC3918180.
    
    3.Pencina MJ, D'Agostino RB Sr, D'Agostino RB Jr, Vasan RS. Evaluating the added 
    predictive ability of a new marker: from area under the ROC curve to reclassification 
    and beyond. Stat Med. 2008 Jan 30;27(2):157-72; discussion 207-12. 
    doi: 10.1002/sim.2929. PMID: 17569110.
    
    4.Confidence Intervl is calculated referred to:
    https://cdn-links.lww.com/permalink/ede/a/ede_25_1_2013_09_25_kerr_ede13-166_sdc1.pdf

    Args:
        df (_type_): dataframe generated by pretreat function.
        n (_type_): number generated by pretreat function, which is the count of all the samples.
    """    
    n=n
    value_summry = df['gold_std'].value_counts(ascending=True)

    a = df[df.gold_std == 1].index.tolist() #index of 1
    b = df[df.gold_std == 0].index.tolist() #index of 0

    na = value_summry[1] # count of result is 1
    nb = value_summry[0] # count of result is 0
    
    d = df['new_model']-df['old_model']
    
    nup_ev = sum(d[a] > 0)  
    nup_ne = sum(d[b] > 0)
    ndown_ev = sum(d[a] < 0)
    ndown_ne = sum(d[b] < 0)
    
    pup_ev = nup_ev/na 
    pup_ne = nup_ne/nb
    pdown_ev = ndown_ev/na
    pdown_ne = ndown_ne/nb    
    
    nri_ev = pup_ev - pdown_ev   #event NRI
    v_nri_ev = (nup_ev + ndown_ev)/(na^2) - ((nup_ev - ndown_ev)^2)/(na^3)
    se_nri_ev = cmath.sqrt(v_nri_ev) #SE of NRI of events
    z_nri_ev = nri_ev/se_nri_ev #Z score for NRI of events
    
    nri_ne = pdown_ne - pup_ne #nonevent NRI
    v_nri_ne = (ndown_ne + nup_ne)/(nb^2) - ((ndown_ne - nup_ne)^2)/(nb^3)
    se_nri_ne = cmath.sqrt(v_nri_ne) #SE of NRI of non-events
    z_nri_ne = nri_ne/se_nri_ne #Z score for NRI of non-events
    
    nri = pup_ev - pdown_ev - (pup_ne - pdown_ne)
    se_nri = cmath.sqrt(v_nri_ev + v_nri_ne) #standard error of NRI
    z_nri  = nri/se_nri #Z score for NRI

    
    improveSens =  sum(d[a])/na
    improveSpec = -sum(d[b])/nb
    idi = np.mean(d[a]) - np.mean(d[b]) #Integrated Discrimination Index
    var_ev = np.var(d[a])/na
    var_ne = np.var(d[b])/nb
    se_idi = cmath.sqrt(var_ev + var_ne) #SE of IDI
    z_idi = idi/se_idi #Z score of IDI
    
    dataoutput={"total_sample number":n, 
                "number of patients":na, 
                "number of healthy people":nb, 
                "fraction of new predicts positive while old predicts negaitve in patients":pup_ev,
                "fraction of new predicts positive while old predicts negaitve in healthy":pup_ne,
                "fraction of new predicts negative while old predicts positive in patients":pdown_ev,
                "fraction of new predicts negative while old predicts positive in healthy":pdown_ne,
                "Net Reclassification Index(NRI)":nri,
                "standard error of NRI":se_nri,   
                "Z score for NRI":z_nri,
                "event NRI" :nri_ev, 
                "SE of NRI of events":se_nri_ev,
                "Z score for NRI of events":z_nri_ev,
                "nonevent NRI":nri_ne,
                "SE of NRI of non-events":se_nri_ne,
                "Z score for NRI of non-events":z_nri_ne,
                "improvement in sensitivity":improveSens,
                "improvement in specificity":improveSpec,
                "se.idi":idi, 
                "Z score of IDI":z_idi}
    data= pd.DataFrame(dataoutput,index=[0])
    

    
    return data


if __name__ == '__main__':
    example=pd.read_csv(r"C:\Users\mjdee\Desktop\example.csv")
    old_model = example['old_model']
    new_model = example['new_model']
    gold_std = example['gold_std']
    dic={"old_model":old_model,
         "new_model":new_model,
         "gold_std":gold_std}


    df,y=pretreat(old_model,new_model,gold_std)
    data= nri_cal(df,y)
    data.to_csv(r"C:\Users\mjdee\Desktop\nri_result.csv")
    #print(ndown_ev,ndown_ne)
