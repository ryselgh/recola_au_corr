import re
import warnings
from os import listdir
from os.path import isfile, join
from scipy import stats
import numpy as np
import sklearn.preprocessing as skl
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from pandas.plotting import autocorrelation_plot as acf_plot
from pandas.plotting import lag_plot
import matplotlib.pyplot as plt
import matplotlib as mpl
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf

#initialization:
register_matplotlib_converters()
warnings.filterwarnings("ignore")
mpl.rcParams['figure.dpi'] = 1200
scaler = skl.MinMaxScaler(feature_range=(-1, 1), copy=False)

valence_path = './emotional_behaviour/valence/'
arousal_path = './emotional_behaviour/arousal/'
val_gs_path = './emotional_behaviour/gold_standard/valence/'
aro_gs_path = './emotional_behaviour/gold_standard/arousal/'
au_path = './AU_reindex/'
index_name = 'time'
gs_key = ['gold standard']

va_cols = ['FM1','FM2','FM3','FF1','FF2','FF3']
au_cols = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU06_r', 'AU07_r', 'AU09_r', 'AU10_r', 'AU12_r', 'AU14_r', 'AU15_r', 'AU17_r', 'AU20_r', 'AU23_r', 'AU25_r', 'AU26_r', 'AU45_r']

valence_csv = [f for f in listdir(valence_path) if isfile(join(valence_path, f))]
arousal_csv = [f for f in listdir(arousal_path) if isfile(join(arousal_path, f))]
au_csv = [f for f in listdir(au_path) if isfile(join(au_path, f))]

valence = []
for csv_file in valence_csv:
    new_valence = pd.read_csv(valence_path + csv_file, sep=';')
    new_valence.columns = new_valence.columns.str.replace(' ', '')
    valence.append(new_valence)
for x in valence:
    x.index = x[index_name]
    x.drop(x.columns.difference(va_cols), 1, inplace=True)
    
val_ewe = []
for csv_file in valence_csv:
    new_val_ewe = pd.read_csv(val_gs_path + csv_file, sep=',')
    val_ewe.append(new_val_ewe)    
for x in val_ewe:
    x.index = x[index_name]
    x.drop([index_name], 1, inplace=True)
    
val_train = pd.DataFrame(columns=gs_key)
#set number of series to concatenate for training set
train_range = 2
for i in range(train_range): #default=12
    temp_df = pd.DataFrame(val_ewe[i])
    temp_df.index = temp_df.index + 300*i
    val_train = val_train.append(temp_df)
val_valid = pd.DataFrame(columns=gs_key)
for i in range(train_range, 14):
    temp_df = pd.DataFrame(val_ewe[i])
    temp_df.index = temp_df.index + 300*i
    val_valid = val_valid.append(temp_df)

arousal = []
for csv_file in arousal_csv:
    new_arousal = pd.read_csv(arousal_path + csv_file, sep=';')
    new_arousal.columns = new_arousal.columns.str.replace(' ', '')
    arousal.append(new_arousal)
for x in arousal:
    x.index = x[index_name]
    x.drop(x.columns.difference(va_cols), 1, inplace=True)
    
aro_ewe = []
for csv_file in arousal_csv:
    new_aro_ewe = pd.read_csv(aro_gs_path + csv_file, sep=',')
    aro_ewe.append(new_aro_ewe)
for x in aro_ewe:
    x.index = x[index_name]
    x.drop([index_name], 1, inplace=True)
    
aro_train = pd.DataFrame(columns=gs_key)
for i in range(train_range):
    temp_df = pd.DataFrame(aro_ewe[i])
    temp_df.index = temp_df.index + 300*i
    aro_train = aro_train.append(temp_df)
aro_valid = pd.DataFrame(columns=gs_key)
for i in range(train_range, 14):
    temp_df = pd.DataFrame(aro_ewe[i])
    temp_df.index = temp_df.index + 300*i
    aro_valid = aro_valid.append(temp_df)
    
au = []
for csv_file in au_csv:
    new_au = pd.read_csv(au_path + csv_file, sep=',')
    new_au.columns = new_au.columns.str.replace(' ', '')
    au.append(new_au)
for x in au:
    x.index = x[index_name]
    x.index.names = [index_name]
    x.drop(x.columns.difference(au_cols), 1, inplace=True)
    scaler.fit(np.array((0, 5)).reshape(-1, 1))
    for col in au_cols:
        scaler.transform(x[col].values.reshape(-1, 1))

