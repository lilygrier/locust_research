import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.pipeline import Sentencizer, EntityRuler
#import contextualSpellCheck
from itertools import *
import re

nlp = spacy.load("en_core_web_sm")

#matcher = Matcher(nlp.vocab)
LOCUST_VERBS = ['mature', 'lay', 'lie', 'fledge', 'breed', 'hatch', 'copulate', 'fly', 
                'decline', 'scatter', 'isolate'] # can look for lemma of verb
LOCUST_GERUNDS = ['breeding', 'hatching', 'laying']
LOCUST_TYPES = ["locust", "locusts", "fledgling", "hopper", "adult", "group", "swarm", 'band', 'mature', 'swarmlet', 
                'infestation', 'population', 'scatter', 'isolate'] # took out scatter, isolate and moved to verbs (moved back tho)
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]
DIRECTIONS = ['north', 'south', 'east', 'west', 'southwest', 'southeast', 'northwest', 'northeast']
#LOCUST_ADJ = ["immature", 'mature', 'solitarious', 'gregarious', 'isolated']


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
    Span.set_extension('is_solitarious', default=None, force=True)
    Span.set_extension('get_name_only', default=None, force=True)


    #text = prep_text(text) # re-write this as pipeline function?
    nlp.add_pipe(sentencizer, first=True)
    nlp.add_pipe(ruler, before='ner')
    nlp.add_pipe(refine_entities)
    nlp.add_pipe(is_solitarious)
    nlp.add_pipe(get_name_only)

    return nlp

def get_snippets(df, col_name, new_col_name):
    '''
    Makes column in df for snippets.
    Input:
        df: a Pandas dataframe
        col_name: either 'SITUATION' or 'FORECAST'
        new_col_name (string): the name of the column containing the snippets
    Note: modifies the df in place to add the column
    '''
    #snippets = []
    nlp = make_nlp()
    df[new_col_name] = None
    #for doc in 
    for i, doc in enumerate(nlp.pipe(iter(df[col_name]), batch_size = 1000, n_threads=-1)):
        #print("doc is: ", doc)
        #print('type of doc is: ', type(doc))
        if not doc: # situation is missing
            continue
        #doc = nlp(text)
        doc_ents = []
        for sent in doc.sents:
            doc_ents.append([ent.text for ent in sent.ents])
        #doc_ents = []
        df.loc[i][new_col_name] = doc_ents
        #snippets.append(doc_ents)
    #print('len snippets is')
    #df[new_col_name] = snippets
        #return doc_ents
    return None

def corroborate(pred, forecast1, forecast2):
    '''
    First pass at corroborating predictions.
    Simply checks if any locust groups/predictions/behaviors end up in forecasted locations.
    '''
    prediction = [get_data(sent) for sent in pred.sents]
    situation = [get_data(sent) for sent in forecast1.sents].extend([get_data(sent) for sent in forecast2.sents])

    return None

def get_data(sent, granular=False):
    '''
    Pulls out locations, locust types, and behaviors from text.
    Inputs:
        sent: a sentence of an nlp object of text
        granular (bool): whether the data should be extracted at location-level rather than sentence-level
    '''
    #for sent in text.sents:
    locations = [ent for ent in sent.ents if ent.label_ in ('GEN_LOC', 'SPEC_LOC')]
    behaviors = [ent for ent in sent.ents if (ent.label_ == 'ACTION' and ent.text not in ('scattered', 'isolated'))]
    locust_groups = [ent for ent in sent.ents if ent.label_=='LOC_TYPE']
    #granular version:
    if granular:
        tuples = []
        for group in locust_groups:
            for place in locations:
                tuples.append((group, place))
        for behavior in behaviors:
            for place in locations:
                tuples.append((behavior, place))
        return tuples
    # non granular version
    return (locations, behaviors, locust_groups)

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
                

