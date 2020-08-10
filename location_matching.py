'''
Matches referenced locations.
'''
import pandas as pd
import spacy
import datetime

STARTING_DATE = 'FIGURE THIS OUT'

MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE', 'JULY', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

def locations_to_match(nlp_df, country):
    '''
    Generates a list of locations to match for a single country.
    Inputs:
        nlp_df: a Pandas dataframe of nlp objects
    '''
    country_df = nlp_df[nlp_df['COUNTRY'] == country]
    country_df['DATE'] = pd.to_datetime(country_df['DATE'], format='%b_%Y')
    forecast = country_df['FORECAST'].where(country_df['DATE'] == STARTING_DATE)
    sit_1 = country_df['SITUATION'].where(country_df['DATE'] == STARTING_DATE + monthdelta(1))
    sit_2 = country_df['SITUATION'].where(country_df['DATE'] == STARTING_DATE + monthdelta(2))

    country_df['forecast_locs'] = set(get_locations(forecast)) - set(get_locations(sit_1)).union(get_locations(sit_2))
    country_df['sit_locs'] = set(get_locations(sit_1)).union(get_locations(sit_2)) - set(get_locations(forecast))

    return country_df

def get_locations(nlp_col):
    '''
    Gets mentions of locations from nlp object.
    '''
    locations = [ent for ent in nlp_col.ents if ent.label_ in ['SPEC_LOC', 'GEN_LOC']]

    return locations




    

