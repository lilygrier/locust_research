'''
Matches referenced locations.
'''
import pandas as pd
import numpy as np
import spacy
import datetime
from dateutil.relativedelta import relativedelta
from treelib import Node, Tree
from fuzzywuzzy import fuzz
from dateutil import rrule


MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUNE', 'JULY', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC']

def locations_to_match(nlp_df):
    '''
    Adds columns containing locations to match to dataframe.
    Inputs:
        nlp_df: a Pandas dataframe where situation and forecast columns are nlp objects
    Returns:
        dataframe with columns containing locations to match
    '''
    nlp_df['forecast_locs'] = nlp_df['FORECAST'].apply(lambda x: get_locations(x))
    nlp_df['sit_locs_1'] = nlp_df['SIT_1'].apply(lambda  x: get_locations(x))
    nlp_df['sit_locs_2'] = nlp_df['SIT_2'].apply(lambda  x: get_locations(x))
    nlp_df['unmatched_forecast'] = nlp_df.apply(lambda x: get_unmatched_forecast(x['forecast_locs'], x['sit_locs_1'], x['sit_locs_2']), axis=1)
    nlp_df['unmatched_sit'] = nlp_df.apply(lambda x: get_unmatched_sit(x.forecast_locs, x.sit_locs_1, x.sit_locs_2), axis=1)
    nlp_df.loc[:, 'unmatched_forecast'] = nlp_df.apply(lambda x: remove_common_locs_forecast(x.unmatched_forecast, x.unmatched_sit), axis=1)
    nlp_df.loc[:, 'unmatched_sit'] = nlp_df.apply(lambda x: remove_common_locs_sit(x['unmatched_forecast'], x['unmatched_sit']), axis=1)
    nlp_df.drop(columns=['forecast_locs', 'sit_locs_1', 'sit_locs_2'], inplace=True)

    return nlp_df

def remove_common_locs_forecast(unmatched_forecast, unmatched_sit):
    '''
    Removes locations that appear in both situation and forecast from forecast list; 
    leaves only unmatched people.
    Inputs:
        unmatched_forecast (list): list of unmatched loctaions in forecast
        unmatched_sit (list): list of unmatched locations in situation
    '''
    forecast_to_keep = []
    for item in unmatched_forecast:
        if not any(fuzz.partial_ratio(item, sit_item) == 100 for sit_item in unmatched_sit):
            forecast_to_keep.append(item)
    return forecast_to_keep

def remove_common_locs_sit(unmatched_forecast, unmatched_sit):
    '''
    Removes locations that appear in both situation and forecast from situation list; 
    leaves only unmatched people.
    Inputs:
        unmatched_forecast (list): list of unmatched loctaions in forecast
        unmatched_sit (list): list of unmatched locations in situation
    '''
    sit_to_keep = []
    for item in unmatched_sit:
        if not any(fuzz.partial_ratio(item, fore_item) == 100 for fore_item in unmatched_forecast):
            sit_to_keep.append(item)
    return sit_to_keep

def get_unmatched_forecast(forecast_locs, sit_locs_1, sit_locs_2):
    '''
    Takes in locations mentioned in forecast and situation, returns locations 
    mentioned in forecast that aren't mentioned in situation.
    Inputs:
        forecast_locs: a list of locations mentioned in forecast
        sit_locs_1: a list of locations mentioned in first situation report
        sit_locs_2: a list of locations mentioned in second situation reportf
    Returns:
        a set of forecast locations without matches
    '''
    return set(forecast_locs) - set(sit_locs_1).union(set(sit_locs_2))


def get_unmatched_sit(forecast_locs, sit_locs_1, sit_locs_2):
    '''
    Takes in locations mentioned in forecast and situation, returns locations 
    mentioned in siutation reports that aren't mentioned in forecast report.
    Inputs:
        forecast_locs: a list of locations mentioned in forecast
        sit_locs_1: a list of locations mentioned in first situation report
        sit_locs_2: a list of locations mentioned in second situation reportf
    Returns:
        a set of situation locations not found in forecast report
    '''
    return set(sit_locs_1).union(set(sit_locs_2)) - set(forecast_locs)


def get_locations(doc):
    '''
    Gets mentions of locations from nlp object.
    Inputs:
        doc: a spaCy nlp doc object
    returns:
        a list of locations (strings)
    '''
    if type(doc) != spacy.tokens.doc.Doc:
        return []
    locations = [ent.text for ent in doc.ents if ent.label_ in ['SPEC_LOC', 'GEN_LOC']]

    return locations

def summarize_unmatched(df):
    '''
    Creates a table summarizing unmatched locations and their frequencies.
    Input:
        df: a Pandas dataframe
    Returns:
        a dataframe summarizing unmatched locations and their frequencies
    '''
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

def has_common_loc(forecast_locs, sit_locs, summary_df):
    '''
    Whether a row contains a commonly unmatched location.
    Used by pull_out_common find create dataframe that has examples for location-verification.
    Inputs:
        forecast_locs: a list of unmatched forecast locations
        sit_locs: a list of unmatched situation locations
        summary_df: a dataframe summarizing frequently unmatched locations
    Returns:
        a boolean indicating whether a row contains a commonly unmatched location
    '''
    summary_locs = set(summary_df['unmatched_forecast']).union(set(summary_df['unmatched_sit']))

    return bool(set(forecast_locs).union(set(sit_locs)).intersection(summary_locs))
    
def pull_out_common(country_name, df, summary_df=None):
    '''
    Given a specified country name, pulls out rows 
    that contain commonly unmatched locations for manual verification.
    Should be used for location-verification process.
    Inputs:
        country_name (str): the name of the country
        df: a Pandas dataframe containing 'unmatched_forecast' and 'unmatched_sit' location cols
        summary_df: a dataframe summarizing unmatched locations (defaults to None)
    Returns:
        dataframe of rows with common unmatched locs
    '''
    
    if summary_df is None:
        summary_df = summarize_unmatched(df)

    crit_1 = df.apply(lambda x: has_common_loc(x.unmatched_forecast, x.unmatched_sit, summary_df), axis=1)
    crit_2 = df['COUNTRY'] == country_name

    return df[crit_1 & crit_2]

def get_matching_node(unmatched_place, country_tree):
    '''
    Given a place, returns the matching node from an unmatched tree.
    If no node matches, returns None
    Inputs:
        unmatched_place (str): a location
        country_tree: a location matching tree object
    Returns:
        either a node object or None
    '''
    for node in country_tree.nodes:
        if fuzz.token_set_ratio(node, unmatched_place) == 100:
            return node
    return None

def match_places(place_1, place_2, loc_matching=False, country_tree=None):
    '''
    Determine if two places match.
    Inputs:
        place_1 (str): a location
        place_2 (str): a location
        loc_matching (bool): whether or not to use a location matching tree
        country_tree: if loc_matching is True, must supply a tree for location matching
    '''
    if (place_1 == '' or place_2 == '') or (fuzz.token_set_ratio(place_1, place_2) == 100):
        return True
    if not loc_matching:
        return False
    place_1 = get_matching_node(place_1, country_tree)
    place_2 = get_matching_node(place_2, country_tree)
    if place_1 and place_2:
        return country_tree.is_ancestor(place_1, place_2) or country_tree.is_ancestor(place_2, place_1)