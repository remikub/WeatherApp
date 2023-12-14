#%%
############################################################################################################
# libraries import
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
import pydeck as pdk
import folium
from streamlit_folium import folium_static
import plotly.express as px
import openpyxl

############################################################################################################
# SQL configuration
DB_USER = 'user'
DB_PASS = 'pass'
DB_NAME = 'db'
SERVER='ip'
DSN_STRING = f"DSN=POP;UID={DB_USER};PWD={DB_PASS};DATABASE={DB_NAME}"
#def get_db_connection():
#    return pyodbc.connect(DSN_STRING)

############################################################################################################
# OpenWeatherMap API configuration
api_key = '5cb3ca5b537359d0cae2889ad5c2c282'
api_url = 'http://api.openweathermap.org/data/2.5/weather'
api_url2 = 'http://api.openweathermap.org/data/2.5/onecall'
api_url3 = 'http://api.openweathermap.org/data/2.5/air_pollution'
api_url4 = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'

############################################################################################################
# HKS downloaded data
excel_file = 'HKSdata.xlsx'
downloaded_hks_data = pd.read_excel(excel_file)
downloaded_hks_data['Date'] = downloaded_hks_data['Date'].dt.date

############################################################################################################
# HKS live data from SQL
def get_hks_customer_data(daycount):
    return None
    #con = pymssql.connect(host='ip',user='user',password='pass',database='db')
    #cur = con.cursor()
    #cur.execute(f"EXEC GetHKSCustomerData {daycount}")
    #data = cur.fetchall()
    #columns = [column[0] for column in cur.description]
    #df = pd.DataFrame(data, columns=columns)
    #return df

