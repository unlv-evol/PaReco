import requests
import json
from dateutil import parser
from constants import constant
from utils import helpers


class GetOutOfLoop(Exception):
    pass


def pr_patches(repo, diverge_date, least_date, token_list, ct):
    '''
    Get details of pull requests which part of patches 

    Args:
        repo (String): repository containing pull requests
        diverge_date (datetime): date the variant diverged from the mainline
        least_date (datetime): date of last commit
        token_list (String): list of GitHub API tokens
        ct (int): token counter
    Return:
        pr (list): list of pull request
        pr_all_merged (list): list of all pull requests
        title (list): list of pull request titles 
    '''
    pr = []
    pr_all_merged = []
    title = []
    tot_com = 0
    bug_keyword = helpers.unique(constant.BUGFIX_KEYWORDS)

    p = 1
    count = 0
    try:
        while True:
            url = f"{constant.GITHUB_BASE_URL}{repo}/pulls?page={str(p)}&per_page=100&state=closed&sort=created&direction=desc"
            p = p + 1
            count = 1

            pulls_arrays, ct = helpers.get_response(url, token_list, ct)
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
