'''
Takes in a string of text and makes a pandas dataframe
'''
from get_text import clean_page
import pandas as pd
import re
import os

if __name__=='__main__':
    make_csv()

def make_csv():
    '''
    Goes through all files, adds data to a pandas dataframe, exports as csv.
    '''
    root_dir = '../../dataRAW/FAO_Reports'
    ignore_list = ['JAN_1996', 'FEB_1996', 'MAR_1996', 'APR_1996', 'MAY_1996', 'JUNE_1996']
    df = new_df()
    for subdir, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if int(d) >= 1996]
        files[:] = [f for f in files if f not in ignore_list]
        for f in files:
            file_path = os.path.join(subdir, f)
            df = parse_text(file_path, df)
            print("added to df: ", file_path)
    df.to_csv(path_or_buf='../../dataCSV/FAO_Reports/report_text.csv')
    print("csv added")
    return df


def new_df():
    '''
    Makes a new Pandas dataframe with appropriate columns.
    '''
    cols = ['YEAR', 'MONTH', 'COUNTRY', 'SITUATION', 'FORECAST']
    df = pd.DataFrame(columns=cols)
    return df


def parse_text(file_path, df):
    '''
    Takes a single file and adds its contents to an existing Pandas dataframe.
    '''
    rel_text = clean_page(file_path)
    regions = ["WESTERN REGION", "WEST AFRICA", 'NORTH-WEST AFRICA', 'EASTERN AFRICA', 
    'NEAR EAST', 'SOUTH-WEST ASIA', "CENTRAL REGION", "EASTERN REGION", 'MEDITERRANEAN', 'EUROPE']
    countries = get_countries(rel_text)
    year = int(file_path[-4:])
    month = re.findall(r'.+/(.+)_\d+', file_path)[0]
    region = "WESTERN REGION"    
    for country, situation, forecast in countries:
        dif_formatting = False
        country_list = re.split(r",? \n?AND|, ?", country.upper())
        if re.match(r'SYRIA\nAND TURKEY', country_list[-1]):
            country_list[-1] = 'SYRIA'
            country_list.append('TURKEY')
        elif re.match(r'TURKEY\nAND UAE', country_list[-1]):
            country_list[-1] = 'TURKEY'
            country_list.append('UAE')
        for cty in country_list:
            cty = cty.lstrip()
            if any(region in cty.upper() for region in regions) and "MEDITERRANEAN SEA" not in cty.upper(): # if the string contains a region
                region_list = cty.split('\n')
                region = region_list[0]
                cty = region_list[1]
            cty = re.sub('\n', " ", cty)
            cty = re.sub(r'AND |and ', "", cty)
            if not forecast:
                print("no forecast!!")
                print('file is: ', file_path)
            med_sea_split = re.split(r'\nMEDITERRANEAN SEA\n', forecast) # weird bit with no situation or forecast
            if len(med_sea_split) > 1:
                forecast = med_sea_split[0]
                df = df.append({'YEAR': year, 'MONTH': month, 'REGION': 'MEDITERRANEAN SEA', 'COUNTRY': 'MEDITERRANEAN SEA', 
                        'SITUATION': med_sea_split[1], 'FORECAST': None}, ignore_index=True)
            if len(re.split(r'\n•?(?: +)?FORECAST\n', forecast)) > 1: 
                forecast, to_enter = dif_format_countries(forecast)
                dif_formatting = True 
            for item in [cty, situation, forecast]:
                if 'FORECAST' in item or 'SITUATION' in item:
                    print("something's up")
                    print(file_path)
                    print(item)
                
            df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': cty, 
                        'SITUATION': situation, 'FORECAST': forecast}, ignore_index=True)
        if dif_formatting:
            for name, info in to_enter.items():
                sit = to_enter[name]['SITUATION']
                fcast = to_enter[name]['FORECAST']
                if any(region in name.upper() for region in regions) and "MEDITERRANEAN SEA" not in name.upper(): # if the string contains a region
                    name = name.lstrip()
                    region_list = name.split('\n')
                    region = region_list[0].lstrip()
                    name = region_list[1].lstrip()
                name = re.sub('\n', " ", name)
                df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': name, 
                'SITUATION': sit, 'FORECAST': fcast}, ignore_index=True)
    df['SITUATION'] = df.apply(lambda x: prep_text(year, month, x.SITUATION), axis=1)
    df['FORECAST'] = df.apply(lambda x: prep_text(year, month, x.FORECAST), axis=1)

    return df
        
def dif_format_countries(og_text):
    '''
    Finds countries that don't have labeled situations or bullets before 'FORECAST'.
    This mostly occurs in 2004.
    Returns a dictionary of entries.
    Inputs:
        og_text: the original text containing mulitple countries
    Returns:
        old_forecast (str): the forecast to be replaced
        to_enter: a dictionary of countries as keys with dictionary of
            their corresponding situation and forecast reports as values.
    '''
    by_country = re.split(r'\n•?(?: +)?FORECAST\n', og_text)
    if len(by_country) == 1:
        return
    new_countries = []
    for country in by_country[:-1]:
        for item in re.findall(r'(.+\.)((?:\n[A-Z]+?)?\n(?:.+?))\n(.+)', country, re.DOTALL)[0]:
            new_countries.append(item)
    old_forecast = new_countries[0]
    to_enter = {}
    final_list = new_countries[1:]
    final_list.append(by_country[-1])
    sorted_tuples = [(final_list[i], final_list[i + 1], final_list[i + 2]) for i in range(0, len(final_list), 3)]
    for country, situation, forecast in sorted_tuples:
        to_enter[country] = {"SITUATION": situation, 'FORECAST': forecast}

    return old_forecast, to_enter

def get_countries(text):
    '''
    Parses country names, situation, and forecast out of text file.
    Inputs:
        text (str): the full text
    Returns:
        countries: a list of tuples of countries, situations, and forecasts
    '''
    countries = re.findall(r'(.+?)(?:\n(?:  )?• SITUATION ? ?\n(.+?))?\n(?: +)?• FORECAST ?\n(.+?)(?=$|[^.]+(?:\n(?:  )?• SITUATION ? ?\n.+)?• FORECAST)', 
                            text, re.DOTALL|re.IGNORECASE)
    countries = re.findall(r'(.+?)(?:\n(?:  )?• SITUATION ? ?\n(.+?))?\n(?: +)?• FORECAST ?\n(.+?)(?=$|[^.]+(?:\n(?:  )?• SITUATION ? ?\n.+)?\n(?: +)?• FORECAST)', 
                            text, re.DOTALL|re.IGNORECASE)
    return countries

def prep_text(year, month, text):
    '''
    Prepares text for processing.
    Inputs:
        year (str): the year of the report
        month (str): the month of the report
        text (str): text extracted from the PDF
    '''
    if int(year) < 2002 or (int(year) == 2002 and month in ['JAN', 'FEB', 'MAR', 'APR']):
        text = re.sub(r'-\n', "", text)
        text = re.sub(r'\n', " ", text)
    if not text:
        text = ""
    else:
        text = re.sub(r'\n', "", text)
    text = re.sub(r' ([B-Z]) ([a-z]+)', r' \1\2', text) # should handle the above case
    text = re.sub(r'no reports of ([a-z]+)', r'no \1', text)
    text = re.sub(r'(signifi) +(cant)', r'\1\2', text)

    return text