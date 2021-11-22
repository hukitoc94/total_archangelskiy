
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import geopandas as gpd
import pandas as pd
import warnings
warnings.simplefilter('ignore')

import time


def get_station_id(ROI):
    """geometry - маска геометрий

       closest_station - ближайшкая метеостанция  
    """
    ROI = gpd.read_file('fields.geojson')

    geometry = ROI.dissolve(by = "farmer_land_name").reset_index()
    lon = geometry.centroid[0].x
    lat = geometry.centroid[0].y

    #исходная БД с данными о ID метеостанций и их координаты 
    stations = pd.read_csv('meteostations_codes.txt', sep = '\t', names = ['station_№', 'name','lat','lon','elev','country']) 
    stations['lat'] = stations['lat'].str.replace(',','.').astype(float)
    stations['lon'] = stations['lon'].str.replace(',','.').astype(float)
    #в этом куске мы считаем евклидово растояние от центральной точки до ближайшей метеостанции - не совсем корректно и очень грубо но  это не главное 
    stations['lat'] = abs(abs(stations['lat']) - lat)
    stations['lon'] = abs(abs(stations['lon']) - lon)
    stations['distance_km'] =  (((stations['lat']**2) + (stations['lon']**2)) ** 0.5) * 111
    closest_station = stations.sort_values(by = ['distance_km']).reset_index()['station_№'][0]
    return(closest_station)


def get_weather(first, last, closest_station ):
    """first - с какого числа
        last - по акое число 
        closest_station - номер метеостанции
    """
    first = first.split('-')
    first = first[2] + '.' + first[1] + '.' + first[0]
    last = last.split('-')
    last = last[2] + '.' + last[1] + '.' + last[0]

    URL = "https://rp5.ru/%D0%90%D1%80%D1%85%D0%B8%D0%B2_%D0%BF%D0%BE%D0%B3%D0%BE%D0%B4%D1%8B_%D0%BD%D0%B0_%D0%BE._%D0%9F%D0%B0%D1%81%D1%85%D0%B8,_%D0%9C%D0%B0%D1%82%D0%B0%D0%B2%D0%B5%D1%80%D0%B8_(%D0%B0%D1%8D%D1%80%D0%BE%D0%BF%D0%BE%D1%80%D1%82)"



    driver = webdriver.Chrome()
    driver.get(url=URL)

    station_field = driver.find_element_by_id("wmo_id")
    station_field.clear()
    station_field.send_keys(closest_station.astype('str'))
    time.sleep(1)

    station_field.send_keys(Keys.ENTER)

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
    time.sleep(2) #надо пофиксить на фуннкцию ожидания до того момента пока не появится линк
    link =  driver.find_element_by_link_text("Скачать").get_property('href')
    driver.close()
    data = pd.read_csv(link ,sep=';' , comment= "#" ,encoding="ANSI", index_col=False  )
    return(data)

def prepair_weather(weather_data):
    df = weather_data.copy()
    df['RRR'] = df['RRR'].fillna(0)
    df['RRR'][df['RRR'].isin(["Осадков нет",'Следы осадков'])] = 0
    df['RRR'] = pd.to_numeric(df['RRR'])

    df["sss"] = df["sss"].fillna(0)
    df["sss"][df["sss"].isin(['Снежный покров не постоянный.','Менее 0.5'])] = 0.1
    df['sss'] = pd.to_numeric(df['sss'])

    T = df[["date" , "T"]].groupby('date', axis = 0).mean().reset_index()
    Percipitation = df[["date" , "RRR"]].groupby('date', axis = 0).sum().reset_index()
    Snow = df[['date', 'sss']].groupby('date', axis = 0).mean().reset_index()
    weather = pd.DataFrame(T['date'])
    weather['mean_temperature'] = T['T']
    weather['sum_percepetation'] = Percipitation['RRR']
    weather['snow'] = Snow['sss']
    return(weather)






        

