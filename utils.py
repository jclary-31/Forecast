#utility
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stat
from scipy.interpolate import griddata 
#from matplotlib.dates import DateFormatter
import types
#import xml.etree.ElementTree as ET 
import xarray as xr 
import urllib.request
from geopy.geocoders import Nominatim
import requests
import pytz


###########################Location helper###########################
#####################################################################

def get_location_fromcity(city,country):
    geolocator = Nominatim(user_agent="my_user_agent")
    try:
        loc = geolocator.geocode(city+','+ country)
    except :
        print('geolocator not reached! hhtps connection failed')
        print('reference taken= Montréal')
        adic=dict()
        adic['latitude']=45.509
        adic['longitude']=-73.562
        loc=types.SimpleNamespace(**adic)   

    lat=loc.latitude
    lon=loc.longitude
    tzone=get_tzone(lat,lon)

    return [(lat,lon,city+' '+country,tzone)]

def get_tzone(lat,lon):
    #from timezonefinder import TimezoneFinder ##some bug on wsl
    #obj = TimezoneFinder()
    #zone = obj.timezone_at(lng=lon,lat= lat)
    #tzone=pytz.timezone(zone)
    #tutc=Mydf.index
    #
    #use api because i have a bug with timezonefinder on wsl
    #api format f"http://timezonefinder.michelfe.it/api/{mode}_{lat}_{lon}"#error ! it is {lon}_{lat}
    #url=https://timezonefinder.michelfe.it/gui
    mode=0#'TimezoneFinder.timezone_at()'
    call=f"http://timezonefinder.michelfe.it/api/{mode}_{lon}_{lat}"
    response=requests.get(call)
    zone=response.json()['tz_name']
    tzone=pytz.timezone(zone)
    return tzone

def get_locname_fromlatlon(lat,lon):
    geolocator = Nominatim(user_agent="nearby_search")
    #locname=geolocator.reverse((lat, lon))[0].split(',')[0].replace(' ','_')
    locdic=geolocator.reverse((lat, lon)).raw['address']
    if 'city' in locdic.keys():
        locname=locdic['city']
    else:
        locname=locdic['county']  

    locname=locname.replace(' ','_')
    return locname      





###########################Data Extraction###########################
#####################################################################

def nearest_index(ds,location):
    #
    #see maps here https://eccc-msc.github.io/msc-animet/
    #see https://stackoverflow.com/questions/58758480/xarray-select-nearest-lat-lon-with-multi-dimension-coordinates
    idx=[]
    idy=[]
    for loca in location:
        lat,lon,_,_=loca
        d_lat = ds.latitude - lat
        d_lon = ds.longitude - lon
        r2 = d_lat**2 + d_lon**2
        i_j_loc = np.where(r2 == np.min(r2))
        idx.append(i_j_loc[1])
        idy.append(i_j_loc[0])
    #
    #put in the right format: a list of number
    idx=np.array(idx).flatten().tolist()
    idy=np.array(idy).flatten().tolist()
    return (idy,idx)




