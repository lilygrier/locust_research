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

    forecast = country_df['FORECAST'].where(country_df['DATE'] == STARTING_DATE)
    sit_1 = country_df['SITUATION'].where(country_df['DATE'] == STARTING_DATE + monthdelta(1))
    sit_2 = country_df['SITUATION'].where(country_df['DATE'] == STARTING_DATE + monthdelta(2))



    

