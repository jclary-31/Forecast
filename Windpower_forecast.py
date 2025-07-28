from utils import *
import sys
#on my computer _tkinter.TclError: failed to allocate font due to internal system font engine problem
# if plt is called after using xarray.open_dataset() ... very strange
# I need a false call of plt before
x=[1,2,3,4,5,6,5,4,3]
plt.plot(x)
plt.close()

horizon=24#in hour

#load
###load us wind turbine database
uswt_file='US_Wind_Turbine_Database.csv'
uswt_db=pd.read_csv(uswt_file,low_memory=False)
#uwstdb acronym here https://energy.usgs.gov/uswtdb/api-doc/
uswt_db=uswt_db.drop(uswt_db[uswt_db['eia_id']<0].index)
uswt_db=uswt_db.drop(uswt_db[uswt_db['t_cap']<0].index)
uswt_db=uswt_db.drop(uswt_db[uswt_db['p_cap']<0].index)
uswt_db=uswt_db.drop(uswt_db[uswt_db['t_hh']<0].index)


if len(sys.argv)==1:
    #test case/default
    sys.argv.append('-state')
    territory='TX'
    Df,location =WT_USagg(uswt_db,'state',territory)

elif len(sys.argv)>1:
    if sys.argv[-1]=='-market':
        print('For a comprehensive map of US energy market : https://www.ferc.gov/electric-power-markets')
        territory=input('US market: ')

        ##get US market from eia plants/generator database
        eia_file='eia_generator_202506.xlsx'
        eia_db=pd.read_excel(eia_file,sheet_name='Operating',header=2)
        eia_db.rename(columns={'Balancing Authority Code':'Market',
                            'Plant ID':'eia_id'},
                            inplace=True)
        eia_db=eia_db[eia_db['Energy Source Code']=='WND'] # only wind wanted
        eia_db=eia_db[eia_db['Status'].str.contains('OP')]# only active wanted


        # complete uswtb with info from eia_db ; i.e. add Market columns
        Id=uswt_db['eia_id'].unique().tolist()
        for eia_id in Id:
            if (eia_db['eia_id']==eia_id ).any():  # if wanted eia_id exist in both database
                markett=eia_db[eia_db['eia_id']==eia_id]['Market'].unique()[0]
                uswt_db.loc[uswt_db['eia_id']==eia_id,'Market']=markett

        #uswt_db=uswt_db[uswt_db['Market']==market]
        Df,location=WT_USagg(uswt_db,'market',territory)
    

    elif sys.argv[-1]=='-state':
        territory=input('US state (abbreviation): ') 
        Df,location =WT_USagg(uswt_db,'state',territory)

    else:
        'error'
        #return    


# if multiple location, just a dumb test to know if multiple location#then suppose it is for wind energy production
if len(location)>1:
    var_codes=['WIND_AGL-80m']

    WForecast=extract_ensemble('WIND_AGL-80m',location,maxhour=horizon)
    #dimensions are (time, nmodels,nlocation)

CF=0.35#capacity factor see last figure https://www.eia.gov/todayinenergy/detail.php?id=45476
#web site article is from 2020
Power_All=[]
for k in range(len(location)):
    df_WF=Df.iloc[k]
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
tzone=get_tzone(Df['ylat'].mean(),Df['xlong'].mean())
mean_loc=(Df['ylat'].mean(),Df['xlong'].mean(),territory,tzone) 

aForecast=Power_agg
fig4prod(aForecast,mean_loc,'Power')
    #compare with https://www.ercot.com/gridmktinfo/dashboards/combinedwindandsolar for texas