def extract_ensemble(var_code,location,maxhour=None):    

    if maxhour is None:
        maxhour=24
    Allds=[]
    for n in np.arange(0,maxhour+1,3):
        nhour='{:03.0f}'.format(n)
        webdir='https://dd.meteo.gc.ca/ensemble/reps/10km/grib2/00/'+nhour+'/'


        allgrib2=[]
        try:
            Req=requests.get(webdir)
        except requests.exceptions.HTTPError as err:
            print ("Http Error:",err)
        
        splitted=Req.text.split('href=')
        for txt in splitted : 
            if 'grib2' in txt:
                file=txt.split('grib2')[0][1::] + 'grib2'
                allgrib2.append(file)

        tokeep=[]
        #note : first 2 are text!
        for gribfile in allgrib2:
            if var_code in gribfile:
                tokeep.append(gribfile)

        if len(tokeep)>1:
            print('conflict in files!')

        todownload=webdir+tokeep[0]
        print('retrieving: ' +nhour+'h '+ tokeep[0].split('.')[0][13:-9])
        urllib.request.urlretrieve(todownload, 'temp.grib2')

        ds = xr.open_dataset('temp.grib2',engine='cfgrib',filter_by_keys={'dataType':'pf'})
        idxfile='temp.grib2.923a8.idx'
        if idxfile in os.listdir():    #this is to avoid a warning message at next iteration 
            os.remove(idxfile)

        data_name=list(ds.keys())[0]

        #nearest_index(ds,(a,b)) give (400,600) ;!! ok
        iy,ix=nearest_index(ds,location)
        ds_extract=ds.interp(y=('z',iy), x=('z',ix)) #ix and iy are lists ; see advanced interpolation for xarray

        vals=ds_extract[data_name].values#.flatten() #flatten ok if len(iy and ix)=1   
        time_utc=pd.to_datetime(ds['valid_time'].values,utc=True)

        newds=xr.Dataset(
            data_vars=dict(variable=(['models','loc'],vals)),
            coords=dict(lon=('loc',ds_extract.longitude.values),
                        lat=('loc',ds_extract.latitude.values),
                        time_utc=time_utc,
                        models=ds.number.values)
        )

        var_name=ds[data_name].standard_name
        if var_name=='unknown':
            var_name=ds[data_name].long_name.replace(' ','_')

        newds['variable'].attrs['standard_name']=var_name
        newds['variable'].attrs['units']=ds[data_name].units

        if 'TMP' in todownload: #convert kelvin into celsius degrees
            newds['variable'].values+=-273.15 
            newds['variable'].attrs['units']='C'

        Allds.append(newds)

    Extract=xr.concat(Allds,dim='time')                

    return Extract

def wind_power_byWF(Wind,df_WF):
    ''' see https://www.e-education.psu.edu/emsc297/node/649
    this is a first approximation
    power=0.5*airdensity*WTcrossarea*windspeed**3
    '''
    airdensity=1.225 #this is standar air density ; kg/m**3
    wind_max=22# max accepted wind ; m/s
    wind_min=2#minimum wind speed needed to start production m/s
    WTcrossarea=df_WF['t_rsa'] #aversage cross area by wtg for a given wind farm ; m**2
    power_max=df_WF['t_cap'] #average power by wtg at a wind farm ; kW
    nwtg=df_WF['count'] #number of wtg
    #
    Power_bywtg=.5*airdensity*WTcrossarea*Wind**3/1000# 1/1000 to convert Watt in kiloWatt
    Power_bywtg.values[Wind>wind_max]=np.nan #no energy produced if wind too strong
    Power_bywtg.values[Wind<wind_min]=np.nan #no energy produced if wind too small
    #
    Power_bywtg.values[Power_bywtg>power_max]=power_max# each WTG have a maximum production
    Power=Power_bywtg*nwtg
    Power.attrs['units']='kW'
    Power.attrs['standard_name']='power'
    Power.attrs['WFname']=df_WF.p_name[0] 
    return Power

def  WT_USstate(uswt_db,state):
    df_state=uswt_db[uswt_db.t_state==state]

    #power by state can be seen  at https://windexchange.energy.gov/maps-data/321
    #uwstdb acronym here https://energy.usgs.gov/uswtdb/api-doc/
    
    agg_dic={'xlong':'mean','ylat':'mean',
            't_cap':'mean','t_hh':'mean','t_rsa':'mean',
            'p_name':'unique',
            'eia_id':'count'
            }
    Df_state=df_state.groupby(['eia_id']).agg(agg_dic)
    Df_state['count']=Df_state.pop('eia_id')

    #total power
    tot=(Df_state['t_cap']*Df_state['count']).sum()/1e6
    print('total power in ' + state + ' is ' + '{:2.2f}'.format(tot)+'MW')

    location=[]
    for i in range(len(Df_state)):
        lat=Df_state.iloc[i]['ylat']
        lon=Df_state.iloc[i]['xlong']
        locname=Df_state.iloc[i]['p_name'][0]
        if i==0:#time zone is the same for all the stat so do it once only
            tzone=get_tzone(lat,lon)
        loc=([lat,lon,locname,tzone])
        location.append(loc)

    return Df_state,location      

###########################Ensemble analysis########################
####################################################################

