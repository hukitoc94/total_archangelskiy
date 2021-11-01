from GEE_scripts import MODIS_NDVI
import pandas as pd
import os
from parsing_climat import get_weather
from pandas.io.parsers import read_csv
from visualisation_scripts import weather_visualisation
import ee


class field_scale:
    """входные параметры - 
        start - дата начала отбора данных в формате YYYY-MM-DD
        finish - когда заканчивать отбирать данные в формате YYYY-MM-DD
        region_geometry - геометрия по которой будет происходить обрезка, для полевого уровня это просто полигон по которому
            обрезать формат geojson
        ROI - регионы нас интересующие - конкретные поля формат geojson
    """
    def __init__(self, start, finish, region_geometry, ROIs):
        ee.Initialize()
        self.start = start 
        self.finish = finish 
        self.region_geometry = region_geometry
        self.ROIs = ROIs

    def get_NDVI_by_ROIs(self, download = 'yes'):
        NDVI_df = MODIS_NDVI(self.start, self.finish, self.region_geometry, self.ROIs ) #получили данны NDVI
        self.NDVI_df = NDVI_df
        if download.lower() == 'no':
            return NDVI_df
        else:  
            NDVI_modis_filename = 'anual_data//NDVI//NDVI_modis.csv'
            if os.path.isfile(NDVI_modis_filename): 
                print(f'file {NDVI_modis_filename} alredy exists')
                NDVI_old = pd.read_csv(NDVI_modis_filename)
                NDVI_new = NDVI_df
                NDVI_new = NDVI_old.append(NDVI_new).drop_duplicates()
                NDVI_new.to_csv(path_or_buf=NDVI_modis_filename, index= False)
            else:
                NDVI_df.to_csv(path_or_buf=NDVI_modis_filename, index= False)
            return NDVI_df
    def anual_weather(self, url, download = 'yes', plot_data = "yes"):
        """ url - ссылка на архив с RP5
        на выход скачивается динамик погоды  
        climat_df - эти данные 
        """
        climat_data = get_weather(self.start, self.finish , url)
        self.climat_data = climat_data
        if download.lower() == 'no':
            pass
        else:
            weather_filename = 'anual_data/Weather/weather.csv'
            if os.path.isfile(weather_filename): 
                old_climat_data = read_csv(weather_filename)
                new_climat_data = climat_data
                new_climat_data = old_climat_data.append(new_climat_data).drop_duplicates()
                new_climat_data.to_csv(path_or_buf=weather_filename, index= False)
            else:
                climat_data.to_csv(path_or_buf=weather_filename, index= False)
        weather_plot = weather_visualisation(self.start,self.finish )
        if plot_data.lower() == 'no':
            pass
        else: 
            weather_plot.savefig(f'output/weather/weather_{self.start}_{self.finish}.jpg')
        return(climat_data, weather_plot)

            



        


        
        

        










    