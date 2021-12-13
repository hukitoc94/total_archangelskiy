import pandas as pd
import geopandas as gpd
import os
from parsing_climat import get_weather, get_station_id, prepair_weather
from pandas.io.parsers import read_csv
from visualisation_scripts import weather_visualisation
import ee
from GEE_scripts import MODIS_NDVI, DZZ_collection





class field_scale:
    """входные параметры - 
        start - дата начала отбора данных в формате YYYY-MM-DD
        finish - когда заканчивать отбирать данные в формате YYYY-MM-DD
        region_geometry - геометрия по которой будет происходить обрезка, для полевого уровня это просто полигон по которому
            обрезать формат геопандас
        ROI - регионы нас интересующие - конкретные поля формат геопандас
    """
    def __init__(self, start, finish, ROIs, region_geometry):
        ee.Initialize()
        self.start = start 
        self.finish = finish 
        self.region_geometry = region_geometry

        self.ROIs = ROIs
     #  self.ROIs_copy = ROIs.copy() #одна версия будет исходной и она и будет передаваться для скачивания данных 


    def get_NDVI_by_ROIs(self, download = 'yes'):
        NDVI_df = MODIS_NDVI(self.start, self.finish, self.region_geometry, self.ROIs ) #получили данны NDVI
        self.NDVI_df = NDVI_df
        if download.lower() == 'no':
            pass
        else:  
            NDVI_modis_filename = 'anual_data//NDVI//NDVI_modis.csv'
            if os.path.isfile(NDVI_modis_filename): 
                print(f'file {NDVI_modis_filename} alredy exists')
                NDVI_old = pd.read_csv(NDVI_modis_filename)
                NDVI_new = NDVI_df
                NDVI_new = NDVI_old.append(NDVI_new).drop_duplicates()
                NDVI_new.to_csv(path_or_buf=NDVI_modis_filename, index= False)
                self.NDVI_df = NDVI_df
            else:
                NDVI_df.to_csv(path_or_buf=NDVI_modis_filename, index= False)
                self.NDVI_df = NDVI_df

    def anual_weather(self,  download = 'yes', plot_data = "yes"):
        """ url - ссылка на архив с RP5
        на выход скачивается динамик погоды  
        climat_df - эти данные 
        """

        station_id = get_station_id(self.region_geometry)
        self.climat_data = get_weather(self.start, self.finish , station_id)
        print(self.climat_data.head(10))
        self.climat_data = prepair_weather(self.climat_data)
        if download.lower() == 'no':
            pass
        else:
            weather_filename = 'anual_data/Weather/weather.csv'
            if os.path.isfile(weather_filename): 
                old_climat_data = read_csv(weather_filename)
                new_climat_data = self.climat_data
                new_climat_data = old_climat_data.append(new_climat_data).drop_duplicates()
                new_climat_data.to_csv(path_or_buf=weather_filename, index= False)
            else:
                self.climat_data.to_csv(path_or_buf=weather_filename, index= False)
        if plot_data.lower() == 'no':
            pass
        else: 
            weather_plot = weather_visualisation(self.start,self.finish )
            weather_plot.savefig(f'output/weather/weather_{self.start}_{self.finish}.jpg')
        return(self.climat_data)
    
    def get_collection(self):
        preparing = DZZ_collection(self.start ,self.finish)
        preparing.get_sattelit_collection('sentinel2', self.region_geometry, self.region_geometry)
        preparing.DownloadImages()
        #self.download_minNDTI = preparing.Download_minNDTI()
        

          









        


        
        

        










    