#Some analysis
def confidence_interval(df,perc):
    #confidence interval using student t test
    #confidence is standard error (or meaasurement precision) * tvalue
    #se= np.std(a)/np.sqrt(len(a)-1) #standard error
    #tvalue=2.093 #for 95% and dof=19 ; see https://www.scribbr.com/statistics/students-t-table/
    #
    CI_low=[]
    CI_up=[]
    for i in range(df.shape[0]):#along ligns as each lign is a date
        a=df.iloc[i]
        ci=stat.t.interval(perc, len(a)-1, loc=np.mean(a), scale=stat.sem(a))
        CI_low.append(ci[0])
        CI_up.append(ci[1])
        CI=(CI_low,CI_up)
    return CI


def gaussian_density(Df,n=None):
    if n==None:
        n=20
    minval=np.min(Df.min())
    maxval=np.max(Df.max())
    eval_vec=np.linspace(minval,maxval,n)
    Proba=[]
    for i in range(len(Df)):
        kde=stat.gaussian_kde(Df.iloc[i]).evaluate(eval_vec)
        Proba.append(kde/sum(kde))#sum (All probailities at a given time) =1
    Proba=np.transpose(Proba)
    return Proba, eval_vec


###########################Visualization###########################
####################################################################
#Figure
def fig4prod(aForecast,location,var_code):
    #aForecast
    
    Mydf=pd.DataFrame(aForecast.variable.values)
    units=aForecast.attrs['units']
    name=aForecast.attrs['standard_name']

    #timestuff
    time_utc=pd.to_datetime(aForecast.time_utc.values,utc=True)
    #time_utc=aForecast.time_utc.values
    tzone=location[-1]
    time_local=time_utc.tz_convert(tzone)
    Mydf.index=time_local
    timeformat='%m-%d, %Hh'
    timelabel=[x.strftime(timeformat) for x in Mydf.index]
    #time_vec=Mydf.index
    #Mydf_hourly=Mydf.resample('h').interpolate(method='cubic')

    #get location of true city or county
    lon=location[1]
    lat=location[0]
    locname=location[2]#get_locname_fromlatlon(lat,lon)###not good if Forecst respresent an ensemble of points!


    CI=confidence_interval(Mydf,0.95)
    df_CI=pd.DataFrame(CI).T
    df_CI.index=time_local

    #check here if lon lat taken in  grib are close to the one asked (which are stored in location)
    ###coder harvesine en propre!
    #lon=aForecast.lon.values.tolist()
    #lat=aForecast.lat.values.tolist()
    #lat_asked=location[0]
    #lon_asked=location[1]
    #dist= np.sqrt((lat-lat_asked)**2+(lon-lon_asked))**2 *6370 #this is an approximation

    fig,ax=plt.subplots(figsize=(8,4))
    #ax.plot(Mydf.index,Mydf.T.quantile(.25),'k',linewidth=1)
    p0,=ax.plot(Mydf.index,Mydf.mean(axis=1),'r',linewidth=2)
    p2=ax.plot(Mydf.index,df_CI,
                'k',linewidth=1)
    ax.set_xticks(Mydf.index, labels=timelabel)
    #ax.xaxis.set_major_formatter(date_form)
    ax.tick_params(axis='x', labelrotation=45)
    ax.fill_between(Mydf.index,df_CI[0],df_CI[1],alpha=0.2)
    ax.legend([p0,p2[0]],
            ['mean ensemble', '95% confidence interval'])
    ax.set_title('time serie for ' +var_code + ' at '+locname)
    ax.set_xlabel('time')
    ax.set_ylabel(name +'('+units+')')
    fig.tight_layout()
    #fig.show()
    fig.savefig('results/prod/'+locname+'_Timeserie_'+var_code+'.jpg',bbox_inches='tight')


    fig,ax=plt.subplots(figsize=(8,4))
    sns.boxplot(Mydf.T)
    ax.set_xticks(np.arange(0, Mydf.shape[0], step=1), labels=timelabel)
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_title('boxplot for '+var_code + ' at '+ locname)
    ax.set_xlabel('time')
    ax.set_ylabel(name +'('+units+')')
    fig.tight_layout()
    fig.savefig('results/prod/'+locname+'_Boxplot_'+var_code+'.jpg',bbox_inches='tight')


