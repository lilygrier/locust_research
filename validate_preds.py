import spacy
import pandas as pd
from fuzzywuzzy import fuzz
from location_matching import match_places
from dateutil.relativedelta import relativedelta



def make_merged_df(df):
    '''
    Creates a dataframe with forecast and situations aligned.
    '''
    #
    # df['DATE'] = str(df['MONTH'])+'_'+str(df['YEAR'])
    df.loc[:, 'DATE'] = pd.to_datetime(df['DATE'], format='%b_%Y')
    df['ONE_MONTH_OUT'] = df['DATE'].apply(lambda x: x + relativedelta(months=+1))
    df['TWO_MONTHS_OUT'] = df['DATE'].apply(lambda x: x + relativedelta(months=+2))
    one_month = df[['COUNTRY', 'SITUATION', 'ONE_MONTH_OUT']].copy()
    one_month.rename(columns={'SITUATION': 'SIT_1'}, inplace=True)
    two_months = df[['COUNTRY', 'SITUATION', 'TWO_MONTHS_OUT']].copy()
    two_months.rename(columns={'SITUATION': 'SIT_2'}, inplace=True)
    df.drop(columns=['ONE_MONTH_OUT', 'TWO_MONTHS_OUT'], inplace=True)
    df = df.merge(one_month,
                left_on = ['COUNTRY', 'DATE'],
                right_on = ['COUNTRY', 'ONE_MONTH_OUT'],
                 how='left')
    df = df.merge(two_months,
                     left_on=['COUNTRY', 'DATE'],
                     right_on = ['COUNTRY', 'TWO_MONTHS_OUT'],
                     how='left')
    return df

