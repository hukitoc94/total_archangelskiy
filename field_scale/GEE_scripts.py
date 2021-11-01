import ee, geemap
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
        .filterBounds(geemap.geojson_to_ee(region_bounds)) \
        .filterDate(first_date, last_date) \
        .select('NDVI')  #берем только NDVI


    modis_collection = modis_collection.toBands()
    getData =  modis_collection.reduceRegions(geemap.geojson_to_ee(ROI), ee.Reducer.median()) #считаем медиану
    geemap.ee_export_vector(getData , 'anual_data//NDVI//row_data.csv') #сначала скачиваем данные
    df = pd.read_csv('anual_data//NDVI//row_data.csv') #потом читаем и фильтруем их
    df = df.drop(["system:index"], axis = 1)
    dates = [i[:-5] for i in  df.columns[:-1]]
    dates.append("type")
    df.columns = dates
    df = pd.melt(df, id_vars= ['type'],var_name= 'Dates' , value_name = 'NDVI') # в данные перекидываем
    df.NDVI = df.NDVI * 0.0001 # модис имеет масштаб 10 000
    return (df)