def fig4test(aForecast,location,var_code):

    Mydf=pd.DataFrame(aForecast.variable.values)

    #timestuff
    time_utc=pd.to_datetime(aForecast.time_utc.values,utc=True)
    tzone=location[-1]
    time_local=time_utc.tz_convert(tzone)
    Mydf.index=time_local
    timeformat='%m-%d, %Hh'
    #date_form = DateFormatter(timeformat) #this transform local time back into utc, not good
    timelabel=[x.strftime(timeformat) for x in Mydf.index]
    time_vec=Mydf.index

    #compute confidence interval to compare with 25 and 75% quantile
    CI=confidence_interval(Mydf,0.95)
    df_CI=pd.DataFrame(CI).T
    df_CI.index=time_local



    fig,ax=plt.subplots(figsize=(8,4))
    ax.plot(Mydf.index,Mydf,color='k',linestyle='dashed',linewidth=.5)
    ax.plot(Mydf.index,Mydf.mean(axis=1).T,color='r')
    ax.set_xticks(Mydf.index, labels=timelabel)
    ax.tick_params(axis='x', labelrotation=45)
    fig.savefig('results/test/'+var_code+'_ensemble_timeseries.jpg',bbox_inches='tight')
    #plt.show()

    fig,ax=plt.subplots(figsize=(8,4))
    sns.boxplot(Mydf)
    fig.savefig('results/test/'+var_code+'_models_variabilities.jpg',bbox_inches='tight')


    fig,ax=plt.subplots(figsize=(8,4))
    sns.boxplot(Mydf.T)
    #ax.xtick( labelrotation=45)
    ax.set_xticks(np.arange(0, Mydf.shape[0], step=1), labels=timelabel)
    ax.tick_params(axis='x', labelrotation=45)
    fig.savefig('results/test/'+var_code+'_ensemble_boxplot.jpg',bbox_inches='tight')
    #plt.show()


    fig,ax=plt.subplots(figsize=(8,4))
    sns.heatmap(Mydf.T)
    ax.set_xticks(np.arange(0, Mydf.shape[0], step=1), labels=timelabel)
    ax.tick_params(axis='x', labelrotation=45)
    fig.savefig('results/test/'+var_code+'_ensemble_heatmap.jpg',bbox_inches='tight')
    #plt.show()



    fig,ax=plt.subplots(figsize=(8,4))
    #ax.plot(Mydf.index,Mydf.T.quantile(.25),'k',linewidth=1)
    p0,=ax.plot(Mydf.index,Mydf.mean(axis=1),'r',linewidth=2)
    p1=ax.plot(Mydf.index,Mydf.T.quantile([.25,.75]).T,
                'k',linestyle='-.',linewidth=1)
    p2=ax.plot(Mydf.index,df_CI,
                'k',linewidth=1)
    ax.set_xticks(Mydf.index, labels=timelabel)
    ax.tick_params(axis='x', labelrotation=45)
    ax.fill_between(Mydf.index,df_CI[0],df_CI[1],alpha=0.2)
    ax.legend([p0,p1[0],p2[0]],
            ['mean ensemble', '25% and 75% quantile', '95% confidence interval'])
    #fig.show()
    fig.savefig('results/test/'+var_code+'+_Confidence_interval.jpg',bbox_inches='tight')
    fig.tight_layout()




    Proba,eval_vec=gaussian_density(Mydf,n=None)
    #Proba,eval_vec=gaussian_density(Mydf_hourly,n=None)
    #if Proba.shape[1]!=Mydf.shape[0]:
    #    timelabel=[x.strftime(timeformat) for x in Mydf_hourly.index]
    #    time_vec=Mydf_hourly.index
  
    #ca cest pas pire
    fig,ax=plt.subplots(figsize=(8,4))
    cf=sns.heatmap(Proba,cmap='Greys') #niveau de proba en niveau de gris??
    ax.set_xticks(np.arange(0+.5, Proba.shape[1]+.5, step=1), labels=timelabel)
    ax.set_yticks(np.arange(0+.5, len(eval_vec)+.5, step=2), labels=['{:0.2f}'.format(n) for n in eval_vec][::2])
    #ax.yaxis.set_inverted(True)
    ax.invert_yaxis()
    #ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.2f'))
    ax.tick_params(axis='x', labelrotation=45)

    ax.set_title('Proba density for '+  var_code + ' at (' + str(location[0])+'N' +', '+ str(location[1])+'E)')

    fig.savefig('results/test/'+var_code+'_Probaheatmap_'+'.jpg',bbox_inches='tight')




    fig,ax=plt.subplots(figsize=(8,4))
    cf=ax.contourf(time_vec,eval_vec,Proba,40,cmap='Greys')
    ax.plot(time_vec,Mydf.T.quantile(.25),'k',linewidth=1)
    ax.plot(time_vec,Mydf.mean(axis=1),'r',linewidth=2)
    ax.plot(time_vec,Mydf.T.quantile(.75),'k',linewidth=1)
    ax.set_xticks(time_vec, labels=timelabel)
    cbar=fig.colorbar(cf,ax=ax)
    fig.savefig('results/test/'+var_code+'_Proba_contourf.jpg',bbox_inches='tight')
    #fig.show()

    #### test in log space
    z=np.log10(Proba+1e-4)#sometime Proba=0
    z1=(z-np.min(z,axis=0))/(np.max(z,axis=0)-np.min(z,axis=0))#standartisation aka min-max scaling 
    z2= z-np.mean(z,axis=0)/np.std(z,axis=0)#normalize
    z1=z1/(np.sum(z1,axis=0)+1e-6)# AND  Proba, so sum must be 1
    z2=z2/(np.sum(z1,axis=0)+1e-6)# AND  Proba, so sum must be 1
    Proba_log1=z1
    Proba_log2=z2

    fig,ax=plt.subplots(1,2,figsize=(8,4))
    cf=ax[0].contourf(time_vec,eval_vec,Proba_log1,40,cmap='Greys')
    ax[0].plot(Mydf.index,Mydf.T.quantile(.25),'k',linewidth=1)
    ax[0].plot(Mydf.index,Mydf.mean(axis=1),'r',linewidth=2)
    ax[0].plot(Mydf.index,Mydf.T.quantile(.75),'k',linewidth=1)
    ax[0].set_xticks(Mydf.index, labels=timelabel)
    cbar=fig.colorbar(cf,ax=ax[0])

    cf=ax[1].contourf(time_vec,eval_vec,Proba_log2,40,cmap='Greys')
    ax[1].plot(Mydf.index,Mydf.T.quantile(.25),'k',linewidth=1)
    ax[1].plot(Mydf.index,Mydf.mean(axis=1),'r',linewidth=2)
    ax[1].plot(Mydf.index,Mydf.T.quantile(.75),'k',linewidth=1)
    ax[1].set_xticks(Mydf.index, labels=timelabel)
    cbar=fig.colorbar(cf,ax=ax[1])
    fig.savefig('results/test/'+var_code+'_Proba_logspace.jpg',bbox_inches='tight')


    #other test : increase resol in value space
    x=np.arange(0,Proba.shape[1])
    y=eval_vec
    xnew=x
    ynew=np.arange(np.min(y),np.max(y),0.1)
    X,Y= np.meshgrid(x, y)
    Xnew,Ynew= np.meshgrid(xnew, ynew)
    Proba_hr=griddata((X.flatten(),Y.flatten()),Proba.flatten(),(Xnew,Ynew),'cubic')

    Mydf_hourly=Mydf.resample('h').interpolate(method='cubic')
    fig,ax=plt.subplots(figsize=(8,4))
    cf=ax.contourf(time_vec,ynew,Proba_hr,40,cmap='Greys')
    ax.plot(Mydf_hourly.index,Mydf_hourly.T.quantile(.25),'k',linewidth=1)
    ax.plot(Mydf_hourly.index,Mydf_hourly.mean(axis=1),'r',linewidth=2)
    ax.plot(Mydf_hourly.index,Mydf_hourly.T.quantile(.75),'k',linewidth=1)

    fig.savefig('results/test/'+var_code+'_Proba_hr.jpg',bbox_inches='tight')
    #fig.show()

