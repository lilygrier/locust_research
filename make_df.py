'''
Takes in a string of text and makes a pandas dataframe
'''
from get_text import clean_page
import pandas as pd
import re

def make_csv():
    '''
    Goes through all files, adds data to a pandas dataframe, exports as csv
    '''
    df = new_df()

    


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
    cols = ["YEAR", 'MONTH', 'COUNTRY', 'SITUATION', 'FORECAST']
    df = pd.DataFrame(columns=cols)
    rel_text = get_relevant_text(text)
    countries = get_countries(rel_text)
    year = int(file_path[-4:])
    month = re.match(r'\\(.+)_\d+')
    print("month is: ", month)
    
    for country, sit, forecast in countries:
        #print(country)
        country_list = re.split(r",? AND|, ?", country.upper())
        for cty in country_list:
            df.append({'YEAR': year, 'MONTH': month, 'COUNTRY': cty, 
                        'SITUATION': situation, 'FORECAST': forecast})
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
    countries = re.findall(r'(.+?)(?:\n• SITUATION ?\n(.+?))?\n• FORECAST\n(.+?)(?=$|[^.]+(?:\n• SITUATION ?\n.+)?• FORECAST)', 
                            text, re.DOTALL|re.IGNORECASE)
    return countries

def get_relevant_text(text):
    result = re.findall(r'(?:Situation and Forecast)(.+?)(?:Announcements?|Other Locusts\n|Glossary of Terms|Other Species)', 
                        text, flags = re.DOTALL|re.IGNORECASE)[0]
    print(result)
    print("type of result: ", type(result))
    # get rid of headers and footers
    to_keep = []
    for line in result.split('\n'):
        if line and not re.match(r'D E S E R T  L O C U S T  B U L L E T I N|No. \d+|\( see also the summary', line, re.IGNORECASE):
            to_keep.append(line)
    return '\n'.join(to_keep)
    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)

    #return re.sub(r'(.+)D E S E R T  L O C U S T  B U L L E T I N|No. \d+(.+)', r'\1\2', result, re.IGNORECASE|re.DOTALL)
