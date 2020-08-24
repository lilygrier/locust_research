import pandas as pd
import extract_info
import validate_preds

'''
Analyze results of predictions.
'''

df = pd.read_csv("report_text_2.csv")

def gen_merged_df(df):
    df = extract_info.get_snippets(df, 'SITUATION')
    df = extract_info.get_snippets(df, 'FORECAST')
    df = extract_info.prelim_cleaning(df)
    return validate_preds.make_merged_df(df)
     


def gen_results_df(df):


    df['most_gran_results'] = df.apply(lambda x: validate_preds.granular_corroborate(x.FORECAST, x.SIT_1, x.SIT_2, match_type='exact'), axis=1)
    df['most_gran_results_pct'] = df.apply(lambda x: validate_preds.percent_true(x.most_gran_results), axis=1)
    df['any_by_place'] = df.apply(lambda x: validate_preds.results_by_place(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['any_by_place_pct'] = df.apply(lambda x: validate_preds.percent_true(x.any_by_place), axis=1)
    df['sentence_by_gen_stage'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['sent_by_gen_stage_pct'] = df.apply(lambda x: validate_preds.percent_true(x.sentence_by_gen_stage), axis=1)

    return df

def any_true(results_list):
    return any(result == True for result in results_list)


def count_true(results_list):
    '''
    Gives a raw count of true predictions.
    '''
    return sum([result for result in results_list if result == True])

def count_false_no_match(results_list):
    return len([result for result in results_list if result == "False - No match"])

def count_false(results_list):
    '''
    count all false, including no match
    '''
    return len([result for result in results_list if result != True])



