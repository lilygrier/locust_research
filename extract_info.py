import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from fuzzywuzzy import fuzz
from spacy.pipeline import Sentencizer, EntityRuler
from itertools import *
import re

nlp = spacy.load("en_core_web_sm")

LOCUST_VERBS = ['mature', 'lay', 'lie', 'fledge', 'breed', 'hatch', 'copulate', 'fly', 
                'decline', 'decrease', 'scatter', 'isolate']
LOCUST_GERUNDS = ['breeding', 'hatching', 'laying']
LOCUST_TYPES = ["locust", "locusts", "fledgling", "hopper", "adult", "group", "swarm", 'band', 'mature', 'swarmlet', 
                'infestation', 'population', 'scatter', 'isolate']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]
DIRECTIONS = ['north', 'south', 'east', 'west', 'southwest', 'southeast', 'northwest', 'northeast']
#LOCUST_ADJ = ["immature", 'mature', 'solitarious', 'gregarious', 'isolated']

#if __name__ == "__main__":
    

def prep_text(year, month, text):
    '''
    Prepares text for processing.
    '''
    if int(year) < 2002 or (int(year) == 2002 and month in ['JAN', 'FEB', 'MAR', 'APR']):
        text = re.sub(r'-\n', "", text)
        text = re.sub(r'\n', " ", text)
    else:
        text = re.sub(r'\n', "", text)
    text = re.sub(r' ([B-Z]) ([a-z]+)', r' \1\2', text)
    text = re.sub(r'no reports of ([a-z]+)', r'no \1', text)
    text = re.sub(r'(signifi) +(cant)', r'\1\2', text)


    return text

def make_nlp():
    '''
    generates nlp object and adds pipelines
    '''
    nlp = spacy.load("en_core_web_sm")
    sentencizer = Sentencizer(punct_chars=['.'])
    ruler = make_entity_ruler(nlp)
    Token.set_extension('is_solitarious', default=None, force=True)
    Span.set_extension('subject_decline', default=False, force=True)
    Span.set_extension('contains_adults', default=None, force=True)
    Span.set_extension('ent_solitarious', default=None, force=True)
    merge_ents = nlp.create_pipe("merge_entities")
    combine_ents_ruler = combine_entities_ruler(nlp)
    nlp.add_pipe(sentencizer, first=True)
    nlp.add_pipe(ruler, before='ner')
    nlp.add_pipe(refine_entities)
    nlp.add_pipe(subject_decline)
    nlp.add_pipe(merge_ents)
    nlp.add_pipe(combine_ents_ruler)
    nlp.add_pipe(is_solitarious)
    nlp.add_pipe(contains_adults)
    nlp.add_pipe(ent_solitarious)

    return nlp


def get_snippets(df, col_name, new_col_name=None):
    '''
    Converts to column of text to column of nlp objects.
    Input:
        df: a Pandas dataframe
        col_name: either 'SITUATION' or 'FORECAST'
        new_col_name (string): the name of the column containing the snippets
    Returns:
        dataframe with specified col converted to nlp object
    '''
    df.loc[:, col_name] = df[col_name].apply(str)
    nlp = make_nlp()
    if new_col_name:
        df[new_col_name] = None
    nlp_col = []
    for i, doc in enumerate(nlp.pipe(iter(df[col_name].astype('str')), batch_size = 1000, n_threads=-1)):
        if not doc:
            nlp_col.append(None)
            continue
        doc_ents = []
        for sent in doc.sents:
            doc_ents.append([ent for ent in sent.ents])
        if new_col_name:
            df.loc[i][new_col_name] = doc_ents       
        nlp_col.append(doc)
    df.loc[:, col_name] = nlp_col
    
    return df


def prelim_cleaning(df):
    '''
    Some preliminary cleaning of the dataframe to extract information.
    Inputs:
        df: a Pandas dataframe
    Returns:
        a cleaned Pandas dataframe
    '''
    df['MONTH'].replace(r'(.+)\\(.+)', r'\2', regex=True, inplace=True) # works with newer one
    df['COUNTRY'] = df['COUNTRY'].str.strip()
    df['COUNTRY'] = df['COUNTRY'].str.upper()
    df['COUNTRY'].replace(r'(\w)  +(\w)', r'\1 \2', regex=True, inplace=True)
    df['COUNTRY'].replace(r'GUINEA BIS- SAU', r'GUINEA BISSAU', regex=True, inplace=True)
    df['COUNTRY'].replace(r'CÔTE D’IVOIRE', r'COTE D’IVOIRE', regex=True, inplace=True)
    df['COUNTRY'].replace(r'UNITED ARAB EMIRATES', r'UAE', regex=True, inplace=True)
    df['COUNTRY'].replace(r'CAPE VERDE ISLANDS', r'CAPE VERDE', regex=True, inplace=True)
    df['DATE'] = df.apply(lambda x: make_date_col(x.MONTH, x.YEAR), axis=1)
    df['DATE'].replace(r'JULY_', r'JUL_', regex=True, inplace=True)
    df['DATE'].replace(r'JUNE_', r'JUN_', regex=True, inplace=True)
    df['DATE'].replace(r'SEPT_', r'SEP_', regex=True, inplace=True)

    return df

