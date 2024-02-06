# -*- coding = utf-8 -*-

import warnings
import pandas as pd
import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
# plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.size'] = 22
plt.rcParams["figure.autolayout"] = True
mpl.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')

from Connect_Database.connect_database import ConnectDatabase

def industry_distribution_tool(data):
    """
    :param data: 日期，股票代码，权重，行业代码，一级行业代码
    """
    df = data.copy()
    # 计算每个日期下不同行业的股票权重和
    df_grouped = df.groupby(['date', 'industry_name'])['weight'].sum().unstack().fillna(0)
    # 获取行业列表和颜色字典
    industries = df['industry_name'].unique()
    colors = cm.get_cmap('tab20', len(industries)) # 根据实际行业进行修改，tab20有20中颜色，wind一级行业11个，够用

    bottom = None  # 用于追踪每个行业的底部起始位置
    plt.figure(figsize=(30,10))
    for i, industry in enumerate(industries):
        values = df_grouped[industry]
        plt.bar(df_grouped.index, values, bottom=bottom, label=industry, color=colors(i), width=1)

        if bottom is None:
            bottom = values
        else:
            bottom += values

    # 设置图形标题和轴标签
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(12))
    # plt.subplots_adjust(left=0.3, right=0.7, bottom=0.1, top=0.9)
    plt.title('Industry Weight Distribution')
    plt.xlabel('Date')
    plt.ylabel('Weight(%)')
    plt.legend(fontsize=11, loc='best')
    plt.xticks(rotation=30)

    # 显示图形
    plt.show()

if __name__ == '__main__':
    root = '/'
    start_date = '20230101'
    end_date = datetime.today().strftime('%Y%m%d')
    data_start_date = datetime.strptime(start_date, '%Y%m%d').date() - timedelta(days=700)
    data_start_date = data_start_date.strftime('%Y%m%d')
    assets = ['000300.SH']

    # 指数及成分股日行情数据
    temp_dict = dict()
    for asset in assets:
        # 筛选 指数 成分股每日权重及对应的行业代码
        sql1 = f'''
               SELECT A.S_CON_WINDCODE, A.TRADE_DT, A.I_WEIGHT, B.WIND_IND_CODE 
               FROM AINDEXHS300CLOSEWEIGHT A, ASHAREINDUSTRIESCLASS B 
               WHERE  A.TRADE_DT >= {start_date} AND A.S_CON_WINDCODE = B.S_INFO_WINDCODE   
               AND ((A.TRADE_DT BETWEEN B.ENTRY_DT AND  B.REMOVE_DT) OR (A.TRADE_DT >= B.ENTRY_DT AND B.CUR_SIGN = 1))
               '''
        cd1 = ConnectDatabase(sql1)
        data = cd1.get_data()
        data = data.rename(columns={'S_CON_WINDCODE': 'symbol', 'TRADE_DT': 'date',
                                    'I_WEIGHT': 'weight', 'WIND_IND_CODE': 'industry'})
        data = data.sort_values(['symbol', 'date']).copy()
        # data[data.columns[2:]] = (data[data.columns[2:]].apply(pd.to_numeric))
        data['1st_industry'] = data.industry.str[:4]

        # 筛选一级行业代码对应的行业
        sql2 = f'''
                SELECT INDUSTRIESCODE, INDUSTRIESNAME
                FROM ASHAREINDUSTRIESCODE
                WHERE INDUSTRIESCODE LIKE '62%' AND LEVELNUM = 2
        '''
        cd2 = ConnectDatabase(sql2)
        industry_code = cd2.get_data()
        industry_code.rename(columns={'INDUSTRIESCODE': 'industry_code', 'INDUSTRIESNAME': 'industry_name'}, inplace=True)
        industry_code['1st_industry'] = industry_code['industry_code'].str[:4]
        result = pd.merge(data, industry_code, on='1st_industry')
        industry_distribution_tool(result)
