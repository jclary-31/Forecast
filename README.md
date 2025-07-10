Most of today forecast come from deterministic models, where confidence is difficult to estimate. For example, how much a model statement like 'tomorrow temperature in New York at 12h will be 30 Celsius' is correct? 
Here I use ensemble forecast from ECCC to estimate forecasts on temperature or relative humidity (for example) I estimate confidence interval. The larger the confidence interval, the lower the confidence is. 


The following code can either :
- give forecast for a given location, it needs a location as city, country or it needs a position (lat,lon).
- give wind energy production in a USA state, with a confidence interval. Here the confidence interval is only evaluated from winds, because electrical grid state (for example) is not known

To run the code, one can execute:
python ensemble_forecast  #no input is required. Forecast will be computed for default location
or
python ensemble_forecast -city # 2 input are then asked : city, and then country. Country is required to not mistake Lonond in Canada with London in G.B (for example)
or
python ensemble_forecast -latlon # 2 input are then asked latitude, and longitude
or
python ensemble_forecast -WF # input must be the two letter acronym of a USA state



# Weather Forecast

To get latitude and longitude from a city name, I had to use a geolocator from geopy which sometimes does not work. In that case, default location is set to Montréal and a message is sent in the terminal as 'Geolocator not reached! hhtps connection failed. Reference taken= Montréal' 

# US energy market (wind farm)
 I wanted to do it for US energy market, but I didn't find the required information. I think it exist somewhere on the internet. For energy production, the forecasts is now fixed for Texas, because Texas is the state with the largest number of wind farms, because I found a clear estimation of the coefficient factor, and most importantly because Texas' forecasts are easy to compare with Ercot market prediction (Ercot~ Texas), see https://www.ercot.com/gridmktinfo/dashboards/combinedwindandsolar


The csv file forUnited States Wind Turbine Database can be downloaded here : https://energy.usgs.gov/uswtdb/data/
The nominal power by state can vizualised here :https://windexchange.energy.gov/maps-data/321. Nominal power is when coefficent factor=1 , i.e. when wind farm have 100% efficiency. Usually, efficiency is around 30-40%, because of maintenance, low needs (almost no battery to stock energy),  electrical grid,... 

#Side note

Getting the energy production is much faster than weather forecast because the code exploit vectorized interpolation to get wind at all wind farm in once (for a given date) whereas for weather I have to seek in different files (one per variable). 