def make_date_col(month, year):
    '''
    Makes a date column from month and year.
    Inputs:
        month: the name of the month
        year (int): the year
    Returns:
        a string in the format month_year
    '''
    return str(month)+'_'+str(year)

def subject_decline(doc):
    '''
    Indicates whether a locust group is predicted to decrease.
    Inputs:
        doc: an nlp doc object
    Returns:
        the doc with entities having subject_decline attribute marked
    '''
    for i, ent in enumerate(doc.ents):
        if ent.label_ in ('ACTION', 'LOC_TYPE') and i < len(doc.ents) - 1:
            if doc.ents[i + 1].root.lemma_ == 'decline' or doc.ents[i + 1].root.lemma_ == 'decrease':
                ent._.subject_decline = True
    return doc               

def is_solitarious(doc):
    '''
    A token attribute. Indicates whether token references solitarious locusts.
    Inputs:
        doc: an nlp doc object
    Returns:
        doc with tokens having is_solitarious attribute marked
    '''

    for token in doc:
        if token.ent_type_ == 'LOC_TYPE':
            if contains_sol_word(token):
                token._.is_solitarious = True
                continue
            for child in token.children:
                if contains_sol_word(child):
                    token._.is_solitarious = True
                    continue
            for conj in token.conjuncts:
                for child in conj.children:
                    if contains_sol_word(child):
                        token._.is_solitarious = True
            if not token._.is_solitarious:
                token._.is_solitarious = False
    return doc


def ent_solitarious(doc):
    '''
    Indicates whether an entity contains solitarious locusts.
    Inputs:
        doc: an nlp doc object
    Returns:
        doc with entities having is_solitarious attribute marked
    '''
    for ent in doc.ents:
        for token in ent:
            if token._.is_solitarious:
                ent._.ent_solitarious = True
        ent._.ent_solitarious = False

    return doc

def contains_sol_word(token):
    '''
    Determines whether a token contains a solitarious-referencing word.
    Inputs:
        token: an nlp token
    Returns:
        boolean of whether token contains solitarious-referencing word
    '''
    return bool(set(['isolated', 'scattered', 'solitarious', 'groups', 'few']).intersection(str.lower(token.text).split()))

def contains_adults(doc):
    '''
    Extension that determines whether a LOC_TYPE entity refers to adults
    Inputs:
        doc: an nlp doc object
    Returns:
        doc with entities having contains_adults attribute marked
    '''
    for ent in doc.ents:
        if ent.label_ == 'LOC_TYPE':
            ent._.contains_adults = 'adult' in ent.text

    return doc


