import ee, geemap, os, datetime

#общие процессы при подготовке данных - создание маски, обрезка региона, создание мозаик изображений расчет индексов 

###### цикл обработки данных для сентинел 

class collection:
    """первый опыт в ООП хочу реализовать коллекцию через класс, и чтоб класс сразу был коллекций уже обрезанной под наши задачи, со всякими вег индексами и прочими сфисто-перделками"""
    def __init__(self, platform, first_date, last_date, region_geometry, region_of_interest, cloud_cover_threshold = 20): 
        """ входные параметры - platform - платформа данных ДЗЗ - по умолчанию стоит sentinel2 /альтернативные аргументы landsat8 , landsat7 (возможно запилю сюда 5-6)
            fist_date - дата с которой начинаем отчет
            last_date - дата по которую мы отбираем данные 
            region_geometry - границы региона по которому мы работаем 
            agricultural_lands - земли сельхоз назначения 
            cloud_cover_threshold - облачность не более --- по умолчанию 20 процентов
        """
        self.start = ee.Date(first_date)
        self.end = ee.Date(last_date)
        self.platform = platform
        self.region_geometry = region_geometry
        self.region_of_interest = region_of_interest

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
            date = ee.Date(date)
            newlist = ee.List(newlist)

            filtered = row_image.filterDate(date , date.advance(1,'day'))

            image = ee.Image(filtered.mosaic()).reproject(crs = crs , crsTransform = transform)

            return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist))

        def NDTI_calculate(image):
                NDTI = image.normalizedDifference(ndti_bands).rename('NDTI').select("NDTI")
                image = image.addBands(NDTI)
                return image
        def get_time_lst(time_lst):
            unique_dates = list()
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
                .filterBounds(region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start") 
            masking = L8masking

                    
        elif platform == 'landsat7':
            ndvi_bands = ['B4', 'B3']
            ndti__bands = ['B5', 'B7']
            row_image = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR") \
                .filterDate(first_date, last_date) \
                .filterBounds(region_geometry) \
                .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
                .sort("system:time_start")
            masking = L7masking                      
        else:
            ndvi_bands = ['B8', 'B4']
            ndti_bands = ['B11', 'B12']
            row_image = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterDate(first_date, last_date) \
                .filterBounds(region_geometry.geometry()) \
                .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', cloud_cover_threshold) \
                .sort("system:time_start")
            masking = S2masking
                    




        time_lst = row_image.aggregate_array("system:time_start").getInfo()

        unique_dates = get_time_lst(time_lst)
        row_image = row_image.map(calulate_NDVI).map(clipper_region) #NDVI и обрезка по границам региона
        crs = row_image.first().select('B1').projection().getInfo()['crs'] # система координат
        transform = row_image.first().select('B1').projection().getInfo()['transform'] # параметры трансформации 
        ####создание мозайки
        diff = self.end.difference(self.start , 'day')





        Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  self.start.advance(day,'day'))
        mosaic_collection = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
        mosaic_collection.getInfo()
        #построили NDTI 
        mosaic_collection = mosaic_collection.map(NDTI_calculate)
        result_collection = mosaic_collection.map(clipper_region_agricultural).map(masking)
        
        if len(unique_dates) == 0:
            raise Exception("коллекция не имеет изображений")
        self.unique_dates = unique_dates
        self.row = row_image
        self.mosaic = mosaic_collection
        self.result = result_collection
        self.crs = crs

#####отдельные общие скрипты

def clipper_region(image):  #########обрезка по искомому региону
        clipped = image.clip(region_geometry.geometry())
        return  clipped 
def calulate_NDVI(image):
    NDVI = image.normalizedDifference(ndvi_bands).rename('NDVI').select('NDVI')
    image = image.addBands(NDVI)
    return image
def clipper_region_agricultural(image): 
        clipped = image.clip(agricultural_lands.geometry()) #функция обрезки изображения по границам региона - граница geometry будет как исходные данные
        return  clipped
def NDTI_calculate(image):
        NDTI = image.normalizedDifference(ndti_bands).rename('NDTI').select("NDTI")
        image = image.addBands(NDTI)
        return image
def get_time_lst(time_lst):
    unique_dates = list()
    for i in time_lst:
            unique_date_str = str(i)[:10]
            unique_date = int(unique_date_str)
            unique_dates.append(datetime.datetime.fromtimestamp(unique_date).strftime("%Y-%m-%d"))
    return(unique_dates)
def day_mosaics(date , newlist):
    date = ee.Date(date)
    newlist = ee.List(newlist)

    filtered = row_image.filterDate(date , date.advance(1,'day'))

    image = ee.Image(filtered.mosaic()).reproject(crs = crs , crsTransform = transform)

    return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist))


#функции по фильтрации 
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
       

