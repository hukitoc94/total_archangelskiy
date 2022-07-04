import re
import warnings
warnings.filterwarnings("ignore")
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib.patches as mpatches
import matplotlib.transforms as transforms
import seaborn as sns
from scipy.ndimage.filters import gaussian_filter1d
import statsmodels.api as sm
from statsmodels.multivariate.manova import MANOVA #мультфакторная анова
from statsmodels.formula.api import ols #линейные модели 
from scipy.stats import f_oneway as ANOVA
import scipy


################БЛОК ПО АГРОХИМИИ###################
def aov_for_nominal(df, agrochem_property, by_points = 0):    
    """
    Считает многофакторный дисперсионный анализ по переменным 
    input - dataframe by agrochemical_proprerty
    output - resul of MANOVA
    """
    dispers = df.copy()
    agrochem_property_ = re.sub(r'[\(),.%№ /-]', '' , agrochem_property)
    dispers.columns = dispers.columns.str.replace(r'[\(),.%№ /-]', '', )
    if by_points == 0:
        reg = ols('{} ~ Глубина  *  Типобработки'.format(agrochem_property_) ,  data=dispers).fit()
    else:
        reg = ols('{} ~ Глубина  *  GPS'.format(agrochem_property_) ,  data=dispers).fit()
    aov = sm.stats.anova_lm(reg)
    aov = aov[["PR(>F)"]]
    aov.columns = ['p-value']
    aov = aov.iloc[:4,:]
    aov['p-value'] = round(aov['p-value'] , 3)
    return aov

def anova(df, varible, agrochem_property):
    """
    Считает дисперсионный анализ по глубинам



    """
    stat_test_df = pd.DataFrame()
    for ind,depth in enumerate(df["Глубина"].unique()): 
        df_by_depth = df[df["Глубина"] == depth]
        sample_list = []
        for value  in df[varible].unique():
            sample = df_by_depth[agrochem_property][df[varible] == value].values
            sample_list.append(sample) 
        
        p_val = ANOVA(*sample_list)[1]
        local_df = pd.DataFrame({"глубина":depth, 'p-value' : p_val}, index = [ind])
        stat_test_df = stat_test_df.append(local_df)
    stat_test_df["p-value"] = round(stat_test_df["p-value"],3)
    return(stat_test_df)
    
def ploting( df, hue,  agrochem_property , aov ,stat_test_df, to_lable = "по обработкам" ):
    fig = plt.figure(figsize=(7,7))
    ax1 = plt.subplot2grid((3,2), (0, 0), colspan=2, rowspan = 2)
    ax2 = plt.subplot2grid((3,2), (2, 0))
    ax3 = plt.subplot2grid((3,2), (2, 1))
    if len(df[hue].unique()) == 2:
        pal =  "prism_r"
    else:
        pal =  "tab10"
    sns.pointplot(data = df,
        x = "Глубина",
        y = agrochem_property,
        hue = hue,
        palette = pal,
        scale = 1.2,
        ci = 95,
        dodge= 0.5,
        join = False,
        capsize = .05,
        ax = ax1)
    ax1.set_title('Сравнение по {}'.format(to_lable))

    ax2.axis('off')
    ax2.axis('tight')
    ax2.table(aov.values,rowLabels=aov.index , colLabels = aov.columns ,loc='center')
    ax2.set_title('MANOVA \nпо {} '.format(to_lable),  y=0.75 , x = 0.5)

    ax3.axis('off')
    ax3.axis('tight')
    ax3.table(stat_test_df.values, colLabels = stat_test_df.columns ,loc='center')
    ax3.set_title('ANOVA по глубинам \n {} '.format(to_lable),  y=0.75 , x = 0.5)
    plt.show(block=True)
    return fig 

def data_processing_agrochem(df, type_ , agrochem_property , to_lable = "1", by_points = 0 ):
    stats_type = df.groupby([type_,'Глубина']).agg({ np.mean,  np.std, scipy.stats.variation})
    if by_points == 0:
        features = [ 'Тип обработки', 'Глубина']
    else:
        features = ['GPS №', 'Глубина']
    features.append(agrochem_property) #добавление фичи
    df = df[features]
    stats = df.groupby([type_,'Глубина']).agg({ np.mean,  np.std, scipy.stats.variation})

    aov = aov_for_nominal(df, agrochem_property, by_points)
    stat_test_df = anova(df, type_, agrochem_property)
    fig = ploting(df, type_, agrochem_property, aov,stat_test_df,to_lable  )

    return(stats , aov, stat_test_df,fig )

