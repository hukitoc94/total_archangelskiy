import ee, geemap, os.path, datetime 
ee.Initialize()

    
class DZZ_collection:
    """первый опыт в ООП хочу реализовать коллекцию через класс, и чтоб класс сразу был коллекций уже обрезанной под наши задачи, со всякими вег индексами и прочими сфисто-перделками"""
    def __init__(self,  first_date, last_date): 
        """ входные параметры - platform - платформа данных ДЗЗ - по умолчанию стоит sentinel2 /альтернативные аргументы landsat8 , landsat7 (возможно запилю сюда 5-6)
            fist_date - дата с которой начинаем отчет
            last_date - дата по которую мы отбираем данные 
        """
        self.first_date = first_date
        self.last_date = last_date
        #self.region_geometry = geemap.geojson_to_ee(region_geometry)    
    def get_sattelit_collection(self ,platform, region_geometry, region_of_interest, cloud_cover_threshold = 20):

        """"platform - платформа которую мы используем  
            region_geometry - ссылка на директорию с json 
            agricultural_lands - ссылка на директорию с json  
            cloud_cover_threshold - облачность не более --- по умолчанию 20 процентов
        """


        self.start = ee.Date(self.first_date)
        self.end = ee.Date(self.last_date)
        self.platform = platform
        self.region_of_interest = geemap.geojson_to_ee(region_of_interest)
        self.region_geometry = geemap.geojson_to_ee(region_geometry)

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
        elif platform == 'landsat5':
            ndvi_bands = ['B4', 'B3']
            ndti_bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR") \
                .filterDate(self.first_date, self.last_date) \
                .filterBounds(self.region_of_interest) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") \
                .map(L5masking)
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

        #self.row_image_cliped_by_regin = row_image.map(clipper_region) #обрезали по маске региона
        #self.row_image_cliped_by_roi = self.row_image_cliped_by_regin.map(clipper_region_agricultural) # обрезали только интересующие нас объекты
        self.row_image_NDVI = self.row_image.map(calulate_NDVI) # построили NDVI 
        self.row_image_NDTI = self.row_image_NDVI.map(NDTI_calculate) # построили NDTI

        self.crs = self.row_image_NDTI.first().select('B1').projection().getInfo()['crs'] #извлекли систему координат
        self.transform = self.row_image_NDTI.first().select('B1').projection().getInfo()['transform'] #извлекли параметры трансформации 

 

        diff = self.end.difference(self.start , 'day')
        Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  self.start.advance(day,'day'))
        self.mosaic = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 



        self.row_image_cliped_by_region = self.mosaic.map(clipper_region) #обрезали по маске региона
        self.result = self.row_image_cliped_by_region.map(clipper_region_agricultural) # обрезали только интересующие нас объекты
        self.minNDTI = self.result.select('NDTI').min().reproject(crs = self.crs, scale = 10)


        
       

        
        
        



