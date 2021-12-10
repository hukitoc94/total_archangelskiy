import ee, geemap,datetime, os
import pandas as pd

def MODIS_NDVI(first_date ,last_date, region_bounds, ROI):
    """входные параметры - 
        start - дата начала отбора данных в формате YYYY-MM-DD
        finish - когда заканчивать отбирать данные в формате YYYY-MM-DD
        region_geometry - геометрия по которой будет происходить обрезка, для полевого уровня это просто полигон по которому
            обрезать формат geojson
        ROI - регионы нас интересующие - конкретные поля формат geojson
    """
    modis_collection = ee.ImageCollection('MODIS/006/MOD13Q1') \
        .filterBounds(geemap.geopandas_to_ee(region_bounds)) \
        .filterDate(first_date, last_date) \
        .select('NDVI')  #берем только NDVI


    modis_collection = modis_collection.toBands()
    getData =  modis_collection.reduceRegions(geemap.geopandas_to_ee(ROI), ee.Reducer.median()) #считаем медиану
    geemap.ee_export_vector(getData , 'anual_data//NDVI//row_data.csv') #сначала скачиваем данные
    df = pd.read_csv('anual_data//NDVI//row_data.csv') #потом читаем и фильтруем их
    df = df.drop(["system:index"], axis = 1)
    dates = [i[:-5] for i in  df.columns[:-2]]
    dates.extend(list(df.columns[-2:]))
    df.columns = dates
    df = pd.melt(df, id_vars= list(df.columns[-2:]),var_name= 'Dates' , value_name = 'NDVI') # в данные перекидываем
    df.NDVI = df.NDVI * 0.0001 # модис имеет масштаб 10 000
    return (df)

class DZZ_collection:
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
        self.ROI = geemap.geopandas_to_ee(region_of_interest)
        self.region_geometry = geemap.geopandas_to_ee(region_geometry)

        global  ndvi_bands
        global  ndti_bands 


        def clipper_region(image):  #########обрезка по искомому региону
            clipped = image.clip(self.region_geometry.geometry())
            return  clipped 
        def clipper_ROI(image):
            clipped = image.clipToCollection(self.ROI)
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
            
        def L5masking(image):
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
                .filterBounds(self.region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L8masking)
        elif platform == 'landsat7':
            ndvi_bands = ['B4', 'B3']
            ndti_bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR") \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L7masking)
        elif platform == 'landsat5':
            ndvi_bands = ['B4', 'B3']
            ndti_bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR") \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L5masking)
        else:
            ndvi_bands = ['B8', 'B4']
            ndti_bands = ['B11', 'B12']
            row_image = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_geometry) \
                .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(S2masking)
                    
        
        self.row_image = row_image

        time_lst = row_image.aggregate_array("system:time_start").getInfo() #получили даты
        self.unique_dates = get_time_lst(time_lst) # перевели даты в лист убрали повторы

        if len(self.unique_dates) == 0:
            raise Exception("коллекция не имеет изображений") #если лист пустой и изображений нет, уронили систему 

        self.row_image_NDVI = self.row_image.map(calulate_NDVI) # построили NDVI 
        self.row_image_NDTI = self.row_image_NDVI.map(NDTI_calculate) # построили NDTI

        self.crs = self.row_image_NDTI.first().select('B1').projection().getInfo()['crs'] #извлекли систему координат
        self.transform = self.row_image_NDTI.first().select('B1').projection().getInfo()['transform'] #извлекли параметры трансформации 

 

        diff = self.end.difference(self.start , 'day')
        Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  self.start.advance(day,'day'))
        self.mosaic = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 



        #self.clip_region = self.mosaic.map(clipper_region) #обрезали по маске региона
        #self.result = self.mosaic.map(clipper_ROI) # обрезал по коллекции

        #self.minNDTI = self.result.select('NDTI').min().reproject(crs = self.crs, scale = 10)



        #NDTI_collection = self.result.select('NDTI').toBands().rename(self.unique_dates)
        #getData =  NDTI_collection.reduceRegions(self.ROI, ee.Reducer.median()) #считаем медиану
        #geemap.ee_export_vector(getData , 'anual_data//NDTI//row_data.csv') #сначала скачиваем данные
        #df = pd.read_csv('anual_data//NDTI//row_data.csv') #потом читаем и фильтруем их
        #df = df.drop(["system:index"], axis = 1)
        #dates = list(df.columns[:-2])


        #dates.extend(list(df.columns[-2:]))
        #df.columns = dates
        #self.NDTI_df = pd.melt(df, id_vars= list(df.columns[-2:]),var_name= 'Dates' , value_name = 'NDTI') # в данные перекидываем

        #minNDTI_collection = self.minNDTI.reduceRegions(self.ROI, ee.Reducer.median())
        #geemap.ee_export_vector(minNDTI_collection , 'anual_data//minNDTI//row_data.csv') #сначала скачиваем данные
        #df = pd.read_csv('anual_data//minNDTI//row_data.csv') #потом читаем и фильтруем их
        #df = df.drop(["system:index"], axis = 1)
        
        #self.minNDTI_df = df
    def Download_minNDTI(self,farmer_lands_name , season, bands = 'all' ):


        '''идея в том что через эту фунцию мы будем скачивать данные
    формат названия файла на выходе следующий масштаб_Платформа_дата_чтополучаем.tiff
    договоримся так когда у нас полное изображение - каналы + индексы это будет называться scene , когда minNDTI- minNDTI за указанный период и даты будет 2 - начало и конец '''
        file_name = f'{farmer_lands_name}_minNDTI_{season}.tif'
        directory = 'raster_data/minNDTI/' + file_name
        geemap.ee_export_image(self.minNDTI, filename=directory, region= self.ROI.geometry() ,scale = 10,  file_per_band=False)

    def DownloadImages(self, bands = 'all' ):


            '''идея в том что через эту фунцию мы будем скачивать данные
        формат названия файла на выходе следующий масштаб_Платформа_дата_чтополучаем.tiff
        договоримся так когда у нас полное изображение - каналы + индексы это будет называться scene , когда minNDTI- minNDTI за указанный период и даты будет 2 - начало и конец '''
            for i in self.unique_dates:
                #чтобы не сломать голову! в любом случае порядок каналов в бэнде будет следующий - Blue, Green. Red, NIR, SWIR1 , SWIR2, NDVI, NDTI так будет проще не запутаться в дальнейшем
                if self.platform == 'landsat5':
                    band_list = ['B3','B2','B1','B4','B5','B7','NDVI','NDTI'] 
                elif self.platform == 'landsat7':
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
                    geemap.ee_export_image(composit_to_download, filename=directory,region=self.region_geometry.geometry(),scale = 10,  file_per_band=False)





        

            













    
    




    


    