au_train = pd.DataFrame(columns=au_cols)
for i in range(train_range):
    temp_au_df = pd.DataFrame(au[i])
    temp_au_df.index = temp_au_df.index + 300*i
    au_train = au_train.append(temp_au_df)
au_valid = pd.DataFrame(columns=au_cols)
for i in range(train_range, 14):
    temp_au_df = pd.DataFrame(au[i])
    temp_au_df.index = temp_au_df.index + 300*i
    au_valid = au_valid.append(temp_au_df)


#functions:
def plot_data(data, ylabel, title, show_ewe=False, va_ewe=None, fs=8):
    for col in data.columns:
        plt.plot(data[col], label=col)
    title = re.sub(r'(.txt|.csv)', '', title)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xlabel(data.index.names[0])
    
    if show_ewe:
        plt.plot(va_ewe, color='black', linewidth=2, label="EWE")
        
    plt.legend(loc='best', fontsize=fs)
    plt.show()

def plot_ewe():
    for i in range(len(valence)):
        plot_data(valence[i], 'valence', valence_csv[i] + ': Evaluator Weighted Estimator', show_ewe=True, va_ewe=val_ewe[i])
    for i in range(len(arousal)):
        plot_data(arousal[i], 'arousal', arousal_csv[i] + ': Evaluator Weighted Estimator', show_ewe=True, va_ewe=aro_ewe[i])

def get_stationarity(data, win, ylabel, can_plot=True):
    
    # rolling statistics
    rolling_mean = data.rolling(window = win).mean()
    rolling_std = data.rolling(window = win).std()
    
    # plot
    if can_plot:
        plt.plot(data, color = 'lightblue', label = 'Original')
        plt.plot(rolling_mean, color = 'orange', label = 'Rolling Mean')
        plt.plot(rolling_std, color = 'darkred', label = 'Rolling Std')
        plt.legend(loc = 'best')
        plt.title('Rolling Mean & Rolling Standard Deviation')
        plt.ylabel(ylabel + ' (gold std)')
        plt.xlabel(index_name)
        plt.show()

    # Dickey–Fuller test:
    result = adfuller(data.iloc[:,0].values)
    """print('------- ' + ylabel + ' -------')
    print('ADF Statistic: {}'.format(result[0]))
    print('p-value: {}'.format(result[1]))
    print('Critical Values:')"""
    for key, value in result[4].items():
        print('\t{}: {}'.format(key, value))
    print('')
    
def get_aug_stationarity(data, significance=0.05):
    
    p_value = None
    is_stationary = None

    #Dickey-Fuller test:
    adf_test = adfuller(data.iloc[:,0].values, autolag='AIC')
    
    p_value = adf_test[1]
    
    if (p_value < significance):
        is_stationary = True
    else:
        is_stationary = False
    
    results = pd.Series(adf_test[0:4], index=['ADF Test Statistic','P-Value','# Lags Used','# Observations Used'])

    #Add Critical Values
    for key,value in adf_test[4].items():
        results['Critical Value (%s)'%key] = value

    """ print('Augmented Dickey-Fuller Test Results:')
    print(results)
    print('Is the time series stationary? {0}'.format(is_stationary))"""
    
    return adf_test[2]
    
def get_all_stationarity(win, can_plot=True):
    for i in range(len(val_ewe)):
        print('---- File: ' + valence_csv[i] + ' ----' )
        get_stationarity(val_ewe[i], win, 'valence', can_plot)
        get_stationarity(aro_ewe[i], win, 'arousal', can_plot)
        print('')

def plot_ACF(df, custom_title=''):
    minus_shift = df - df.shift()
    minus_shift.dropna(inplace=True)
    df = minus_shift
    custom_title = re.sub(r'(.txt|.csv)', '', custom_title)
    plot_acf(df, ax=plt.gca(), lags=range(50), title=custom_title+'Partial Autocorrelation')
    plt.show()
    
def plot_PACF(df, custom_title=''):
    minus_shift = df - df.shift()
    minus_shift.dropna(inplace=True)
    df = minus_shift
    custom_title = re.sub(r'(.txt|.csv)', '', custom_title)
    plot_pacf(df, ax=plt.gca(), lags=range(50), title=custom_title+'Partial Autocorrelation')
    plt.show()

def plot_ACF_PACF(df):
    plot_ACF(df)
    plot_PACF(df)

