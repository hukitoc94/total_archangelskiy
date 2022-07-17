import rasterio
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from rasterio.plot import  show, adjust_band #для визуализации при помощи матплот либа
from matplotlib.colors import LinearSegmentedColormap
from rasterio.mask import mask 
from scipy.stats import kruskal




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
    ROIs = ROIs.to_crs(dataset.crs)

    RGB_norm = adjust_band(RGB)

    fig, axes = plt.subplots(2,3, figsize=(8,8)) 

    color_map = plt.cm.get_cmap('RdYlGn')
    color_map = color_map.reversed()

    show(RGB_norm, transform= dataset.transform, ax = axes[0,0])
    ROIs.plot(column = "type",ax = axes[0,0],cmap =color_map, facecolor='none' , legend=True, edgecolor ='green', linewidth = 3)
    axes[0,0].set_title("RGB", fontsize = 16)


    NDVI_hiden = axes[0,1].imshow(NDVI, cmap='RdYlGn')
    NDVI_vis = show(NDVI,transform= dataset.transform, ax = axes[0,1], cmap='RdYlGn', vmin= 0.0 , vmax = 0.8)
    axes[0,1].set_title('NDVI', fontsize = 16)
    fig.colorbar(NDVI_hiden,fraction=0.046, pad=0.04, ax=axes[0,1]).set_ticks([0,0.4,0.8])
    NDVI_hiden.set_clim(vmin = 0 , vmax = 0.8)


    NDTI_hiden =  axes[0,2].imshow(NDTI, cmap = 'Oranges')
    NDTI_vis = show(NDTI,transform= dataset.transform, ax = axes[0,2], cmap='Oranges', vmin= 0.0 , vmax = 0.2)
    axes[0,2].set_title('NDTI', fontsize = 16)
    fig.colorbar(NDTI_hiden,fraction=0.046, pad=0.04, ax=axes[0,2]).set_ticks([0,0.1,0.2])
    NDTI_hiden.set_clim(vmin = 0 , vmax = 0.2)

    axes[0,0].axis('off')
    axes[0,1].axis('off')
    axes[0,2].axis('off')

    fig.suptitle(Date, fontsize = 16)


    NDVI_NDTI_df = pd.DataFrame()
    for i in ROIs['type'].unique():
        df, _ = mask(dataset, ROIs[ROIs['type'] == i].geometry,nodata=np.nan, invert=False)
        _df = df[6:8].reshape(2,-1)
        _df = _df.T[~np.isnan(_df.T).any(axis=1)]

        _df = pd.DataFrame(data= _df, columns= ['NDVI', "NDTI"])
        _df['type'] = i
        _df['date'] = Date
        NDVI_NDTI_df = NDVI_NDTI_df.append(_df)

    cmap = LinearSegmentedColormap.from_list(name='test',  colors=['red','white','green','white','red'])

    colors = ["#FF0000" ,"#096716"]

    sns.scatterplot(data = NDVI_NDTI_df.sample(1000), x = 'NDTI', y = 'NDVI',hue = 'type',hue_order= ['TT','PP'],palette= sns.color_palette(colors), ax = axes[1,0])

    sns.boxplot(data = NDVI_NDTI_df.sample(1000),x = 'type' ,y = 'NDTI' ,hue= 'type', hue_order= ['TT','PP'], palette= sns.color_palette(colors), ax = axes[1,1])
    axes[1,1].set(xlabel=None, ylabel = None, title = 'NDTI')

    pp = NDVI_NDTI_df.NDTI[NDVI_NDTI_df['type'] == 'PP'].values
    tt = NDVI_NDTI_df.NDTI[NDVI_NDTI_df['type'] == 'TT'].values
    test_result = kruskal(pp, tt)[1]

    axes[1,2].set(xlabel=None, ylabel = None)  # remove the axis label
    axes[1,2].set(xticklabels=[], yticklabels=[])  
    axes[1,2].text(0.2,0.4, f"        NDTI\nKruskal-Wallis\n H-test = {test_result}\n    \u03B1 = 0.05", fontsize  = 16)

    



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
    two_week_resample = year_weather_sample.groupby(pd.Grouper(key='new_date', axis=0, freq='1M')).agg({ "mean_temperature" : 'mean',"sum_percepetation":'sum' }).reset_index()
    two_week_resample['str_date'] = two_week_resample['new_date'].dt.strftime('%d-%m-%Y') #важный переделали даты в удобный формат


    sns.set_style("ticks")
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax1 = sns.barplot(data = two_week_resample , x = 'str_date', y  = 'sum_percepetation',color = "#00C9FF" )
    ax1.set( ylabel='Осадки (мм)',xlabel = "", title=f'Климатические показатели {start}-{end} (шаг 1 месяц, по данным rp5)' )

    ax2 = ax1.twinx()
    ax2 = sns.lineplot(data = two_week_resample["mean_temperature"], color = 'r',linewidth = 1  )
    ax2.set( ylabel=f'Температура (\xb0C)') 

    plt.locator_params(axis='x', nbins=10)
   
    return(fig)
