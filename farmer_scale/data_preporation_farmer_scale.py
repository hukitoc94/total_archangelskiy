import pandas as pd
import geopandas as gpd
import os
from parsing_climat import get_weather, get_station_id, prepair_weather
from pandas.io.parsers import read_csv
from visualisation_scripts import weather_visualisation, PCA_k_means_visualisation
import ee
from GEE_scripts import MODIS_NDVI, DZZ_collection



class farmer_scale:
    """входные параметры - 
        start - дата начала отбора данных в формате YYYY-MM-DD
        finish - когда заканчивать отбирать данные в формате YYYY-MM-DD
        region_geometry - геометрия по которой будет происходить обрезка, для полевого уровня это просто полигон по которому
            обрезать формат geojson
        ROI - регионы нас интересующие - конкретные поля формат geojson
    """
    def __init__(self, start, finish, ROIs, region_geometry):
        ee.Initialize()
        self.start = start 
        self.finish = finish 
        self.region_geometry = region_geometry

        self.ROIs = ROIs
        self.ROIs_copy = ROIs.copy() #одна версия будет исходной и она и будет передаваться для скачивания данных 
        self.farmer_lands_name = ROIs.farmer_land_name.unique()[0]

    def get_NDVI_by_ROIs(self, download = 'yes'):
        NDVI_df = MODIS_NDVI(self.start, self.finish, self.region_geometry, self.ROIs_copy ) #получили данны NDVI
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

                
    def cluster_data(self, plot_data = "yes"):
        NDVI_plot , self.NDTI_start, self.season, self.cluster = PCA_k_means_visualisation(self.NDVI_df, self.start, self.finish, self.region_geometry,self.ROIs, self.farmer_lands_name)
        if plot_data.lower() == 'no':
            pass
        else: 
            NDVI_plot.savefig(f'output/NDVI_NDTI_plots/NDVI_{self.farmer_lands_name}_по_кластерам_{self.season}.jpg')
    
    
    
    def anual_weather(self,  download = 'yes', plot_data = "yes"):
        """ url - ссылка на архив с RP5
        на выход скачивается динамик погоды  
        climat_df - эти данные 
        """

        station_id = get_station_id(self.ROIs)
        climat_data = get_weather(self.start, self.finish , station_id)
        climat_data = prepair_weather(climat_data)
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



        
    def get_NDTI(self, download = "yes"):
        self.season = self.finish.split('-')[0]
        

        preparing = DZZ_collection(f'{self.season}-07-15' ,self.finish)
        preparing.get_sattelit_collection('sentinel2', self.region_geometry, self.ROIs_copy)
        preparing.Download_minNDTI(self.farmer_lands_name, self.season)



        if download.lower() == 'no':
                    pass
        else:  
            NDTI_filename = 'anual_data/NDTI/NDTI.csv'
        
            if os.path.isfile(NDTI_filename): 
                print(f'file {NDTI_filename} alredy exists')
                NDTI_old = pd.read_csv(NDTI_filename)
                NDTI_new = preparing.NDTI_df
                NDTI_new = NDTI_old.append(NDTI_new).drop_duplicates()
                NDTI_new.to_csv(path_or_buf=NDTI_filename, index= False)
                self.NDTI_df = NDTI_new
            else:
                preparing.NDTI_df.to_csv(path_or_buf=NDTI_filename, index= False)
                self.NDTI_df = preparing.NDTI_df
            
            minNDTI_filename = 'anual_data/minNDTI/minNDTI.csv'

            preparing.minNDTI_df['season'] = self.season

            if os.path.isfile(minNDTI_filename):



                print(f'file {minNDTI_filename} alredy exists')
                minNDTI_old = pd.read_csv(minNDTI_filename)
                minNDTI_new = preparing.minNDTI_df
                minNDTI_new = minNDTI_old.append(minNDTI_new).drop_duplicates()
                minNDTI_new.to_csv(path_or_buf=minNDTI_filename, index= False)
                self.minNDTI_df = minNDTI_new
            else:
                preparing.minNDTI_df.to_csv(path_or_buf=minNDTI_filename, index= False)
                self.NDTI_df = preparing.minNDTI_df





            



        


        










    