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
    rel_text = clean_page(file_path)
    #print(rel_text)
    # find all situation and forecast
    cols = ["YEAR", 'MONTH', 'REGION', 'COUNTRY', 'SITUATION', 'FORECAST']
    regions = ["WESTERN REGION", "WEST AFRICA", 'NORTH-WEST AFRICA', 'EASTERN AFRICA', 
    'NEAR EAST', 'SOUTH-WEST ASIA', "CENTRAL REGION", "EASTERN REGION", 'MEDITERRANEAN']
    df = pd.DataFrame(columns=cols)
    countries = get_countries(rel_text)
    
    # country debugging statement:
    #for country in countries:
        #print(country)
    year = int(file_path[-4:])
    month = re.findall(r'.+/(.+)_\d+', file_path)[0]
    region = "WESTERN REGION"
    #print("month is: ", month)
    
    for country, situation, forecast in countries:
        dif_formatting = False
        #print(country)
        country_list = re.split(r",? \n?AND|, ?", country.upper())
        for cty in country_list:
            cty = cty.lstrip()
            #print("cty is: ", cty)
            if any(region in cty.upper() for region in regions) and "MEDITERRANEAN SEA" not in cty.upper(): # if the string contains a region
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
            #bad_words = ['SITUATION', 'FORECAST']
            #if 'SITUATION' in (cty, situation, forecast) or 'FORECAST' in (cty, situation, forecast):
            med_sea_split = re.split(r'\nMEDITERRANEAN SEA\n', forecast) # weird bit with no situation or forecast
            if len(med_sea_split) > 1:
                forecast = med_sea_split[0]
                df = df.append({'YEAR': year, 'MONTH': month, 'REGION': 'MEDITERRANEAN SEA', 'COUNTRY': 'MEDITERRANEAN SEA', 
                        'SITUATION': med_sea_split[1], 'FORECAST': None}, ignore_index=True)
            # funky formats where situation not labeled + forecast has no bullet
            if len(re.split(r'\n(?: +)?FORECAST\n', forecast)) > 1: 
                forecast, to_enter = dif_format_countries(forecast)
                dif_formatting = True 
            for item in [cty, situation, forecast]:

                if 'FORECAST' in item or 'SITUATION' in item:
                    print("something's up")
                    print(file_path)
                    print(item)
                    #print(forecast)

                
            df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': cty, 
                        'SITUATION': situation, 'FORECAST': forecast}, ignore_index=True)

        #if len(re.split(r'\n(?: +)?FORECAST\n', forecast)) > 1: 
        if dif_formatting:
            #forecast, to_enter = dif_format_countries(forecast) # updates dataframe in place
            print("to_enter: ", to_enter)
            for name, info in to_enter.items():
                sit = to_enter[name]['SITUATION']
                fcast = to_enter[name]['FORECAST']
                if any(region in name.upper() for region in regions) and "MEDITERRANEAN SEA" not in name.upper(): # if the string contains a region
                    #print("name is", name)
                    name = name.lstrip()
                    region_list = name.split('\n')
                    #region = region_list[0]
                    region = region_list[0].lstrip()
                    name = region_list[1].lstrip()
                    #print("region is: ", region)
                    #print("name is: ", name)
                    #name = re.sub('\n', " ", name)
                #name = region_list[1]
            #print("cty is: ", cty)
            #if re.match(r'.+\n.+', cty):

                name = re.sub('\n', " ", name)
                df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': name, 
                'SITUATION': sit, 'FORECAST': fcast}, ignore_index=True)



            #df['COUNTRY'] = cty
            #df['SITUATION'] = sit
            #df['FORECAST'] = forecast
        #if re.search(r',|, ?and ', country, re.IGNORECASE):
            #print("country: ", country)
            #print(re.split(r", ?|,? AND ", country.upper()))
            #print(re.split(r",? AND|, ?", country.upper()))

            #print("match")
    #print("dataframe updated")
    return df
        
def dif_format_countries(og_text):
    '''
    Finds countries that don't have labeled situations or bullets before 'FORECAST'.
    This mostly occurs in 2004.
    Returns a dictionary of entries
    '''
    # forecast of first country
    #re.findall(r'.+?')
    #re.findall(r'\.\n(\w+?)\n(.+?)\n(?: +)?FORECAST\n(.+?)(?=$|[^\.]\n(?:.+?)\n(?:.+?)\n(?: +)?FORECAST\n)', text, re.DOTALL)
    # check for a new region
    by_country = re.split(r'\n(?: +)?FORECAST\n', og_text)
    if len(by_country) == 1:
        print("no hidden countries found! returning...")
        return
    #print('entering function on country: ', old_country)
    #
    # print('by country looks like: ', by_country)
    new_countries = []
    for country in by_country[:-1]:
        #info = re.findall(r'(.+\.)\n(.+?)\n(.+)', country, re.DOTALL)[0]
        # AMEND FOLLOWING LINE FOR REGION
        #for item in re.findall(r'(.+\.)\n(.+?)\n(.+)', country, re.DOTALL)[0]:
        # try to capture regions:
        #for item in re.findall(r'(.+\.)((?:\n.+?)?\n(?:.+?))\n(.+)', country, re.DOTALL)[0]:
        for item in re.findall(r'(.+\.)((?:\n[A-Z]+?)?\n(?:.+?))\n(.+)', country, re.DOTALL)[0]:


            new_countries.append(item)
        #print(info)
        #old_forecast = info[0]
        #df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': old_country, 
                    #'SITUATION': old_situation, 'FORECAST': old_forecast}, ignore_index=True) # append old forecast with old country and situation
        #print("added to df: ", old_country)
        # update old country and situation
        #old_country = info[1]
        #old_situation = info[2]
    old_forecast = new_countries[0]
    to_enter = {}
    # store as tuples of country, sit, forecast
    final_list = new_countries[1:]
    final_list.append(by_country[-1])
    sorted_tuples = [(final_list[i], final_list[i + 1], final_list[i + 2]) for i in range(0, len(final_list), 3)]
    for country, situation, forecast in sorted_tuples:
        to_enter[country] = {"SITUATION": situation, 'FORECAST': forecast}
    #old_forecast = by_country[-1]
    #df = df.append({'YEAR': year, 'MONTH': month, 'REGION': region, 'COUNTRY': old_country, 
                    #'SITUATION': old_situation, 'FORECAST': old_forecast}, ignore_index=True) # append the stuff again

        #old_forecast = re.findall(r'(.+\.)\n(.+?)\n(.+)', country)[0][0]

        #old_forecast, new_name, new_sit = re.findall(r'(.+\.)\n(.+?)\n(.+)', country)[0]
        #print(re.findall(r'(.+\.)\n(.+?)\n(.+)', country, re.DOTALL))
    #forecast = old_forecast
    #df = df.append()


    #re.split(r'\.\n\w\n', text)
    #print("dataframe updated")
    # old forecast and dictionary of new entries
    return old_forecast, to_enter

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
    countries = re.findall(r'(.+?)(?:\n(?:  )?• SITUATION ? ?\n(.+?))?\n(?: +)?• FORECAST ?\n(.+?)(?=$|[^.]+(?:\n(?:  )?• SITUATION ? ?\n.+)?• FORECAST)', 
                            text, re.DOTALL|re.IGNORECASE)
    #print("countries: ", countries)
    return countries
