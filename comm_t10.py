# To jest wersja 9 z Arima

import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import appdirs as ad
CACHE_DIR = ".cache"
# Force appdirs to say that the cache dir is .cache
ad.user_cache_dir = lambda *args: CACHE_DIR
# Create the cache dir if it doesn't exist
Path(CACHE_DIR).mkdir(exist_ok=True)
import yfinance as yf
from sklearn.linear_model import LinearRegression
from streamlit import set_page_config
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

# Set page configuration for full width
set_page_config(layout="wide")

# start definicji strony
st.title('The main global economy indicators and my own EUR/PLN D5 LSTM prediction model')

# Definicje
today = date.today()
comm_dict = {'EURUSD=X':'USD_EUR','CNY=X':'USD/CNY','CL=F':'Crude_Oil',
             '^DJI':'DJI30','GC=F':'Gold','^IXIC':'NASDAQ',
             '^GSPC':'SP_500','^TNX':'10_YB',
             'HG=F':'Copper','GBPUSD=X':'USD_GBP',
             'JPY=X':'USD_JPY','EURPLN=X':'EUR/PLN','PLN=X':'PLN/USD'
             ,'^FVX':'5_YB','RUB=X':'USD/RUB','PL=F':'Platinum',
             'SI=F':'Silver','NG=F':'Natural Gas','ZR=F':'Rice Futures',
             'ZS=F':'Soy Futures','KE=F':'KC HRW Wheat Futures'}

# Pobieranie danych
def comm_f(comm):
    global df_c1
    for label, name in comm_dict.items():
        if name == comm:
            df_c = pd.DataFrame(yf.download(f'{label}', start='2000-09-01', end = today,interval='1d'))
            df_c1 = df_c.reset_index()
           
    return df_c1   

# Dane historyczne                    
def comm_data(comm):
    global Tab_his1
    shape_test=[]
    sh = df_c1.shape[0]
    start_date = df_c1.Date.min()
    end_date = df_c1.Date.max()
    close_max = "{:.2f}".format(df_c1['Close'].max())
    close_min = "{:.2f}".format(df_c1['Close'].min())
    last_close = "{:.2f}".format(df_c1['Close'].iloc[-1])
    v = (comm, sh, start_date,end_date,close_max,close_min,last_close)
    shape_test.append(v)
    Tab_length = pd.DataFrame(shape_test, columns= ['Name','Rows', 'Start_Date', 'End_Date','Close_max','Close_min','Last_close'])   
    Tab_his = Tab_length[['Start_Date','End_Date','Close_max','Close_min','Last_close']]
    Tab_his['Start_Date'] = Tab_his['Start_Date'].dt.strftime('%Y-%m-%d')
    Tab_his['End_Date'] = Tab_his['End_Date'].dt.strftime('%Y-%m-%d')
    Tab_his1 = Tab_his.T
    Tab_his1.rename(columns={0: "Details"}, inplace=True)
    
    return Tab_his1

st.sidebar.title('Commodities, Indexies, Currencies & Bonds')
comm = st.sidebar.selectbox('What do you want to analyse today ?', list(comm_dict.values()))
comm_f(comm)
st.sidebar.write('You selected:', comm)
st.sidebar.dataframe(comm_data(comm))

# tu wstawimy wykresy 15 minutowe
def t1_f(char1):
    global tf_c1
    for label, name in comm_dict.items():
        if name == char1:
            box = yf.Ticker(label)
            tf_c = pd.DataFrame(box.history(period='1d', interval="1m"))
            tf_c1 = tf_c[-100:]
    return tf_c1 

def t2_f(char2):
    global tf_c2
    for label, name in comm_dict.items():
        if name == char2:        
            box = yf.Ticker(label)
            tf_c = pd.DataFrame(box.history(period='1d', interval="1m"))
            tf_c2 = tf_c[-100:]
    return tf_c2 


