import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import logging
import sqlite3
from datetime import datetime
import schedule
import time

class WebScraper:
    def __init__(self, url):
        self.url = url
        self.dataframe = pd.DataFrame()

    def scrape_webpage(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            logging.info(f'Successfully retrieved data from {self.url}')
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')
            headers = [header.text.strip() for header in table.find_all('th')]
            rows = []
            for row in table.find_all('tr'):
                cols = [col.text.strip() for col in row.find_all('td')]
                if cols:
                    rows.append(cols)
            self.dataframe = pd.DataFrame(rows, columns=headers)
            logging.info('Data scraping completed successfully.')
        except Exception as e:
            logging.error(f'Error while scraping: {e}')

    def clean_data(self):
        if self.dataframe.empty:
            logging.warning('Dataframe is empty. Skipping cleaning step.')
            return
        try:
            logging.info('Starting data cleaning process...')
            self.dataframe['Population (2024)'] = self.dataframe['Population (2024)'].str.replace(',', '').astype(int)
            self.dataframe['Yearly Change'] = self.dataframe['Yearly Change'].str.replace('%', '').astype(float)
            logging.info('Data cleaning completed successfully.')
        except Exception as e:
            logging.error(f'Error while cleaning data: {e}')

    def save_to_database(self):
        try:
            conn = sqlite3.connect('population_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS PopulationData (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Country TEXT,
                    Population INTEGER,
                    YearlyChange REAL,
                    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            for _, row in self.dataframe.iterrows():
                cursor.execute('''
                    INSERT INTO PopulationData (Country, Population, YearlyChange)
                    VALUES (?, ?, ?)
                ''', (row['Country (or dependency)'], row['Population (2024)'], row['Yearly Change']))
            conn.commit()
            conn.close()
            logging.info('Data saved to database successfully.')
        except Exception as e:
            logging.error(f'Error while saving data to database: {e}')

    def export_data(self, filename='population_data.csv'):
        if not self.dataframe.empty:
            self.dataframe.to_csv(filename, index=False)
            logging.info(f'Data exported to {filename}')
        else:
            logging.warning('Dataframe is empty, cannot export data.')

class Dashboard:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def create_dashboard(self):
        if self.dataframe.empty:
            logging.warning('Dataframe is empty. Skipping dashboard creation.')
            return
        try:
            logging.info('Creating dashboard...')
            # Create a bar plot showing population by country
            bar_fig = px.bar(self.dataframe, x='Country (or dependency)', y='Population (2024)', title='Population by Country in 2024')
            # Create a line plot showing yearly change for each country
            line_fig = go.Figure(data=[
                go.Scatter(x=self.dataframe['Country (or dependency)'], y=self.dataframe['Yearly Change'], mode='lines', name='Yearly Change')
            ])
            bar_fig.show()
            line_fig.show()
            logging.info('Dashboard created successfully.')
        except Exception as e:
            logging.error(f'Error while creating dashboard: {e}')

def job():
    url = 'https://www.worldometers.info/world-population/population-by-country/'
    scraper = WebScraper(url)
    scraper.scrape_webpage()
    scraper.clean_data()
    scraper.save_to_database()
    scraper.export_data()

    dashboard = Dashboard(scraper.dataframe)
    dashboard.create_dashboard()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run the job immediately once
    job()
