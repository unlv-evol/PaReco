import sys
import time
from constants import constant
from utils import common
from utils import helpers

def fetch_pullrequest_data_old(source, variant, pullrequests, variant_sha, token_list, ct):
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
            pr_request = f'{constant.GITHUB_API_BASE_URL}{source}/pulls/{pullrequest}'
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
            pullrequest_data[pullrequest]['destination_sha'] = variant_sha
            
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
                            if helpers.find_file(file_name, variant, token_list[ct], variant_sha):
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
                            if helpers.find_file(file_name, variant, token_list[ct], variant_sha):
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

def fetch_pullrequest_data(mainline, variant, pullrequests, variant_sha, token_list, ct):
    print('Fetching files and commit information from patches...')
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
            # get the merge_commit_sha
            pr_request = f'{constant.GITHUB_API_BASE_URL}{mainline}/pulls/{pullrequest}'
            pr = helpers.api_request(pr_request, token_list[ct])
            ct += 1
            req += 1

            # merge_commit_sha = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['created_at'] = pr['created_at']
            pullrequest_data[pullrequest]['merged_at']  = pr['merged_at']
            pullrequest_data[pullrequest]['merge_commit_sha']  = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['commits']  = pr['commits'] # number of commits 
            pullrequest_data[pullrequest]['changed_files'] = pr['changed_files']
            pullrequest_data[pullrequest]['commits_data'] = list()
            pullrequest_data[pullrequest]['destination_sha'] = variant_sha

            # get the commit sha before pull request creation date
            pr_created_at = pr['created_at']
            url = f'{constant.GITHUB_API_BASE_URL}{mainline}/commits?page=1&per_page=1&until={pr_created_at}'
            last_commit_sha = helpers.api_request(url, token_list[ct])

            pullrequest_data[pullrequest]['commit_sha_before'] = last_commit_sha['sha']

            # get files and patches
            if ct == token_length:
                ct = 0

            #files_merged = f'{constant.GITHUB_API_BASE_URL}{mainline}/commits/{merge_commit_sha}'
            files_merged = f'{constant.GITHUB_API_BASE_URL}{mainline}/pulls/{pullrequest}/files?page=1&per_page=100'
            pullrequest_files_merged = helpers.api_request(files_merged, token_list[ct])
            ct += 1
            req += 1

            commits_data = {}
            try:
                for file in  pullrequest_files_merged:
                    file_name = file['filename']
                    commits_data[file_name] = list()
                    if ct == token_length:
                        ct = 0
                        
                        if helpers.find_file(file_name, variant, token_list[ct], variant_sha):
                            sub = {}
                            sub['status'] = file['status']
                            sub['additions'] = file['additions']
                            sub['deletions'] = file['deletions']
                            sub['changes'] = file['changes']
                            sub['patch'] = file['patch']
                            commits_data[file_name].append(sub)
                        else:
                            print(f"Missing file in target_head.......: {file_name}")
                        ct += 1
            except Exception as e:
                print(e)
                print('This should only happen if there are no files changed in a pull request')
            pullrequest_data[pullrequest]['commits_data'].append(commits_data)
        except Exception as e:
            print(e)
    end = time.time()
    runtime = end - start
    print('Fetch Runtime: ', runtime)

    return ct, pullrequest_data, req, runtime
         

def get_variant_sha(variant, cut_off_date, token_list, ct):
    """Get the commit sha at git_head of the variant 
    
    Args:
        variant (String): the repo name of the variant fork e.g. linkedin/kafka
        cut_off_date (DateTime): the least commit date. This may be the git_head last commit date, depending on the cut_off_date
        token_list (List): list of GitHub tokens
        ct (int): token controller used to rotate token 
    Return:
        The last commit sha
    """
    lenTokens = len(token_list)
    if ct == lenTokens:
        ct = 0
    try:
        cut_off_commits = helpers.api_request(f'{constant.GITHUB_API_BASE_URL}{variant}/commits?page=1&per_page=1&until={cut_off_date}', token_list[ct])
        ct += 1
        variant_sha = cut_off_commits[0]['sha']
    except Exception as e:
        print("ERORR in func: get_variant_sha: ", e)
    return variant_sha, ct