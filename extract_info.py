import spacy
#import contextualSpellCheck
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from fuzzywuzzy import fuzz
from spacy.pipeline import Sentencizer, EntityRuler
#import contextualSpellCheck
from itertools import *
import re

nlp = spacy.load("en_core_web_sm")

#matcher = Matcher(nlp.vocab)
LOCUST_VERBS = ['mature', 'lay', 'lie', 'fledge', 'breed', 'hatch', 'copulate', 'fly', 
                'decline', 'decrease', 'scatter', 'isolate'] # can look for lemma of verb
LOCUST_GERUNDS = ['breeding', 'hatching', 'laying']
LOCUST_TYPES = ["locust", "locusts", "fledgling", "hopper", "adult", "group", "swarm", 'band', 'mature', 'swarmlet', 
                'infestation', 'population', 'scatter', 'isolate'] # took out scatter, isolate and moved to verbs (moved back tho)
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
    #text = re.sub(r'J ask', r'Jask', text)
    # REWRITE LINE BELOW WITH BACK REFERENCING
    text = re.sub(r' ([B-Z]) ([a-z]+)', r' \1\2', text) # should handle the above case
    text = re.sub(r'no reports of ([a-z]+)', r'no \1', text)
    text = re.sub(r'(signifi) +(cant)', r'\1\2', text)


    return text

def get_specific_locations():
    '''
    Extracts locations with lat/long specified
    '''
    pattern = {}
    #re.findall(r'[A-Z][a-z]+ \(.+?\)', text)
    re.findall(r'(([A-Z][a-z]+ ?)+ \(.+?\))', text) # take just first entry of each tuple

def make_nlp():
    '''
    generates nlp object and adds pipelines
    '''
    nlp = spacy.load("en_core_web_sm")
    sentencizer = Sentencizer(punct_chars=['.'])
    ruler = make_entity_ruler(nlp)
    Token.set_extension('is_solitarious', default=None, force=True)
    Span.set_extension('get_name_only', default=None, force=True)
    Span.set_extension('subject_decline', default=False, force=True)
    Span.set_extension('contains_adults', default=None, force=True)
    Span.set_extension('ent_solitarious', default=None, force=True)
    merge_ents = nlp.create_pipe("merge_entities")
    combine_ents_ruler = combine_entities_ruler(nlp)


    #text = prep_text(text) # re-write this as pipeline function?
    nlp.add_pipe(sentencizer, first=True)
    #contextualSpellCheck.add_to_pipe(nlp)
    nlp.add_pipe(ruler, before='ner')
    nlp.add_pipe(refine_entities)
    nlp.add_pipe(get_name_only)
    nlp.add_pipe(subject_decline)
    nlp.add_pipe(merge_ents)
    nlp.add_pipe(combine_ents_ruler)
    nlp.add_pipe(is_solitarious)
    nlp.add_pipe(contains_adults)
    nlp.add_pipe(ent_solitarious)

    #nlp.add_pipe(remove_decline)


    return nlp

def get_snippets(df, col_name, new_col_name=None):
    '''
    Makes column in df for snippets.
    Input:
        df: a Pandas dataframe
        col_name: either 'SITUATION' or 'FORECAST'
        new_col_name (string): the name of the column containing the snippets
    Note: modifies the df in place to add the column
    '''
    #snippets = []
    df.loc[:, col_name] = df[col_name].apply(str)
    nlp = make_nlp()
    if new_col_name:
        df[new_col_name] = None
    #for i, doc in enumerate(nlp.pipe(iter(df[col_name].astype('str')), batch_size = 1000, n_threads=-1)):
    nlp_col = []
    for i, doc in enumerate(nlp.pipe(iter(df[col_name].astype('str')), batch_size = 1000, n_threads=-1)):
        #print('df[col] is : ', df[col_name])
        #print("doc is: ", doc)
        #print('type of doc is: ', type(doc))
        if not doc: # situation is missing
            #print('no doc, moving on')
            nlp_col.append(None)
            continue
        #doc = nlp(text)
        doc_ents = []
        for sent in doc.sents:
            doc_ents.append([ent for ent in sent.ents]) # changed ent.text to ent
        #doc_ents = []
        if new_col_name:
            df.loc[i][new_col_name] = doc_ents
        
        nlp_col.append(doc)
        #df[col_name][i] = doc
        #df.loc[i, col_name] = doc # update text to nlp object
        #snippets.append(doc_ents)
    #print('len snippets is')
    #df[new_col_name] = snippets
        #return doc_ents
    df.loc[:, col_name] = nlp_col
    return df

