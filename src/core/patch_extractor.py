import time
from dateutil import parser
from src.constants import constant
from src.utils import helpers


class GetOutOfLoop(Exception):
    pass


def pullrequest_patches(repo, diverge_date, least_date, token_list, ct):
    start = time.time()
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
    pr_all_merged = [] # not used at the moment
    title = []

    bug_keyword = helpers.unique(constant.BUGFIX_KEYWORDS)

    page_number = 1
    try:
        while True:
            url = f"{constant.GITHUB_API_BASE_URL}{repo}/issues?page={str(page_number)}&per_page=100&state=closed&since={diverge_date}"
            page_number = page_number + 1

            issues_data, ct = helpers.get_response(url, token_list, ct)
            
            if issues_data is not None:
                print(url)
                # end loop is you start getting empty data array
                if len(issues_data) == 0:
                    break
                for issue in issues_data:
                    try:
                        # filter pull request from issues 
                        if 'pull_request' not in issue:
                            continue

                        # skip closed but not merged pull requests 
                        if issue['pull_request']['merged_at'] is None:
                            continue
                            
                        pull_created_at = issue['created_at']
                        pull_merged_at = issue['pull_request']['merged_at']

                        if parser.parse(pull_created_at) > parser.parse(least_date):
                            continue
                        if parser.parse(pull_merged_at) > parser.parse(least_date):
                            continue
                            
                        if parser.parse(pull_merged_at) < parser.parse(diverge_date):
                            end = time.time()
                            runtime = end - start
                            print("--- %s seconds ---" % runtime)
                            return pr, title, ct
                                                    
                        pr_all_merged.append(issue['number'])
                        pull_title = issue['title'].lower().replace(';', '-').replace(',', '-')
                        for bug in bug_keyword:
                            if bug in pull_title:
                                pr.append(issue['number'])
                                title.append(pull_title)
                                break
                    except Exception as e:
                        print("Error... ", e)
            
    except GetOutOfLoop:
        print("Stopping data extraction....")
        
    end = time.time()
    runtime = end - start
    print("---%s seconds ---" % runtime)

    return pr, title, ct