####################################################################################################
################БЛОК ПО МОРФОЛОГИИ##################################################################

labs = ["CO\u2083\u00B2\u207B и HCO\u2083\u207B" , 
    "Cl\u207B",
    "SO\u2084\u00B2\u207B",
    "Ca\u00B2\u207A",
    "Mg\u00B2\u207A",
    "Na\u207A",
    "K\u207A"]
def profile_plot(sample,plot_name , horizonts = None,depth = None, colors = None, ):
    sns.set_theme(style="white", palette=None)
    agrochem_features =[
    "Сумма поглощенных оснований по Каппену, ммоль/100 г",
    'М.д. содержания  гипса (по Хитрову), %',
    'Массовая доля общего содержания карбонатов (по Козловскому), % (CO2)',
    'Органический углерод, %'
    ]

    agrochem_features_labs = [
        "СПО, ммоль/100 г",
        "Гипс, %",
        "Карботнаты, %",
        "Орг. Углерод, %" ]
    limits = [
        (20,30),
        (0,9), 
        (0,5),
        (0,2)

    ]
    hr = {'height_ratios': [ 2,4,2,2,2,2,1]}
    
    fig, ax  = plt.subplots(7,1, figsize = (10,15), gridspec_kw=hr )

    profile = sns.lineplot(data =sample, y ='Органический углерод, %' , x = "depth" ,alpha = 0,ci=None, ax = ax[-1])
    ax[-1].set( ylabel ='Горизонт', yticks =[], xlim=(0,200)  )
    ax[-1].set_xticklabels(ax[-1].get_xticks(), rotation = 90)
    ax[-1].set_xlabel('глубина', rotation = 180)
    ax[-1].set_title('№ скважины {}'.format(plot_name), fontsize = 16, rotation = 90, x = -0.1, y = 2)
    


    if horizonts != None:
        for hor in range(len(horizonts)):
            ax[-1].fill_between(x =depth[hor],y1 = 2, color=colors[hor],  hatch = ['+'])
            text_position = (depth[hor][1] - depth[hor][0])/2 + depth[hor][0]
            ax[-1].text(x = text_position , y = 0.6, s = horizonts[hor],size = 16,weight='bold' , rotation = 90)
            ax[-1].axvline(depth[hor][1],color =  "black", alpha = 0.5, linestyle = "--")

    ax_num = [2,3,4,5]
    for num, prop in enumerate(agrochem_features):

        property = gaussian_filter1d(sample[prop].astype('float'), sigma = 0.75)
        sns.lineplot(y = property , x = sample["depth"] ,color = 'black', ci=None, ax = ax[ax_num[num]])
        ax[ax_num[num]].set(xticks =[], xlabel=None, ylabel =agrochem_features_labs[num] , ylim=limits[num], xlim=(0,200))
        ax[ax_num[num]].set_yticklabels(ax[ax_num[num]].get_yticks(), rotation = 90)
        if horizonts != None:
            for line in depth:
               ax[ax_num[num]].axvline(line[1],color =  "black", alpha = 0.5, linestyle = "--")

    #соли

    kations = ['Массовая доля кальция (водорастворимая форма), ммоль/100 г почвы',
        'Массовая доля магния (водорастворимая форма), ммоль/100 г почвы',
        'Массовая доля натрия (водорастворимая форма), мг•экв на 100 г почвы',
        'Массовая доля калия (водорастворимая форма), мг•экв на 100 г почвы'
    ]
    anions = ['Карбонат и бикарбонат-ионы, ммоль/100 г', 
        'Массовая доля иона хлорида, ммоль/100 г',
        'Массовая доля иона сульфата, ммоль/100 г'
    ]
    sample[anions] = sample[anions] * -1 


    anions.extend(kations)
    salts = anions.copy()
    anions.extend(["Массовая доля плотного остатка водной вытяжки, %", "depth"])
    salt_sample = sample[anions]

    colors = ['#FF0000', "#FFF300", "#13FF00", "#00FFFB","#0000FF","#C500FF", "#FF0068" ]
    labs = ["CO\u2083\u00B2\u207B и HCO\u2083\u207B" , 
    "Cl\u207B",
    "SO\u2084\u00B2\u207B",
    "Ca\u00B2\u207A",
    "Mg\u00B2\u207A",
    "Na\u207A",
    "K\u207A"]
    legend_list = []
    for i in range(len(labs)):
        legend_list.append(mpatches.Patch(color=colors[i], label= labs[i],alpha=0.5))


    sns.lineplot(y =gaussian_filter1d(salt_sample["Массовая доля плотного остатка водной вытяжки, %"], sigma = 0.75) , x = salt_sample["depth"], color = 'black' ,ci=None, ax = ax[0])
    ax[0].invert_xaxis()
    ax[0].set(xticks=[], xlabel=None, ylabel ='Плотн.ост, %' )
    ax[0].set(ylim=(0, 2), label = '', xlim=(0,200))
    ax[0].set_yticklabels(ax[0].get_yticks(), rotation = 90)

    for line in depth:
        ax[0].axvline(line[1],color =  "black", alpha = 0.5, linestyle = "--")


    for num, sal in enumerate(salts):
        sns.lineplot( y =gaussian_filter1d(salt_sample[sal] , sigma = 0.75) , x = salt_sample["depth"] ,color = colors[num], ci=None, ax = ax[1])
        ax[1].fill_between(x =salt_sample["depth"],y1 = 0, y2 = gaussian_filter1d(salt_sample[sal] , sigma = 0.75), color= colors[num], alpha=0.5)

    ax[1].set(ylim=(-5, 5), ylabel ='Концентрация растворимых солей\nммоль/100 г', xlim=(0,200))
    ax[1].axhline(0,color =  "black")
    ax[1].set(xticks =[])
    ax[1].set_xlabel('', rotation = 180)
    ax[1].set_yticklabels(ax[1].get_yticks(), rotation = 90)
    for line in depth:
        ax[1].axvline(line[1],color =  "black", alpha = 0.5, linestyle = "--")

    ax[-1].set_title('№ скважины {}'.format(plot_name), fontsize = 16, rotation = 90, x = -0.1, y = 2)
    plt.legend(handles=legend_list, title='Растворимые соли', loc='lower left', mode = 'expand',ncol = 3, bbox_to_anchor=(1, 0.5, 0.5, 0.5))


