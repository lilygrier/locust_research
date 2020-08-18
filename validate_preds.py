import spacy
import pandas as pd
from fuzzywuzzy import fuzz
from dateutil.relativedelta import relativedelta



def make_merged_df(df):
    '''
    Creates a dataframe with forecast and situations aligned.
    '''

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

def results_by_sentence(pred, sit_1, sit_2, match_type='general_type'):
    '''
    If anything in the prediction sentence is correct, returns true.
    '''
    results = []
    situations = []
    for sit in [sit_1, sit_2]:
        if type(sit) == spacy.tokens.doc.Doc:
            for sent in sit.sents:
                situations.extend(get_data(sent, granular=True))
    for sent in pred.sents:
        predictions = get_data(sent, granular=True)
        if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        #print('preds and not sits!!')
        #print(predictions)
            if predictions[0][0].text.lower().startswith('no sign') or (predictions[0][0].text.lower() == 'no' and predictions[0][1].text.lower.startswith('sign')):
                results.append(True)
        else:
            results.append(any(compare_one_granular(prediction, situations, match_type=match_type) for prediction in predictions))
            #for prediction in predictions:
                #results.append(compare_one_granular(prediction, situations, match_type=match_type))

    return results

        

def results_by_place(pred, sit_1, sit_2, match_type='any_locusts'):
    '''
    First pass at accuracy. For each location in which locusts were predicted,
    did locusts appear?
    '''
    
    predictions, situations = get_tuple_list(pred, sit_1, sit_2)
    if predictions and not situations: # case where there is no situation report and pred is nothing significant will happen
        #print('preds and not sits!!')
        #print(predictions)
        if predictions[0][0].text.lower().startswith('no sign') or (predictions[0][0].text.lower() == 'no' and predictions[0][1].text.lower.startswith('sign')):
            return [True]
    pred_locs = {}
    for group, place in predictions:
        #print('place', place)
        #print('type of place', type(place))
        if not place:
            place_name = ''
        else:
            place_name = place.text
        if place_name in pred_locs:
            pred_locs[place_name].append(group)
        else:
            pred_locs[place_name] = [group]
    sit_locs = {}
    for group, place in situations:
        if not place:
            place_name = ''
        else:
            place_name = place.text
        if place_name in sit_locs:
            sit_locs[place_name].append(group)
        else:
            sit_locs[place_name] = [group]
    results = []
    #print('pred dict: ', pred_locs)
    #print('sit dict: ', sit_locs)
    for place, pred_list in pred_locs.items():
        #print('place is: ', place)
        result = False
        if not place:
            #print("not place is: ", place)
            for pred in pred_list:
                for sit_list in sit_locs.values():
                    #print('pred is: ', pred)
                    #print('sit is: ', sit_list)
                    if any(compare_predictions(pred, sit, match_type) for sit in sit_list):
                        #print('in common!')
                        result = True
                        break
                else:
                    continue
                break
        elif place in sit_locs:
            #print('place is in sit_locs. Entering loop')
            for pred in pred_locs[place]:
                poss_sits = sit_locs[place]
                if '' in sit_locs:
                    poss_sits.extend(sit_locs[''])
                if any(compare_predictions(pred, sit, match_type) for sit in poss_sits):
                    result = True
                    break
        results.append(result)
        #print('results', result)
    #print(results)
    return results

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

def granular_corroborate(pred, sit_1, sit_2, match_type='general_type'):
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
            return [True]
    for pred in predictions:
        #print('pred: ', pred)
        results.append(compare_one_granular(pred, situations, match_type=match_type))
        #print('result: ', compare_one_granular(pred, situations, match_type=match_type))
    return results


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



def compare_one_granular(pred, situations, match_type='general_type'):
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
        if not (pred[1] and sit[1]) or fuzz.token_set_ratio(pred[1], sit[1]) == 100: # deal with not sit[1] separately
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



def corroborate(pred, sit_1, sit_2):
    '''
    First pass at corroborating predictions.
    Simply checks if any locust groups/predictions/behaviors end up in forecasted locations.
    '''
    results = []
    predictions = [get_data(sent) for sent in pred.sents]
    print('sit 1 is: ', sit_1)
    print('type of sit1 is: ', type(sit_1))
    if sit_1:
        situations = [get_data(sent) for sent in sit_1.sents]
    else:
        situations = []
    if sit_2:
        situations.extend([get_data(sent) for sent in sit_2.sents if sit_2])
    if not situations:
        #print('no sits, pred is: ', predictions[0][2][0][0].text.lower())
        if predictions[0][2][0][0].text.lower() == 'no':
            return [True]
    for pred in predictions:
        results.append(check_one_pred(pred, situations))
        #print('pred: ', pred)
        #print('result: ', check_one_pred(pred, situations))
    return results



def check_one_pred(pred_list, sits):
    '''
    Validates a single sentence of a prediction against ALL situations.
    '''
    #for pred_list in preds:
    if sits:
        for sit_list in sits:
            #print('locs compared: ', compare_locs(pred_list, sit_list))
            if compare_locs(pred_list, sit_list) or not (pred_list[0] and sit_list[0]):
                if compare_groups(pred_list, sit_list) or compare_behaviors(pred_list, sit_list):
                    return True
    #else:
        #print('no sits')
    return False


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