def refine_entities(doc):
    '''
    Edits the doc entities. Removes entities that shouldn't be there.
    Removes locations referenced in the context of locusts being from a place.
    Adds coastal locations, adds "east/west/etc. of PLACE" locations.
    Inputs:
        doc: an nlp doc object
    Returns:
        the doc object with entities edited
    '''
    doc_ents = []
    for sent in doc.sents:
        new_ents = []
        for i, ent in enumerate(list(sent.ents)):
            if ent.label_ in ['DATE', 'ACTION', 'LOC_TYPE', 'GEN_LOC', 'SPEC_LOC', 'TREATMENT', 'RISK']:
                if doc[ent.start:ent.end].text.lower() == 'nan':
                    continue
                if doc[ent.start:ent.end].text == 'May.':
                    continue
                if doc[ent.start].text == 'and':
                    new_ent = Span(doc, ent.start + 1, ent.end, label=ent.label)
                    new_ents.append(new_ent)
                    continue
                if ent.label_ in ('GEN_LOC', 'SPEC_LOC') and ent.end != len(doc):
                    if doc[ent.start].text == 'the':
                        new_ent = Span(doc, ent.start + 1, ent.end, label=ent.label)
                        continue
                    if doc[ent.end - 1].text == 'as':
                        new_ent = Span(doc, ent.start, ent.end - 1, label=ent.label)
                        continue
                    next_token = doc[ent.end]
                    if next_token.text in ('coast'):
                        new_ent = Span(doc, ent.start, ent.end + 1, label=ent.label)
                        new_ents.append(new_ent)
                        continue
                    if next_token.text in ('of'): # remove 'north of' place, just keep place
                        continue
                if ent.label_ in ('DATE', 'ACTION') and ent.end != len(doc):
                    next_token = doc[ent.end]
                    if next_token.text in ('breeding', 'areas'):
                        continue
                if ent.label_ in ('GEN_LOC', 'SPEC_LOC') and ent.start != 0: # take out 'from' locations
                    prev_token = doc[ent.start - 1]
                    if prev_token.text in ('from'):
                        continue
                    if ent.start != 1:
                        prev_prev_token = doc[ent.start - 2]
                        if prev_prev_token.text == 'from' and prev_token.text == 'the': # takes out from the
                            continue
                new_ents.append(ent)
        if new_ents:
            doc_ents.extend(new_ents)
    doc.ents = doc_ents # rewrite entities
    return doc

def combine_entities_ruler(nlp):
    '''
    Looks for patterns of multiple entites (i.e., LOC near LOC) and combines into single entity.
    Inputs:
        nlp: an nlp object
    Returns:
        combine_ruler: a spaCy EntityRuler object
    '''
    patterns = []
    combine_ruler = EntityRuler(nlp, validate=True, overwrite_ents=True)
    place_near_place = [{'LOWER': {'IN': DIRECTIONS}, 'OP': '?'},
                        {'LOWER': 'of', 'OP': '?'},
                        {'LOWER': 'the', 'OP': '?'},
                        {'ENT_TYPE': {'IN': ['GEN_LOC', 'SPEC_LOC']}},
                        {'LOWER': 'near'},
                        {'ENT_TYPE': {'IN': ['GEN_LOC', 'SPEC_LOC']}}]
    patterns.append({'label': 'SPEC_LOC', 'pattern': place_near_place})
    place_between_place = [{'ENT_TYPE': {'IN': ['GEN_LOC', 'SPEC_LOC']}},
                        {'LOWER': 'between'},
                        {'ENT_TYPE': {'IN': ['GEN_LOC', 'SPEC_LOC']}},
                        {'LOWER': 'and'},
                        {'ENT_TYPE': {'IN': ['GEN_LOC', 'SPEC_LOC']}}]
    patterns.append({'label': 'SPEC_LOC', 'pattern': place_between_place})
    direction_place = [{'ENT_TYPE': 'GEN_LOC'},
                        {'ENT_TYPE': 'SPEC_LOC'}]
    patterns.append({'label': 'SPEC_LOC', 'pattern': direction_place})
    isolated_scattered = [{'LOWER': {'IN': ['isolated', 'scattered']}, 'OP': '?'},
                         {'ENT_TYPE': 'LOC_TYPE', 'OP': '+'}]
    patterns.append({'label': 'LOC_TYPE', 'pattern': isolated_scattered})
    combine_ruler.add_patterns(patterns)
    combine_ruler.name = 'combine_ruler'

    return combine_ruler
            

