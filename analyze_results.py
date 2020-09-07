import pandas as pd
import numpy as np
import extract_info
import validate_preds
import seaborn as sns
import matplotlib.pyplot as plt

'''
Analyze results of predictions.
'''

def gen_merged_df(df):
    '''
    Takes a dataframe and creates a merged dataframe through self-joins
    such that a forecast is matched up to its two corresponding situations.
    Converts situation and forecast text to nlp objects.
    Inputs:
        df: a Pandas dataframe where each row represents a country 
            in a particular month
    Returns:
        a merged dataframe!
    '''
    df = extract_info.get_snippets(df, 'SITUATION')
    df = extract_info.get_snippets(df, 'FORECAST')
    df = extract_info.prelim_cleaning(df)
    return validate_preds.make_merged_df(df)
     


def gen_results_df(df, loc_matching=False):
    '''
    Creates a dataframe with a columns containing results corresponding to 
    the different prediction methods.
    Inputs:
        df: a Pandas dataframe where forecasts are paired with corresponding situations
        loc_matching (bool): whether or not to use location-matching trees
    Returns:
        a dataframe with columns containing results
    '''
    
    df['most_gran_data'] = df.apply(lambda x: validate_preds.granular_corroborate(x.FORECAST, x.SIT_1, x.SIT_2, match_type='exact'), axis=1)
    df['most_gran_results'] = df['most_gran_data'].apply(lambda most_gran_data: most_gran_data[0])
    df['most_gran_results_sig_preds'] = df['most_gran_data'].apply(lambda most_gran_data: most_gran_data[1])
    df['most_gran_results_pct_true'] = df.apply(lambda x: validate_preds.percent_result_type(x.most_gran_results, True), axis=1)
    df['most_gran_results_pct_false'] = df.apply(lambda x: validate_preds.percent_result_type(x.most_gran_results, False), axis=1)
    df['most_gran_results_pct_no_match'] = df.apply(lambda x: validate_preds.percent_result_type(x.most_gran_results, "Unknown"), axis=1)

    df['any_by_place_data'] = df.apply(lambda x: validate_preds.results_by_place(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['any_by_place'] = df['any_by_place_data'].apply(lambda any_by_place_data: any_by_place_data[0])
    df['any_by_place_sig_preds'] = df['any_by_place_data'].apply(lambda any_by_place_data: any_by_place_data[1])
    df['any_by_place_pct_true'] = df.apply(lambda x: validate_preds.percent_result_type(x.any_by_place, True), axis=1)
    df['any_by_place_pct_false'] = df.apply(lambda x: validate_preds.percent_result_type(x.any_by_place, False), axis=1)
    df['any_by_place_pct_no_match'] = df.apply(lambda x: validate_preds.percent_result_type(x.any_by_place, "Unknown"), axis=1)
    
    df['sentence_by_gen_stage_data'] = df.apply(lambda x: validate_preds.results_by_sentence(x.FORECAST, x.SIT_1, x.SIT_2), axis=1)
    df['sentence_by_gen_stage'] = df['sentence_by_gen_stage_data'].apply(lambda sentence_by_gen_stage_data: sentence_by_gen_stage_data[0])
    df['sentence_by_gen_stage_sig_preds'] = df['sentence_by_gen_stage_data'].apply(lambda sentence_by_gen_stage_data: sentence_by_gen_stage_data[1])
    df['sentence_by_gen_stage_pct_true'] = df.apply(lambda x: validate_preds.percent_result_type(x.sentence_by_gen_stage, True), axis=1)
    df['sentence_by_gen_stage_pct_false'] = df.apply(lambda x: validate_preds.percent_result_type(x.sentence_by_gen_stage, False), axis=1)
    df['sentence_by_gen_stage_pct_no_match'] = df.apply(lambda x: validate_preds.percent_result_type(x.sentence_by_gen_stage, "Unknown"), axis=1)

    return df

def add_totals(df, loc_matching=False):
    '''
    Adds columms to dataframe with totals of true, false, and 
    "no match" for each validation methodology.
    Inputs:
        df: a Pandas dataframe
        loc_matching (bool): whether locations should be verified 
            using a specified location tree
    Returns:
        a dataframe with columns added for result total counts
    '''
    df['total_true_any'] = df.apply(lambda x: count_true(x.any_by_place), axis=1)
    df['total_no_match_any'] = df.apply(lambda x: count_no_match(x.any_by_place), axis=1)
    df['total_false_any'] = df.apply(lambda x: count_false(x.any_by_place), axis=1)

    df['total_true_gen'] = df.apply(lambda x: count_true(x.sentence_by_gen_stage), axis=1)
    df['total_no_match_gen'] = df.apply(lambda x: count_no_match(x.sentence_by_gen_stage), axis=1)
    df['total_false_gen'] = df.apply(lambda x: count_false(x.sentence_by_gen_stage), axis=1)

    df['total_true_exact'] = df.apply(lambda x: count_true(x.most_gran_results), axis=1)
    df['total_no_match_exact'] = df.apply(lambda x: count_no_match(x.most_gran_results), axis=1)
    df['total_false_exact'] = df.apply(lambda x: count_false(x.most_gran_results), axis=1)

    return df

def confusion_matrix(df, results_col, sig_preds_col):
    '''
    Analyzes false and true positives and negatives.
    Inputs:
        df: a Pandas dataframe where forecasts are paired with corresponding situations
        results_col (str): name of column containing results of interest
        sig_preds_col (str): name of column indicating whether significant 
            events were predicted
        Returns:
            None, but displays a confusion matrix heat map analyzing results
    '''
    pred_correct = np.concatenate(df[results_col].reset_index(drop=True))
    pred_sig_pred = np.concatenate(df[sig_preds_col].reset_index(drop=True)) 
    conf_matrix = pd.crosstab(pred_sig_pred, pred_correct, rownames=['sig. event predicted'], 
                                colnames=['pred result'])
    sns.heatmap(conf_matrix, annot=True, fmt='d')

def raw_counts_graph(df):
    '''
    Displays a set of time series graphs of prediction accuracy.
    Inputs:
        df: a Pandas dataframe
    '''
    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(10, 10))
    df.groupby('YEAR').total_true_any.sum().plot(ax=axes[0])
    df.groupby('YEAR').total_false_any.sum().plot(ax=axes[0])
    df.groupby('YEAR').total_no_match_any.sum().plot(ax=axes[0])

    df.groupby('YEAR').total_true_gen.sum().plot(ax=axes[1])
    df.groupby('YEAR').total_false_gen.sum().plot(ax=axes[1])
    df.groupby('YEAR').total_no_match_gen.sum().plot(ax=axes[1])

    df.groupby('YEAR').total_true_exact.sum().plot(ax=axes[2])
    df.groupby('YEAR').total_false_exact.sum().plot(ax=axes[2])
    df.groupby('YEAR').total_no_match_exact.sum().plot(ax=axes[2])
    plt.setp(axes, ylim=(0, 1450))
    axes[0].set(ylabel='any locusts by location')
    axes[1].set(ylabel='general stage by sentence')
    axes[2].set(ylabel='exact match - granular')
    plt.suptitle('Total Prediction Counts by Type')

def percent_type_graph(df):
    '''
    Displays a graph of the percent of total predictions by type.
    Inputs:
        df: a Pandas dataframe
    '''
    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(10, 10))
    df.groupby('YEAR').any_by_place_pct_true.mean().plot(ax=axes[0])
    df.groupby('YEAR').any_by_place_pct_false.mean().plot(ax=axes[0])
    df.groupby('YEAR').any_by_place_pct_no_match.mean().plot(ax=axes[0])

    df.groupby('YEAR').sentence_by_gen_stage_pct_true.mean().plot(ax=axes[1])
    df.groupby('YEAR').sentence_by_gen_stage_pct_false.mean().plot(ax=axes[1])
    df.groupby('YEAR').sentence_by_gen_stage_pct_no_match.mean().plot(ax=axes[1])

    df.groupby('YEAR').most_gran_results_pct_true.mean().plot(ax=axes[2])
    df.groupby('YEAR').most_gran_results_pct_false.mean().plot(ax=axes[2])
    df.groupby('YEAR').most_gran_results_pct_no_match.mean().plot(ax=axes[2])
    plt.setp(axes, ylim=(0, 1.0))
    axes[0].set(ylabel='any locusts by location')
    axes[1].set(ylabel='general stage by sentence')
    axes[2].set(ylabel='exact match - granular')
    axes.legend()
    plt.suptitle('Percent of Total Predictions by Type')


def count_true(results_list):
    '''
    Gives a raw count of true predictions.
    Inputs:
        results_list: a list of prediction results
    '''
    return sum([result for result in results_list if result == True])

def count_no_match(results_list):
    '''
    Gives a raw count of predictions resulting in "unknown."
    Inputs:
        results_list: a list of prediction results
    '''
    return len([result for result in results_list if type(result) == str and result.startswith("Unknown")])

def count_false(results_list):
    '''
    Gives a raw count of false predictions.
    Inputs:
        results_list: a list of prediction results
    '''
    return len([result for result in results_list if result == False])





