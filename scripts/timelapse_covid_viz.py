import pygal
import csv
import pandas as pd
import json
import requests
import time 
import cairosvg
import imageio
from os import listdir
from pygal.style import DefaultStyle as DS, RotateStyle
from pygal.maps.world import COUNTRIES, World 
from datetime import date, timedelta


"""

CC BY-NC-ND 2021 by Matthew Childs

Performs initial set-up by creating a gif of the most recent 180 days worth of COVID intection rate data. The program then 
sleeps for 24 hours, and then updates the available data on a daily basis and reproduces the gif with data from the most recent 
180 days.

"""

no_data_countries = ['AIA', 'BMU', 'CYM', 'FRO', 'FLK', 'GIB', 'GRL', 'GGY', 'HKG', 'IMN', 'JEY', 'MAC', 'MSR', 'OWID_NCY', 'SHN', 'TCA']

convert_countries = {'Russia': 'Russian Federation', 'Iran': 'Iran, Islamic Republic of', 'North Korea': "Korea, Democratic People's Republic of",\
		'South Korea': 'Korea, Republic of', 'Venezuela': 'Venezuela, Bolivarian Republic of', 'Laos': "Lao People's Democratic Republic", 'Eswatini': 'Swaziland', 'Vietnam': 'Viet Nam',\
		'Bolivia': 'Bolivia, Plurinational State of', 'Brunei': 'Brunei Darussalam', 'Czechia': 'Czech Republic', 'Moldova': 'Moldova, Republic of', 'Syria': 'Syrian Arab Republic',\
		'North Macedonia': 'Macedonia, the former Yugoslav Republic of', 'Libya': 'Libyan Arab Jamahiriya', 'Democratic Republic of Congo': 'Congo, the Democratic Republic of the',\
		'Tanzania': 'Tanzania, United Republic of', 'Taiwan': 'Taiwan, Province of China', 'Palestine': 'Palestine, State of'}

url ='https://covid.ourworldindata.org/data/owid-covid-data.json'


def initial_setup(url, file_format='csv'):
	"""
	
	Allows user to select source format for initial setup; file_format parameter can take either 'json' or 'csv' as an argument, with 'csv' as default. 
	
	"""
	if file_format == 'json':
		initial_setup_from_json(url)
	else: initial_setup_from_csv(url)




def initial_setup_from_json(url):
	"""

	Creates the initial 180-day plot, after which only daily updates are needed. 

	"""
	response = requests.get(url)
	r = response.json()
	for i in range(180, 0, -1):
		new_covid_rates = []
		target_date = date.today() - timedelta(i)
		for country in r.keys():
			if country not in no_data_countries: 
				name = r[country]['location']
				r_df = pd.json_normalize(r[country]['data'])
				covid_rate_date = r_df.loc[r_df['date'] == str(target_date)]
				new_covid_rates.append(transform_data(name, covid_rate_date, target_date))
		plot_map(new_covid_rates, target_date)

		
		
def initial_setup_from_csv(url):
	"""

	Creates the initial 180-day plot, after which only daily updates are needed. 

	"""
	covid_data = pd.read_csv('owid-covid-data.csv')
	covid_data = covid_data[['iso_code', 'location', 'date', 'total_cases']]
	countries = list(zip(covid_data.location.unique(), covid_data.iso_code.unique()))
	for i in range(180, 0, -1):
		new_covid_rates = []
		target_date = date.today() - timedelta(i)
		for country, code in countries:
			if code not in no_data_countries: 
				covid_rate_date = covid_data.loc[(covid_data['location'] == country) & (covid_data['date'] == str(target_date)), 'total_cases']
				new_covid_rates.append(transform_data(str(country), covid_rate_date))
		plot_map(new_covid_rates, target_date)

		
		
def transform_data(country, rates):
	"""

	Transforms the original timeseries data to so it is plottable by date by country rather than by country by date. 

	"""
	try:
		COVID_rate = createDict(get_country_code(country), country, rates)
		return COVID_rate
	except KeyError: print(f'Error transforming data for {country}')



def createDict(code, country_name, rate):
	"""

	Returns a dict with the information necessary to plot COVID data on the pygal world map.

	"""
	try: 
		x = { 
		'value': (code, int(float(rate))),
		'label': code,
		'xlink': 'https://www.google.com/search?q=covid+infection+rate+in+' + country_name,
		}
	except: 
		x = { 
		'value': (code, 0),
		'label': code,
		'xlink': 'https://www.google.com/search?q=covid+infection+rate+in+' + country_name,
		}
	return x



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
	COVID_rates_3 = [country for country in covid_rates_list if country['value'][1] < 10000000]
	COVID_rates_4 = [country for country in covid_rates_list if country['value'][1] < 100000000]
	COVID_rates_5 = [country for country in covid_rates_list if country['value'][1] >= 100000000]

	wm_style = RotateStyle('#336699', base_style = DS, step=5) 
	wm = World(style = wm_style)
	wm.add('< 100,000', COVID_rates_1)
	wm.add('< 1,000,000', COVID_rates_2)
	wm.add('< 10,000,000', COVID_rates_3)
	wm.add('< 100,000,000', COVID_rates_4)
	if len(COVID_rates_5) > 1:
		wm.add('>= 100,000,000', COVID_rates_5)
	wm.title=f'Total COVID cases by country as of {date}'
	wm.render_to_png(f'GIS_project/COVID_viz/COVID_vis_frame_{date}.png')



def get_daily_updates(url):
	"""
	
	Transforms, encodes and plots the data from the most recent day, and adds the .png file to filenames. This new file will eventually be used to
	produce a new gif, incorporating this data and the preceeding 179 days.
	
	"""
	most_recent = (date.today() - timedelta(1))
	new_covid_rates = []
	response = requests.get(url)
	r = response.json()
	for country in r.keys():
		if country not in no_data_countries: 
			name = r[country]['location']
			r_df = pd.json_normalize(r[country]['data'])
			covid_rate_date = r_df.loc[r_df['date'] == str(most_recent), 'total_cases']
			new_covid_rates.append(transform_data(name, covid_rate_date))
	plot_map(new_covid_rates, most_recent)



def convert_to_gif():
	"""
	
	Converts 180 .png files containing pygal plots into a timelapse gif. 
	
	"""
	filenames = [('GIS_project/COVID_viz/'+f) for f in listdir('GIS_project/COVID_viz') if f[-3:]=='png']
	images = [imageio.imread(filename) for filename in sorted(list(filenames))[-180:]]
	imageio.mimsave(f'GIS_project/COVID_viz/COVID_gif_{date.today()}.gif', images, duration = 0.75)


if __name__ == '__main__':
	initial_setup(url)
	convert_to_gif()
	time.sleep(86400)
	while True:
		get_daily_updates(url)
		convert_to_gif()
		time.sleep(86400)
