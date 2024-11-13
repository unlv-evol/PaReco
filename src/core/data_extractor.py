import time
from src.constants import constant
from src.utils import helpers

from datetime import datetime
import pandas as pd

def fetch_pullrequest_data(mainline, variant, pullrequests, variant_sha, token_list, ct):
    print('Fetching files and commit information from patches...')
    start = time.time()
    req = 0
    pullrequest_data = {}
    # missing_files = []
    token_length = len(token_list)
    
    for pullrequest in pullrequests:
        try:
            pullrequest_data[pullrequest] = {}
            # used to include pr that contain java files only
            found = 0

            # Get the PR
            if ct == token_length:
                ct = 0
            pr_request = f'{constant.GITHUB_API_BASE_URL}{mainline}/pulls/{pullrequest}'
            pr = helpers.api_request(pr_request, token_list[ct])
            ct += 1
            req += 1

            # merge_commit_sha = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['pr_url'] = pr_request
            pullrequest_data[pullrequest]['created_at'] = pr['created_at']
            pullrequest_data[pullrequest]['merged_at']  = pr['merged_at']
            pullrequest_data[pullrequest]['merge_commit_sha']  = pr['merge_commit_sha']
            pullrequest_data[pullrequest]['commits']  = pr['commits'] # number of commits 
            pullrequest_data[pullrequest]['changed_files'] = pr['changed_files']
            pullrequest_data[pullrequest]['commits_data'] = list()
            pullrequest_data[pullrequest]['destination_sha'] = variant_sha

            # get the commit sha before pull request creation date
            if ct == token_length:
                ct = 0
            pr_created_at = pr['created_at']
            until_date = datetime.strptime(pr_created_at, "%Y-%m-%dT%H:%M:%SZ")
            
            url = f'{constant.GITHUB_API_BASE_URL}{mainline}/commits?page=1&per_page=1&until={until_date}'
            last_commit_sha = helpers.api_request(url, token_list[ct])
            pullrequest_data[pullrequest]['commit_sha_before'] = last_commit_sha[0]['sha']
            ct += 1
            req += 1

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
                    # # ignore non java files
                    # if file_name.endswith('.java'):
                    #     found = 1
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
                        # else:
                        # # print(f"File missing in target_head.......: {file_name}, Status: {file['status']}")

                        #     missing = {
                        #         'pullrequest_id': pullrequest,
                        #         'filename': file_name,
                        #         'status': file['status'],
                        #         'additions': file['additions'],
                        #         'deletions': file['deletions'],
                        #         'changes': file['changes']
                        #     }
                        #     missing_files.append(missing)
                    ct += 1
            except Exception as e:
                print(e)
                print('This should only happen if there are no files changed in a pull request')
            # if found == 0:
            #     pullrequest_data.pop(pullrequest)
            # else:
            pullrequest_data[pullrequest]['commits_data'].append(commits_data)
        except Exception as e:
            print(f"Error while trying to fetch pull request data....: {e} ..... {token_list[ct]}")
   
    # df = pd.DataFrame(missing_files)
    # df.to_csv('missing_files_java-apache.csv')

    end = time.time()
    runtime = end - start
    print("---%s seconds ---" % runtime)

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
        url = f'{constant.GITHUB_API_BASE_URL}{variant}/commits?page=1&per_page=1&until={cut_off_date}'
        cut_off_commits = helpers.api_request(url, token_list[ct])
        ct += 1
        variant_sha = cut_off_commits[0]['sha']
    except Exception as e:
        print("ERORR in func: get_variant_sha: ", e)
    return variant_sha, ct