import sys
import time
from constants import constant
from utils import common
from utils import helpers
import urllib.request
from unidiff import PatchSet

def fetch_pullrequest_data(source, destination, pullrequests, destination_sha, token_list, ct):
    print('Fetching commit information and files from patches...')
    start = time.time()
    req = 0
    pullrequest_data = {}
    token_length = len(token_list)
    
    for pullrequest in pullrequests:
        try:
            pullrequest_data[pullrequest] = {}

            # Get the PR
            if ct == token_length:
                ct = 0
            pr_request = f'{constant.GITHUB_BASE_URL}{source}/pulls/{pullrequest}'
            pr = helpers.api_request(pr_request, token_list[ct])
            ct += 1
            req += 1

            # Get the commit
            if ct == token_length:
                ct = 0
            commits_url = pr['commits_url']
            commits = helpers.api_request(commits_url, token_list[ct])
            common.verbose_print(f'ct ={ct}')
            ct += 1
            req += 1

            commits_data = {}

            nr_files = pr['changed_files']

            pullrequest_data[pullrequest]['pr_url'] = pr_request
            pullrequest_data[pullrequest]['commits_url'] = commits_url
            pullrequest_data[pullrequest]['changed_files'] = nr_files
            pullrequest_data[pullrequest]['commits_data'] = list()
            pullrequest_data[pullrequest]['destination_sha'] = destination_sha
            
            for i in commits:
                if ct == token_length:
                    ct = 0
                commit_url = i['url']
                commit = helpers.api_request(commit_url, token_list[ct])
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

                        #file_ext = commitloader.get_file_type(file_name)
                        if file_name not in commits_data:
                            commits_data[file_name] = list()
                            if ct == token_length:
                                ct = 0
                            if helpers.find_file(file_name, destination, token_list[ct], destination_sha):
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
                            if ct == token_length:
                                ct = 0
                            if helpers.find_file(file_name, destination, token_list[ct], destination_sha):
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
            pullrequest_data[pullrequest]['commits_data'].append(commits_data)
        except Exception as e:
            print('An error occurred while fetching the pull request information from GitHub.')
            print (f'Error has to do with: {e}')

    end = time.time()
    runtime = end - start
    print('Fetch Runtime: ', runtime)
    
    return ct, pullrequest_data, req, runtime

def fetch_pullrequest_data_unidiff(repository, pullrequests):
    pullrequest_data = {}
    for pullrequest in pullrequests:
        diff = urllib.request.urlopen(f'{constant.GITHUB_BASE_URL}{repository}/pull/{pullrequest}.diff')
        encoding  = diff.headers.get_charsets()[0]
        patches  = PatchSet(diff, encoding=encoding)
        for patch in patches:
            pass



def get_destination_sha(destination, cut_off_date, token_list, ct):
    """Get the commit sha at git_head of the variant 
    
    Args:
        destination (String): the repo name of the variant fork e.g. linkedin/kafka
        cut_off_date (DateTime): the least commit date. This can be the git_head last commit data
        token_list (List): list of GitHub tokens
        ct (int): token controller used to rotate token 
    Return:
        The last commit sha
    """
    lenTokens = len(token_list)
    if ct == lenTokens:
        ct = 0
    try:
        cut_off_commits = helpers.api_request(f'{constant.GITHUB_BASE_URL}{destination}/commits?page=1&per_page=1&until={cut_off_date}', token_list[ct])
        ct += 1
        destination_sha = cut_off_commits[0]['sha']
    except Exception as e:
        print("ERORR in func: get_destination_sha: ", e)
    return destination_sha, ct