def results_by_sentence(pred, sit_1, sit_2, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    If anything in the prediction sentence is correct, returns true.
    '''
    results = []
    situations = []
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
    pos_preds = []
    for sent in pred.sents:
        predictions = get_data(sent, granular=True)
        no_sig = False
        for pred in predictions:
            if pred[0].text.lower().startswith('no sign'):
                no_sig = True
        pos_preds.append(no_sig)
        #no_sig = predictions[0][0].text.lower().startswith('no sign') or (predictions[0][0].text.lower() == 'no' and predictions[0][1].text.lower.startswith('sign'))
        #pos_preds.append(no_sig)
        if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        #print('preds and not sits!!')
        #print(predictions)
            if no_sig:
                results.append(True)
            else:
                results.append(False)
        
        else:
            #print('test', all((compare_one_granular(prediction, situations, match_type=match_type, 
            #loc_matching=loc_matching, country_tree=country_tree) == "False - No match") for prediction in predictions))
            if all((compare_one_granular(prediction, situations, match_type=match_type, 
            loc_matching=loc_matching, country_tree=country_tree) == "False - No match") for prediction in predictions):
                        results.append('False - No match')
            else:
                results.append(any((compare_one_granular(prediction, situations, match_type=match_type, 
                            loc_matching=loc_matching, country_tree=country_tree) == True) for prediction in predictions))
            #for prediction in predictions:
                #results.append(compare_one_granular(prediction, situations, match_type=match_type))
    #for pred, loc in predictions:
        #if pred.text.lower().startswith('no sign') or pred.text
    #print('predictions is: ', predictions)
    # if not predictions:
    #     pos_preds = [False]
    # else:
    #     no_sig = predictions[0][0].text.lower().startswith('no sign')
    #     pos_preds = [not no_sig * len(list(pred.sents))]
    return results, pos_preds

def results_by_place(pred, sit_1, sit_2, match_type='any_locusts', loc_matching=False, country_tree=None):
    '''
    Most lenient pass at accuracy. For each location in which locusts were predicted,
    did locusts appear?
    All predictions for a single place are combined, and if any are true, returns true.
    '''
    predictions, situations = get_tuple_list(pred, sit_1, sit_2)
    if predictions and not situations:
        if predictions[0][0].text.lower().startswith('no sign') or (predictions[0][0].text.lower() == 'no' and predictions[0][1].text.lower.startswith('sign')):
            return ([True], [False])
        else:
            return ([False], [True])
    pred_locs = generate_by_place_dict(predictions)
    sit_locs = generate_by_place_dict(situations)
    results = []
    print('pred_locs: ', pred_locs)
    print('sit_locs: ', sit_locs)
    pos_preds = []
    for pred_loc, pred_list in pred_locs.items():
        matching_locs = [sit_loc for sit_loc in sit_locs.keys() if match_places(pred_loc, sit_loc, loc_matching, country_tree)]
        print('pred_loc', pred_loc)
        print('matching locs: ' , matching_locs)
        if matching_locs:
            #for pred in pred_list:
            results.append(any(compare_preds_by_place(pred_list, sit_group, match_type) for sit_group in sit_locs.values()))
        else:
            #for pred in pred_list:
            #results.append(False)
            results.append('False - No match')
        print('pred_list is: ', pred_list)
        has_sig = True
        for pred in pred_list:
            if pred.text.lower().startswith('no sign'):
                has_sig = False
        pos_preds.append(has_sig)
        #pos_preds.append(pred_list[0].text.lower().startswith('no sign') or (len(pred_list) >= 2 and pred_list[0].text.lower() == 'no' and pred_list[1].text.lower.startswith('sign'))
        
        #pos_preds.append(any(pred.text.lower().startswith('no sign') or (pred.text.lower() == 'no' and pred[1].text.lower.startswith('sign'))))
    #print('results: ', results)
    #print('pred_locs is: ', pred_locs)
    #for pred_loc, pred_list
    #no_sig = pred_locs[0][0].text.lower().startswith('no sign') or (pred_locs[0][0].text.lower() == 'no' and pred_locs[0][1].text.lower.startswith('sign'))
    #pos_preds = [not no_sig * len(pred_locs)]
    return results, pos_preds


def generate_by_place_dict(tuple_list):
    '''
    Takes in list of tuples and generates a dictionary clustering predictions/reports of locust 
    groups or activity into associated locations.
    '''
    by_locs = {}
    for group, place in tuple_list:
        #print('place', place)
        #print('type of place', type(place))
        if not place:
            place_name = ''
        else:
            place_name = place.text
        if place_name in by_locs:
            by_locs[place_name].append(group)
        else:
            by_locs[place_name] = [group]

    return by_locs



def get_tuple_list(pred, sit_1, sit_2):
    '''
    Creates list of tuples from predictions and situations.
    '''
    predictions = []
    situations = []
    for sent in pred.sents:
        predictions.extend(get_data(sent, granular=True))
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
    return (predictions, situations)

def percent_result_type(results_list, result_type, distinguish_false=False):
    '''
    Given a results list of true and false, returns percent of true predictions.
    Inputs:
        results_list: a list of results
        result_type: the type of result (either True, False, or 'False - No match')
        distinguish_false: if True, will exclude falses labeled "no match" or 
        "no report received" from the calculation of the final score
    '''
    #print('results list is: ', results_list)
    if not results_list:
        return 0
    
    if distinguish_false:
        valid_results = [result for result in results_list if result in [True, False]]
        if not valid_results:
            return 0
    else:
        valid_results = results_list
    return len([result for result in results_list if result==result_type])/len(valid_results)
    #else:
        #true_results = [result for result in results_list if result==True]
        #return sum(results_list)/len(results_list)

def granular_corroborate(pred, sit_1, sit_2, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    Breaks each prediction into granular tuples. Sees if those
    specific tuples occur later.
    '''
    results = []
    predictions = []
    if all((type(item) != spacy.tokens.doc.Doc) for item in [pred, sit_1, sit_2]):
        return []
    for sent in pred.sents:
        predictions.extend(get_data(sent, granular=True))
    #print('sit 1 is: ', sit_1)
    #print('type of sit1 is: ', type(sit_1))
    situations = []
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
        #situations = [get_data(sent, granular=True) for sent in sit_1.sents]
    #else:
        #situations = []
    #if type(sit_2) == spacy.tokens.doc.Doc:
        #for sent in sit_2.sents:
            #situations.extend(get_data(sent, granular=True))
    #print('situations: ', situations)
    if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        #print('no sits, pred is: ', predictions[0][2][0][0].text.lower())
        if predictions[0][0].text.lower().startswith('no signi'):
            return ([True], [False])
    for pred in predictions:
        #print('pred: ', pred)
        results.append(compare_one_granular(pred, situations, match_type=match_type))
        #print('result: ', compare_one_granular(pred, situations, match_type=match_type))
    pos_preds = positive_prediction(predictions)
    #print('results', results)
    #print('pos_preds', pos_preds)
    return (results, pos_preds)

def compare_preds_by_place(pred_groups, sit_groups, match_type='general_type'):
    '''
    Compares a list of predictions to a list of situations. If any of them are in common, 
    returns true.
    '''
    for pred in pred_groups:
        for sit in sit_groups:
            if (compare_predictions(pred, sit, match_type)):
                return True
    return False




def compare_predictions(pred_group, sit_group, match_type='general_type'):
    '''
    Compares two locust groups or actions and returns whether or not they're a match.
    '''
    #print('pred_group', pred_group)
    #print('sit_group', sit_group)
                #print('situation: ', sit)

    if pred_group._.subject_decline: # matches locusts will decline to no locusts
        #print('pred subject decline', pred[0]._.subject_decline)
        if sit_group._.subject_decline or is_negated(sit_group):
            #print('negated?', is_negated(sit[0]))
            return True
        else:
            return False
    #if is_negated(pred[0]) != is_negated(sit[0]): # one is negated and one is not, not a match
        #continue
    if is_negated(pred_group) and is_negated(sit_group): # match no devs to no locusts
        return True
    if is_negated(pred_group) != is_negated(sit_group): # make sure 'no locusts' won't match to 'locusts'
        return False
    if fuzz.token_set_ratio(pred_group, sit_group) == 100: # matches mature as verb to mature locusts
        return True
    if pred_group.label_ == 'ACTION' and sit_group.label_ == 'ACTION':
        if fuzz.token_set_ratio(pred_group.lemma_, sit_group.lemma_) == 100 or set([pred_group, sit_group]) == set(['laying', 'lay']): # NEED TO ADDRESS LAYING VS LAY
            return True
    elif pred_group.label_ == 'LOC_TYPE' and sit_group.label_ == 'LOC_TYPE': # already filtered out negations
        #print('two locust types')
        #print('match_type: ', match_type)
        if match_type == 'any_locusts':
            return True
        if pred_group.text.lower() == 'locusts' or pred_group.text.lower() == 'populations': # if just locusts is predicted, will match to anything
            return True
        elif match_type == 'general_type':
            if pred_group._.contains_adults == sit_group._.contains_adults:
                if pred_group._.ent_solitarious == sit_group._.ent_solitarious:
                    return True
        elif match_type == 'exact':
            return fuzz.partial_ratio(pred_group, sit_group) == 100



def compare_one_granular(pred, situations, match_type='general_type', loc_matching=False, country_tree=None):
    '''
    compares one granular prediction tuple against all situations.
    Inputs:
        pred: an nlp object of a single prediction
        situations: a list of nlp object of situation statements
        match_type (string):
            'any_locusts': matches based on being able to predict any locusts
            'general_type': matches on adult vs. hopper, solitarious vs. gregarious,
                            and immature vs. mature
            'exact': matches on exact wording (e.g., 'few small groups' will only 
                                                match to 'few small groups')
    '''
    for sit in situations:
        if not sit and pred:
            continue
        #print('situations: ', situations)
        #print('situation', sit)
        #print('pred: ', pred)
        if pred[1] and not sit[1]: # pred has a location but sit doesn't... deal with this later
            continue
        if loc_matching:
            locs_match = not(pred[1] and sit[1]) or match_places(pred[1], sit[1], country_tree)
        else:
            locs_match = not (pred[1] and sit[1]) or fuzz.token_set_ratio(pred[1], sit[1]) == 100 # deal with not sit[1] separately
        if locs_match:
            #print('pred: ', pred)
            #print('situation: ', sit)

            if pred[0]._.subject_decline: # matches locusts will decline to no locusts
                #print('pred subject decline', pred[0]._.subject_decline)
                if sit[0]._.subject_decline or is_negated(sit[0]):
                    #print('negated?', is_negated(sit[0]))
                    return True
                else:
                    continue
            #if is_negated(pred[0]) != is_negated(sit[0]): # one is negated and one is not, not a match
                #continue

            if is_negated(pred[0]) and is_negated(sit[0]): # match no devs to no locusts
                return True
            if is_negated(pred[0]) != is_negated(sit[0]): # make sure 'no locusts' won't match to 'locusts'
                continue
            if fuzz.token_set_ratio(pred[0], sit[0]) == 100: # matches mature as verb to mature locusts
                return True
            if pred[0].label_ == 'ACTION' and sit[0].label_ == 'ACTION':
                if fuzz.token_set_ratio(pred[0].lemma_, sit[0].lemma_) == 100 or set([pred[0], sit[0]]) == set(['laying', 'lay']): # NEED TO ADDRESS LAYING VS LAY
                    return True
            elif pred[0].label_ == 'LOC_TYPE' and sit[0].label_ == 'LOC_TYPE':
                #print('two locust types')
                #print('match_type: ', match_type)
                if match_type == 'any_locusts':
                    return True
                if pred[0].text.lower() == 'locusts' or pred[0].text.lower() == 'populations': # if just locusts is predicted, will match to anything
                    return True
                elif match_type == 'general_type':
                    if pred[0]._.contains_adults == sit[0]._.contains_adults:
                        if pred[0]._.ent_solitarious == sit[0]._.ent_solitarious:
                            return True
                elif match_type == 'exact':
                    return fuzz.partial_ratio(pred[0], sit[0]) == 100
        else:
            return "False - No match"

    return False

def general_type_match(pred, sit):
    if pred[0]._.contains_adults == sit[0]._.contains_adults:
        if pred[0]._.is_solitarious == sit[0]._.is_solitarious:
            return True


def is_negated(ent):
    '''
    Returns whether an ent is negated (i.e., 'no locusts')
    '''
    #print(ent[0].text.lower())
    return ent[0].text.lower().startswith('no ')



def compare_behaviors(pred_list, sit_list, granular=False):
    if granular:
        return fuzz.partial_ratio(pred_bx.root.lemma_, sit_bx.root.lemma_) == 100
    # sentence level:
    for pred_bx in pred_list[1]:
        for sit_bx in sit_list[1]:
            if fuzz.partial_ratio(pred_bx.root.lemma_, sit_bx.root.lemma_) == 100:
                return True
    #elif 'no significant developments' in []
    
    return False

def compare_groups(pred_list, sit_list):
    '''
    Takes in two lists of locust groups.
    Compares them based on whether or not they're solitarious or gregarious 
    as well as life stage (based on ent.lemma_ for now).
    Checks if entities have the same lemma, then checks if they're solitarious.
    '''
    print(pred_list, sit_list)
    for group_1 in pred_list[2]:
        for group_2 in sit_list[2]:
            if group_1[0].text.lower() == 'no' or 'decline' in [word.text for word in sit_list[1]]: # match no significant devs to no locusts
                if group_2[0].text.lower() == 'no': # match 'decline' to 'no locusts'
                    return True
            elif group_1.root.lemma_ == group_2.root.lemma_:
                if group_1._.is_solitarious == group_2._.is_solitarious:
                    return True
    return False

def compare_locs(pred_list, sit_list, granular=False):
    '''
    Takes in two lists of locations. Returns true if the lists contain at least one matching location.
    ADD IN FUNCTIONALITY FOR COMPARING GENERAL TO SPECIFIC 
    '''
    #match = False
    if granular:
        return fuzz.token_set_ratio(loc_1, loc_2) == 100
    
    for loc_1 in pred_list[0]:
        for loc_2 in sit_list[0]:
            if fuzz.token_set_ratio(loc_1, loc_2) == 100:
                return True
    return False



def get_data(sent, granular=False):
    '''
    Pulls out locations, locust types, and behaviors from text.
    Inputs:
        sent: a sentence of an nlp object of text
        granular (bool): whether the data should be extracted at location-level rather than sentence-level
    '''
    #for sent in text.sents:
    locations = [ent for ent in sent.ents if ent.label_ in ('GEN_LOC', 'SPEC_LOC')]
    behaviors = [ent for ent in sent.ents if (ent.label_ == 'ACTION' and ent.text not in ('scattered', 'isolated', 'decline', 'decrease'))]
    locust_groups = [ent for ent in sent.ents if ent.label_=='LOC_TYPE']
    #granular version:
    #print('locations: ', locations)
    if granular:
        tuples = []
        for group in locust_groups:
            if locations:
                for place in locations:
                    tuples.append((group, place))
            else:
                #print('no locations: ', locations)
                tuples.append((group, ''))
        for behavior in behaviors:
            if locations:
                for place in locations:
                    tuples.append((behavior, place))
            else:
                tuples.append((behavior, ''))
        #print('tuples: ', tuples)
        return tuples
    # non granular version
    return (locations, behaviors, locust_groups)

def positive_prediction(preds_list):
    '''
    Creates a list of booleans indicating whether a prediction indicates something other than
    "no significant developments."
    Inputs:
        preds_list: a list of tuples containing predictions
    '''
    rv = []
    for pred in preds_list:
        no_sig = pred[0].text.lower().startswith('no sign') or (pred[0].text.lower() == 'no' and pred[1].text.lower.startswith('sign'))
        rv.append(not no_sig)
    return rv