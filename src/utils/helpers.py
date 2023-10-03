import pandas as pd
import requests
import json
from dateutil import parser
from datetime import datetime, timedelta
from constants import constant

def unique(list):
    unique_list = pd.Series(list).drop_duplicates().to_list()
    return unique_list

def get_response(url, token_list, ct):
    '''get content of the requested endpoint

    Args:
        url (String): url of the request
        token_list (list): GitHub API token list
        ct (int): token counter
    
    Return:
        Jsondata (object): json data 
    '''
    jsonData = None

    # token_list, len_tokens = tokens()
    len_tokens = len(token_list)
    try:
        ct = ct % len_tokens
        headers = {'Authorization': 'Bearer {}'.format(token_list[ct])}
        request = requests.get(url, headers=headers)
        jsonData = json.loads(request.content)
        ct += 1
    except Exception as e:
        print(e)
    return jsonData, ct


def repo_commit_date(repo, date, token_list, ct):
    # start a day before the last commit date
    start_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") - timedelta(days=1)
    url = f'{constant.GITHUB_BASE_URL}{repo}/commits?since={start_date}'
    try:
        content_arrays, ct = get_response(url, token_list, ct)
        sha = ''
        sha = content_arrays[0]['sha']
    except Exception as e:
        print(e)
    # commit_date = content_arrays[0]['commit']['committer']['date']
    return sha, ct


def repo_dates(repo, token_list, ct):
    '''get the repo creation date and date of last update

    Args:
        repo (String): the name of the repo e.g. apache/kafka
        token_list (list): GitHub API token list
        ct (int): token counter
    
    Return:
        created_at: 
        updated_at:
        ct:
    '''
    created_at = ''
    updated_at = ''
    url = f'{constant.GITHUB_BASE_URL}{repo}'
    # print(url)
    content_arrays, ct = get_response(url, token_list, ct)
    if content_arrays is not None:
        created_at = content_arrays['created_at'] # format: 0000-00-00T00:00:00Z
        updated_at = content_arrays['updated_at']
    return created_at, updated_at, ct


def divergence_date(mainline, variant, token_list, ct, least_date='', diverge_date=''):
    # least_date a.k.a cut off date
    ahead = 0
    behind = 0
    created_ml, date_ml, ct = repo_dates(mainline, token_list, ct)
    fork_date, date_vr, ct = repo_dates(variant, token_list, ct)

    date_ml1 = parser.parse(date_ml) #format: 0000-00-00 00:00:00+00:00
    date_vr1 = parser.parse(date_vr)

    if least_date == '':
        if date_ml1 < date_vr1:
            least_date = date_ml
        else:
            least_date = date_vr

    sha_vr, ct = repo_commit_date(variant, least_date, token_list, ct)
    sha_ml, ct = repo_commit_date(mainline, least_date, token_list, ct)

    fork1 = variant.split('/') # linkeIn/kafka = linkedin; gets the username
    url_ml = f'{constant.GITHUB_BASE_URL}{mainline}/compare/{sha_ml}...{fork1[0]}:{sha_vr}'
    try:
        content_arrays_ml, ct = get_response(url_ml, token_list, ct)
        commits = content_arrays_ml['commits'][0]
        if diverge_date == '':
            diverge_date = commits['commit']['committer']['date']
        ahead = content_arrays_ml['ahead_by']
        behind = content_arrays_ml['behind_by']

    except:
        print(f'{constant.GITHUB_BASE_URL}{mainline}/compare/{sha_ml}...{fork1[0]}:{sha_vr}')

    return fork_date, diverge_date, least_date, ahead, behind, ct