############################################################################################################
# current weather function
def fetch_weather(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        print('Error fetching weather data.')
        return None
    
############################################################################################################
# weather 6 days forecast function
def get_6_days_forecast(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric',
    }
    response = requests.get(api_url2, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('daily', [])[:7]  # Extract the first 3 days of the forecast
    else:
        print('Error fetching weather data 3days.')
        return None
    
############################################################################################################
# air quality index
def fetch_air_quality(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
    }
    response = requests.get(api_url3, params=params)
    if response.status_code == 200:
        data = response.json()
        aqi_data = data['list'][0]['main']
        components_data = data['list'][0].get('components', None)
        return aqi_data, components_data
    else:
        print('Error fetching air quality data.')
        return None, None
def categorize_air_quality(row, limits):
    """
    Categorize air quality based on specified limits for each component.
    """
    component = row['Component']
    value = row['Value']

    for i, upper_limit in enumerate(limits[1:]):
        if value < upper_limit:
            return i + 1  # Air quality category: 1-based index

    return len(limits)
        
############################################################################################################
# historical data
def fetch_historical_data(lat, lon, days_back):
    api_key = '5cb3ca5b537359d0cae2889ad5c2c282'
    endpoint = "https://api.openweathermap.org/data/3.0/onecall/day_summary"
    
    historical_data = []
    
    for i in range(days_back):
        # Calculate the date by subtracting i days from the current date
        date = datetime.now() - timedelta(days=i)
        
        # Format the date as YYYY-MM-DD
        formatted_date = date.strftime('%Y-%m-%d')
        metric = "metric"
        params = {
            "lat": lat,
            "lon": lon,
            "date": formatted_date,
            "tz": "+01:00",  # Adjust the timezone as needed
            "appid": api_key,
            "units": metric
        }

        response = requests.get(endpoint, params=params)
        data = response.json()
        historical_data.append(data)

    return historical_data

# Function to process daily historical data
def process_daily_historical_data(historical_data):
    data_list = []
    
    for data in historical_data:
        # Extract relevant information
        date = data["date"]
        temperature_min = data["temperature"]["min"]
        temperature_max = data["temperature"]["max"]
        humidity_afternoon = data["humidity"]["afternoon"]
        precipitation_total = data["precipitation"]["total"]
        wind_speed_max = data["wind"]["max"]["speed"]

        # Create a DataFrame for easy plotting
        df = pd.DataFrame({
            "Date": [date],
            "Min Temperature": [temperature_min],
            "Max Temperature": [temperature_max],
            "Humidity (Afternoon)": [humidity_afternoon],
            "Precipitation Total": [precipitation_total],
            "Wind Speed Max": [wind_speed_max],
        })

        data_list.append(df)

    return pd.concat(data_list, ignore_index=True)




############################################################################################################
# weather icon function
def get_weather_icon_url(icon_code):
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"


############################################################################################################
# left sidebar cities dropdown list
city_coordinates = {
    'Wręcza': {'lat': 51.99566, 'lon': 20.45117},
    'Toruń': {'lat': 53.00886, 'lon': 18.60518},
    'Warszawa': {'lat': 52.23161, 'lon': 21.00866},
    'Kraków': {'lat': 50.05914, 'lon': 19.93848},
    'Łódź': {'lat': 51.76224, 'lon': 19.45867},
    'Wrocław': {'lat': 51.11062, 'lon': 17.03163},
    'Poznań': {'lat': 52.40351, 'lon': 16.92867},
    'Gdańsk': {'lat': 54.34802, 'lon': 18.65688},
    'Szczecin': {'lat': 53.42894, 'lon': 14.55302},
    'Bydgoszcz': {'lat': 53.12350, 'lon': 18.00844},
    'Lublin': {'lat': 51.24647, 'lon': 22.56845},
    'Białystok': {'lat': 53.13249, 'lon': 23.16884},
    'Katowice': {'lat': 50.25965, 'lon': 19.01811},
    'Kielce': {'lat': 50.87033, 'lon': 20.62752},
    'Olsztyn': {'lat': 53.47117, 'lon': 20.60856},
    'Opole': {'lat': 50.66695, 'lon': 17.92436},
    'Rzeszów': {'lat': 50.04132, 'lon': 21.99901},
    'Gorzów Wielkopolski': {'lat': 52.73479, 'lon': 15.22978}
}

############################################################################################################
# set page title
def main():
    st.set_page_config(page_title='Weather Dashboard', page_icon='🌞', layout='wide')

############################################################################################################
# left sidebar config
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #0C2487;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        color: white;
    }
    [data-testid=stSidebar] .stSelectbox label {
        color: white; /* Set the sidebar header text color to white */
            text-align: center;
    }
    .stSelectbox select {
        color: white; /* Set the color of the dropdown options to white */
            text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# display the logo 
logo_url = "https://parkofpoland.com/build/images/logos/logo.svg"
st.sidebar.markdown(
    f'<div style="display: flex; justify-content: center; margin-bottom: 25px;">'
    f'<img src="{logo_url}" width="150" alt="Park of Poland Logo">'
    f'</div>',
    unsafe_allow_html=True
)

# enable or disable SQL connection checkbox
enable_sql_connection = st.sidebar.checkbox("Enable SQL Connection", value=False)

# cities dropdown list
city_names = [city for city in sorted(city_coordinates.keys()) if city != "Wręcza"]
selected_city = st.sidebar.selectbox('Select a City to check weather', city_names, index=0)
# display Wrecza weather info
wręcza_data = city_coordinates['Wręcza']
wręcza_latitude, wręcza_longitude = wręcza_data['lat'], wręcza_data['lon']
wręcza_weather_data = fetch_weather(wręcza_latitude, wręcza_longitude)
if wręcza_weather_data:
    wręcza_name = wręcza_weather_data['name']
    wręcza_temperature = wręcza_weather_data['main']['temp']
    wręcza_weather_description = wręcza_weather_data['weather'][0]['description']
    wręcza_col1 = st.sidebar.columns(1)[0]
    with wręcza_col1:
        st.sidebar.markdown('<h2 style="color: white; text-align: center;">Current weather in Wręcza</h2>', unsafe_allow_html=True)
        st.markdown("""
        <style>
            .centered-content {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
        </style>
        """, unsafe_allow_html=True)
        center_container = st.container()
        icon_url_wrecza = get_weather_icon_url(wręcza_weather_data['weather'][0]['icon'])
        st.sidebar.markdown(
            f'<div class="centered-content">'
            f'<img src="{icon_url_wrecza}" width="100" alt="Weather Icon">'
            f'<p>Temperature: {wręcza_temperature}°C</p>'
            f'<p>Condition: {wręcza_weather_description}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
# display Suntago weather info
st.sidebar.markdown('<h2 style="color: white; text-align: center;">Current weather in SUNTAGO</h2>', unsafe_allow_html=True)
st.sidebar.markdown(
    f'<div class="centered-content">'
    f'<img src="https://images.emojiterra.com/google/noto-emoji/unicode-15.1/color/svg/1f31e.svg" width="75" alt="Weather Icon">'
    f'<p>Temperature: 32°C</p>'
    f'<p>Condition: HOT & SUNNY :)</p>'
    f'</div>',
    unsafe_allow_html=True
)

############################################################################################################
# weather dashboard config
st.title('Weather Dashboard')

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Current Weather", "6 days Forecast", "AQI", "Map", "Historical Data"])

with tab1:
    city_data = city_coordinates[selected_city]
    latitude, longitude = city_data['lat'], city_data['lon']
    weather_data = fetch_weather(latitude, longitude)
    if weather_data:
        city_name = weather_data['name']
        temperature = weather_data['main']['temp']
        weather_description = weather_data['weather'][0]['description']
        humidity = weather_data['main']['humidity']
        pressure = weather_data['main']['pressure']
        wind_speed = weather_data['wind']['speed']
        if 'rain' in weather_data:
            rain = weather_data['rain']
        else:
            rain = {'1h': 0.0}
        if 'clouds' in weather_data:
            clouds = weather_data['clouds']['all']
        else:
            clouds = 0

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f'Weather in {city_name}')
            icon_url = get_weather_icon_url(weather_data['weather'][0]['icon'])
            st.image(icon_url, width=100)
            st.write(f'Condition: {weather_description}')
        with col2:
            st.write(f'Temperature: {temperature}°C')
            st.write(f'Humidity: {humidity}%')
            st.write(f'Pressure: {pressure} hPa')
            st.write(f'Wind Speed: {wind_speed} m/s')
            st.write(f'Rain (1h): {rain["1h"]} mm')
            st.write(f'Cloudiness: {clouds}%')
with tab2:
    city_data = city_coordinates[selected_city]
    latitude, longitude = city_data['lat'], city_data['lon']
    forecast_data = get_6_days_forecast(latitude, longitude)
    city_name = weather_data['name']
    st.subheader(f'Weather in {city_name}')
    if forecast_data:
        forecast_col1, forecast_col2, forecast_col3, forecast_col4, forecast_col5, forecast_col6 = st.columns(6)
        for i, day in enumerate(forecast_data):
            timestamp = day.get('dt', '')
            temperature_min = day.get('temp', {}).get('min', '')
            temperature_max = day.get('temp', {}).get('max', '')
            weather_description = day.get('weather', [{}])[0].get('description', '')
            date_object = datetime.utcfromtimestamp(timestamp)
            date = date_object.strftime('%Y-%m-%d')
            icon_url = get_weather_icon_url(day.get('weather', [{}])[0].get('icon', ''))
            
            col = None  # Initialize col to None

            if i == 0:
                pass
            elif i == 1:
                col = forecast_col1
            elif i == 2:
                col = forecast_col2
            elif i == 3:
                col = forecast_col3
            elif i == 4:
                col = forecast_col4
            elif i == 5:
                col = forecast_col5
            else:
                col = forecast_col6

            if col is not None:
                with col:
                    st.write(f'{date}')
                    st.write(f'Min Temp: {temperature_min}°C')
                    st.write(f'Max Temp: {temperature_max}°C')
                    st.image(icon_url, width=100)
                    st.write(f'Condition: {weather_description}')


with tab3:
    city_data = city_coordinates[selected_city]
    latitude, longitude = city_data['lat'], city_data['lon']
    air_quality_data, components_data = fetch_air_quality(latitude, longitude)

    if air_quality_data and components_data:
        aqi = air_quality_data.get("aqi")
        st.write(f'Air Quality Index in {selected_city}')
        
        # Visual scale based on AQI levels
        if aqi == 1:
            st.success(f'AQI = {aqi}: Good')
        elif aqi == 2:
            st.warning(f'AQI = {aqi}: Fair')
        elif aqi == 3:
            st.warning(f'AQI = {aqi}: Moderate')
        elif aqi == 4:
            st.error(f'AQI = {aqi}: Poor')
        elif aqi == 5:
            st.error(f'AQI = {aqi}: Very Poor')
        else:
            st.error(f'AQI = {aqi}: Very Unhealthy')

        st.write('Air Quality Components')
        components_df = pd.DataFrame(components_data.items(), columns=['Component', 'Value'])
        st.table(components_df)
        limits = {
            'no': [0, 25, 50, 75, 100],
            'nh3': [0, 20, 50, 100, 200],
            'so2': [0, 20, 80, 250, 350],
            'no2': [0, 40, 70, 150, 200],
            'pm10': [0, 20, 50, 100, 200],
            'pm2_5': [0, 10, 25, 50, 75],
            'o3': [0, 60, 100, 140, 180],
            'co': [0, 4400, 9400, 12400, 15400]
        }


    else:
        st.error('Error fetching air quality data.')

with tab4:
    # Create a folium map centered on Poland
    poland_map = folium.Map(location=[52.0, 19.0], zoom_start=6, control_scale=True)

    # Add markers for all cities
    for city_name, coordinates in city_coordinates.items():
        latitude, longitude = coordinates['lat'], coordinates['lon']
        temperature_data = fetch_weather(latitude, longitude)

        if temperature_data:
            temperature = temperature_data['main']['temp']
            weather_icon = temperature_data['weather'][0]['icon']

            # Add a marker for each city with a popup displaying the temperature and weather icon
            folium.Marker(
                location=[latitude, longitude],
                popup=f"{city_name} - {temperature}°C",
                icon=folium.CustomIcon(icon_image=f"http://openweathermap.org/img/w/{weather_icon}.png", icon_size=(50, 50)),
            ).add_to(poland_map)

        else:
            st.warning(f'Error fetching temperature data for {city_name}.')

    # Display the folium map using folium_static
    folium_static(poland_map)

with tab5:
    days_back = st.number_input('Enter the number of days back:', min_value=1, max_value=30, value=7)

    city_data = city_coordinates[selected_city]
    latitude, longitude = city_data['lat'], city_data['lon']
    historical_data = fetch_historical_data(latitude, longitude, days_back)

    if st.button("Fetch Data"):
        # Fetch historical data
        historical_data = fetch_historical_data(latitude, longitude, days_back)

        # Process and display data
        daily_data = process_daily_historical_data(historical_data)

        # Plot the data using Plotly Express
        fig = px.line(daily_data, x="Date", y=["Min Temperature", "Max Temperature"],
                      labels={"value": "Temperature (°C)", "variable": "Item"})

        fig.add_bar(x=daily_data["Date"], y=daily_data["Precipitation Total"], name="Precipitation Total",
                    text=daily_data["Precipitation Total"].astype(str) + " mm",
                    hoverinfo="text+y")
        fig.add_scatter(x=daily_data["Date"], y=daily_data["Wind Speed Max"], mode="markers", name="Wind Speed Max",
                        text=daily_data["Wind Speed Max"].astype(str) + " m/s",
                        hoverinfo="text+y")

        st.plotly_chart(fig)




############################################################################################################
# customer visits data
st.title('Suntago Customer Visits')

if enable_sql_connection:
    daycount_slider = st.slider('Select Days Range for Live Data:', min_value=0, max_value=14, value=0)

visits_tab1, visits_tab2, visits_tab3, visits_tab4 = st.tabs(["Live Data", "Live Data Graph", "Downloaded Data", "Downloaded Data Graph"])

with visits_tab1:
    if enable_sql_connection:
        result_df = get_hks_customer_data(daycount=daycount_slider)
        st.dataframe(result_df, hide_index=True)
    else:
        st.warning('SQL connection is disabled.')

with visits_tab2:
    if enable_sql_connection:
        graph_results_df = result_df[['Date', 'Jamango', 'Relax', 'Saunaria']]
        graph_results_df['Date'] = pd.to_datetime(graph_results_df['Date']).dt.strftime('%Y-%m-%d')
        graph_results_df.set_index('Date', inplace=True)
        melted_df = pd.melt(graph_results_df.reset_index(), id_vars=['Date'], var_name='Activity', value_name='Visits')
        color_scale = alt.Scale(domain=['Jamango', 'Relax', 'Saunaria'], range=['#009111', '#2BBABE', '#1E2C7C'])
        chart = alt.Chart(melted_df).mark_bar().encode(
            x='Date:O',
            y='Visits:Q',
            color=alt.Color('Activity:N', scale=color_scale),
            order=alt.Order('Activity', sort='ascending'),
            tooltip=['Date', 'Visits', 'Activity']
        ).properties(
            width=700,
            height=400,
            title='Customer Visits'
        )
        chart = chart.configure_axisX(
            labelAngle=0,
            labelAlign='center',
            labelBaseline='middle'
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning('SQL connection is disabled.')

with visits_tab3:
    st.table(downloaded_hks_data)

with visits_tab4:
    graph_results_df4 = downloaded_hks_data[['Date', 'Jamango', 'Relax', 'Saunaria']]
    graph_results_df4['Date'] = pd.to_datetime(graph_results_df4['Date']).dt.strftime('%Y-%m-%d')
    graph_results_df4.set_index('Date', inplace=True)
    melted_df4 = pd.melt(graph_results_df4.reset_index(), id_vars=['Date'], var_name='Activity', value_name='Visits')
    color_scale4 = alt.Scale(domain=['Jamango', 'Relax', 'Saunaria'], range=['#009111', '#2BBABE', '#1E2C7C'])
    chart4 = alt.Chart(melted_df4).mark_bar().encode(
        x='Date:O',
        y='Visits:Q',
        color=alt.Color('Activity:N', scale=color_scale4),
        order=alt.Order('Activity', sort='ascending'),
        tooltip=['Date', 'Visits', 'Activity']
    ).properties(
        width=700,
        height=400,
        title='Customer Visits'
    )
    chart4 = chart4.configure_axisX(
        labelAngle=0,
        labelAlign='center',
        labelBaseline='middle'
    )
    st.altair_chart(chart4, use_container_width=True)
############################################################################################################

