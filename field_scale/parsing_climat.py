
from selenium import webdriver
import pandas as pd
import warnings
warnings.simplefilter('ignore')

import time

def get_weather(first, last, url ):
    driver = webdriver.Chrome()
    driver.get(url=url)
    driver.find_element_by_id("tabSynopDLoad").click()
    driver.find_element_by_xpath(".//*[contains(text(), 'CSV (текстовый)')]").click()
    time.sleep(3)
    first_date = driver.find_element_by_id("calender_dload")
    first_date.clear()
    first_date.send_keys(first)
    last_date = driver.find_element_by_id('calender_dload2')
    last_date.clear()
    last_date.send_keys(last)
    time.sleep(3)
    driver.find_element_by_xpath(".//*[contains(text(), 'Выбрать в файл GZ')]").click()
    time.sleep(5)


    link =  driver.find_element_by_link_text("Скачать").get_property('href')

    driver.close()

    data = pd.read_csv(link ,sep=';' , comment= "#" ,encoding="ANSI", index_col=False  )
    data[['date', 'time']] = data.iloc[:, 0].str.split(' ' , expand = True)
    data = data[['date', 'time', 'T', 'RRR']]
    data['RRR'] = data['RRR'].fillna(0)
    data['RRR'][data['RRR'].isin(["Осадков нет",'Следы осадков'])] = 0
    data['RRR'] = pd.to_numeric(data['RRR'])
    T = data[["date" , "T"]].groupby('date', axis = 0).mean().reset_index()
    Percipitation = data[["date" , "RRR"]].groupby('date', axis = 0).sum().reset_index()
    weather = pd.DataFrame(T['date'])
    weather['mean_temperature'] = T['T']
    weather['sum_percepetation'] = Percipitation['RRR']

    return(weather)




        