#   plt.savefig('{}_профиль.png'.format(plot_name)) 

def gransostav_plot(gran_sostav, point):
    sample = gran_sostav[gran_sostav["GPS №"] == point]
    sns.set(rc={ 'figure.facecolor':'white'})
    small_labs = sample.columns[1:7]
    big_labs = sample.columns[7:9]
    fig, ax  = plt.subplots(2,1, figsize = (4,8))

    ax[0].pie(x = sample[big_labs].values.reshape(-1),autopct="%.1f%%",explode=[0.05]  * 2 ,wedgeprops={'edgecolor': 'black'}, labels = big_labs, shadow=True)
    ax[1].pie(x = sample[small_labs].values.reshape(-1),autopct="%.1f%%",explode=[0.05]  * 6 , wedgeprops={'edgecolor': 'black'}, labels = small_labs, shadow=True)
    ax[0].set_title("Гранулометрический состав {}".format(point))

    plt.show()


    #####################################################
    ###############Физика################################
def agrofiz_plot(data, proprety):
        sns.set(font_scale = 14)

        sns.set_theme(style="white", palette=None)
        fig = plt.figure(figsize=(7,7))
        plot = sns.pointplot(data = data,
                        x = "Тип обработки",
                        y = proprety,
                        hue = "Тип обработки",
                        palette = "prism",
                        scale = 1.2,
                        ci = 95,
                        join = False,
                        capsize = .05,)
        plot.set_title('Сравнение по обработкам')
        

        samp = data[["Тип обработки",proprety ]]
        stats = samp.groupby(["Тип обработки"]).agg({ np.mean,  np.std, scipy.stats.variation})
        a = samp[proprety][samp["Тип обработки"] == 'ТТ'].values
        b = samp[proprety][samp["Тип обработки"] != 'ТТ'].values
        AOV = ANOVA(a,b)

        return(stats,AOV,plot )

