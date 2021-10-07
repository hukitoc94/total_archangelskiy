import ee, geemap, os.path, datetime 
import pandas as pd
from pandas.io.parsers import read_csv
import geopandas as gpd

import warnings
warnings.simplefilter('ignore')

import time


import numpy as np
import build_maps
import parsing_climat
ee.Initialize()
#общие процессы при подготовке данных - создание маски, обрезка региона, создание мозаик изображений расчет индексов 

###### цикл обработки данных для сентинел 

class collection:
    """первый опыт в ООП хочу реализовать коллекцию через класс, и чтоб класс сразу был коллекций уже обрезанной под наши задачи, со всякими вег индексами и прочими сфисто-перделками"""
    def __init__(self,  first_date, last_date): 
        """ входные параметры - platform - платформа данных ДЗЗ - по умолчанию стоит sentinel2 /альтернативные аргументы landsat8 , landsat7 (возможно запилю сюда 5-6)
            fist_date - дата с которой начинаем отчет
            last_date - дата по которую мы отбираем данные 
        """
        self.first_date = first_date
        self.last_date = last_date

    def get_sattelit_collection(self ,platform, region_geometry, region_of_interest, cloud_cover_threshold = 20):

        """"platform - платформа которую мы используем  
        region_geometry - ссылка на директорию с json 
            agricultural_lands - ссылка на директорию с json  
            cloud_cover_threshold - облачность не более --- по умолчанию 20 процентов
        """


        self.start = ee.Date(self.first_date)
        self.end = ee.Date(self.last_date)
        self.platform = platform
        self.region_geometry = geemap.geojson_to_ee(region_geometry)
        self.region_of_interest = geemap.geojson_to_ee(region_of_interest)

        global  ndvi_bands
        global  ndti_bands 


        def clipper_region(image):  #########обрезка по искомому региону
            clipped = image.clip(self.region_geometry.geometry())
            return  clipped 
        def clipper_region_agricultural(image): 
            clipped = image.clip(self.region_of_interest.geometry()) #функция обрезки изображения по границам региона - граница geometry будет как исходные данные
            return  clipped
        def calulate_NDVI(image):
            NDVI = image.normalizedDifference(ndvi_bands).rename('NDVI').select('NDVI')
            image = image.addBands(NDVI)
            return image
        def day_mosaics(date , newlist):
            date_ee = ee.Date(date)
            newlist = ee.List(newlist)

            filtered = self.row_image_NDTI.filterDate(date_ee , date_ee.advance(1,'day'))

            image = ee.Image(filtered.mosaic()).reproject(crs = self.crs, scale = 10)
            #добовляем дату к каждой мозайке 
            image = image.set({'Date' : date})

            

            return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist))
        def NDTI_calculate(image):
                NDTI = image.normalizedDifference(ndti_bands).rename('NDTI').select("NDTI")
                image = image.addBands(NDTI)
                return image
        def get_time_lst(time_lst):
            unique_dates = []
            for i in time_lst:
                    unique_date_str = str(i)[:10]
                    unique_date = int(unique_date_str)
                    unique_dates.append(datetime.datetime.fromtimestamp(unique_date).strftime("%Y-%m-%d"))
            dates = list(set(unique_dates))
            dates.sort()

            return(dates)

        def S2masking(image): 
            cloudProb = image.select('MSK_CLDPRB')  # покрытие облаками
            snowProb = image.select('MSK_SNWPRB') # покрытие снегом
            cloud = cloudProb.lt(1) # создали бинарную маску иными словами просто все что имеет значение меньше 5 одна группа выше другая
                                # а мы помним что пиксели принимают значения от 0 до 255
            snow = snowProb.lt(1) # тоже самое что с облаками
            scl = image.select('SCL') # слой с классификатором(есть в sentinel 2 уровня обработки 2А)
            shadow = scl.neq(3);# 3 в классификации это тени от облаков
            cirrus_medium = scl.neq(8) # тоже по классификации облака 
            cirrus_high = scl.neq(9) # аналогично облака
            cirrus = scl.neq(10); # 10 это перистые облака или цирусы
            return  image.updateMask(cirrus).updateMask(cirrus_medium).updateMask(cirrus_high)

        def L8masking(image): 
            cloudShadowBitMask = (1 << 3)
            cloudsBitMask = (1 << 5)
            snowBitMask = (1<<4)
            qa = image.select('pixel_qa')

            shadow_mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)

            cloud_mask = qa.bitwiseAnd(cloudsBitMask).eq(0)

            snow_mask = qa.bitwiseAnd(snowBitMask).eq(0)

            return image.updateMask(shadow_mask).updateMask(cloud_mask).updateMask(snow_mask)
        def L7masking(image): 
            cloudShadowBitMask = (1 << 3)
            cloudsBitMask = (1 << 5)
            snowBitMask = (1<<4)
            qa = image.select('pixel_qa')
            shadow_mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
            cloud_mask = qa.bitwiseAnd(cloudsBitMask).eq(0)
            snow_mask = qa.bitwiseAnd(snowBitMask).eq(0)
            return image.updateMask(shadow_mask).updateMask(cloud_mask).updateMask(snow_mask)
            
        if platform == 'landsat8':
            ndvi_bands = ['B5', 'B4']
            ndti_bands = ['B6', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_of_interest) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L8masking)
        elif platform == 'landsat7':
            ndvi_bands = ['B4', 'B3']
            ndti_bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR") \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_of_interest) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L7masking)
        else:
            ndvi_bands = ['B8', 'B4']
            ndti_bands = ['B11', 'B12']
            row_image = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_of_interest) \
                .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(S2masking)
                    
        
        self.row_image = row_image

        time_lst = row_image.aggregate_array("system:time_start").getInfo() #получили даты
        self.unique_dates = get_time_lst(time_lst) # перевели даты в лист убрали повторы

        if len(self.unique_dates) == 0:
            raise Exception("коллекция не имеет изображений") #если лист пустой и изображений нет, уронили систему 

        self.row_image_cliped_by_regin = row_image.map(clipper_region) #обрезали по маске региона
        self.row_image_cliped_by_roi = self.row_image_cliped_by_regin.map(clipper_region_agricultural) # обрезали только интересующие нас объекты
        self.row_image_NDVI = self.row_image_cliped_by_roi.map(calulate_NDVI) # построили NDVI 
        self.row_image_NDTI = self.row_image_NDVI.map(NDTI_calculate) # построили NDTI 


        self.crs = self.row_image_NDTI.first().select('B1').projection().getInfo()['crs'] #извлекли систему координат
        self.transform = self.row_image_NDTI.first().select('B1').projection().getInfo()['transform'] #извлекли параметры трансформации 


        ####создание мозайки
        diff = self.end.difference(self.start , 'day')
        Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  self.start.advance(day,'day'))
        self.result = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
            #построили NDTI 
            #кусок посвященный тому как вынуть изображения NDVI только с имеющимися пикселями
        NDVI = self.result \
            .select('NDVI') \
            .toBands() \
            .rename(self.unique_dates)
        date_value_dictionary = NDVI.reduceRegion(ee.Reducer.count(),geometry = self.region_of_interest ).getInfo()
        
        pixels_count_list = list(date_value_dictionary.values())
        part_of_pixels = (np.mean(pixels_count_list)/3) * 2

        good_date_list = [] #лист где будут даты из которых выпады не больше трети
        for (key, val) in date_value_dictionary.items():
            if val > part_of_pixels:
                good_date_list.append(key)
        self.good_date_list = good_date_list

        if len(good_date_list) == 0:
            raise Exception("коллекция не имеет изображений") #если лист пустой и изображений нет, уронили систему 

    def DownloadImages(self, bands = 'all' ):


            '''идея в том что через эту фунцию мы будем скачивать данные
        формат названия файла на выходе следующий масштаб_Платформа_дата_чтополучаем.tiff
        договоримся так когда у нас полное изображение - каналы + индексы это будет называться scene , когда minNDTI- minNDTI за указанный период и даты будет 2 - начало и конец '''
            for i in self.good_date_list:
                #чтобы не сломать голову! в любом случае порядок каналов в бэнде будет следующий - Blue, Green. Red, NIR, SWIR1 , SWIR2, NDVI, NDTI так будет проще не запутаться в дальнейшем
                if self.platform == 'landsat7':
                    band_list = ['B3','B2','B1','B4','B5','B7','NDVI','NDTI'] 
                elif self.platform == 'landsat8':
                    band_list = ['B4','B3','B2','B5','B6','B7','NDVI','NDTI']
                else:
                    band_list = ['B4','B3','B2','B8','B11','B12','NDVI','NDTI']


                composit_to_download = self.result.filterMetadata('Date', 'equals', ee.Date(i)).first()
                composit_to_download = composit_to_download.select(band_list) # тут надо еще поправить бэнды в зависимости от платформы
                file_name = 'Field_scale_' + self.platform + "_" + i + '_scene.tif'                  
                directory = 'raster_data/' + file_name
                if os.path.isfile(directory): 
                    print(f'file {file_name} alredy exists')
                else:
                    with open("./raster_data/file_list.txt", "a") as file_object:
                        file_object.write(file_name + '\n') # имеет смысл наверное создать txt с именами фаилов которые мы будем получать после скачивания, чтобы потом легче их вынуть
                    geemap.ee_export_image(composit_to_download, filename=directory,region=self.region_of_interest.geometry(),scale = 10,  file_per_band=False)

    def get_raster_plots(self, ROIs):
        """ROIs - регионы для того чтобы сэмплить 
        в нашем случае пока оставляем только по полям чтобы было ТТ и ПП потом возможно надо будет расширить"""

        crs = int(self.crs[5:])
        ROIs = gpd.read_file(ROIs).to_crs(crs)


        build_maps.start(ROIs, self.platform)
    

    def anual_ndvi(self, regions_to_reduce):
        """ regions_to_reduce - регионы для которых надо извлекать данные
        на выход скачивается динамик NDVI по интересующим нас объектам 
        df - эти данные 
        """
        NDVI_modis_filename = 'anual_data//NDVI//NDVI_modis.csv'

        def MODIS_NDVI(first_date ,last_date, region_bounds, region_to_reduce):
            MODIS_NDVI = ee.ImageCollection('MODIS/006/MOD13Q1') \
                .filterBounds(region_bounds) \
                .filterDate(first_date, last_date) \
                .select('NDVI')  #берем только NDVI
            MODIS_NDVI = MODIS_NDVI.toBands()
            getData =  MODIS_NDVI.reduceRegions(geemap.geojson_to_ee(region_to_reduce), ee.Reducer.median()) #считаем медиану
            geemap.ee_export_vector(getData , 'anual_data//NDVI//row_data.csv') #сначала скачиваем данные
            df = pd.read_csv('anual_data//NDVI//row_data.csv') #потом читаем и фильтруем их
            df = df.drop(["system:index"], axis = 1)
            dates = [i[:-5] for i in  df.columns[:-1]]
            dates.append("type")
            df.columns = dates
            df = pd.melt(df, id_vars= ['type'],var_name= 'Dates' , value_name = 'NDVI') # в данные перекидываем
            df.NDVI = df.NDVI * 0.0001 # модис имеет масштаб 10 000
            return(df)

        if os.path.isfile(NDVI_modis_filename): 
            print(f'file {NDVI_modis_filename} alredy exists')
            NDVI_old = pd.read_csv(NDVI_modis_filename)
            NDVI_new = MODIS_NDVI(self.first_date ,self.last_date, self.region_geometry, regions_to_reduce)
            NDVI_new = NDVI_old.append(NDVI_new).drop_duplicates()
            NDVI_new.to_csv(path_or_buf=NDVI_modis_filename, index= False)
        
        else:
            NDVI_new = MODIS_NDVI(self.first_date ,self.last_date, self.region_geometry, regions_to_reduce)
             # модис имеет масштаб 10 000
            NDVI_new.to_csv(path_or_buf=NDVI_modis_filename, index= False)

    
        return(NDVI_new)


        
    def anual_weather(self, url):
        """ url - ссылка на архив с RP5
        на выход скачивается динамик погоды  
        climat_data - эти данные 
        """


        
        
        first = self.first_date.split('-')
        first = first[2] + '.' + first[1] + '.' + first[0]
             
        last = self.last_date.split('-')
        last = last[2] + '.' + last[1] + '.' + last[0]
        weather_filename = 'anual_data/Weather/weather.csv'
        if os.path.isfile(weather_filename): 
            climat_data = read_csv(weather_filename)
            new_climat_data = parsing_climat.get_weather(first, last, url)
            climat_data = climat_data.append(new_climat_data).drop_duplicates()
            climat_data.to_csv(path_or_buf=weather_filename, index= False)
        else:
            climat_data = parsing_climat.get_weather(first, last, url)
            climat_data.to_csv(path_or_buf=weather_filename, index= False)

        return(climat_data)

