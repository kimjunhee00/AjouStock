# /data/skyrocket.py
# 급등주 포착 알고리즘으로 구매할 종목 추천
import time
import datetime
import requests
import traceback
import pandas as pd
from bs4 import BeautifulSoup as bs


code_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header=0)[0]
code_df.종목코드 = code_df.종목코드.map('{:06d}'.format)
code_df = code_df[['회사명', '종목코드']]
code_df = code_df.rename(columns={'회사명': 'name', '종목코드': 'code'})
df_head = code_df.head(3)


code_list=[]
for i in range(len(df_head)):
    code = df_head.loc[i].code
    code_list.append(code)


class Skyrocket:
    def parsing(self, code, page):
        try:
            url = 'http://finance.naver.com/item/sise_day.nhn?code={code}&page={page}'.format(code=code, page=page)
            res = requests.get(url)

            soup = bs(res.text, 'lxml')
            dataframe = pd.read_html(str(soup.find("table")), header=0)[0]
            dataframe = dataframe.dropna()
            return dataframe
        except Exception as e:
            traceback.print_exc()
        return None


    def get_volume_df(self, code_list):
        for i in range(len(code_list)):
            code = code_list[i]
            url = 'http://finance.naver.com/item/sise_day.nhn?code={code}'.format(code=code)
            res = requests.get(url)
            res.encoding = 'utf-8'
            soup = bs(res.text, 'lxml')

            time.sleep(1.0)

            el_table_navi = soup.find("table", class_="Nnavi")
            el_td_last = el_table_navi.find("td", class_="pgRR")
            pg_last = el_td_last.a.get('href').rsplit('&')[1]
            pg_last = pg_last.split('=')[1]
            pg_last = int(pg_last)

            start_date = datetime.date.today() + datetime.timedelta(days=-26)
            start_date = datetime.datetime.strftime(start_date, '%Y.%m.%d')
            end_date = datetime.datetime.strftime(datetime.datetime.today(), '%Y.%m.%d')

            df_21 = None
            for page in range(1, pg_last+1):
                dataframe = self.parsing(code, page)
                dataframe_filtered = dataframe[dataframe['날짜'] > start_date]
                if df_21 is None:
                    df_21 = dataframe_filtered
                else:
                    df_21 = pd.concat([df_21, dataframe_filtered])
                if len(dataframe) > len(dataframe_filtered):
                    break

            df_21.columns = ["date", "close", "compare", "open", "high", "low", "volume"]
            df_21.drop(['close', 'compare', 'open', 'high', 'low'], axis=1, inplace=True)
            df_21['volume'] = df_21['volume'].astype(int)
            df_21 = df_21.round(0)
            df_21['date'] = pd.to_datetime(df_21.date)
            df_21 = df_21.sort_values(by='date', ascending=False)

            return(df_21)


    def check_skyrocket(self, df_21, code_list):
        df = self.get_volume_df(code_list)
        volumes = df['volume']

        if len(volumes) < 15:
            return False

        sum_vol14 = 0   # 일별 거래량 누적
        today_vol = 0   # 조회 시작일 거래량

        for i, vol in enumerate(volumes):
            if i == 0:
                today_vol = vol
            elif 1 <= i <= 14:
                sum_vol14 += vol
            else:
                break

        avg_vol14 = sum_vol14 / 14
        if today_vol > avg_vol14 * 10:
            return True
        else:
            return False


    def run(self, df_21, code_list):
        buy_list = []
        num = len(code_list)

        for i, code in enumerate(code_list):
            print(i, '/', num)
            if self.check_skyrocket(df_21, code_list):
                print(code_list[i], "is SKYROCKET!!!!!!!!!!!!!!!!!!")
                buy_list.append(code_list[i])
            else:
                print(code_list[i], "is nothing.")

        self.update_buy_list(buy_list)


    def update_buy_list(self, buy_list):
        f = open("buy_list.txt", "wt")
        for code in buy_list:
            f.writelines("매수;"+ code + ";시장가;10;0;매수전\n")   # 개수는 수정해야 함
        f.close()


    def update_sell_list(self, sell_list):
        f = open("sell_list.txt", "wt")
        for code in sell_list:
            f.writelines("매도;"+ code + ";시장가;10;0;매도전\n")
        f.close()


if __name__ == "__main__":
    sky = Skyrocket()
    df_21 = sky.get_volume_df(code_list)
    sky.run(df_21, code_list)


"""
* 급등주 포착 알고리즘
특정 거래일의 거래량이 이전 시점의 평균 거래량보다 1000% 이상 급증하는 종목을 매수
'이전 시점의 평균 거래량'을 특정 거래일 이전의 20일(거래일 기준) 동안의 평균 거래량으로 정의
'거래량 급증'은 특정 거래일의 거래량이 평균 거래량보다 1000% 초과일 때 급등한 것으로 정의
"""

# sk = Skyrocket()
# df_21 = sk.get_volume_df(code_list)
# sk.check_skyrocket(df_21, code_list)
# sk.run(df_21, code_list)