col1, col2 = st.columns([0.47, 0.53])
with col1:
    box = list(comm_dict.values())
    char1 = st.selectbox('Daily trading dynamics', box, index= box.index('Crude_Oil'),key = "<char1>")
    t1_f(char1)
    data_x1 = tf_c1.index
    fig_char1 = px.line(tf_c1, x=data_x1, y=['Open','High','Low','Close'],color_discrete_map={
                 'Open':'yellow','High':'red','Low':'blue','Close':'green'}, width=500, height=400) 
    fig_char1.update_layout(showlegend=False)
    fig_char1.update_layout(xaxis=None, yaxis=None)
    st.plotly_chart(fig_char1) #use_container_width=True
with col2:
    char2 = st.selectbox('Daily trading dynamics', box, index=box.index('PLN/USD'),key = "<char2>")
    t2_f(char2)
    data_x2 = tf_c2.index
    fig_char2 = px.line(tf_c2, x=data_x2, y=['Open','High','Low','Close'],color_discrete_map={
                 'Open':'yellow','High':'red','Low':'blue','Close':'green'}, width=500, height=400) 
    fig_char2.update_layout(showlegend=True)
    fig_char2.update_layout(xaxis=None, yaxis=None)
    st.plotly_chart(fig_char2)

# tutaj wprowadzamy kod do wykresów 
st.subheader(comm+' Prices in NYSE')
xy = (list(df_c1.index)[-1] + 1)  
col3, col4, col5 = st.columns([0.4, 0.3, 0.3])
with col3:
    oil_p = st.slider('How long prices history you need?', 0, xy, 100, key = "<commodities>")
with col4:
    nums = st.number_input('Enter the number of days for short average',value=30, key = "<m30>")
with col5:
    numl = st.number_input('Enter the number of days for long average',value=90, key = "<m35>")
    
def roll_avr(nums,numl):
    global df_c_XDays
    # Oblicz krótkoterminową i długoterminową średnią kroczącą
    df_c1['Short_SMA']= df_c1['Close'].rolling(window=nums).mean()
    df_c1['Long_SMA']= df_c1['Close'].rolling(window=numl).mean()
    
    # Generuj sygnały kupna i sprzedaży
    df_c1['Buy_Signal'] = (df_c1['Short_SMA'] > df_c1['Long_SMA']).astype(int).diff()
    df_c1['Sell_Signal'] = (df_c1['Short_SMA'] < df_c1['Long_SMA']).astype(int).diff()
     
    df_c_XDays = df_c1.iloc[xy - oil_p:xy]
      
    fig1 = px.line(df_c_XDays, x='Date', y=['Close','Short_SMA','Long_SMA'], color_discrete_map={'Close':'#d62728',
                  'Short_SMA': '#f0f921','Long_SMA':'#0d0887'}, width=900, height=400)
    fig1.add_trace(go.Scatter(x=df_c_XDays[df_c_XDays['Buy_Signal'] == 1].Date, y=df_c_XDays[df_c_XDays['Buy_Signal'] == 1]['Short_SMA'], name='Buy_Signal', mode='markers', 
                             marker=dict(color='green', size=15, symbol='triangle-up')))
    fig1.add_trace(go.Scatter(x=df_c_XDays[df_c_XDays['Sell_Signal'] == 1].Date, y=df_c_XDays[df_c_XDays['Sell_Signal'] == 1]['Short_SMA'], name='Sell_Signal',
                              mode='markers', marker=dict(color='red', size=15, symbol='triangle-down')))
    fig1.update_layout(xaxis=None, yaxis=None)
    st.plotly_chart(fig1, use_container_width=True)

roll_avr(nums,numl)
    