def make_entity_ruler(nlp):
    ruler = EntityRuler(nlp, validate=True, overwrite=True)
    patterns = []
    patterns.append({'label': 'LOC_TYPE', 'pattern': [{'LOWER': 'no'}, {'LOWER': 'desert', 'OP': '?'}, {'LEMMA': {'IN': ['Locusts', 'locust', 'swarm']}}]})
    patterns.append({'label': 'LOC_TYPE', 'pattern':[{'POS': 'ADJ', 'OP': '?'},
    {'LOWER': 'and', 'OP': '?'},
    {'LOWER': 'isolated', 'OP': '?'},
    {'POS': {'IN': ['ADJ', 'PROPN']}, 'OP': '*'},
    {'LEMMA': {'IN': LOCUST_TYPES}},
                 {'LOWER': 'AND', 'OP': '?'},
                 {'LEMMA': {'IN': LOCUST_TYPES}, 'OP': '?'}]})
    pat_no_devs = [{'LOWER': 'no'}, {'LOWER': 'significant'}, {'LOWER': 'developments'}]
    pat_no_devs_variation = [{'LOWER': {'IN': ['no', ' no']}}, 
                {'LOWER': 'signiﬁ'},
                {'LOWER': 'ca'},
                {'LOWER': 'nt'},
                {'LOWER': 'developments'}]
    patterns.append({'label': 'LOC_TYPE', 'pattern': pat_no_devs})
    patterns.append({'label': 'LOC_TYPE', 'pattern': pat_no_devs_variation})
    pat_locust_gerunds = [{'LOWER': 'no', 'OP': '?'},
                        {'POS': 'ADJ', 'OP': '?'},
                        {'LOWER': {'IN': LOCUST_GERUNDS}, 'POS': {'IN': ['ADJ', 'NOUN']}}]
    pat_actions = [{'LEMMA': {'IN': LOCUST_VERBS}}]
    patterns.append({'label': 'ACTION', 'pattern': pat_actions})
    patterns.append({'label': 'ACTION', 'pattern': pat_locust_gerunds})
    pat_specific_loc = [{'POS': 'PROPN', 'OP': '+'},
                    {'TEXT': '('},
                    {'TEXT': {'REGEX': r'\d{4}\w/\d{4}\w'}},
                    {'TEXT': ')'}]
    patterns.append({'label': 'SPEC_LOC', 'pattern': pat_specific_loc})
    pat_gen_loc = [{'POS': 'PROPN', 'OP': '*', 'TEXT': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control', 'mid', '-', '.']}},
                {'LOWER': {'IN': ['-', 'el', 'des']}, 'OP': '?'},
                {'POS': 'PROPN', 'OP': '+', 'TEXT': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control', 'mid', '-', '.']}}]
    pat_lowlands = [{'POS': 'ADJ'}, {'LOWER': 'lowlands'}]
    patterns.append({'label': 'GEN_LOC', 'pattern': pat_gen_loc})
    patterns.append({'label': 'GEN_LOC', 'pattern': pat_lowlands})
    pat_directions = [#{'POS': 'ADP', 'OP': '?'},
                    {'LOWER': 'the', 'OP': '?'},
                    {'LOWER': {'IN': DIRECTIONS}},
                    {'LOWER': '-', 'OP': '?'},
                    {'LOWER': {'IN': DIRECTIONS}, 'OP': '?'}]
    pat_south_of = [{'LOWER': {'IN': DIRECTIONS}},
                    {'LOWER': 'of'},
                    {'LOWER': {'REGEX': r'\d\d[NSEW]'}}]
    patterns.append({'label': 'GEN_LOC', 'pattern': pat_directions})
    patterns.append({'label': 'GEN_LOC', 'pattern': pat_south_of})
    borders =  [{'IS_TITLE': True, 'OP': '*'},
                {'LOWER': 'and', 'OP': '?'},
                {'IS_TITLE': True, 'OP': '+'},
                {'LEMMA': 'border'}]
    patterns.append({'label': 'GEN_LOC', 'pattern': borders})
    situation_status = [[{'LOWER': 'situation'}, {'OP': '*'}, {'LEMMA': 'improve'}],
                        [{'LOWER': 'calm'}],
                        #[{'LOWER': 'no'}, {'LOWER': 'significant'}, {'LOWER': 'developments'}],
                        [{'LOWER': 'no'}, {'LOWER': {'REGEX': r'signiﬁ *cant'}}, {'LOWER': 'developments'}]]
    for pattern in situation_status:
        patterns.append({'label': 'ACTION', 'pattern': pattern})
    treatment = [[{'LOWER': {'IN': ['ground', 'aerial']}, 'OP': '?'},
                    {'LOWER': 'and', 'OP': '?'},
                    {'LOWER': {'IN': ['ground', 'aerial']}, 'OP': '?'},
                    {'LOWER': 'control'},
                    {'LOWER': 'operations'}],
                    [{'LEMMA': 'treat'}]]
    for pattern in treatment:
        patterns.append({'label': 'TREATMENT', 'pattern': pattern})

    no_reports_received = [{'LOWER': 'no'},
                            {'LOWER': 'reports'},
                            {'LOWER': 'were', 'OP': '?'},
                            {'LOWER': 'received'}]
    patterns.append({'label': 'NOREPORTS', 'pattern': no_reports_received})
    risk = [[{'POS': 'ADJ'}, {'LOWER': 'risk'}],
            [{'LOWER': 'unlikely'}]]
    for pattern in risk:
        patterns.append({'label': 'RISK', 'pattern': pattern})
    ruler.add_patterns(patterns)

    return ruler