def is_solitarious(doc):
    for ent in doc.ents:
        if ent.label_ == 'LOC_TYPE':
            #is_solitarious = any()
            #print(ent.text.split())
            has_sol_words = bool(set(['isolated', 'scattered', 'solitarious', 'groups', 'few']).intersection(str.lower(ent.text).split()))
            # pick up on adults were scattered
            scattered_head = ent.root.head.head.text in ('scattered', 'isolated', 'solitarious') # added 2nd .head, could be bad
            ent._.is_solitarious = has_sol_words or scattered_head
            #ent._.is_solitarious = bool(set(['isolated', 'scattered', 'solitarious', 'groups']).intersection(str.lower(ent.text).split()))
    return doc

def add_dates(nlp_sent, keywords_list):
    '''
    Adds dates to list of keywords for the sentence
    '''
    for ent in nlp_sent.ents:
        if ent.label_ == 'DATE':
            keywords_list.append(ent.text)
    return None

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
    for sent in doc.sents:
        new_ents = []
        for ent in sent.ents:
            #print('ent is: ', ent.text, '-->', ent.label_)
            if ent.label_ in ['DATE', 'ACTION', 'LOC_TYPE', 'GEN_LOC', 'SPEC_LOC', 'TREATMENT', 'RISK']:
                # if entity followed by breeding areas or areas, skip
                # get rid of 'and'
                if doc[ent.start].text == 'and':
                    new_ent = Span(doc, ent.start + 1, ent.end, label=ent.label)
                    new_ents.append(new_ent)
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
                #print(ent.text, '-->', ent.label_)
                new_ents.append(ent)
        if new_ents:
            #snippets.append([ent.text for ent in new_ents])
            doc_ents.extend(new_ents)
    doc.ents = doc_ents # rewrite entities
    return doc

def add_entity(ent_label):
    return doc.ents.append()

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
                    {'LOWER': {'IN': DIRECTIONS}}]
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
                        [{'LOWER': 'no'}, {'LOWER': 'significant'}, {'LOWER': 'developments'}],
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

