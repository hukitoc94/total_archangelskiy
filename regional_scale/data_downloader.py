import ee, geemap, geopandas as gpd
import matplotlib.pyplot as plt , seaborn as sns
from math import ceil
import shutil
from tqdm import tqdm
from shapely.geometry import Polygon
import os
import rasterio 
from rasterio.merge import merge
from rasterio.plot import show
from rasterio.plot import show
ee.Initialize()






def Get_sentinel_raster(mask, output_raster_name = 'raster'):
    """
    input
    mask - gpd.file
    output_raster_name - raster name (defolt - raster)
    """
    batch_download_dir = "raster/batch_download" #директория куда будет качаться файл
    if not os.path.exists(batch_download_dir): #если директория не существует ее создаст
        os.makedirs(batch_download_dir)
    mosaic, mosaic_crs = get_gee_mosaic(mask) #получение мозайки
    name_list = batch_download(mask,mosaic,batch_download_dir ) #скачивание мозаики по батчам 
    build_local_mosaic(name_list, batch_download_dir, output_raster_name) # постройка мозаики локально
    shutil.rmtree(batch_download_dir) # удаление директории с батчами потому что она не нужна




def get_gee_mosaic(mask, first_date = '2021-05-01', last_date = '2021-09-30'):
    '''на вход геометрия маски по которой искать и обрезать + необязательно даты
        на выход изображение и сиситема координат
    '''
    collection = ee.ImageCollection('COPERNICUS/S2_SR') \
                    .filterDate('2021-05-01', '2021-09-30') \
                    .filterBounds(geemap.geopandas_to_ee(mask)) \
                    .filterMetadata("CLOUD_COVERAGE_ASSESSMENT", 'less_than', 0.1) \
                    .sort("system:time_start") \
            

    crs = collection.first().select('B1').projection().getInfo()['crs']
    scale = 10 

    collection_median = collection.median().reproject(crs = crs,scale = scale)
    collection_median = collection_median.clip(geemap.geopandas_to_ee(mask).geometry())
    collection_median = collection_median.select(['B4','B3','B2',"B8"])

    return(collection_median, crs)
def batch_download(mask,mosaic, batch_download_dir,step = 0.15 ):
    """
    input
    mask - геометрия
    mosaic - мозайка GEE которую выкачивать
    batch_download_dir - директория куда выкачиваются батчи
    step = размер батча в градусах


    output
    batches_dir_list - лист с названиями выкаченных батчей
    """
    MinMax_coords = mask.total_bounds  #получение крайних точек
    lat_ = MinMax_coords[2] - MinMax_coords[0] # расстояния между крайними точками в градусах 
    lon_ = MinMax_coords[3] - MinMax_coords[1] # расстояния между крайними точками в градусах 
    step = 0.15 #шаг окна

    lat_range = ceil(lat_/step)
    lon_range = ceil(lon_/step)
    print('-'*20)
    print('скачивание батчей...')
    for y in tqdm(range(lon_range) ,desc="Row"): #lon_range
        bottom_left_angle = [MinMax_coords[0],MinMax_coords[1]+(step * y)] #точка начала отчета левый нижний угол каждую итерацию Y поднимается вверх на y

        for  x in tqdm(range(lat_range),desc="Col"): #lat_range
            bottom_left_angle = bottom_left_angle 
            top_left_angle = [bottom_left_angle[0] ,bottom_left_angle[1] +  step] 
            top_right_angle = [bottom_left_angle[0] + step ,bottom_left_angle[1] + step]
            bottom_right_angle = [bottom_left_angle[0] + step ,bottom_left_angle[1] ] 


            poly = Polygon([bottom_left_angle,top_left_angle,  top_right_angle,bottom_right_angle,])
            poly = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[poly])

            file_name = "{}_{}.tif".format(y,x)


            cliped = mosaic.clip(geemap.geopandas_to_ee(poly).geometry()).float() #попытка снизить размерность
            
        
            
            bottom_left_angle = bottom_right_angle
            geemap.ee_export_image(cliped, 
                                    filename="{}/{}".format(batch_download_dir, file_name),
                                    scale = 10,
                                    file_per_band=False)
    batches_names_list = os.listdir(batch_download_dir) #вот она ошибка надо править((((
    return(batches_names_list)
    
def build_local_mosaic(batches_names_list, batch_download_dir, raster_name = "raster_mosaic"):
    rasters = []
    for dir in batches_names_list:
        raster = rasterio.open("{}/{}".format(batch_download_dir, dir))
        rasters.append(raster)


    mosaic, out_trans = merge(rasters)
    metadata = raster.meta.copy() #метаданные из любого батча который мы вынимаем 
    print('-'*20)
    print('построение мозайки...')
    metadata.update({"height": mosaic.shape[1],
                        "width": mosaic.shape[2],
                        "transform": out_trans})
    print('-'*20)
    print('запись мозайки...')
    with rasterio.open('raster/{}.tif'.format(raster_name), "w", **metadata) as dest:
        dest.write(mosaic)
    print("удачно")
    