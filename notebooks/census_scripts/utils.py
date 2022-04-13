import pandas as pd
import numpy as np
import requests
import yaml
import csv
import re
import pandas as pd
import numpy as np
from functools import reduce
from itertools import chain, repeat
import operator

# Requests
create_session = lambda : requests.Session()


#Need to update to follow API rules as shown here - https://api.census.gov/data/2019/acs/acs5/examples.html

def format_request(endpoint, codes, state):
    base = 'https://api.census.gov/data'
    #Register for a key here: https://api.census.gov/data/key_signup.html
    key = ''
    date = '2019'
    
    codes = f"get=NAME,{','.join(map(str,codes))}"
    
    state = f'in=state:{pad_with_zero(state)}'
    key = f'key={key}'
    
    #bg = 'for=block%20group:*'
    tract = f'for=tract:*'
    args = '&'.join(map(str, [codes, tract, state, key]))
    
    url = f'{base}/{date}/{endpoint}?{args}'
    print(url)
    return url

def make_request(url, session):
    """A wrapper/bracket for making HTTP requests"""
    try:
        req = session.get(url)

        return req
    except Exception as e:
        return e
    

    
def result_to_dataframe(res):
    x = pd.DataFrame(res[1:], columns=res[0])
    return x

        
def collect_results(endpoints, codes, states, session):
    dfs = []
    
    for endpoint in endpoints:
        endpoint_codes = codes[endpoint]
        
        for st in states:
            state = pad_with_zero(st)
            url = format_request(endpoint, endpoint_codes, state)
            df = result_to_dataframe(make_request(url, session).json())
            dfs.append(df)
            
    return dfs
    
    
def small_batch_request(session, endpoint, state, codes):
    """ make small batch requests to the Census API. The limit is 50. This function makes requests of 40."""
        
    try:
        res = result_to_dataframe(make_request(format_request(endpoint, codes, state), session).json())
    except:
        return None 
    
    return res

def small_batch_all(session, endpoints, state, codes):
    """small batch requests are done for each endpoint and then concatenated into a final dataframe."""
    res = small_batch_request(session, endpoints[0], state, codes[endpoints[0]])
    
    for endpoint in endpoints[1:]:
        if type(res) != pd.DataFrame:
            res = small_batch_request(session, endpoint, state, codes[endpoint])
        else:
            tmp = small_batch_request(session, endpoint, state, codes[endpoint])
            
            if type(tmp) == pd.DataFrame:                
                #res = pd.concat([res, tmp], axis=1)
                res = res.merge(tmp, how = "inner", on=["state","tract","county","NAME"])
                
    if type(res) != pd.DataFrame:

        return res
    else:
        pass

    return res   
    
def gather_results(session, endpoints, states, codes, dfs=[], start=0, debug=False):
    """ Main entry point into the execution of a call to the census API. Requires:
    (1) session: requests.Session
    (2) part:  a list of acs_endpoints
    (3) config:   the configuration lambda at the top of this file
    (4) codes: a dictionary of strings of an ACS source (i.e. acs5 or acs5/profile) mapping to a list of string variable names
    (5) state_county: list of valid states and counties
    """
    failure_point = -1
    for i in range(start, len(states)):
        state = states[i]
        try:
            # Reach this is the state-county is valid.
            # we make a bunch of requests and append the results to a list
            tmp = [small_batch_all(session, endpoints, state, codes)]
            #print(tmp)
            list(map(lambda x: tmp.remove(x) if type(x) != pd.DataFrame else x, tmp[:]))
            if len(tmp) != 0:
                dfs.append(tmp)
            print(f"Status: {((i+1)/len(states))*100:.2f}%")
        except:
            # if there is a failure record this index as the failure point and break. Print out the point where the task failed for debugging.
            failure_point = i
            break
    if failure_point == -1:
        df = pd.concat(list(chain(*dfs)), ignore_index=True)
        df = df.fillna(-1)
        return df
    else:
        print(f"The task failed at this point: {failure_point}")
        return 0 
    
            

pad_with_zero =  lambda x : str(x) if len(str(x)) > 1 else "0"+str(x)
