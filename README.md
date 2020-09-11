# locust_research
This project examined monthly locust bulletins produced by the UN. Each bulletin contains a country-level situation report and 
forecasted predcitions. I used the spaCy NLP library to analyze the text and confirm the the accuracy of the UN predictions based on varying definitions of correctness.
## Guide to files  
### Getting the Data
  
`scraping.py` - code used to scrape locust bulletins from FAO website and save to machine  
  
`get_text.py` - code used to extract text from PDFs  
  
`make_df.py` - code used to parse text into dataframe. Downloads CSV to machine.  

### Using the Data
  
`extract_info.py` - code used to extract information from text through natural language processing  
  
`validate_preds.py` - code used for prediction validation  
  
### Analyzing the Data
  
`analyze_results.py` - code used to produce summary visualizations  
  
`location_matching.py` - code used to produce dataframe of unmatched locations  
  
`location_bank.py` - sample code used to show idea of possible location-matching technique
  
## How to Use
If you were starting from scratch, running scraping.py in the command line will scrape the web for the locust bulletins and save them on your machine. To extract text into a csv, 
you would run run make_df.py in the command line. However, I saved the resulting CSV from these steps as report_text.csv.  

Running `analyze_results.df_with_validated_results()` will call files needed to extract information and validate predictions through natural language processing. To generate the graphs used in my report, I ran the following functions, where df was the result of calling `analyze_results.df_with_validated_results()`:  
  
`analyze_results.confusion_matrix(df, 'any_by_place', 'any_by_place_sig_preds')`  
`analyze_results.confusion_matrix(df, 'most_gran_results', 'most_gran_results_sig_preds')`  
`analyze_results.confusion_matrix(df, 'sentence_by_gen_stage', 'sentence_by_gen_stage_sig_preds')`  
`analyze_results.raw_counts_graph(df)`  

