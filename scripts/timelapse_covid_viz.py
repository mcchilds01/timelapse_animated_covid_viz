import pygal
import csv
import pandas as pd
import json
import requests
import time 
import cairosvg
from pygal.style import LightColorizedStyle as LCS, LightenStyle as LS, RotateStyle
from pygal.maps.world import COUNTRIES, World 
from datetime import date, timedelta


"""
Documentation

To do:

creative commons license

exception handling 

"""

no_data_countries = ['AIA', 'BMU', 'CYM', 'FRO', 'FLK', 'GIB', 'GRL', 'GGY', 'HKG', 'IMN', 'JEY', 'MAC', 'MSR', 'OWID_NCY', 'SHN', 'TCA']

convert_countries = {'Russia': 'Russian Federation', 'Iran': 'Iran, Islamic Republic of', 'North Korea': "Korea, Democratic People's Republic of",\
		'South Korea': 'Korea, Republic of', 'Venezuela': 'Venezuela, Bolivarian Republic of', 'Laos': "Lao People's Democratic Republic", 'Eswatini': 'Swaziland', 'Vietnam': 'Viet Nam',\
		'Bolivia': 'Bolivia, Plurinational State of', 'Brunei': 'Brunei Darussalam', 'Czechia': 'Czech Republic', 'Moldova': 'Moldova, Republic of', 'Syria': 'Syrian Arab Republic',\
		'North Macedonia': 'Macedonia, the former Yugoslav Republic of', 'Libya': 'Libyan Arab Jamahiriya', 'Democratic Republic of Congo': 'Congo, the Democratic Republic of the',\
		'Tanzania': 'Tanzania, United Republic of', 'Taiwan': 'Taiwan, Province of China', 'Palestine': 'Palestine, State of'}

url ='https://covid.ourworldindata.org/data/owid-covid-data.json'

filenames = set()


def initial_setup():
	"""

	Creates the initial 180-day plot, after which only daily updates are needed. 

	"""
	for i in range(180, 0, -1):
		target_date = date.today() - timedelta(i)
		new_covid_rates = []
		response = requests.get(url)
		r = response.json()
		for country in r.keys():
			if country not in no_data_countries: 
				name = r[country]['location']
				r_df = pd.json_normalize(r[country]['data'])
				covid_rate_date = r_df.loc[r_df['date'] == str(most_recent)]
				new_covid_rates.append(transform_data(name, covid_rate_date, most_recent))
				plot_map(new_covid_rates, most_recent)


def transform_data(country, rates_df, date):
	"""

	Transforms the original timeseries data to so it is plottable by date by country rather than by country by date. 

	"""
	try:
		COVID_rate = createDict(get_country_code(country), country, rates_df['total_cases'].values)
		return COVID_rate
	except KeyError: print(f'KeyError for {country}')



def createDict(code, country_name, rate):
	"""

	Returns a dict with the information necessary to plot COVID data on the pygal world map.

	"""
	return { 
		'value': (code, int(float(rate))),
		'label': code,
		'xlink': 'https://www.google.com/search?q=covid+infection+rate+in+' + country_name,
		}



def get_country_code(country_name):
	"""

	Return the Pygal 2-digit country code for the given country.

	"""
	if country_name in convert_countries.keys():
		country_name = convert_countries[country_name]
	for code, name in COUNTRIES.items():
		if country_name == name:
			return code 



def plot_map(covid_rates_list, date):
	"""

	Creates a .png-format plot of the COVID infection rate data, using the pygal WORLD shapefile, classed based on number of cases

	"""
	COVID_rates_1 = [i for i in covid_rates_list if i['value'][1] < 100000]
	COVID_rates_2 = [country for country in covid_rates_list if country['value'][1] < 1000000] 
	COVID_rates_3 = [country for country in covid_rates_list if country['value'][1] >= 1000000]

	wm_style = RotateStyle('#336699', base_style = LCS)
	wm = World(style = wm_style)
	wm.add('< 100000', COVID_rates_1)
	wm.add('< 1000000', COVID_rates_2)
	wm.add('>= 1 mil', COVID_rates_3)
	wm.title=f'Total COVID cases by country as of {date}'
	wm.render_to_png(f'COVID_viz/COVID_vis_frame_{date}.png')
	filenames.add(f'COVID_viz/COVID_vis_frame_{date}.png')



def get_daily_updates(url):
	most_recent = (date.today() - timedelta(1))
	new_covid_rates = []
	response = requests.get(url)
	r = response.json()
	for country in r.keys():
		if country not in no_data_countries: 
			name = r[country]['location']
			r_df = pd.json_normalize(r[country]['data'])
			covid_rate_date = r_df.loc[r_df['date'] == str(most_recent)]
			new_covid_rates.append(transform_data(name, covid_rate_date, most_recent))
			plot_map(new_covid_rates, most_recent)



def convert_to_gif(files_set):
	images = [images.append(imageio.imread(filename)) for filename in filenames[-180:]]
	imageio.mimsave('COVID_viz/COVID_gif.gif', images)


if __name__ == '__main__':
	"""

	Performs initial set-up by creating a gif of the most recent 180 days worth of COVID intection rate data. The program then 
	sleeps for 24 hours, and then updates the available data on a daily basis and reproduces the gif with data from the most recent 
	180 days.

	"""
	initial_setup(url)
	convert_to_gif(filenames)
	time.sleep(86400)
	while True:
		get_daily_updates(url)
		convert_to_gif(filenames)
		time.sleep(86400)




