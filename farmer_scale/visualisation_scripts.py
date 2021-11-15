import rasterio
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from rasterio.plot import  show, adjust_band #для визуализации при помощи матплот либа
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import time



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

def PCA_k_means_visualisation(df ,start, end, mask,ROI, name):
    """
    df - данны NDVI
    start - дата начала, 
    end - дата конца поиска,
    mask - маска для визуализации полигонов,
    ROI - геопандасовскиий фаил к которому добавятся кластеры по годам
    name - имя хозяйства
    
    на выход построится график динамики NDVI по кластерам, выдасться дата от которой искать NDTI, и к данным добавятся кластеры
    """

    ROI_copy = ROI.copy()
    year = end.split('-')[0]

    NDVI_df = df
    NDVI_df['new_date'] = pd.to_datetime(NDVI_df.Dates , format = '%Y_%m_%d')
    NDVI_df.sort_values(by = 'new_date').reset_index()
    NDVI_df_sample = NDVI_df[ (NDVI_df['new_date'] >= start ) & (NDVI_df['new_date'] < end)][['new_date','farmer_land_name',	'fieldID',"NDVI"]]
    NDVI_df_sample = NDVI_df_sample.pivot_table(index = ['fieldID'], columns = 'new_date', values = 'NDVI').reset_index(drop = True)
    NDVI_array = NDVI_df_sample.to_numpy()
    pca = PCA(n_components=3)
    scaler = StandardScaler()

    Kmeans = KMeans(n_clusters=3)
    clusters = Kmeans.fit_predict(scaler.fit_transform(NDVI_array))
    NDVI_df_sample['cluster'] = clusters #кластеры для визуализации
    ROI_copy[f'culture{year}'] = clusters


    pca_result = pca.fit_transform(scaler.fit_transform(NDVI_array))

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    plt.figure(figsize=(8,8))





    ax1 = sns.scatterplot(x = pca_result[:,0],y =  pca_result[:,1], hue  = clusters, palette='Set1', ax=axes[0])

    ax1.set_title(f'{year} PCA')

    columns = NDVI_df_sample.columns[:-1]

    NDVI_df_sample_long = pd.melt(NDVI_df_sample, id_vars=['cluster'], value_vars=columns,value_name = 'NDVI'  )


    NDVI_cuted = NDVI_df_sample_long[NDVI_df_sample_long.new_date > f"{year}-06-01"]
    NDVI_grouped = NDVI_cuted.groupby(by = ["cluster", 'new_date']).mean().reset_index()
    datelist = []
    for i in NDVI_grouped.cluster.unique():
        date = NDVI_grouped[(NDVI_grouped.NDVI < 0.3) & (NDVI_grouped.cluster == i)].new_date.iloc[0]
        datelist.append(date)
    NDTI_start = max(datelist)
    print(NDTI_start)
    NDTI_finish = max(NDVI_df_sample_long.new_date)
    ax2 = sns.lineplot(data = NDVI_df_sample_long, x = 'new_date',y = 'NDVI', hue = 'cluster', palette='Set1',ax=axes[1] )
    ax2.set_title(f'{year} динамика NDVI \n(медиана MODIS MOD13Q1)')
    ax2.fill_between(x = [NDTI_start , NDTI_finish], y1 = 0, y2 = 0.9, color = 'y', alpha = 0.3)
    ax2.text(NDTI_start , 0.5,'NDTI\nzone', fontsize=12)


    color_for_mapping = ["#FF0000", "#0F00FF", "#06C512", "#E80AD4","#FC9A00" ]
    unique_clusters = list(set(clusters))
    for i in range(len(unique_clusters)):
        ax3 = ROI_copy[ROI_copy[f'culture{year}'] == i].plot( legend=True, edgecolor ='black', linewidth = 1, color = color_for_mapping[i], ax=axes[2])
    axes[2].set_xlim(mask.geometry.bounds.minx[0]-0.01, mask.geometry.bounds.maxx[0]+0.01)
    axes[2].set_ylim(mask.geometry.bounds.miny[0]-0.01, mask.geometry.bounds.maxy[0]+0.01)
    ax3.set_title('Геометрии полей хозяйства')
    fig.suptitle(f"хозяйство {name}" , fontsize=14)

    return(fig , NDTI_start ,year,  clusters  )

def clustering(df,farm , start, finish):

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    import matplotlib.pyplot as plt 
    import seaborn as sns 
    import numpy as np
    
    def visualise_clusters(pca, clusters, df):
        plt.show(block=False)
        fig, axes = plt.subplots(1, 2, figsize=(10, 6))
        sns.scatterplot(x = pca_result[:,0],y =  pca_result[:,1], hue  = clusters, palette='Set1', ax = axes[0])
        sns.lineplot(data = df, x = 'new_date',y = 'NDVI', hue = 'clusters', palette='Set1',ax=axes[1] )
        plt.show()
        return fig

    df['new_date'] = pd.to_datetime(df.Dates , format = '%Y_%m_%d') #переформатирование данных по датам
    year = finish.split('-')[0]
    df = df[ (df.new_date >= start) & (df.new_date < finish) ][[	'fieldID','new_date',"NDVI"]] #отбор только интересующих нас колонок

    number_dates = df.new_date.unique().shape[0] #колличество уникальных дат 


    df_wide = df.pivot_table(index = ['fieldID'], columns = 'new_date', values = 'NDVI').reset_index() #переход в широкий варинт представлений 

    arr = df_wide.iloc[:,1:].to_numpy() #создание массива 
    pca = PCA(n_components=3)
    scaler = StandardScaler()
    clusters = 0
    df["clusters"] = 0
    pca_result = pca.fit_transform(scaler.fit_transform(arr))
    visualise_clusters(pca_result, clusters, df)


    satisfaction = 'start'
    while satisfaction.lower() != 'ok':
        n_klusters = int(input('колличество кластеров:'))
        Kmeans = KMeans(n_clusters=n_klusters)
        clusters = Kmeans.fit_predict(scaler.fit_transform(arr))
        df["clusters"] = np.tile(clusters, number_dates)
        
        visualise_clusters(pca_result, clusters, df)


        #print('если колличество кластеров удовлетворяет введите ok')
        satisfaction = str(input('удовлетворяет ли колличество кластеров?(если удвлетворяет введите ok'))
    satisfaction = 'start'
    while satisfaction.lower() != 'ok':
        print('каким культурам соотвествуют кластеры?')
        cluster_lables = list(set(clusters))
        lables_dict = {}
        for lable in cluster_lables:
            lables_dict[lable] = str(input(f'{lable} - название кластера'))
        print(lables_dict)
        satisfaction = str(input('все ли верно?(введите ok)'))

    labled_clusters = [lables_dict[letter] for letter in clusters]
    df["clusters"] = np.tile(labled_clusters, number_dates)
    plot = visualise_clusters(pca_result, labled_clusters , df)
    Import_plot  = str(input('сохранить изображение кластеров?(ok)'))
    if Import_plot.lower() == 'ok':
        plot.savefig(f"output/NDVI_NDTI_plots/clusters_{farm}_{year}.jpg")
    
    return(labled_clusters)