def make_matcher():
    '''
    creates the matcher object with specified patterns
    '''
    # maybe move relevant global vars into this function
    matcher = Matcher(nlp.vocab)
    actions = [[{'LEMMA': {'IN': LOCUST_VERBS}}]]
    locust_groups = [[{'LOWER': 'no'}, {'LOWER': 'desert', 'OP': '?'}, {'LEMMA': {'IN': ['Locusts', 'locust', 'swarm']}}],
        [{'POS': 'ADJ', 'OP': '?'},
    {'LOWER': 'and', 'OP': '?'},
    {'LOWER': 'isolated', 'OP': '?'},
    {'POS': {'IN': ['ADJ', 'PROPN']}, 'OP': '*'},
    {'LEMMA': {'IN': LOCUST_TYPES}},
                 {'LOWER': 'AND', 'OP': '?'},
                 {'LEMMA': {'IN': LOCUST_TYPES}, 'OP': '?'}]]
    locust_gerunds = [[{'LOWER': 'no', 'OP': '?'},
                        {'POS': 'ADJ', 'OP': '?'},
                        {'LOWER': {'IN': LOCUST_GERUNDS}, 'POS': {'NOT IN': ['VERB']}}]] # add logic to later remove breeding areas
    specific_loc = [[{'POS': 'PROPN', 'OP': '+'},
                    {'ORTH': '('},
                    {'LOWER': {'REGEX': r'\d{4}\w/\d{4}\w'}},
                    {'ORTH': ')'}]]
    gen_loc = [[{'POS': 'PROPN', 'OP': '*', 'ORTH': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control', 'mid', '-', '.']}},
                {'LOWER': {'IN': ['-', 'el', 'des']}, 'OP': '?'}, # add 'des' here
                {'POS': 'PROPN', 'OP': '+', 'ORTH': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control', 'mid', '-', '.']}}],
                [{'POS': 'ADJ'}, {'LOWER': 'lowlands'}]]
    directions = [[#{'POS': 'ADP', 'OP': '?'},
                    {'LOWER': 'the', 'OP': '?'},
                    {'LOWER': {'IN': DIRECTIONS}}],
                    [{'LOWER': {'IN': DIRECTIONS}},
                    {'LOWER': 'of'},
                    {'LOWER': {'REGEX': r'\d\d[NSEW]'}}]]
    borders =  [[{'IS_TITLE': True, 'OP': '*'},
                {'LOWER': 'and', 'OP': '?'},
                {'IS_TITLE': True, 'OP': '+'},
                {'LEMMA': 'border'}]]
    #dates = [[{'LOWER': {'REGEX': r'\d+-?(\d+)?'}},
                #{'ORTH': {'IN': MONTHS}}]]
    situation_status = [[{'LOWER': 'situation'}, {'OP': '*'}, {'LEMMA': 'improve'}],
                        [{'LOWER': 'calm'}],
                        [{'LOWER': 'no'}, {'LOWER': 'significant'}, {'LOWER': 'developments'}]]
    treatment = [[{'LOWER': {'IN': ['ground', 'aerial']}, 'OP': '?'},
                    {'LOWER': 'and', 'OP': '?'},
                    {'LOWER': {'IN': ['ground', 'aerial']}, 'OP': '?'},
                    {'LOWER': 'control'},
                    {'LOWER': 'operations'}],
                    [{'LEMMA': 'treat'}]]
    risk = [[{'POS': 'ADJ'}, {'LOWER': 'risk'}],
            [{'lower': 'unlikely'}]]
    matcher.add("actions", actions)
    matcher.add("loc_group", locust_groups)
    matcher.add("gerunds", locust_gerunds)
    matcher.add("specific_loc", specific_loc)
    matcher.add("gen_loc", gen_loc)
    matcher.add("directions", directions)
    matcher.add("border", borders)
    matcher.add("treatment", treatment)
    matcher.add("risk", risk)
    #matcher.add("dates", dates)
    matcher.add("situation_status", situation_status)
    return matcher

def parse_info(text):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]
    d = {'locs': [],
        #'spec_locs': [],
        'stage': [],
        'action': []}
    for i, chunk in enumerate(text.noun_chunks):
        if chunk.root.dep_.startswith('nsubj'):
            #print(chunk)
            #who = []
            #what = []
            # subject and verb pair
            #who.append(chunk.text)
            #what.append(chunk.root.head.text)
            d['stage'].append((chunk.text, chunk.root.head.text))
            #d['action'].append(chunk.root.head.text)
        #if chunk.root.dep_ in ['pobj', 'conj', 'dobj']:
            if chunk.root.head.text == 'form': # form and mature and the like
                #print("we got a form")
                #print("here's the thing")
                #print([word.text for word in chunk.root.head.subtree if word.dep_ == 'conj' and word.pos_ == 'VERB'])
                d['action'].extend([word.text for word in chunk.root.head.subtree if word.dep_ == 'conj' and word.pos_ == 'VERB'])
                #verb = [child for child in chunk.root.head.children if child.dep_ == 'conj' and child.text in LOCUST_VERBS]
                #print(verb)
                #if verb:
                    #d['stage'].append(('previous', str(verb)))
                #what.extend([child for child in chunk.root.head.children if child.dep_ == 'conj' and child in LOCUST_VERBS])
            #d['stage'].append((who, what))
        #elif chunk.root.head.text == 'groups' and chunk.root.dep_ == 'conj':
            #d['stage'].append((chunk.text, 'previous'))
        # handle hopper groups and bands, etc. as one chunk
        elif chunk.root.text == 'groups':
            #print("here's the other thing" ,list(chunk.root.subtree))
            d['stage'].append((' '.join([word.text for word in chunk.root.subtree]), None))
            #d['stage'].extend(' '.join(list(chunk.root.subtree)))
            # also want to skip the next noun chunk
        elif set(LOCUST_TYPES).intersection(chunk.text.split()):
            d['stage'].append((chunk.text, None))
        else:
            #print(chunk)
            if not set(months).intersection(chunk.text.split()) and not re.search(r'\d', chunk.text): # doesn't have a month in it
                d['locs'].append(chunk.text)
        #for word in text:
            #if word.pos_ == 'VERB' and word.text in LOCUST_VERBS:
                #d['action'].append(word)
    return d
