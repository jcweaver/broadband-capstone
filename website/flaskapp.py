# from flask import Flask, render_template
# app = Flask(__name__)

# @app.route("/")
# def flaskapp():
#     file="about9.jpg"
#     return render_template("flaskapp.html",file=file)

# if __name__ == "__main__":
#     app.run()

import flask
import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64 #needed for images

df = pd.read_csv("/groups/broadband_impact/flaskapp/static/all_data.csv", converters = {"tract_geoid" : lambda x: str(x)})

## Models dictionary
models = {}

# Use pickle to load in the pre-trained model.
with open(f'/groups/broadband_impact/flaskapp/static/rf_hi_model.pkl', 'rb') as f:
    models['pct_health_ins_19_64'] = pickle.load(f)

with open(f'/groups/broadband_impact/flaskapp/static/emp_rate_rf_user_exp_2.pkl', 'rb') as f:
    try:    
        models['employment_rate'] = pickle.load(f)
    except Exception as e:
        print("broadband_impact failed to read employment model", e)
        models['employment_rate'] = models['pct_health_ins_19_64']

with open(f'/groups/broadband_impact/flaskapp/static/poverty_rate_random_forest_2.sav', 'rb') as f:
    #print("broadband_impact", "opened file but did not load yet")
    models['poverty_rate'] = pickle.load(f) 

with open(f'/groups/broadband_impact/flaskapp/static/education_xgb_model_final_2.pkl', 'rb') as f:
        models['pct_pop_hs+'] = pickle.load(f) 


## Global model variable dictionary
model_vars = {
    'pct_health_ins_19_64' : ['pct_only_cellular', 'pct_internet_broadband_fiber',
 'pct_computing_device_with_broadband', 'pct_internet_broadband_satellite',
 'pct_computing_device', 'Ookla Median Download Speed (Mbps)',
 'pct_internet_broadband_any_type', 'pct_internet',
 'Wired_Provider_Count_100', 'pct_only_smartphone', 'pct_hisp_latino',
 'pct_pop_income_gt_100k', 'pct_pop_foreign_born', 'ave_family_size',
 'log_median_house_value', 'median_house_value', 'pct_white',
 'log_median_income', 'pct_pop_hs+', 'median_income', 'ATT_present',
 'employment_rate', 'ave_household_size', 'pct_pop_some_college',
 'population_density'],

     'employment_rate' : ['pct_only_cellular', 'pct_internet_broadband_fiber',
 'pct_computing_device_with_broadband', 'pct_internet_broadband_satellite',
 'pct_computing_device', 'Ookla Median Download Speed (Mbps)',
 'pct_internet_broadband_any_type', 'pct_internet',
 'Wired_Provider_Count_100', 'pct_only_smartphone', 'pct_hisp_latino',
 'pct_pop_income_gt_100k', 'pct_pop_foreign_born', 'ave_family_size',
 'log_median_house_value', 'median_house_value', 'pct_white',
 'log_median_income', 'pct_pop_hs+', 'median_income', 'ATT_present',
 'employment_rate', 'ave_household_size', 'pct_pop_some_college',
 'population_density'],


 'pct_pop_hs+' : ['pct_computing_device_with_broadband',
 'pct_pop_income_gt_100k',
 'pct_pop_gt_200k',
 'pct_only_smartphone',
 'pct_desktop_or_laptop',
 'Primary RUCA Code - 1.0',
 'pct_internet',
 'ave_family_size',
 'pct_tablet',
 'pct_computing_device',
 'pct_internet_broadband_any_type',
 'pct_hisp_latino',
 'Secondary RUCA Code - 1.0',
 'ave_household_size',
 'All_Provider_Count_25',
 'All_Provider_Count_100',
 'Ookla Median Download Speed (Mbps)',
 'log_median_income',
 'ruca_metro',
 'ruca_rural',
 'log_median_income_over_log_median_house',
 'pct_pop_foreign_born',
 'pct_pop_disability'],

 'poverty_rate' : ['pct_internet', 'pct_computing_device_with_broadband', 
 'median_age_overall',
'pct_white',
'employment_rate',
'pct_pop_20_to_24',
'pct_pop_disability',
'pct_only_cellular',
'pct_internet_broadband_satellite',
'pct_computing_device',
'Ookla Median Download Speed (Mbps)',
'pct_internet_broadband_any_type',
'Wired_Provider_Count'],

# 'employment_rate' : ['pct_internet', 
#                 'pct_only_cellular',
#                 'pct_computing_device_no_internet',
#               'pct_internet_broadband_satellite',
#               'pct_computing_device_with_broadband',
#               'log_median_income',  'pct_pop_foreign_born','pct_pop_lt_10k', 'pct_pop_10k_thru_15k',
#               'pct_internet_broadband_any_type','pct_ages_lt_19', 'Wired_Provider_Count', 'pct_computing_device',
#               'Ookla Median Download Speed (Mbps)','poverty_rate', 'pct_pop_80_to_84', 'median_age_male',
#        'pct_pop_bachelors+', 'pct_pop_75_to_79', 'ave_household_size',
#        'pct_pop_70_to_74', 'pct_pop_income_lt_30k', 'pct_pop_25_to_29','pct_pop_15_to_19',
#        'median_age_female', 'pct_pop_ged', 'pct_ages_gt_50',
#        'pct_pop_disability', 'pct_pop_30_to_34', 'median_age_overall'],
}

