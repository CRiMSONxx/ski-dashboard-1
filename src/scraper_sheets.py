import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
def get():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQxy9OIle28SzGUOMwz8-jsLv1bWFl5iuZVU5E9DWwy1hUC9ni7HpZORR-Fa0WPaSzyboo229vPv5aN/pubhtml?gid=1836612665&single=true&widget=false&headers=false"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')

    data = []
    # Find all rows in the table
    for row in table.find_all('tr'):
        row_data = []
        cells = row.find_all(['td', 'th'])
        
        for cell in cells:
            # Get the text
            text = cell.get_text(strip=True)
            
            # Get the style attribute to find background-color
            style = cell.get('style', '')
            print(style)
            # Use regex to find hex codes like #FFFFFF or color names
            color_match = re.search(r'background-color:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}|rgb\([^)]+\))', style)
            bg_color = color_match.group(1) if color_match else "None"
            
            # Store as a tuple or dictionary
            row_data.append({'value': text, 'color': bg_color})
        
        if row_data:
            data.append(row_data)

    # To make this "Data Science" friendly, convert to two separate DataFrames
    # One for values, one for colors
    df_values = pd.DataFrame([[cell['value'] for cell in row] for row in data])
    df_colors = pd.DataFrame([[cell['color'] for cell in row] for row in data])
    print(df_colors.head())
    return df_values, df_colors

    print("Data Values:")
    print(df_values.head())