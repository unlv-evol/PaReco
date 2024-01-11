import pandas as pd
import requests
import json
import sys
import os
from time import time
from functools import wraps
from dateutil import parser
from datetime import datetime, timedelta
from constants import constant
from . import common

class GetOutOfLoop(Exception):
    pass

def unique(list):
    unique_list = pd.Series(list).drop_duplicates().to_list()
    return unique_list

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
    elif ext == 'js':
        magic_ext = common.FileExt.JavaScript
    elif ext == 'ts':
        magic_ext = common.FileExt.TypeScript
    else:
        magic_ext = common.FileExt.Text
    return magic_ext 


def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kwargs, te - ts))
        return result

    return wrap