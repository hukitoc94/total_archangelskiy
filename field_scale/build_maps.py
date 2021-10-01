import rasterio
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from rasterio.plot import  show, adjust_band #для визуализации при помощи матплот либа

def start():
    with open("raster_data/file_list.txt") as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
    for i in lines:
        get_maps(i)
    




def get_maps(file_name):
    raster_name = file_name
    directory = "raster_data/"
    directory += raster_name

    Date = raster_name.split('_')[3]

    dataset = rasterio.open(directory)
    image = dataset.read()

    image[image == 0] = np.nan

    fig, (ax1, ax2, ax3) = plt.subplots(1,3, figsize=(12,4)) 

    RGB = image[0:3]
    NDVI = image[6]
    NDTI = image[7]
    RGB_norm = adjust_band(RGB)
    show(RGB_norm, ax=ax1)
    ax1.set_title("RGB", fontsize = 16)

    NDVI_vis = ax2.imshow(NDVI, cmap='RdYlGn')
    ax2.set_title('NDVI', fontsize = 16)
    fig.colorbar(NDVI_vis,fraction=0.046, pad=0.04, ax=ax2).set_ticks([0,0.4,0.8])
    NDVI_vis.set_clim(vmin = 0 , vmax = 0.8)


    NDTI_vis =  ax3.imshow(NDTI, cmap = 'Oranges')
    ax3.set_title('NDTI', fontsize = 16)
    fig.colorbar(NDTI_vis,fraction=0.046, pad=0.04, ax=ax3).set_ticks([0,0.1,0.2])
    NDTI_vis.set_clim(vmin = 0 , vmax = 0.2)

    ax1.axis('off')
    ax2.axis('off')
    ax3.axis('off')

    fig.suptitle(Date, fontsize = 16)


    output_dir = "output\RGB_NDVI_NDTI\ " +  Date + ".jpg" 


    plt.savefig(output_dir)
    plt.close(fig)

