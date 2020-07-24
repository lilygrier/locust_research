import spacy
from spacy.matcher import Matcher
from spacy.pipeline import Sentencizer
from itertools import *
import re

nlp = spacy.load("en_core_web_sm")

#matcher = Matcher(nlp.vocab)
LOCUST_VERBS = ['form', 'mature', 'lay', 'fledge', 'breed', 'hatch', 'copulate', 'fly', 'decline'] # can look for lemma of verb
LOCUST_GERUNDS = ['breeding', 'hatching', 'laying']
LOCUST_TYPES = ["locust", "fledgling", "hopper", "adult", "group", "swarm", 'band', 'swarmlet', 'infestation', 'population']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', "November", "December"]

#LOCUST_ADJ = ["immature", 'mature', 'solitarious', 'gregarious', 'isolated']

def prep_text(text):
    '''
    Prepares text for processing.
    '''
    text = re.sub(r'\n', "", text)
    #text = re.sub(r'J ask', r'Jask', text)
    # REWRITE LINE BELOW WITH BACK REFERENCING
    text = re.sub(r'[B-Z] [a-z]+', r'[B-Z][a-z]+', text) # should handle the above case
    text = re.sub(r'no reports of [a-z]+', r'no [a-z]+', text)

    return text

def get_specific_locations():
    '''
    Extracts locations with lat/long specified
    '''
    pattern = {}
    #re.findall(r'[A-Z][a-z]+ \(.+?\)', text)
    re.findall(r'(([A-Z][a-z]+ ?)+ \(.+?\))', text) # take just first entry of each tuple

def get_snippets(text):
    snippets = []
    nlp = spacy.load("en_core_web_sm")
    sentencizer = Sentencizer(punct_chars=['.'])
    text = prep_text(text) # re-write this as pipeline function?
    nlp.add_pipe(sentencizer)
    for sent in nlp(text).sents:
        #sent = nlp(sent)
        keywords = sent_matches(sent)
        add_dates(sent, keywords)
        if keywords:
            snippets.append(keywords)
    return snippets

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

def make_matcher():
    '''
    creates the matcher object with specified patterns
    '''
    # maybe move relevant global vars into this function
    matcher = Matcher(nlp.vocab)
    actions = [[{'LEMMA': {'IN': LOCUST_VERBS}}]]
    locust_groups = [[{'POS': 'ADJ', 'OP': '?'},
    {'LOWER': 'and', 'OP': '?'},
    {'LOWER': 'isolated', 'OP': '?'},
    {'POS': {'IN': ['ADJ', 'PROPN']}, 'OP': '*'},
    {'LEMMA': {'IN': LOCUST_TYPES}},
                 {'LOWER': 'AND', 'OP': '?'},
                 {'LEMMA': {'IN': LOCUST_TYPES}, 'OP': '?'}],
                 [{'LOWER': 'no'}, {'LOWER': 'desert', 'OP': '?'}, {'LOWER': 'locusts'}]]
    locust_gerunds = [[{'LOWER': {'IN': LOCUST_GERUNDS}, 'POS': {'NOT IN': 'VERB'}},
                        {'LOWER': 'areas', 'OP': '!'}]]
    specific_loc = [[{'POS': 'PROPN', 'OP': '+'},
                    {'ORTH': '('},
                    {'LOWER': {'REGEX': r'\d{4}\w/\d{4}\w'}},
                    {'ORTH': ')'}]]
    gen_loc = [[{'POS': 'PROPN', 'OP': '+', 'ORTH': {'NOT_IN': MONTHS}, 'LOWER': {'NOT_IN': ['ground', 'control']}}]]
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
    matcher.add("actions", actions)
    matcher.add("loc_group", locust_groups)
    matcher.add("gerunds", locust_gerunds)
    matcher.add("specific_loc", specific_loc)
    matcher.add("gen_loc", gen_loc)
    matcher.add("border", borders)
    matcher.add("treatment", treatment)
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
