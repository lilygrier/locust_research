'''
Matches referenced locations.
'''
import pandas as pd
import numpy as np
import spacy
import datetime
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import fuzz


#from monthdelta import MonthDelta


STARTING_DATE = datetime.date(1996, 8, 1)
ENDING_DATE = datetime.date(2020, 3, 1)
from dateutil import rrule


MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE', 'JULY', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

def locations_to_match(nlp_df):
    nlp_df['forecast_locs'] = nlp_df['FORECAST'].apply(lambda x: get_locations(x))
    nlp_df['sit_locs_1'] = nlp_df['SIT_1'].apply(lambda  x: get_locations(x))
    nlp_df['sit_locs_2'] = nlp_df['SIT_2'].apply(lambda  x: get_locations(x))
    # need to treat this as a lambda situation probably
    nlp_df['unmatched_forecast'] = nlp_df.apply(lambda x: get_unmatched_forecast(x['forecast_locs'], x['sit_locs_1'], x['sit_locs_2']), axis=1)
    nlp_df['unmatched_sit'] = nlp_df.apply(lambda x: get_unmatched_sit(x.forecast_locs, x.sit_locs_1, x.sit_locs_2), axis=1)
    nlp_df.loc[:, 'unmatched_forecast'] = nlp_df.apply(lambda x: remove_common_locs_forecast(x.unmatched_forecast, x.unmatched_sit), axis=1)
    nlp_df.loc[:, 'unmatched_sit'] = nlp_df.apply(lambda x: remove_common_locs_sit(x['unmatched_forecast'], x['unmatched_sit']), axis=1)
    nlp_df.drop(columns=['forecast_locs', 'sit_locs_1', 'sit_locs_2'], inplace=True)
    return nlp_df

def remove_common_locs_forecast(unmatched_forecast, unmatched_sit):
    forecast_to_keep = []
    for item in unmatched_forecast:
        if not any(fuzz.partial_ratio(item, sit_item) == 100 for sit_item in unmatched_sit):
            forecast_to_keep.append(item)
    return forecast_to_keep

def remove_common_locs_sit(unmatched_forecast, unmatched_sit):
    sit_to_keep = []
    for item in unmatched_sit:
        if not any(fuzz.partial_ratio(item, fore_item) == 100 for fore_item in unmatched_forecast):
            sit_to_keep.append(item)
    return sit_to_keep

def get_unmatched_forecast(forecast_locs, sit_locs_1, sit_locs_2):
    #print('set1:', set(forecast_locs))
    #print('set2:', set(sit_locs_1).union(set(sit_locs_2)))
    #print('set diff:' ,set(forecast_locs) - set(sit_locs_1).union(set(sit_locs_2)))
    return set(forecast_locs) - set(sit_locs_1).union(set(sit_locs_2))

def get_unmatched_sit(forecast_locs, sit_locs_1, sit_locs_2):
    return set(sit_locs_1).union(set(sit_locs_2)) - set(forecast_locs)

def old_locations_to_match(nlp_df, country):
    '''
    Generates a list of locations to match for a single country.
    Inputs:
        nlp_df: a Pandas dataframe of nlp objects
    '''

    country_df = nlp_df[nlp_df['COUNTRY'] == country]
    country_df['DATE'] = pd.to_datetime(country_df['DATE'], format='%b_%Y')
    #country_df['DATE'] = pd.to_datetime(country_df['DATE'], infer_datetime_format=True)
    #next_month = STARTING_DATE.
    for start_month in rrule.rrule(rrule.MONTHLY, dtstart=STARTING_DATE, until=ENDING_DATE):

        forecast = country_df['FORECAST'].where(country_df['DATE'] == start_month)
        sit_1 = country_df['SITUATION'].where(country_df['DATE'] == start_month + relativedelta(months=+1))
        sit_2 = country_df['SITUATION'].where(country_df['DATE'] == start_month + relativedelta(months=+2))

        country_df['fore_locs'] = set(get_locations(forecast)) - set(get_locations(sit_1)).union(get_locations(sit_2))
        country_df['sit_locs'] = set(get_locations(sit_1)).union(get_locations(sit_2)) - set(get_locations(forecast))

    return country_df

def get_locations(doc):
    '''
    Gets mentions of locations from nlp object.
    '''
    if type(doc) != spacy.tokens.doc.Doc:
        return []
    locations = [ent.text for ent in doc.ents if ent.label_ in ['SPEC_LOC', 'GEN_LOC']]

    return locations

def summarize_unmatched(df):
    for country in df['COUNTRY'].unique():
        count_df = df[df['COUNTRY'] == country]
        forecast = pd.Series(np.concatenate(count_df['unmatched_forecast'].reset_index(drop=True)))
        sit = pd.Series(np.concatenate(count_df['unmatched_sit'].reset_index(drop=True)))
        print('country: ', country)
        print('most common unmatched forecast', forecast.value_counts()[:5])
        print('most common unmatched situation', sit.value_counts()[:5])
    return None