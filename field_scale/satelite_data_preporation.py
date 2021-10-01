import ee, geemap, os.path, datetime
from geetools import batch

import numpy as np
import build_maps
ee.Initialize()
#общие процессы при подготовке данных - создание маски, обрезка региона, создание мозаик изображений расчет индексов 

###### цикл обработки данных для сентинел 

class collection:
    """первый опыт в ООП хочу реализовать коллекцию через класс, и чтоб класс сразу был коллекций уже обрезанной под наши задачи, со всякими вег индексами и прочими сфисто-перделками"""
    def __init__(self, platform, first_date, last_date, region_geometry, region_of_interest, cloud_cover_threshold = 20): 
        """ входные параметры - platform - платформа данных ДЗЗ - по умолчанию стоит sentinel2 /альтернативные аргументы landsat8 , landsat7 (возможно запилю сюда 5-6)
            fist_date - дата с которой начинаем отчет
            last_date - дата по которую мы отбираем данные 
            region_geometry - ссылка на директорию с json 
            agricultural_lands - ссылка на директорию с json  
            cloud_cover_threshold - облачность не более --- по умолчанию 20 процентов
        """
        self.start = ee.Date(first_date)
        self.end = ee.Date(last_date)
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

            filtered = row_image_NDTI.filterDate(date_ee , date_ee.advance(1,'day'))

            image = ee.Image(filtered.mosaic()).reproject(crs = crs , crsTransform = transform)
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
                masked_img = image.updateMask(cloud).updateMask(shadow).updateMask(cirrus).updateMask(cirrus_medium).updateMask(cirrus_high)
                return(image)
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
                .filterDate(first_date, last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") 
            masking = L8masking          
        elif platform == 'landsat7':
            ndvi_bands = ['B4', 'B3']
            ndti_bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR") \
                .filterDate(first_date, last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start")
            masking = L7masking                      
        else:
            ndvi_bands = ['B8', 'B4']
            ndti_bands = ['B11', 'B12']
            row_image = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterDate(first_date, last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', cloud_cover_threshold) \
                .sort("system:time_start")
            masking = S2masking
                    
        
        self.row = row_image

        time_lst = row_image.aggregate_array("system:time_start").getInfo() #получили даты
        unique_dates = get_time_lst(time_lst) # перевели даты в лист убрали повторы

        if len(unique_dates) == 0:
            raise Exception("коллекция не имеет изображений") #если лист пустой и изображений нет, уронили систему 

        row_image_cliped = row_image.map(clipper_region) #обрезали по маске региона
        row_image_cliped = row_image_cliped.map(clipper_region_agricultural) # обрезали только интересующие нас объекты
        row_image_NDVI = row_image_cliped.map(calulate_NDVI) # построили NDVI 
        row_image_NDTI = row_image_NDVI.map(NDTI_calculate) # построили NDTI 


        crs = row_image_NDTI.first().select('B1').projection().getInfo()['crs'] #извлекли систему координат
        transform = row_image_NDTI.first().select('B1').projection().getInfo()['transform'] #извлекли параметры трансформации 
        ####создание мозайки
        diff = self.end.difference(self.start , 'day')
        Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  self.start.advance(day,'day'))
        mosaic_collection = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
        #построили NDTI 
        result_collection = mosaic_collection.map(masking)# сделали маску для итого изображения     





        self.unique_dates = unique_dates
        self.row = row_image
        self.mosaic = mosaic_collection
        self.crs = crs
        self.result = result_collection

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
                    geemap.ee_export_image(composit_to_download, filename=directory,region=self.region_of_interest.geometry(),  file_per_band=False)

    def get_raster_plots(self):
        build_maps.start()


