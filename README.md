# USA energy market
A nice introduction to USA energy market can be found here [USmarket101](https://www.rff.org/publications/explainers/us-electricity-markets-101/). Other informations are on [wikipedia](https://en.wikipedia.org/wiki/Electricity_sector_of_the_United_States). One can found here that in the past 10 years wind power gain approximatively 10% of the total energy produced in the USA, highlightning wind power important developpment. This is partly due to Biden decisions, which initiated a lot of projects still in construction (not yet operational) 

In the USA, some of the energy market are deregularized market, meaning that prices are not controlled by the governement, but mainly depend on the need-offer balance. Goal is to generate competition to lower prices across the deregulated area. Indeed, in many areas, a customer can choose an electric supplier instead of purchasing electricity from governmental utilities. This indroduced a retail market for electricity. On one hand, retail prices can help customer to find lower prices or to buy energy from clean energy sources only. On the other hand, customer choosing independant companies are often attached by contract for years while prices are much more volatile than in the regulated market.  

A visual of main energy markets (also called 'Regional Transmission Organizations' aka RTO) can be vizualized in the following picture (taken from the aformentionned website). As one can see, RTO's area is not a state or a set of states. For example, North California is not in California ISO, and PJM interconnection is present in less than 20% of North Carolina. Some informations can also be found [here](https://www.ferc.gov/electric-power-markets).

<p align="center">
 <img width="800" src=main_energy_market.png>
 </p>

In deregulated markets, companies produces energy and buy/loan energy to sell it to customers. So, in those markets, energy is auctionned on a day to day basis. Transactions can be done on real-time market or on the day ahead market. 
The day ahead market represent 90+% of the energy transactions. As a consequence, any company and any trader operating in those market needs to have an estimation of day ahead production capacities. Most, if not all, of today day-ahaed forecasts come from a deterministic model, meaning that a given forecast is 'absolute' in the sense that it have no error and no randomness. However, markets are by nature complex, irregular, and always sensitive to unexpected events. By nature, deterministic forecast will fail time to time. Not knowing how and when is a major issue for shareholders.

[ERCOT example](https://www.ercot.com/gridmktinfo/dashboards/combinedwindandsolar)

# Ensemble forecast
A deterministic model will give a statement as 'tomorrow temperature in New York at 12h will be 30 Celsius'. But is this statement correct? and how much of this statement is true?. Maybe temperature will be 28 Celsius because of a local small cold front coming from the sea,  or maybe it will 34 Celsius because of unexpected low winds and because of local urban heat effects. So, the statement in more an indication than a true prediction. The missing information in the statement is the probability of the prediction, in other words what confidence can I give to the statement. 

Situation is similar for renewableenergy production. In the case of energy produced by wind farms, The most crucial factor, is of course, wind amplitude. Wind is chaotic by nature, especially near the surface, where topography induces turbulence(=chaos) and others small scales phenomenom (which are unpredictible because of resolution limits). 


# Results
The following figure show predictions coming from ensemble forecast. There a several level of comprehension. In a nutshell, using ensemble forecasts give information on when prediction will be less 'secure',  or more 'secure, which permit to better know when to buy or sell energy.


level0 : timeserie with confidence interval (using student test). A smaller confidence interval (gray area) mean better confidence in the prediction. 

<p align="center">
 <img width="800" src=results/prod/ERCO_Timeserie_Power.jpg>
</p>

level1: time serie of [box plot](https://en.wikipedia.org/wiki/Box_plot). Box plot show min, max, 25%, 50% an 75% quartile. Box plot show outliers and give information on distribution assymetry

<p align="center">
 <img width="800" src=results/prod/ERCO_Boxplot_Power.jpg>
</p>

level2: Probability heat map. This map the distribution assymetry. Notice here that colors are NOT symmetric around the median line (in white)

<p align="center">
 <img width="800" src=results/prod/ERCO_Probaheatmap_Power.jpg>
</p>

# Data Source and extra information
- The csv file for United States Wind Turbine Database can be downloaded here : https://energy.usgs.gov/uswtdb/data/
- The excel file containing all electric generator in USA can be found here : https://www.eia.gov/electricity/data/eia860m/
- The nominal power by state can vizualised here :https://windexchange.energy.gov/maps-data/321. Nominal power is when coefficent factor=1 , i.e. when wind farm have 100% efficiency. Usually, efficiency is around 30-40%, because of maintenance, low needs (almost no battery to stock energy),  electrical grid,... 

# The code
The following code can either :
- give wind energy production in a USA state. 
    Command is then python Windpower_forecast.py -state. 
- give wind energy production in a USA energy market. 
    Command is then python Windpower_forecast.py -market.

The code procede in the following order :
- get wind turbine informations
- if '-market', get wind power generator informations, and add it to the wind turbine informations
- extract location, wind turbine power, wind turbine across area,... and aggregate informations to represent each wind farm
- get closest index to the location. This need rework, but it will not be a major improvement
- get the wind forecast at those indexes for all times, from 0 hour to horizon (horizon need be less than 72 hour)
- compute wind power by using some simple rules. This need rework, and it will be a major improvement, but most ofrequired informations. For example power curve are NOT free.
- sum all computed wind power to get the total wind power energy 

# Side note
Getting the energy production exploit vectorized interpolation to get wind at all wind farm in once (for a given date). If 200 wind farm exist in an area of interest, the data extraction is done only once (due to vectorized interpolation) instead of 200 times. This approach reduce computation time by the number of existing wind farms minus 1. 
