'''
Matches referenced locations.
'''
import pandas as pd
import spacy
import datetime
from dateutil.relativedelta import relativedelta

#from monthdelta import MonthDelta


STARTING_DATE = datetime.date(1996, 8, 1)
ENDING_DATE = datetime.date(2020, 3, 1)
from dateutil import rrule


MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE', 'JULY', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

def locations_to_match(nlp_df):
    forecast_locs = nlp_df['FORECAST'].apply(lambda x: get_locations(x))
    sit_locs_1 = nlp_df['SIT_1'].apply(lambda  x: get_locations(x))
    sit_locs_2 = nlp_df['SIT_2'].apply(lambda  x: get_locations(x))
    # need to treat this as a lambda situation probably
    nlp_df['fore_locs'] = set(forecast_locs) - set(sit_locs_1).union(set(sit_locs_2))
    nlp_df['sit_locs'] = set(sit_locs_1).union(set(sit_locs_2)) - set(forecast_locs)

    return nlp_df

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
    locations = [ent for ent in doc.ents if ent.label_ in ['SPEC_LOC', 'GEN_LOC']]

    return locations




    