def get_dataframe(outcome, tract_data):
    """
    Returns a dataframe with columns for all input variables used in the model to generate the outcome
    """
    print("broadband_impact outcome", outcome)
    df_outcome = pd.DataFrame()
    for var in model_vars[outcome]:
        #print("broadband_impact var", var)
        df_outcome[var] = tract_data[var]
    return df_outcome
 
app = flask.Flask(__name__, template_folder='/groups/broadband_impact/flaskapp/templates/')
app.debug = True

@app.route('/tool', methods=['GET', 'POST'])
def flaskapp():
    if flask.request.method == 'GET':
        return(flask.render_template('main_copy.html'))
    
    if flask.request.method == 'POST':
        tract = str(flask.request.form['form_tract'])
        pct_internet = flask.request.form['pct_internet']
        pct_computing_device = flask.request.form['pct_computing_device']
        pct_computing_device_with_broadband = flask.request.form['pct_computing_device_with_broadband']
        ookla_download = flask.request.form['ookla_download']
        pct_internet_broadband_any_type = flask.request.form['pct_internet_broadband_any_type']
        
        print("broadband_impact", "tract", tract)

        ## Generate a dictionary to contain result predictions
        results = {}

        ##Filter to data of just the tract
        tract_data = df.loc[df['tract_geoid'] == tract]

        print("broadband_impact",tract_data)

        ## Pop estimates TODO
        pop_estimates = {}
        total_pop = tract_data['total_population'].values[0]

        ##Iterate through outcomes
        for outcome_var in ['poverty_rate', 'pct_pop_hs+', 'employment_rate', 'pct_health_ins_19_64']:

            ## Update model df with toggle-able form variables
            input_variables = get_dataframe(outcome_var, tract_data)
            input_variables['pct_internet'] = float(pct_internet)
            input_variables['pct_computing_device'] = float(pct_computing_device)
            input_variables['pct_computing_device_with_broadband'] = float(pct_computing_device_with_broadband)
            input_variables['Ookla Median Download Speed (Mbps)'] = float(ookla_download)
            input_variables['pct_internet_broadband_any_type'] = float(pct_internet_broadband_any_type)

            ## Generate prediction
            print("broadband_impact", input_variables)
            prediction = models[outcome_var].predict(input_variables)[0]
            results[outcome_var] = round(prediction, 2)
            pop_estimates[outcome_var] = "{:,}".format(round(total_pop * prediction))

        
        ##Set up orig_data with original values
        orig_data = {'pct_health_ins_19_64' : round(tract_data['pct_health_ins_19_64'].values[0],2),
         'employment_rate' : round(tract_data['employment_rate'].values[0],2),
        'pct_pop_hs+' : round(tract_data['pct_pop_hs+'].values[0],2), 
        'poverty_rate' : round(tract_data['poverty_rate'].values[0],2)}
       

        return flask.render_template('main_copy.html',
                                    #  original_input={
                                    #                 'Percent using the internet':pct_internet,
                                    #                  'Percent using a computing device':pct_computing_device,
                                    #                  'Median download speed':ookla_download,
                                    #                  'Median upload speed':ookla_upload
                                    #              },
                                                 old_input = {
                                                    'pct_internet':pct_internet,
                                                     'pct_computing_device':pct_computing_device,
                                                     'ookla_download':ookla_download,
                                                     'pct_computing_device_with_broadband' : pct_computing_device_with_broadband,
                                                     'pct_internet_broadband_any_type' : pct_internet_broadband_any_type,
                                                     'form_tract' : str(tract)
                                                     #'display_tract' : df.loc[df["tract_geoid"]==tract, 'NAME'].values[0]
                                                 }, result = results, current = orig_data, pop_estimates = pop_estimates)

@app.route('/')
def about():   
    return(flask.render_template('about.html'))

@app.route('/team')
def team():   
    return(flask.render_template('team.html'))

@app.route('/technical')
def technical(): 
    return(flask.render_template('technical.html'))

@app.route('/data-explorer', methods=['GET', 'POST'])
def explorer():
     ## According to: https://towardsdatascience.com/python-plotting-api-expose-your-scientific-python-plots-through-a-flask-api-31ec7555c4a8
    ## Need to convert image to bytes and use this process
    # sns.heatmap(corr)
    # bytes_image = io.BytesIO()
    # plt.savefig(bytes_image, format='png')
    # bytes_image.seek(0)
    # plot_url = base64.b64encode(bytes_image.getvalue()).decode('utf8')


    df_temp = df.drop(columns= ['tract', 'state', 'county', 'tract_geoid'])

    corr = df_temp.corr()

    #Get the columns in the df and remove a few not relevant to show in the correlations
    corr_cols = df_temp.columns.to_list()

    if flask.request.method == 'GET':
        return(flask.render_template('explorer_copy.html', variables = corr_cols))
    
    if flask.request.method == 'POST':
        y_variable = flask.request.form['y_variable']
        #print("broadband_impact", y_variable)
        y_corr = corr[y_variable]


        ## Note can send a table to tables
        return(flask.render_template('explorer_copy.html', variables = corr_cols, 
        tables=[pd.DataFrame(y_corr.sort_values()).to_html(classes=['data', 'table-dark'], header="true")]))

if __name__ == "__main__":
    app.run()

