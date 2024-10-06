import pandas as pd
import requests
import json
import sys
import os
from time import time
from functools import wraps
from dateutil import parser
from datetime import datetime, timedelta
from src.constants import constant
from . import common

class GetOutOfLoop(Exception):
    pass

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
    json_data = None

    # token_list, len_tokens = tokens()
    len_tokens = len(token_list)
    try:
        ct = ct % len_tokens
        headers = {'Authorization': 'Bearer {}'.format(token_list[ct])}
        request = requests.get(url, headers=headers)
        json_data = json.loads(request.content)
        ct += 1
    except Exception as e:
        print(e)
        print("Error in func: [get_response]...")
    return json_data, ct


def api_request(url, token):
    '''Takes the URL for the request and token
    Examples:
        >> apiRequest("https://github.com/linkedin", "xxxxxxxx")
    Args:
        url (String): the url for the request
        token (String): GitHub API token
    Return:
        response body of the request on json format
    '''
    header = {'Authorization': 'token %s' % token}
    response = requests.get(url, headers=header)
    try:
        json_response = json.loads(response.content)
        return json_response
    except Exception as e:
        return response


def repo_commit_date(repo, date, token_list, ct):
    # start a day before the last commit date
    # start_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") - timedelta(days=1)
    url = f'{constant.GITHUB_API_BASE_URL}{repo}/commits?until={date}'
    sha = ''
    try:
        content_arrays, ct = get_response(url, token_list, ct)
        sha = content_arrays[0]['sha']
    except Exception as e:
        print(e, content_arrays)
        print("Error in func: [repo_commit_date]...")
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
    url = f'{constant.GITHUB_API_BASE_URL}{repo}'
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
    url_ml = f'{constant.GITHUB_API_BASE_URL}{mainline}/compare/{sha_ml}...{fork1[0]}:{sha_vr}'
    try:
        content_arrays_ml, ct = get_response(url_ml, token_list, ct)
        if 'commits' in content_arrays_ml:
            commits = content_arrays_ml['commits'][0]
            if diverge_date == '':
                diverge_date = commits['commit']['committer']['date']
        else:
            if diverge_date == '':
                diverge_date = fork_date

        ahead = content_arrays_ml['ahead_by']
        behind = content_arrays_ml['behind_by']

    except Exception as e:
        print(f'{constant.GITHUB_API_BASE_URL}{mainline}/compare/{sha_ml}...{fork1[0]}:{sha_vr}')
        print("Error in func: [divergence_date]...: ", e)

    return fork_date, diverge_date, least_date, ahead, behind, ct


def get_commits_ahead(mainline, fork, compare_token):
    """
    Get the commits that the mainline is ahead of the variant

    Examples:
        >> get_commits_ahead(mainline, fork)
    Args:
        mainline (String): the mainline author/repo
        fork (String): the fork author/repo 
        commitToken (String): the token used for constructing the compareUrl
        compareToken (String): the token used for comparing mainline and fork
    
    Return:
        List of commits a head 
    """  

    compare_url = f"{constant.GITHUB_API_BASE_URL}{fork}/compare/master...{mainline.split('/')[0]}:master"
    json_commits = api_request(compare_url, compare_token)

    return json_commits["commits"]


def find_file(filename, repo, token, sha):
    """
    find_file(filename, repo)
    Check if the file exists in the other repository
    
    Args:
        filename (String): the filename (including path) to be checked for existence
        repo (String): the repository in which the existence of the file must be checked
        token (String): the token for the api request
        sha (String): the GitHub sha
    """
    request_url = f"{constant.GITHUB_API_BASE_URL}{repo}/contents/{filename}?ref={sha}"
    response = api_request(request_url,token) 
    try:
        if response['path']:
            return True
        else:
            return False
    except Exception as e:
        return False


def file_name(name):
    """
    file_name(name)
    Extract the file name used for storing the file
    
    Args:
        name (String): the patch retrieved from the commit api for the file
    """
    if name.startswith('.'):
        return (name[1:])
    elif '/' in name:
        return(name.split('/')[-1])
    elif '/' not in name:
        return(name)
    else: 
        sys.exit(1)


def file_dir(name):
    if name.startswith('.'):
        return (name[1])
    elif '/' in name:
        return(name.split('/')[:-1])
    elif '/' not in name:
        return ''
    else: 
        sys.exit(1)
    

def get_patch(file, storageDir, fileName):
    # Not in use at the moment
    """
    get_patch(url, token)
    Send a request to the github api to find retrieve the patch of a commit and saves it to a .patch file
    
    Args:
        file (String): the patch file
        storageDir (String): the storage directory
        fileName (String): the file name of the patch to be saved
    """
    if not os.path.exists(storageDir):
        os.makedirs(storageDir)
        f = open(storageDir + fileName, 'w')
        f.write(file)
        f.close()
    else:
        f = open(storageDir + fileName, 'w')
        f.write(file)
        f.close()

def save_file(file, storageDir, fileName):
    if not os.path.exists(storageDir):
        os.makedirs(storageDir)
        f = open(storageDir + fileName, 'xb')
        f.write(file)
        f.close()
    else:
        f = open(storageDir + fileName, 'wb')
        f.write(file)
        f.close()


def get_file_type(file_path):
    '''
    Guess a file type based upon a file extension (mimetypes module)

    Args:
        file_path (String): the file path
    Return:
        magic_ext
    '''
    ext = file_path.split('.')[-1]
    magic_ext = None

    if ext == 'c' or ext == 'h':
        magic_ext = common.FileExt.C
    elif ext == 'java':
        magic_ext = common.FileExt.Java
    elif ext == 'sh':
        magic_ext = common.FileExt.ShellScript
    elif ext == 'pl':
        magic_ext = common.FileExt.Perl
    elif ext == 'py':
        magic_ext = common.FileExt.Python
    elif ext == 'php':
        magic_ext = common.FileExt.PHP
    elif ext == 'rb':
        magic_ext = common.FileExt.Ruby
    else:
        magic_ext = common.FileExt.Text
    return magic_ext 


def get_first_last_commit(repo, pullrequest, token_list, ct):
    '''
    Retrieve the first and the last commit of a pull request
    
    Args:
        pr_commits (String): List of commits in a pull request
    Return:
        The frist and last commit
    '''
    commits = []
    page_number = 1
    try:
        while True:
            url = f"{constant.GITHUB_API_BASE_URL}{repo}/pulls/{pullrequest}/commits?page={str(page_number)}&per_page=100"
            page_number = page_number + 1

            pullrequest_commits, ct = get_response(url, token_list, ct)

            if pullrequest_commits is None:
                break
            for commit in pullrequest_commits:
                commit_sha = commit['sha']
                commits.append(commit_sha)
    except GetOutOfLoop:
        print("Stopping data extraction in func: [get_first_last_commit]....")

    first_commit = commits[0]
    last_commit = commits[-1]

    return first_commit, last_commit


def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kwargs, te - ts))
        return result

    return wrap