#AR,0,0
#AR: PACF
#fit -> theta, alpha
"""We're usign SARIMAX"    
def apply_ARIMA(data, ylabel, p=2, d=1, q=2, exogenous=None, plot=True, test=False):
    model = ARIMA(data[gs_key], order=(p,d,q), exog=exogenous)
    #fit esegue il template del modello con p=p' d=d' q=q'
    results = model.fit(disp=-1)
    print("Parameters")   
    aic = results.aic
    print(results.aic)
    if test:
        print(results.summary())
    #print(results.mean_squared_error)
    
    if plot:
        minus_shift = data - data.shift()
        #minus_shift.dropna(inplace=True) 
        plt.figure(figsize=(15,5))
        plt.plot(minus_shift, color='lightblue', label = 'minus shift', linewidth=0.1)
        plt.plot(results.fittedvalues, color='red', label = 'ARIMA', linewidth=0.1)
        plt.legend(loc = 'best')
        plt.title('ARIMA model')
        plt.ylabel(ylabel)
        plt.xlabel(index_name)
        plt.show()
        print('End')
        predictions_ARIMA_diff = pd.Series(results.fittedvalues, copy=True)
        predictions_ARIMA_diff_cumsum = predictions_ARIMA_diff.cumsum()
        predictions_ARIMA_log = pd.Series(data[gs_key].iloc[0], index=data.index)
        predictions_ARIMA_log = predictions_ARIMA_log.add(predictions_ARIMA_diff_cumsum, fill_value=0)
        predictions_ARIMA = np.exp(predictions_ARIMA_log) - 1
        plt.plot(data, label='original')
        plt.plot(predictions_ARIMA, label='ARIMA prediction')
        plt.legend(loc = 'best')
        plt.title('ARIMA Predictions')
        plt.ylabel(ylabel)
        plt.xlabel(index_name)
        plt.show()
    return aic
   
    
def auto_ARIMA(df, moving_average=0, exogenous=None, plot=True, p=3):
    lag = get_aug_stationarity(df)
    plot_PACF(df)
    #print('Applying ARIMA with order=({0},1,0)'.format(lag))
    #apply_ARIMA(df, 'arousal', p=lag, d=1, q=moving_average, exogenous=exogenous)
    print('Applying ARIMA with order=({0},1,0)'.format(p))
    apply_ARIMA(df, 'valence', p=p, d=1, q=moving_average, exogenous=exogenous, test=True)
#start ARIMA for 3 video of arousal and calculate the mean of AIC.
#Repeat for p = {3,5,7,9}   
def auto_ARIMA_all(moving_average=0):
    #len(valence_csv)
    aics_mean = []
    p_array = [3,5,7,9]
    for x in range(len(p_array)):
        
        aics = []
        for i in range(3):
            print('\n---- File: ' + valence_csv[i] + ' ----\n\n')
            print('------- valence -------')
            df_val = val_ewe[i]
            
            "Not used"
            "lag = get_aug_stationarity(df_val)"
            plot_PACF(df_val, custom_title='['+valence_csv[i]+'] Valence ')
            print('Applying ARIMA with order=({0},1,{1})'.format(p_array[x], moving_average))
            aic = apply_ARIMA(df_val, 'valence', p=p_array[x], d=1, q=moving_average, exogenous=au[i].values, plot=False)
            aics.append(aic)
            
            
            not used
            print('------- arousal -------')
            df_aro = aro_ewe[i]
            lag = get_aug_stationarity(df_aro)
            plot_PACF(df_aro, custom_title='['+valence_csv[i]+'] Arousal ')
            print('Applying ARIMA with order=({0},1,{1})'.format(lag, moving_average))
            apply_ARIMA(df_aro, 'arousal', p=lag, d=1, q=moving_average)
            
            
            
        print('\n---- Average ----\n\n')
        print("AIC values")
        print(aics)
        
        print("Average AIC")
        print(np.mean(a=aics))
        aics_mean.append(np.mean(a=aics))
    print(aics_mean)
    print('Min AICs for p = [3,5,7,9]')
    print('minimum Avg AIC at p:')
    print(np.argmin(a=aics_mean))
    print('minimum AIC value:')
    print(np.amin(a=aics_mean))
    return np.argmin(a=aics_mean)"""

def apply_SARIMAX(data, ylabel, p, d=1, q=0, exogenous=None, season_period=300, plot=True, test=False):
   
    print('Applying SARIMAX with order=({0},1,{1}), season period: {2}'.format(p, q, season_period))   
    model = SARIMAX(data[gs_key], exog=exogenous, order=(p,d,q), seasonal_order=(1,1,0,season_period))
    #fit esegue il template del modello con p=p' d=d' q=q'
    results = model.fit(disp=-1)
    print("Parameters")   
    aic = results.aic
    print(results.aic)
    print(results.summary())
    return aic
    
