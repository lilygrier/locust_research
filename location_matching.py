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


def get_locations(doc):
    '''
    Gets mentions of locations from nlp object.
    '''
    if type(doc) != spacy.tokens.doc.Doc:
        return []
    locations = [ent.text for ent in doc.ents if ent.label_ in ['SPEC_LOC', 'GEN_LOC']]

    return locations

def summarize_unmatched(df):
    '''
    Creates a table summarizing unmatched locations and their frequencies.
    '''
    #loc_summaries = pd.DataFrame(columns=['COUNTRY', 'UNMATCHED_FORECAST', 'UNMATCHED_SIT'])
    df = locations_to_match(df)
    rv = pd.DataFrame()
    for country in df['COUNTRY'].unique():
        count_df = df[df['COUNTRY'] == country]
        forecast = pd.Series(np.concatenate(count_df['unmatched_forecast'].reset_index(drop=True)))
        sit = pd.Series(np.concatenate(count_df['unmatched_sit'].reset_index(drop=True)))
        forecast_locs = pd.DataFrame(forecast.value_counts()[:5].reset_index())
        forecast_locs.columns = ['unmatched_forecast', 'forecast_freq']
        forecast_locs['country'] = country
        sit_locs = pd.DataFrame(sit.value_counts()[:5].reset_index())
        sit_locs.columns = ['unmatched_sit', 'sit_freq']
        loc_freqs = pd.concat([forecast_locs, sit_locs], axis=1)
        rv = pd.concat([rv, loc_freqs])
    return rv[['country', 'unmatched_forecast', 'forecast_freq', 'unmatched_sit', 'sit_freq']].reset_index(drop=True)