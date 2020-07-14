'''
Takes in a string of text and makes a pandas dataframe
'''
from get_text import clean_page
import pandas as pd
import re
import os

def make_csv():
    '''
    Goes through all files, adds data to a pandas dataframe, exports as csv
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
    df.to_csv(path='../../dataCSV/FAO_Reports/report_text.csv')
    print("csv added")
    return df


def new_df():
    '''
    Makes a new Pandas dataframe with appropriate columns
    '''
    cols = ['YEAR', 'MONTH', 'COUNTRY', 'SITUATION', 'FORECAST']
    df = pd.DataFrame(columns=cols)
    return df


def parse_text(file_path, df):
    '''
    Takes a single file and adds its contents to an existing Pandas dataframe.
    '''
    text = clean_page(file_path)
    # find all situation and forecast
    cols = ["YEAR", 'MONTH', 'REGION', 'COUNTRY', 'SITUATION', 'FORECAST']
    regions = ["WESTERN REGION", "WEST AFRICA", 'NORTH-WEST AFRICA', 'EASTERN AFRICA', 
    'NEAR EAST', 'SOUTH-WEST ASIA', "CENTRAL REGION", "EASTERN REGION"]
    df = pd.DataFrame(columns=cols)
    rel_text = get_relevant_text(text)
    #print("rel_text is: ", rel_text)
    countries = get_countries(rel_text)
    for country in countries:
        print(country)
    year = int(file_path[-4:])
    month = re.findall(r'.+/(.+)_\d+', file_path)[0]
    region = "WESTERN REGION"
    #print("month is: ", month)
    
    for country, situation, forecast in countries:
        #print(country)
        country_list = re.split(r",? \n?AND|, ?", country.upper())
        for cty in country_list:
            cty = cty.lstrip()
            #print("cty is: ", cty)
            if any(region in cty.upper() for region in regions): # if the string contains a region
                region_list = cty.split('\n')
                region = region_list[0]
                cty = region_list[1]
            #print("cty is: ", cty)
            #if re.match(r'.+\n.+', cty):

            cty = re.sub('\n', " ", cty)
            cty = re.sub(r'AND |and ', "", cty)
            #if not region: # for debugging
                #print("no region!")
                #print('cty is: ', cty)
                #print('file is: ', file_path)
            if not forecast:
                print("no forecast!!")
                print('file is: ', file_path)
            bad_words = ['SITUATION', 'FORECAST']
            #if 'SITUATION' in (cty, situation, forecast) or 'FORECAST' in (cty, situation, forecast):
            for item in [cty, situation, forecast]:
                if 'FORECAST' in item or 'SITUATION' in item:
                    print("something's up")
                    print(file_path)
                    print(item)
                    #print(forecast)
                
            df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': cty, 
                        'SITUATION': situation, 'FORECAST': forecast}, ignore_index=True)
            
            #df['COUNTRY'] = cty
            #df['SITUATION'] = sit
            #df['FORECAST'] = forecast
        #if re.search(r',|, ?and ', country, re.IGNORECASE):
            #print("country: ", country)
            #print(re.split(r", ?|,? AND ", country.upper()))
            #print(re.split(r",? AND|, ?", country.upper()))

            #print("match")
    return df
        


def get_countries(text):
    '''
    Parses country names, situation, and forecast out of text file.
    '''
    #countries = re.split(r'(?:• )?SITUATION', text)
    #country_name = countries[0]
    #for country in countries[1:]:
        #re.findall(r'(.+)\n• FORECAST\n(.+\.)(.+)', country, re.DOTALL)
    #re.findall(r'(.+)\n• SITUATION\n(.+)\n• FORECAST\n(.+\.)', text)
    

    # WE GOT IT OMGGGGG
    #countries = re.findall(r'(.+?)\n• SITUATION ?\n(.+?)\n• FORECAST\n(.+?)(?=$|[^.]+\n• SITUATION ?\n)', 
                            #text, re.DOTALL|re.IGNORECASE)
    # also need to deal with lists of countries that have forecasts but not situations
    countries = re.findall(r'(.+?)(?:\n(?:  )?• SITUATION ? ?\n(.+?))?\n ?• FORECAST ?\n(.+?)(?=$|[^.]+(?:\n(?:  )?• SITUATION ? ?\n.+)?• FORECAST)', 
                            text, re.DOTALL|re.IGNORECASE)
    #print("countries: ", countries)
    return countries

def get_relevant_text(text):
    result = re.findall(r'(?:Situation and Forecast)+(.+?)(?:Announcements?|Other Locusts\n|Glossary of Terms|Other Species)', 
                        text, flags = re.DOTALL|re.IGNORECASE)[0]
    #print(result)
    #
    #print("type of result: ", type(result))ß
    # get rid of headers and footers
    to_keep = []
    for line in result.split('\n'):
        #print("line is: ", line)
        if line and not re.match(r'Desert Locust Situation and Forecast|D E S E R T  L O C U S T  B U L L E T I N|No. \d+|\( ?see also the summary', line, re.IGNORECASE):
            to_keep.append(line)
            #print("appended")
    return '\n'.join(to_keep)
    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)

    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)
