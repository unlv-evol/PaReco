
import requests
import json

from dateutil import parser
from constants import constant


class GetOutOfLoop(Exception):
    pass


def get_response(url, token_list, ct):
    '''
    get content of the requested endpoint

    Args:
        url (String): url of the request
        token_list (list): GitHub API token list
        ct (int): token counter
    
    Return:
        Jsondata (object): json data 
    '''
    jsonData = None

    #     token_list, len_tokens = tokens()
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
    url2 = f'{constant.GITHUB_BASE_URL}{repo}/commits?until={date}'
    content_arrays, ct = get_response(url2, token_list, ct)
    sha = ''
    sha = content_arrays[0]['sha']
    commit_date = content_arrays[0]['commit']['committer']['date']
    return sha, ct


def repo_dates(repo, token_list, ct):
    created_at = ''
    updated_at = ''
    url = f'{constant.GITHUB_BASE_URL}{repo}'
    # print(url)
    content_arrays, ct = get_response(url, token_list, ct)
    if content_arrays is not None:
        created_at = content_arrays['created_at']
        updated_at = content_arrays['updated_at']
    return created_at, updated_at, ct


def divergence_date(mainline, variant, token_list, ct, least_date='', diverge_date=''):
    ahead = 0
    behind = 0
    created_ml, date_ml, ct = repo_dates(mainline, token_list, ct)
    fork_date, date_vr, ct = repo_dates(variant, token_list, ct)

    date_ml1 = parser.parse(date_ml)
    date_vr1 = parser.parse(date_vr)

    if least_date == '':
        if date_ml1 < date_vr1:
            least_date = date_ml
        else:
            least_date = date_vr

    sha_vr, ct = repo_commit_date(variant, least_date, token_list, ct)
    sha_ml, ct = repo_commit_date(mainline, least_date, token_list, ct)

    fork1 = variant.split('/')
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


def pr_patches(repo, diverge_date, least_date, token_list, ct):
    '''
    Get details of pull requests which part of patches 

    Args:
        repo (String): repository containing pull requests
        diverge_date (datetime): date the variant diverged from the mainline
        least_date (datetime): date of last commit
        token_list (String): list of GitHub API tokens
        ct (int): token counter
    Returns:
        pr (list): list of pull request
        pr_all_merged (list): list of all pull requests
        title (list): list of pull request titles 
    '''
    pr = []
    pr_all_merged = []
    title = []
    tot_com = 0
    bug_keyword = ['failur', 'fail', 'npe ', ' npe', 'issue', 'except', 'broken',
                   'crash', 'bug', 'differential testing', 'error', 'incorrect', 'flaw',
                   'addresssanitizer', 'hang ', ' hang', 'jsbugmon', 'leak', 'permaorange',
                   'random orange', 'intermittent', 'regression', 'test fix', 'problem',
                   'heap overflow', 'exception', 'daemon', 'stopped', 'broken', ' fault', 'race condition',
                   'deadlock', 'synchronization error', 'dangling pointer', 'null pointer', 'overflow', 'memory leak',
                   'race condition', 'restart', 'steps to reproduce', 'crash', 'assertion', 'failure', 'leak',
                   'stack trace', 'defect', 'mistake', 'fix', 'avoid',
                   'regression', 'test fix', ' hang', 'hang ', 'heap overflow', 'mozregression', 'safemode',
                   'safe mode', 'stop'
                   ]

    p = 1
    count = 0
    try:
        while True:
            # I rearranged the order of the parameters since the previous ordering would only yield 30 
            # objects (pull requests) in the arraylist instead of 100
            url = f'{constant.GITHUB_BASE_URL}{repo}/pulls?page={str(
                p)}&per_page=100&state=closed&sort=created&direction=desc'
            p = p + 1
            count = 1

            pulls_arrays, ct = get_response(url, token_list, ct)
            # tot_com = tot_com + len(pulls_arrays)
            # print(url)
            if pulls_arrays is not None:
                print(url)
                # pr = 0
                if len(pulls_arrays) == 0:
                    break
                for pull_obj in pulls_arrays:
                    # I added a try and accept block since this step would yield and exception of the repo 
                    # pair apache/kafka->linkedin/kafka. For some reason, the exception was not being raised with other 
                    # repo pairs like learningequality/pycaption->pbs/pycaption and 
                    # hzdg/django-enumfields->druids/django-choice-enumfields
                    # I guess there are some commits in apache/kafka->linkedin/kafka that were causing the error. 
                    # A workaround was to ignore them the pull requests that were yielding the exception
                    try:
                        pull_created_at = pull_obj['created_at']
                        if parser.parse(pull_created_at) > parser.parse(least_date):
                            continue
                            # raise GetOutOfLoop

                        if pull_obj['merged_at'] is not None:
                            if parser.parse(pull_obj['merged_at']) > parser.parse(least_date):
                                continue
                            # print(repo, 'parser.parse(pull_obj[merged_at]) = ', parser.parse(pull_obj['merged_at']))
                            # print(repo, 'parser.parse(diverge_date) = ', parser.parse(diverge_date))

                            if parser.parse(pull_obj['merged_at']) < parser.parse(diverge_date):
                                count = 0
                                break
                                # raise GetOutOfLoop
                            pr_all_merged.append(pull_obj['number'])
                            pull_title = pull_obj['title'].lower().replace(';', '-').replace(',', '-')
                            for bug in bug_keyword:
                                if bug in pull_title:
                                    pr.append(pull_obj['number'])
                                    title.append(pull_title)
                                    break
                        if count == 0:
                            break
                    except Exception as e:
                        print(e)
            if count == 0:
                break

    except GetOutOfLoop:
        pass

    return pr, title, pr_all_merged, ct
