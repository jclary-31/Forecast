from utils import *
import sys
#on my computer _tkinter.TclError: failed to allocate font due to internal system font engine problem
# if plt is called after using xarray.open_dataset() ... very strange
# I need a false call of plt before
x=[1,2,3,4,5,6,5,4,3]
plt.plot(x)
plt.close()



if len(sys.argv)==1:
    #test case/default
    city='Montréal'
    country='CA'
    location=get_location_fromcity(city,country)

elif len(sys.argv)>1:
    if sys.argv[-1]=='-city':
        city=input('city:')
        country=input('country: ')
        location=get_location_fromcity(city,country)

    elif sys.argv[-1]=='-latlon':
        lat=input('latitude: ')
        lon=input('longitude: ')
        location=(lat,lon,get_locname_fromlatlon(lat,lon) ,get_tzone(lat,lon))

    elif sys.argv[-1]=='-WF':
        state=input('US state (abbreviation): ') 
        ###load us wind turbine database
        uswt_file='US_Wind_Turbine_Database.csv'
        uswt_db=pd.read_csv(uswt_file,low_memory=False)
        #uwstdb acronym here https://energy.usgs.gov/uswtdb/api-doc/
        uswt_db=uswt_db.drop(uswt_db[uswt_db['eia_id']<0].index)
        uswt_db=uswt_db.drop(uswt_db[uswt_db['t_cap']<0].index)
        uswt_db=uswt_db.drop(uswt_db[uswt_db['p_cap']<0].index)
        Df_state,location =WT_USstate(uswt_db,state)

    else:
        'error'
        #return    



#varcodes: see https://eccc-msc.github.io/open-data/msc-data/nwp_reps/readme_reps-datamart_en/#list-of-variables
#rain is missing!

# if only one location, forecast at a given location
if len(location)==1:
    var_codes=['TMP_AGL-2m','RH_AGL-2m']#,'WIND_AGL-10m',,'TCDC']#,'PRES_SFC']
    #DSWRF_SFC and DLWRF_SFC for surface radiation?
    #SNOD_SFC #snow at surface; add it from november to may?
    #RH =relative humidity
    #TCDC is total cloud cover

    Forecasts=dict()
    for var_code in var_codes:
        Forecasts[var_code]= extract_ensemble(var_code,location)
        #use xr.merge instead? but if so variable need specific name not the generic 'variable' I use

    for i in range(len(var_codes)):
        var_code=var_codes[i]
        for j in range(len(location)):
            aForecast=Forecasts[var_codes[i]]['variable'][:,:,j]
            fig4prod(aForecast,location[j],var_code)

            if i==0 and j==0:
                fig4test(aForecast,location[j],var_code)


# if multiple location, then suppose it is for wind energy production
if len(location)>1:
    var_codes=['WIND_AGL-80m']

    WForecast=extract_ensemble('WIND_AGL-80m',location,maxhour=48)
    #dimensions are (time, nmodels,nlocation)

    CF=0.35#capacity factor see last figure https://www.eia.gov/todayinenergy/detail.php?id=45476
    #web site article is from 2020
    Power_All=[]
    for k in range(len(location)):
        df_WF=Df_state.iloc[k]
        Wind=WForecast['variable'][:,:,k]
        Power_WF=wind_power_byWF(Wind,df_WF)
        Power_WF.values=Power_WF.values*CF
        Power_All.append(Power_WF.T)

    Power=xr.concat(Power_All,dim='WFlocation').T
    #Power dimension is now as Wforecast, i.e (time, nmodels,nlocation)
    Power_agg=Power.sum(axis=2)/1000#dive by 1000 to be in Mw
    Power_agg.attrs['standard_name']='Aggregated power'
    Power_agg.attrs['units']='MW'

    #figure
    tzone=get_tzone(Df_state['ylat'].mean(),Df_state['xlong'].mean())
    mean_loc=(Df_state['ylat'].mean(),Df_state['xlong'].mean(),state,tzone) 
    aForecast=Power_agg
    fig4prod(aForecast,mean_loc,'Power')
    #compare with https://www.ercot.com/gridmktinfo/dashboards/combinedwindandsolar for texas




#Pour visualisation de Df_state voir https://plotly.com/python/pie-charts/

# # all existing variable in  ensemble repo
# xmlfile= 'reps_element.xml'
# #if xml is downoaded
# if xmlfile in os.listdir():    
#     tree = ET.parse(xmlfile)
#     root=tree.getroot() 
# else:    
#     url= 'https://collaboration.cmc.ec.gc.ca/cmc/cmos/public_doc/msc-data/nwp_reps/reps_element.xml'
#     response=requests.get(url)
#     root=ET.fromstring(response.content)

# data_attr=dict()
# for n in range(len(root)):
#     inxml=root[n].attrib
#     cod=inxml.get('code')
#     meaning=inxml.get('title_english')
#     unit=inxml.get('unit_english')
#     data_attr[cod]=[meaning,unit]

# var_code='TMP_AGL-2m'
# var_codes=['TMP_AGL_2m','WIND_AGL_10m','PRES_SFC']

# #in xml 'TGL, whereas is it AGL is web repositories...
# data_attr['TMP_AGL_2m']=data_attr.pop('TMP_TGL_2m')
# for key in list(data_attr.keys()):
#     if 'TGL' in key:
#         newkey=key.replace('TGL','AGL')
#         data_attr[newkey]=data_attr.pop(key)

# ###replace '_'
# for key in list(data_attr.keys()):
#    li=key[::-1].split('_',1)
#    newkey='-'.join(li)[::-1]
#    data_attr[newkey]=data_attr.pop(key) 