def prelim_cleaning(df):
    '''
    Some preliminary cleaning of the dataframe to extract information.
    '''
    df['COUNTRY'] = df['COUNTRY'].str.strip()
    df['COUNTRY'] = df['COUNTRY'].str.upper()
    df['COUNTRY'].replace(r'(\w)  +(\w)', r'\1 \2', regex=True, inplace=True)
    df['COUNTRY'].replace(r'GUINEA BIS- SAU', r'GUINEA BISSAU', regex=True, inplace=True)
    df['COUNTRY'].replace(r'CÔTE D’IVOIRE', r'COTE D’IVOIRE', regex=True, inplace=True)
    df['COUNTRY'].replace(r'UNITED ARAB EMIRATES', r'UAE', regex=True, inplace=True)
    df['COUNTRY'].replace(r'CAPE VERDE ISLANDS', r'CAPE VERDE', regex=True, inplace=True)
    df['DATE'].replace(r'JULY_', r'JUL_', regex=True, inplace=True)
    df['DATE'].replace(r'JUNE_', r'JUN_', regex=True, inplace=True)
    df['DATE'].replace(r'SEPT_', r'SEP_', regex=True, inplace=True)


    return df



def get_name_only(doc):

    for ent in doc.ents:
        name = ""
        if ent.label_ == 'SPEC_LOC':
            for word in ent:
                if word.text.startswith('('):
                    ent._.get_name_only = name
                name += word.text
        if ent.label_ == 'GEN_LOC':
            ent._.get_name_only = ent.text
    return doc

def subject_decline(doc):
    for i, ent in enumerate(doc.ents):
        if ent.label_ in ('ACTION', 'LOC_TYPE') and i < len(doc.ents) - 1:
            if doc.ents[i + 1].root.lemma_ == 'decline' or doc.ents[i + 1].root.lemma_ == 'decrease':
                ent._.subject_decline = True
    return doc               

def is_solitarious(doc):
    for token in doc:
        if token.ent_type_ == 'LOC_TYPE':
            #is_solitarious = any()
            #print(ent.text.split())
            if contains_sol_word(token):
            #if set(['isolated', 'scattered', 'solitarious', 'groups', 'few']).intersection(str.lower(token.text.split())):
                token._.is_solitarious = True
                continue
            # pick up on adults were scattered
            #if not token._.is_solitarious:
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

                #if set(['isolated', 'scattered', 'solitarious', 'groups', 'few']).intersection(str.lower(token.text.split()))
            #scattered_head = ent.root.head.head.text in ('scattered', 'isolated', 'solitarious') # added 2nd .head, could be bad
            #ent._.is_solitarious = has_sol_words or scattered_head
            #print(ent.text, 'sol: ', ent._.is_solitarious)
            #ent._.is_solitarious = bool(set(['isolated', 'scattered', 'solitarious', 'groups']).intersection(str.lower(ent.text).split()))
    return doc

def ent_solitarious(doc):
    for ent in doc.ents:
        for token in ent:
            if token._.is_solitarious:
                ent._.ent_solitarious = True
        ent._.ent_solitarious = False

    return doc

def contains_sol_word(token):
    '''
    Determines whether a token contains a solitarious-referencing word.
    '''
    return bool(set(['isolated', 'scattered', 'solitarious', 'groups', 'few']).intersection(str.lower(token.text).split()))

def contains_adults(doc):
    '''
    Extension that determines whether a LOC_TYPE entity refers to adults
    '''
    for ent in doc.ents:
        if ent.label_ == 'LOC_TYPE':
            ent._.contains_adults = 'adult' in ent.text

    return doc


def sent_matches(sent):
    '''
    Note: this function works on a single sentence
    '''
    rv = []
    ranges = []
    matcher = make_matcher()
    matches = matcher(sent)
    for i in range(0, len(matches)):
        start, end = matches[i][1], matches[i][2]
        span = str(sent[start:end])
        #print("SPAN IS: ", span)
        #if ranges:
            #print(ranges[-1], (start, end))
            #prev_range = ranges[-1]
            #new_range = range(start, end)
        # new logic: if any two intersect, take the longer one

        if ranges and set(range(start, end)).issubset((ranges[-1])):
            #print('longer one already there; skipping')
            # if longer match is already in there, skip it
            continue
        elif ranges and set(ranges[-1]).issubset(range(start, end)):
            #print('replacing shorter match with longer one')
            # if shorter match was added, replace the shorter match with a longer one
            rv[-1] = span
            ranges[-1] = range(start, end)
        elif ranges and set(range(start, end)).intersection((ranges[-1])): # if intersect but not subset, don't worry bout it
            continue
        else:
            rv.append(span)
            ranges.append(range(start, end))
        # need to add code that takes care of duplicates (if same start, take longer one)
        #print("ranges: ", ranges)
        #ranges_to_keep = [max(list(group),key=lambda x: x[1]) for key, group in groupby(ranges, lambda prop: prop[0])]
        #for ran in ranges_to_keep:
            #start, end[]
            #rv.append(str(sent[ran[0]:ran[1]]))    

    return rv

