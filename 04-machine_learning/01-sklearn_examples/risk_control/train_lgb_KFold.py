import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
from sklearn import metrics
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import GradientBoostingClassifier 
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif,chi2
from sklearn.feature_selection import SelectKBest, SelectPercentile
import xgboost as xgb
import lightgbm as lgb
from sklearn.model_selection import KFold, train_test_split, GridSearchCV



def impute_NA_with_avg(data,strategy='mean',NA_col=[]):
    """
    replacing the NA with mean/median/most frequent values of that variable. 
    Note it should only be performed over training set and then propagated to test set.
    """
    
    data_copy = data.copy(deep=True)
    for i in NA_col:
        if data_copy[i].isnull().sum()>0:
            if strategy=='mean':
                data_copy[i+'_impute_mean'] = data_copy[i].fillna(data[i].mean())
            elif strategy=='median':
                data_copy[i+'_impute_median'] = data_copy[i].fillna(data[i].median())
            elif strategy=='mode':
                data_copy[i+'_impute_mode'] = data_copy[i].fillna(data[i].mode()[0])
        else:
            warn("Column %s has no missing" % i)
    return data_copy  




data_path = "data/train.csv"
label_path = "data/train_target.csv"
predict_data_path = "data/test.csv"

df = pd.read_csv(data_path)
df_label  = pd.read_csv(label_path)
df_predict  = pd.read_csv(predict_data_path)

print (df) 
column_headers = list( df.columns.values )
# print(column_headers)


train_data = pd.merge(df, df_label, how='left', on=['id'])

# 全为缺失值删除
train_data.dropna(how='all') 
# 缺失值进行填充
train_data = impute_NA_with_avg(train_data, column_headers) 

df_predict = impute_NA_with_avg(df_predict, column_headers) 

train_data.fillna(0, inplace = True) 
df_predict.fillna(0, inplace = True) 


print (train_data)
column_headers = list( train_data.columns.values )
print(column_headers)

x_columns = [x for x in train_data.columns if x not in ["target", "id"]]
# x_columns = ['certId', 'loanProduct', 'gender', 'age', 'dist', 'edu', 'job', 'lmt', 'basicLevel', 'x_14', 'x_16', 'x_20', 'x_29', 'x_33', 'x_34', 'x_43', 'x_44', 'x_45', 'x_46', 'x_47', 'x_49', 'x_51', 'x_52', 'x_54', 'x_55', 'x_61', 'x_62', 'x_63', 'x_67', 'x_68', 'x_71', 'x_72', 'x_75', 'x_76', 'certValidBegin', 'certValidStop', 'bankCard', 'ethnic', 'residentAddr', 'highestEdu', 'linkRela', 'setupHour', 'weekday']
# AUC Score (Train): 

X = train_data[x_columns]
y = train_data["target"] 


X_predict = df_predict[x_columns]
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.3, random_state=0)
X_train, y_train = X, y


n_splits = 7
kf = KFold(n_splits=n_splits, shuffle=True, random_state=1234)
max_auc = 0
'''
    params = {
        'task': 'train',
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'metric':'auc',
        'num_leaves': 25,
        'learning_rate': 0.01,
        'feature_fraction': 0.7,
        'bagging_fraction': 0.7,
        'bagging_freq': 5,
        'min_data_in_leaf':5,
        'max_bin':200,
        'verbose': 0,
    }
'''
for train_index, test_index in kf.split(X_train):
    print ( ">>>", train_index )
    gbm = lgb.LGBMClassifier(boosting_type='gbdt',  min_data_in_leaf=5, max_bin=200, num_leaves=25, learning_rate=0.01)
    gbm_model = gbm.fit(X_train.iloc[train_index], y_train.iloc[train_index]) 

    y_pred = gbm_model.predict(X_train.iloc[test_index]) 
    y_predprob = gbm_model.predict_proba(X_train.iloc[test_index])[:, 1] 
    print (y_predprob)

    print("Accuracy : %.4g" % metrics.accuracy_score(y_train.iloc[test_index].values, y_pred))  
    auc = metrics.roc_auc_score(y_train.iloc[test_index], y_predprob)
    print("AUC Score (Train): %f" % auc) 

    if auc > max_auc:
        max_auc = auc
        print ("auc>>>>>>", auc)
        y_pp = gbm_model.predict_proba(X_predict)[:, 1] 
        # print (y_pp)
        c ={ "target" : y_pp }
        data_lable = DataFrame(c)#将字典转换成为数据框
        # print ( data_lable )
        id_list = df_predict["id"].tolist()
        # print ( id_list )


        d ={ "id" : id_list, "target" : y_pp  }
        res = DataFrame(d)#将字典转换成为数据框
        print (">>>>", res)
        csv_file = 'lgb_res/res_lgb_kfold' + str(n_splits) + '_'  + str(auc) + '.csv'
        res.to_csv( csv_file ) 