def SVD_vis(agrofiz):
    SVD_by_agregates = agrofiz[[
        'Тип обработки',
        'СВД водоустойчивые >10, мм',
        'СВД водоустойчивые 10-7, мм',
        'СВД водоустойчивые 7-5, мм' ,
        'СВД водоустойчивые 5-3, мм']]


    agregate_list = [
            'СВД водоустойчивые >10, мм',
            'СВД водоустойчивые 10-7, мм',
            'СВД водоустойчивые 7-5, мм' ,
            'СВД водоустойчивые 5-3, мм']

    SVD_by_agregates = SVD_by_agregates.melt(
        id_vars = 'Тип обработки' ,
        value_vars = agregate_list
        , var_name = 'Агрегаты, мм'
        , value_name='Размер, мм')

    SVD_by_agregates['Агрегаты, мм'] = SVD_by_agregates['Агрегаты, мм'].str.split(' ', expand=True)[2].str.replace(',','')

    

    anova = pd.DataFrame({"агрегаты" : agregate_list})

    p_val = []
    for i in agregate_list:
        df = agrofiz[["Тип обработки", i]].copy()

        a = df[i][df["Тип обработки"] == 'ТТ'].values
        b = df[i][df["Тип обработки"] != 'ТТ'].values
        AOV = ANOVA(a,b)[1]
        p_val.append(AOV)

    anova['P-val'] = p_val
    
    agregate_list.append("Тип обработки")
    stats = agrofiz[agregate_list].groupby(["Тип обработки"]).agg({ np.mean,  np.std, scipy.stats.variation})
    
    
    sns.set_theme(style="white", palette=None)
    fig = plt.figure(figsize=(7,7))
    plot = sns.pointplot(data = SVD_by_agregates,
                    x = "Агрегаты, мм",
                    y = "Размер, мм",
                    hue = "Тип обработки",
                    palette = "prism",
                    scale = 1.2,
                    dodge = 0.5,
                    ci = 95,
                    join = False,
                    capsize = .05,)
    plot.set_title('Сравнение по обработкам')
    plt.show()
    return(stats,anova,plot)


def Kvu(agrofiz):
        Kvu_by_agregates = agrofiz[[
            'Тип обработки',
            'Кву >10, мм',
            'Кву 10-7, мм',
            'Кву 7-5, мм' ,
            'Кву 5-3, мм']]
        agregate_list = [
            'Кву >10, мм',
            'Кву 10-7, мм',
            'Кву 7-5, мм' ,
            'Кву 5-3, мм']

        Kvu_by_agregates = Kvu_by_agregates.melt(
            id_vars = 'Тип обработки' ,
            value_vars = agregate_list
            , var_name = 'Агрегаты, мм'
            , value_name='Размер, мм')

        Kvu_by_agregates['Агрегаты, мм'] = Kvu_by_agregates['Агрегаты, мм'].str.split(' ', expand=True)[1].str.replace(',','')

        

        anova = pd.DataFrame({"агрегаты" : agregate_list})

        p_val = []
        for i in agregate_list:
            df = agrofiz[["Тип обработки", i]].copy()

            a = df[i][df["Тип обработки"] == 'ТТ'].values
            b = df[i][df["Тип обработки"] != 'ТТ'].values
            AOV = ANOVA(a,b)[1]
            p_val.append(AOV)

        anova['P-val'] = p_val
        
        agregate_list.append("Тип обработки")
        stats = agrofiz[agregate_list].groupby(["Тип обработки"]).agg({ np.mean,  np.std, scipy.stats.variation})
        
        
        sns.set_theme(style="white", palette=None)
        fig = plt.figure(figsize=(7,7))
        plot = sns.pointplot(data = Kvu_by_agregates,
                        x = "Агрегаты, мм",
                        y = "Размер, мм",
                        hue = "Тип обработки",
                        palette = "prism",
                        scale = 1.2,
                        dodge = 0.5,
                        ci = 95,
                        join = False,
                        capsize = .05,)
        plot.set_title('Сравнение по обработкам')
        plt.show()
        return(stats,anova,plot)


def ob_ves_plot(ob_ves):
        fig= plt.figure(figsize=(7,5))
        plot = sns.pointplot(data = ob_ves,
                x = "GPS №",
                y = "Объемный вес",
                hue = "GPS №",
                palette = "tab10",
                scale = 1.2,
                ci = 95,
                dodge= 0.5,
                join = False,
                capsize = .05,
        )
        plot.set(title =  'Объемный вес')
        plt.show()


        aov_list = []
        for i in ob_ves['GPS №'].unique():
            lst = list(ob_ves["Объемный вес"][ob_ves['GPS №'] == i].values)
            aov_list.append(lst)
        aov = ANOVA(*aov_list)

        stats = ob_ves[["Объемный вес", "GPS №"]].groupby(["GPS №"]).agg({ np.mean,  np.std, scipy.stats.variation})

        return(stats,aov,plot)