#######песня про sentinel2

def get_image_collection_S2(first_date , last_date, region_geometry, agricultural_lands):



    def masking(image): 
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

    cloud_cover_threshold = 20 #процент облачности 
    row_image = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterDate(first_date, last_date) \
        .filterBounds(region_geometry.geometry()) \
        .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', cloud_cover_threshold) \
        .sort("system:time_start")
    time_lst = row_image.aggregate_array("system:time_start").getInfo()
    unique_dates = get_time_lst(time_lst)
    row_image = row_image.map(calulate_NDVI).map(clipper_region) #NDVI и обрезка по границам региона
    crs = row_image.first().select('B1').projection().getInfo()['crs'] # система координат
    transform = row_image.first().select('B1').projection().getInfo()['transform'] # параметры трансформации 
    ####создание мозайки
    diff = last_date.difference(first_date , 'day')
    Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  first_date.advance(day,'day'))
    mosaic_collection = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
    #построили NDTI 
    mosaic_collection = mosaic_collection.map(NDTI_calculate)
    result_collection = mosaic_collection.map(clipper_region_agricultural).map(masking)
    return  unique_dates,mosaic_collection, result_collection, crs


####landsat 8 
def get_image_collection_L8(first_date , last_date, region_geometry, agricultural_lands):
    def masking(image): 
        cloudShadowBitMask = (1 << 3)
        cloudsBitMask = (1 << 5)
        snowBitMask = (1<<4)
        qa = image.select('pixel_qa')

        shadow_mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)

        cloud_mask = qa.bitwiseAnd(cloudsBitMask).eq(0)

        snow_mask = qa.bitwiseAnd(snowBitMask).eq(0)

        return image.updateMask(shadow_mask).updateMask(cloud_mask).updateMask(snow_mask)
    
    cloud_cover_threshold = 20
    row_image = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
        .filterDate(first_date, last_date) \
        .filterBounds(region_geometry) \
        .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
        .sort("system:time_start") 
    time_lst = row_image.aggregate_array("system:time_start").getInfo()
    unique_dates = get_time_lst(time_lst)
    row_image = row_image.map(calulate_NDVI).map(clipper_region) #NDVI и обрезка по границам региона
    crs = row_image.first().select('B1').projection().getInfo()['crs'] # система координат
    transform = row_image.first().select('B1').projection().getInfo()['transform'] # параметры трансформации 
    ####создание мозайки
    diff = last_date.difference(first_date , 'day')
    Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  first_date.advance(day,'day'))
    mosaic_collection = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
    #построили NDTI 
    mosaic_collection = mosaic_collection.map(NDTI_calculate)
    result_collection = mosaic_collection.map(clipper_region_agricultural).map(masking)
    return  unique_dates,mosaic_collection, result_collection, crs
    
    

########landsat7 
def get_image_collection_L7(first_date , last_date, region_geometry, agricultural_lands):  
    def masking(image): 
        cloudShadowBitMask = (1 << 3)
        cloudsBitMask = (1 << 5)
        snowBitMask = (1<<4)
        qa = image.select('pixel_qa')
        shadow_mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
        cloud_mask = qa.bitwiseAnd(cloudsBitMask).eq(0)
        snow_mask = qa.bitwiseAnd(snowBitMask).eq(0)
        return image.updateMask(shadow_mask).updateMask(cloud_mask).updateMask(snow_mask)
    
    cloud_cover_threshold = 20
    row_image = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR") \
        .filterDate(first_date, last_date) \
        .filterBounds(region_geometry) \
        .filterMetadata( 'CLOUD_COVER_LAND', 'less_than', cloud_cover_threshold) \
        .sort("system:time_start") 
      
        
        
    time_lst = row_image.aggregate_array("system:time_start").getInfo()
    unique_dates = get_time_lst(time_lst)
    row_image = row_image.map(calulate_NDVI).map(clipper_region) #NDVI и обрезка по границам региона
    crs = row_image.first().select('B1').projection().getInfo()['crs'] # система координат
    transform = row_image.first().select('B1').projection().getInfo()['transform'] # параметры трансформации 
    ####создание мозайки
    diff = last_date.difference(first_date , 'day')
    Range = ee.List.sequence(0, diff.subtract(1)).map(lambda day :  first_date.advance(day,'day'))
    mosaic_collection = ee.ImageCollection(ee.List(Range.iterate(day_mosaics, ee.List([])))) #получили мозайку изображений 
    #построили NDTI 
    mosaic_collection = mosaic_collection.map(NDTI_calculate)
    result_collection = mosaic_collection.map(clipper_region_agricultural).map(masking)
    return  unique_dates,mosaic_collection, result_collection, crs
    
    
    return row_image, unique_dates,mosaic_collection, result_collection, crs







        







        


