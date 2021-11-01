import rasterio
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from rasterio.plot import  show, adjust_band #для визуализации при помощи матплот либа




#функцию старт имеет смысл вынести в основной скрипт
def start(ROIs, source):
    with open("raster_data/file_list.txt") as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
    for i in lines:
        get_maps(i, ROIs, source)
def get_maps(file_name, ROIs, source):
    raster_name = file_name
    directory = "raster_data/"
    directory += raster_name

    Date = raster_name.split('_')[3]

    dataset = rasterio.open(directory)
    image = dataset.read()

    image[image == 0] = np.nan

    RGB = image[0:3]
    NDVI = image[6]
    NDTI = image[7]


    RGB_norm = adjust_band(RGB)

    fig, (ax1, ax2, ax3) = plt.subplots(1,3, figsize=(12,4)) 

    color_map = plt.cm.get_cmap('RdYlGn')
    color_map = color_map.reversed()

    show(RGB_norm, transform= dataset.transform, ax = ax1)
    ROIs.plot(column = "type",ax = ax1,cmap =color_map, facecolor='none' , legend=True, edgecolor ='green', linewidth = 3)
    ax1.set_title("RGB", fontsize = 16)


    NDVI_hiden = ax2.imshow(NDVI, cmap='RdYlGn')
    NDVI_vis = show(NDVI,transform= dataset.transform, ax = ax2, cmap='RdYlGn', vmin= 0.0 , vmax = 0.8)
    ax2.set_title('NDVI', fontsize = 16)
    fig.colorbar(NDVI_hiden,fraction=0.046, pad=0.04, ax=ax2).set_ticks([0,0.4,0.8])
    NDVI_hiden.set_clim(vmin = 0 , vmax = 0.8)


    NDTI_hiden =  ax3.imshow(NDTI, cmap = 'Oranges')
    NDTI_vis = show(NDTI,transform= dataset.transform, ax = ax3, cmap='Oranges', vmin= 0.0 , vmax = 0.2)
    ax3.set_title('NDTI', fontsize = 16)
    fig.colorbar(NDTI_hiden,fraction=0.046, pad=0.04, ax=ax3).set_ticks([0,0.1,0.2])
    NDTI_hiden.set_clim(vmin = 0 , vmax = 0.2)

    ax1.axis('off')
    ax2.axis('off')
    ax3.axis('off')

    fig.suptitle(Date, fontsize = 16)


    output_dir = "output\RGB_NDVI_NDTI\ " +  Date + ".jpg" 


    plt.savefig(output_dir)
    plt.close(fig)



def weather_visualisation(start, end):

    """на вход подается с какого и по какое строить граффик в формате YYYY-MM-DD
        на выход получаем переменную с граффиком 
    """

    weather = pd.read_csv('anual_data/Weather/weather.csv') #считали данные
    weather['new_date'] = pd.to_datetime(weather.date , format = '%d.%m.%Y') #считал как даты
    weather = weather.sort_values(by = 'new_date').reset_index()
    year_weather_sample = weather[ (weather['new_date'] >= start) & (weather['new_date'] < end)][['new_date', "mean_temperature", "sum_percepetation"]]
    two_week_resample = year_weather_sample.groupby(pd.Grouper(key='new_date', axis=0, freq='2W')).agg({ "mean_temperature" : 'mean',"sum_percepetation":'sum' }).reset_index()
    two_week_resample['str_date'] = two_week_resample['new_date'].dt.strftime('%d-%m-%Y') #важный переделали даты в удобный формат


    sns.set_style("ticks")
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax1 = sns.barplot(data = two_week_resample , x = 'str_date', y  = 'sum_percepetation',color = "#00C9FF" )
    ax1.set( ylabel='Осадки (мм)',xlabel = "", title=f'Климатические показатели {start}-{end} (шаг 2 недели, по данным rp5)' )

    ax2 = ax1.twinx()
    ax2 = sns.lineplot(data = two_week_resample["mean_temperature"], color = 'r',linewidth = 1  )
    ax2.set( ylabel=f'Температура (\xb0C)') 

    plt.locator_params(axis='x', nbins=10)
   
    return(fig)