# Arima - model - prognoza trendu
def Arima_f(comm):
    data = np.asarray(df_c1['Close'][-300:]).reshape(-1, 1)
    p = 10
    d = 0
    q = 5
    n = size_a

    model = ARIMA(data, order=(p, d, q))
    model_fit = model.fit(method_kwargs={'maxiter': 3000})
    model_fit = model.fit(method_kwargs={'xtol': 1e-6})
    fore_arima = model_fit.forecast(steps=n)  
    
    arima_dates = [datetime.today() + timedelta(days=i) for i in range(0, size_a)]
    arima_pred_df = pd.DataFrame({'Date': arima_dates, 'Predicted Close': fore_arima})
    arima_pred_df['Date'] = arima_pred_df['Date'].dt.strftime('%Y-%m-%d')
    arima_df = pd.DataFrame(df_c1[['Date','High','Close']][-500:])
    arima_df['Date'] = arima_df['Date'].dt.strftime('%Y-%m-%d')
    arima_chart_df = pd.concat([arima_df, arima_pred_df], ignore_index=True)
    x_ar = (list(arima_chart_df.index)[-1] + 1)
    arima_chart_dff = arima_chart_df.iloc[x_ar - 30:x_ar]
    
    fig_ar = px.line(arima_chart_dff, x='Date', y=['High', 'Close', 'Predicted Close'], color_discrete_map={
                  'High': 'yellow', 'Close': 'black', 'Predicted Close': 'red'}, width=900, height=500)
    fig_ar.add_vline(x = today,line_width=3, line_dash="dash", line_color="green")
    fig_ar.update_layout(xaxis=None, yaxis=None)
    st.plotly_chart(fig_ar, use_container_width=True)      
    
# definicja wykresu obortów
def vol_chart(comm):
    volc = ['Crude_Oil','Gold','Copper','Platinum','Silver','Natural Gas','Rice Futures','Soy Futures','KC HRW Wheat Futures']
    if comm in volc:

        Co_V = df_c1[['Date', 'Volume']]
        Co_V['Co_V_M']= Co_V['Volume'].rolling(window=90).mean().fillna(0)
        V_end = (list(Co_V.index)[-1] + 1)

        st.subheader(comm+' Volume in NYSE')
        Vol = st.slider('How long prices history you need?', 0, V_end, 100, key = "<volume>") 
        Co_V_XD = Co_V.iloc[V_end - Vol:V_end]

        fig3 = px.area(Co_V_XD, x='Date', y='Volume',color_discrete_map={'Volume':'#1f77b4'})
        fig3.add_traces(go.Scatter(x= Co_V_XD.Date, y= Co_V_XD.Co_V_M, mode = 'lines', line_color='red'))
        fig3.update_traces(name='90 Days Mean', showlegend = False)

        st.plotly_chart(fig3, use_container_width=True)
     
vol_chart(comm)
                               
col6, col7 = st.columns(2)
with col6:
    checkbox_value3 = st.checkbox(f'Arima model trend prediction for x days',key = "<arima_m>")

if checkbox_value3:
    st.subheader(f'{comm} Arima model prediction')
    size_a = st.radio('Prediction for ... days ?: ', [5,4,3,2,1], horizontal=True, key = "<arima21>")
    Arima_f(comm)    

with col7:
    checkbox_value2 = st.checkbox(f'Own LSTM model EUR/PLN prediction for 5 days',key = "<lstm1>")

if checkbox_value2:
    st.subheader('Own LSTM EUR/PLN model prediction')
    val_oil = pd.read_excel('LSTM_mv.xlsx', sheet_name='D5_EUR')
    val_oil1 = val_oil[['Date','EUR/PLN','Day + 5 Prediction']] 
    fig_oil1 = px.line(val_oil1[-50:], x='Date', y=['EUR/PLN','Day + 5 Prediction'],color_discrete_map={
                 'EUR/PLN':'dodgerblue','Day + 5 Prediction':'red'}, width=1200, height=600, title=f'Day + 5 EUR/PLN prediction ') 
    fig_oil1.update_layout(plot_bgcolor='white',showlegend=True,xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='Lightgrey'),
                      yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='Lightgrey'))
    fig_oil1.add_vline(x = today,line_width=1, line_dash="dash", line_color="black")
    fig_oil1.add_annotation(x=today , y= ['Day + 5 Prediction'], text= f'Today - {today}', showarrow=False)
    st.plotly_chart(fig_oil1)
    