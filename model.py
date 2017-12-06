""" Prediction Model Training """

# Standard Python Library
import sqlite3
# Third Party Library
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense, Dropout

def show_train_history(train_history, train, validation):
    """ 繪圖訓練過程 """
    plt.plot(train_history.history[train])
    plt.plot(train_history.history[validation])
    plt.title('Train History')
    plt.ylabel('train')
    plt.xlabel('Epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.show()

def normalize_data(values):
    """ 資料標準化 """
    minimum = np.min(values)
    maximum = np.max(values)
    return (values - minimum) / float(maximum - minimum)

def preprocess_data(raw_df):
    """ 資料預處理 """

    # 去除有 null 的資料
    dframe = raw_df.dropna()
    cols = ['總價元', '建物型態', '主要用途', '主要建材', '建物移轉總面積平方公尺', '建物現況格局-隔間', '建物現況格局-房', '有無管理組織',
            '親友間交易', '含增建', 'LAT_Avg', 'LON_Avg']

    # 過濾資料欄位
    dframe = dframe[cols]
    # 將 DataFrame 轉成 array
    ndarray = dframe.values
    # 將第 0 個欄位(總價元)存入 label
    label = ndarray[:, 0]
    # 將第 1 個欄位以後的欄位都存入 features
    features = ndarray[:, 1:]
    # 標準化 label
    label = normalize_data(label)
    return features, label

def accuracy(result):
    """ 計算準確率 """
    accurate = 0
    origin = result['總價元']
    origin = origin.values
    prediction = result['prediction']
    prediction = prediction.values
    row_number = len(result.index)
    for i in range(row_number):
        if (origin[i] > 0) and (prediction[i] > 0):
            if (float(prediction[i]) / float(origin[i]) >= 0.75) and\
               (float(prediction[i]) / float(origin[i]) <= 1.25):
                accurate += 1
    return float(accurate) / float(row_number)

def main():
    """ Main Function """
    # 連接資料庫
    conn = sqlite3.connect("resources/main.db")
    # 使用 pandas 函式將目標資料存入 df(DataFrame)
    dframe = pd.read_sql_query('''SELECT * FROM '101S4/BUILD' AS ai0
                                  JOIN '101S4/TRX' AS ai1
                                  ON ai0.編號 = ai1.編號
                                  JOIN '101S4/GEO' AS ai2
                                  ON ai1.編號 = ai2.編號
                                  WHERE ai1.縣市 = '臺北市';''', conn)

    msk = np.random.rand(len(dframe)) < 0.8
    # 將部分資料存入訓練資料
    train_df = dframe[msk]
    # 將另一部分資料存入測試資料
    test_df = dframe[~msk]

    # 訓練資料預處理
    train_features, train_label = preprocess_data(train_df)
    # 測試資料預處理
    test_features, test_label = preprocess_data(test_df)

    # 建立 model
    model = Sequential()
    # 加入神經層, units=40 代表輸出 40 個神經元, imput_dim=11 代表訓練資料有 11 個features
    model.add(Dense(units=40, input_dim=11, kernel_initializer='uniform', activation='relu'))
    # 加入神經層
    model.add(Dense(units=30, kernel_initializer='uniform', activation='relu'))
    # 加入神經層
    model.add(Dense(units=1, kernel_initializer='uniform', activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    train_history = model.fit(x=train_features, y=train_label, validation_split=0.1, epochs=30,
                              batch_size=30, verbose=2)

    # 測試的結果存入 scores array
    scores = model.evaluate(x=test_features, y=test_label)
    # 資料預處理
    features, _ = preprocess_data(dframe)
    # 使用建好的 model 進行預測, 將結果存入 all_probability
    all_prediction = model.predict(features)
    cols = ['編號', '總價元', '建物型態', '主要用途', '主要建材', '建物移轉總面積平方公尺', '建物現況格局-隔間', '建物現況格局-房', '有無管理組織',
            '親友間交易', '含增建', 'LAT_Avg', 'LON_Avg']
    df_result = dframe.dropna()
    df_result = df_result[cols]
    # 將預測結果加入到欄位中
    df_result.insert(len(df_result.columns), 'prediction', all_prediction)
    maximum = df_result['總價元'].max()
    minimum = df_result['總價元'].min()
    # 將標準化過後的預測結果還原
    df_result['prediction'] = df_result['prediction'] * (maximum - minimum) + minimum
    # 印出前五項資料
    print(df_result[:5])
    # 印出準確率
    print(accuracy(df_result))

if __name__ == "__main__":
    main()
