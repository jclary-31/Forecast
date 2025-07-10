Most of today forecast come from deterministic models, where confidence is difficult to estimate. For example, how much a model statement like 'tomorrow temperature in New York at 12h will be 30 Celsius' is correct? 
Here I use ensemble forecast from ECCC to estimate forecasts on temperature or relative humidity (for example) I estimate confidence interval. The larger the confidence interval, the lower the confidence is. 




The following code can either :
- give forecast for a given location, it needs a location as city, country or it needs a position (lat,lon).
- give wind energy production in a USA state. I wanted to do it for US energy market, but I didn't find the required information. I think it exist somewhere on the internet. The code exploit vectorized interpolation to get wind at all wind farm in once (for a given date)


For energy production, the forecasts is now fixed for Texas, because Texas is the state with the largest number of wind farms, because I found a clear estimation of the coefficient factor, and most importantly because Texas' forecasts are easy to compare with Ercot market prediction (Ercot~ Texas), see https://www.ercot.com/gridmktinfo/dashboards/combinedwindandsolar