def refine_entities(doc):
    doc_ents = []
    #for ent in d
    #print("original entities:")
    #for ent in doc.ents:
        #print(ent, '-->', ent.label_)
    for sent in doc.sents:
        new_ents = []
        for i, ent in enumerate(list(sent.ents)):
            #print('ent is: ', ent.text, '-->', ent.label_)
            #doc.ents = [ent for ent in doc.ents if ent.label_ in ['DATE', 'ACTION', 'LOC_TYPE', 'GEN_LOC', 'SPEC_LOC', 'TREATMENT', 'RISK']]
            #print("doc.ents", doc.ents)
            if ent.label_ in ['DATE', 'ACTION', 'LOC_TYPE', 'GEN_LOC', 'SPEC_LOC', 'TREATMENT', 'RISK']:
            # if entity followed by breeding areas or areas, skip
            # get rid of 'and'
                if doc[ent.start:ent.end].text.lower() == 'nan':
                    continue
                if doc[ent.start:ent.end].text == 'May.':
                    continue
                if doc[ent.start].text == 'and':
                    new_ent = Span(doc, ent.start + 1, ent.end, label=ent.label)
                    new_ents.append(new_ent)
                    continue
                if ent.label_ in ('GEN_LOC', 'SPEC_LOC') and ent.end != len(doc):
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
                        #print("removing ent", ent.text)
                        continue
                if ent.label_ in ('GEN_LOC', 'SPEC_LOC') and ent.start != 0: # take out 'from' locations
                    prev_token = doc[ent.start - 1]
                    if prev_token.text in ('from'):
                        continue
                    if ent.start != 1:
                        prev_prev_token = doc[ent.start - 2]
                        if prev_prev_token.text == 'from' and prev_token.text == 'the': # takes out from the
                            continue
                #print(ent.text, '-->', ent.label_)
                new_ents.append(ent)
        if new_ents:
            #snippets.append([ent.text for ent in new_ents])
            doc_ents.extend(new_ents)
    doc.ents = doc_ents # rewrite entities
    #print('new ents after first round: ', doc.ents)
    return doc

def combine_entities_ruler(nlp):
    '''
    Looks for patterns of multiple entites (i.e., LOC near LOC) and combines into single entity
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
    combine_ruler.name = 'combine_ruler' # change name to avoid confusion
    return combine_ruler



def old_combine_entities(doc):
    '''
    Looks for patterns such as LOC near LOC and combines into single entity
    '''
    spans_to_merge = []
    #for i, ent in enumerate(doc.ents):
    for token in doc:
        if token.ent_type_ in ('GEN_LOC', 'SPEC_LOC') and token.i < len(doc) - 2:
            next_token = token.nbor()
            next_next_token = token.nbor(2)
            if next_token.text == 'near' and next_next_token.ent_type_ in ('GEN_LOC', 'SPEC_LOC'):
                merged_ent = Span(doc, token.i, token.i + 3, label='SPEC_LOC')
                spans_to_merge.append(merged_ent)
                doc.ents += (merged_ent,)
                #doc.ents = list(doc.ents).append(merged_ent)

    print("spans to merge: ", spans_to_merge)
    list(doc.ents).extend(spans_to_merge)
    with doc.retokenize() as retokenizer:
        for span in spans_to_merge:
            retokenizer.merge(span)
    return doc

def remove_decline(doc):
    doc_ents = [ent for ent in doc.ents if not (ent.label_ == 'ACTION' and ent.root.lemma_ == 'decline')]
    doc.ents = doc_ents
    return doc
    #for ent in doc.ents:
        #if ent.label_ == 'ACTION' and ent.root.lemma_ == 'decline':
            

def make_entity_ruler(nlp):
    ruler = EntityRuler(nlp, validate=True, overwrite=True)
    patterns = [] # list of dictionaries
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
                        {'LOWER': {'IN': LOCUST_GERUNDS}, 'POS': {'IN': ['ADJ', 'NOUN']}}] # should be not in 'verb' but not working
    pat_actions = [{'LEMMA': {'IN': LOCUST_VERBS}}]
    patterns.append({'label': 'ACTION', 'pattern': pat_actions})
    patterns.append({'label': 'ACTION', 'pattern': pat_locust_gerunds})
    pat_specific_loc = [{'POS': 'PROPN', 'OP': '+'},
                    {'TEXT': '('},
                    {'TEXT': {'REGEX': r'\d{4}\w/\d{4}\w'}},
                    {'TEXT': ')'}]
    patterns.append({'label': 'SPEC_LOC', 'pattern': pat_specific_loc})
    pat_gen_loc = [{'POS': 'PROPN', 'OP': '*', 'TEXT': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control', 'mid', '-', '.']}},
                {'LOWER': {'IN': ['-', 'el', 'des']}, 'OP': '?'}, # add 'des' here
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
    risk = [[{'POS': 'ADJ'}, {'LOWER': 'risk'}],
            [{'LOWER': 'unlikely'}]]
    for pattern in risk:
        patterns.append({'label': 'RISK', 'pattern': pattern})
    ruler.add_patterns(patterns)
    #nlp.add_pipe(ruler, overwrite=True)
    return ruler