def auto_SARIMAX_train(moving_average=0, season_period=300):
    
     p_array = [3,5,7,9]
     aics = []
     print('Start to predict series')
     for x in range(len(p_array)):
         print('Predictions with p={0}'.format(p_array[x]))
         aic = apply_SARIMAX(aro_train, 'arousal', p=p_array[x], d=1, q=moving_average, exogenous=au_train.values, season_period=season_period, plot=False)
         aics.append(aic)
     print('AICs for p = [3,5,7,9]')    
     print(aics)
     print('minimum Avg AIC at p:')
     print(p_array[np.argmin(a=aics)])
     return p_array[np.argmin(a=aics)]
#data analysis:
""" Copy-Paste precompiled functions:

plot_data(valence[0], 'valence', valence_csv[0])
plot_data(arousal[0], 'arousal', arousal_csv[0])
plot_data(au[0], 'AU', au_csv[0])

plot_ewe()

get_stationarity(val_ewe[0], 1000, 'valence (gold std)')
get_stationarity(aro_ewe[0], 1000, 'arousal (gold std)')
get_stationarity(aro_ewe[1], 1000, 'arousal (gold std)')

get_all_stationarity(1000)
get_all_stationarity(1000, can_plot=False)

apply_ARIMA(au, 0, au_cols[0], 'AU')
apply_ARIMA(valence, 0, va_cols[0], 'valence')
apply_ARIMA(arousal, 0, va_cols[0], 'arousal')

for i in range(len(au)):
    plot_data(au[i], 'AU', au_csv[i], fs=3)
plot_ewe()
get_all_stationarity(1000)

apply_ARIMA(aro_ewe, 0, 'gold standard', 'arousal (ewe)')
"""


"""
df1 = df1.combine_first(aro_ewe[1])
df1 = df1.merge(aro_ewe[1], left_index=True, right_index=True)
df1.drop(df1.columns.difference(au_cols), 1, inplace=True)

df2 = df2.combine_first(aro_ewe[1])
df2 = df2.merge(aro_ewe[1], left_index=True, right_index=True)
df2.drop(df2.columns.difference(au_cols), 1, inplace=True)

df1[df1.isnull()] = df2.values
print(df1)
plt.plot(df1[au_cols[0]])
"""
#plot_data(au[1], 'AU', au_csv[0])
#print(au[1])
#print(len(au[1]))
#pd.set_option('display.max_rows', df1.shape[0]+1)
#print(df1)
#auto_ARIMA(aro_ewe[1], exogenous=au[1].values)
#best_p = auto_ARIMA_all()

"""show an example of test with ARIMA(best_p,1,0) on video p21
print('ARIMA  with best p on test video P21')
best_p=3
auto_ARIMA(val_ewe[4], exogenous=au[4].values, p=best_p)
"""
"""
plot_data(val_train, 'valence', '12/14 merged EWE for ARIMA training')
plot_data(val_valid, 'valence', 'Last 2 merged EWE for ARIMA validation')
plot_data(aro_train, 'arousal', '12/14 merged EWE for ARIMA training')
plot_data(aro_valid, 'arousal', 'Last 2 merged EWE for ARIMA validation')
plot_data(aro_train, 'arousal', '12/14 merged EWE for ARIMA training')
plot_data(aro_valid, 'arousal', 'Last 2 merged EWE for ARIMA validation')
"""

plt.figure(figsize=(30,5))
plt.plot(val_train, color='blue', label='training set')
#plt.plot(val_valid, color='orange', label='validation set')
plt.plot(au_train['AU01_r'], color='red', label='AU01')
plt.plot(au_valid['AU01_r'], color='red')
plt.title('Merged EWE for ARIMA training')
plt.ylabel('valence')
plt.xlabel('time')
plt.legend(loc='best')
plt.show()

plt.figure(figsize=(30,5))
plt.plot(aro_train, color='blue', label='training set')
plt.plot(aro_valid, color='orange', label='validation set')
plt.plot(au_train['AU01_r'], color='red', label='AU01')
plt.plot(au_valid['AU01_r'], color='red')
plt.title('Merged EWE for ARIMA training')
plt.ylabel('arousal')
plt.xlabel('time')
plt.legend(loc='best')
plt.show()

#season_period = 300
best_p = auto_SARIMAX_train()
print("End")
