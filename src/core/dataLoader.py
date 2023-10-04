import csv
import difflib
import json
import os
import pickle
import re
import sys
import time
from collections import defaultdict
from pprint import pprint

import bitarray
import requests

from constants import constant
from core import commitLoader as commitloader
from utils import common
from utils.helpers import api_request

try:
    import argparse

    import magic
except ImportError as err:
    print (err)
    sys.exit(-1)

def fetch_pullrequest_data(source, destination, prs, destination_sha, token_list, ct):
    print('Fetching commit information and files from patches...')
    start = time.time()
    req = 0
    pr_data = {}
    lenTokens = len(token_list)
    
    for k in prs:
        try:
            pr_data[k] = {}

            # Get the PR
            if ct == lenTokens:
                ct = 0
            pr_request = f'{constant.GITHUB_BASE_URL}{source}/pulls/{k}'
            pr = api_request(pr_request, token_list[ct])
            ct += 1
            req += 1

            # Get the commit
            if ct == lenTokens:
                ct = 0
            commits_url = pr['commits_url']
            commits = api_request(commits_url, token_list[ct])
            common.verbose_print(f'ct ={ct}')
            ct += 1
            req += 1

            commits_data = {}

            nr_files = pr['changed_files']

            pr_data[k]['pr_url'] = pr_request
            pr_data[k]['commits_url'] = commits_url
            pr_data[k]['changed_files'] = nr_files
            pr_data[k]['commits_data'] = list()
            pr_data[k]['destination_sha'] = destination_sha
            
            for i in commits:
                if ct == lenTokens:
                    ct = 0
                commit_url = i['url']
                commit = api_request(commit_url, token_list[ct])
                ct += 1
                req += 1

                try:
                    files = commit['files']
                    for j in files:
                        status = j['status']
                        file_name = j['filename']
                        added_lines = j['additions']
                        removed_lines = j['deletions']
                        changes = j['changes']
                        file_ext = commitloader.get_file_type(file_name)
                        if file_name not in commits_data:
                            commits_data[file_name] = list()
                            if ct == lenTokens:
                                ct = 0
                            if commitloader.find_file(file_name, destination, token_list[ct], destination_sha):
                                sub = {}
                                sub['commit_url'] = commit_url
                                sub['commit_sha'] = commit['sha']
                                sub['commit_date'] = commit['commit']['committer']['date']
                                sub['parent_sha'] = commit['parents'][0]['sha']
                                sub['status'] =status
                                sub['additions'] = added_lines
                                sub['deletions'] = removed_lines
                                sub['changes'] = changes
                                commits_data[file_name].append(sub)
                            ct += 1
                        else:
                            if ct == lenTokens:
                                ct = 0
                            if commitloader.find_file(file_name, destination, token_list[ct], destination_sha):
                                sub = {}
                                sub['commit_url'] = commit_url
                                sub['commit_sha'] = commit['sha']
                                sub['commit_date'] = commit['commit']['committer']['date']
                                sub['parent_sha'] = commit['parents'][0]['sha']
                                sub['status'] =status
                                sub['additions'] = added_lines
                                sub['deletions'] = removed_lines
                                sub['changes'] = changes
                                commits_data[file_name].append(sub)
                            ct += 1
                except Exception as e:
                    print(e)
                    print('This should only happen if there are no files changed in a commit')
            pr_data[k]['commits_data'].append(commits_data)
        except Exception as e:
            print('An error occurred while fetching the pull request information from GitHub.')
            print (f'Error has to do with: {e}')

    end = time.time()
    runtime = end - start
    print('Fetch Runtime: ', runtime)
    
    return ct, pr_data, req, runtime

def get_destination_sha(destination, cut_off_date, token_list, ct):
    destination_sha = ''
    lenTokens = len(token_list)
    if ct == lenTokens:
        ct = 0
    cut_off_commits = api_request(f'{constant.GITHUB_BASE_URL}{destination}/commits?until={cut_off_date}', token_list[ct])
    ct += 1
    destination_sha = cut_off_commits[0]['sha']
    return destination_sha, ct