import os
import requests
import csv
import json
import sys
import re
import time
from collections import defaultdict
import bitarray
import re
import time
import mimetypes
    
from utils import common
from utils.helpers import api_request
from constants import constant
from . import patchLoader as patchloader
from . import sourceLoader as sourceloader

try:
    import argparse
    import magic
except ImportError as err:
    print (err)
    sys.exit(-1)


def get_commits_ahead(mainline, fork, commit_token, compare_token):
    """
    Get the commits that the mainline is ahead of the variant

    Examples:
        >> getCommitsAhead(mainline, fork)
    Args:
        mainline (String): the mainline author/repo
        fork (String): the fork author/repo 
        commitToken (String): the token used for constructing the compareUrl
        compareToken (String): the token used for comparing mainline and fork
    
    Return:
        List of commits a head 
    """  

    compare_url = f"{constant.GITHUB_BASE_URL}{fork}/compare/master...{mainline.split('/')[0]}:master?access_token={compare_token}"
    json_commits = api_request(compare_url)

    return json_commits["commits"]


def get_commit_files(commit, commit_token):
    """Get the files for each commit

    Args:
        commit (String): the commits for which files need to be retrieved
        getCommitToken (String): the token used for the qpi request to get the commit
    
    commitFilesDict={
        "sha": {
            "commitUrl": url
            "files": list(file 1, file 2, ... , file n)
        }
        
    }
    """ 
    commitFilesDict = {}
    sha = commit["sha"]
    commitUrl = commit['url']

    commitFilesDict[sha] = {}
    commitFilesDict[sha]["commitUrl"] = commitUrl
    commitFilesDict[sha]["files"] = list()

    commit = api_request(f'{commitUrl}?access_token={commit_token}')

    return commit

def find_file(filename, repo, token, sha):
    """
    findFile(filename, repo)
    Check if the file exists in the other repository
    
    Args:
        filename (String): the file path to be checked for existence
        repo (String): the repository in which the existence of the file must be checked
        token (String): the token for the api request
        sha (String): the GitHub sha
    """
    request_url = f"{constant.GITHUB_BASE_URL}{repo}/contents/{filename}?ref={sha}"
    response = api_request(request_url,token) 
    path = ''
    try:
        path = response['path']
        return True
    except Exception as e:
        return False


def file_name(name):
    """
    fileName(name)
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