import requests
import time
import re
import json
from datetime import datetime

def token_generator(tokens):

    # Define a generator function to yield tokens one at a time
    for token in tokens:
        yield token

def search_pull_requests(keyword, github_token, since=None):

    url = f"https://api.github.com/search/issues?q='{keyword}'+type:pr"
    per_page = 100  # Number of items per page
    
    if since:
        since_str = datetime.strftime(since, "%Y-%m-%dT%H:%M:%SZ")
        url += f"+created:>={since_str}"
    
    print(url)
    
    # Regular expression pattern to match shared links
    pattern = r"https:\/\/chat\.openai\.com\/share\/[a-zA-Z0-9-]{36}"
    
    merged_prs = []
    pull_requests = []
    result={}
    while True:
        try:
            token_iter = token_generator(github_token)
            token = next(token_iter)
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {
                "per_page": per_page
            }
            # Make a GET request to the GitHub search API
            response = requests.get(url, headers=headers, params=params)
            # print(response.json())
            
            # Check if the response status code indicates rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                # Extract rate limit information from response headers
                limit = int(response.headers['X-RateLimit-Limit'])
                remaining = int(response.headers['X-RateLimit-Remaining'])
                reset_time = int(response.headers['X-RateLimit-Reset'])
                time_to_reset = reset_time - int(time.time())
                
                # If rate limit exceeded, wait until reset time and retry
                if remaining == 0:
                    print(f"Rate limit exceeded. Waiting {time_to_reset} seconds until reset...")
                    time.sleep(time_to_reset)
                    continue
                
            # Raise an exception for other HTTP errors
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Extract relevant information about the pull requests
            # result = {}
            # pull_requests = []

            for item in data.get('items', []):
                print(f"\t {item.get('html_url')}")
                body_text = item.get('body')
                matches = []
                if body_text:
                    # Apply the regular expression to identify matches
                    match = re.findall(pattern, body_text)
                    # print(item.get('html_url'))
                    # continue
                    matches.extend(match)

                # # search PR review comments for 
                # print("\t\t process pr comments")
                # # while True:
                # # header_two = {
                # #             "Authorization": f"token {token}"
                # #             }
                try:
                    token = next(token_iter)
                    comments_url = f"{item.get('pull_request').get('url')}/comments?per_page=100"
                    res = requests.get(comments_url, headers=headers)
                    print(f"\t\t {comments_url}")
                    # Raise an exception for other HTTP errors
                    res.raise_for_status()
                    # Parse the JSON response
                    comments_data = res.json()
                    if len(comments_data) == 0:
                        continue
                    for element in comments_data:
                        if not element.get('body'):
                            continue
                        comment_body = element.get('body')
                        mt = re.findall(pattern, comment_body)
                        matches.extend(mt)
                        # print(matches)
                except Exception as e:
                    print("Iterated over all tokens. Recreating generator and starting again.")
                    token_iter = token_generator(github_token)  # Recreate the token generator
                # Check if there are more pages of results
                # if 'next' in res.links:
                #     comments_url  = res.links['next']['url']  # Get the URL of the next page
                # else:
                #     print("\t\t DONE processing pr comments")
                #     break  # No more pages, exit the loop

                if item.get('pull_request').get('merged_at') is None:
                    state = item.get('state').upper() 
                else:
                    state = "MERGED"
                    merged_prs.append(item.get('html_url'))         

                pull_request = {
                    "Type": "pull request",
                    "URL": item.get('html_url'),
                    "Author": item.get('user').get('login'),
                    "RepoName": item.get('repository_url').split('/repos/')[-1],
                    "Number": item.get('number'),
                    "Title": item.get('title'),
                    "Body": body_text,
                    "CreatedAt": item.get('created_at'),
                    "ClosedAt": item.get('closed_at'),
                    "MergedAt": item.get('pull_request').get('merged_at'),
                    "UpdatedAt": item.get('updated_at'),
                    "State": state,
                    "ChatgptSharing": matches
                }
                pull_requests.append(pull_request)
            # Check if there are more pages of results
            if 'next' in response.links:
                url = response.links['next']['url']  # Get the URL of the next page
                print(url)
            else:
                break  # No more pages, exit the loop
        except requests.exceptions.RequestException as e:
            print("Error while trying to fetch GitHub data: ", e)
            continue
        except StopIteration:
            print("Iterated over all tokens. Recreating generator and starting again.")
            token_iter = token_generator(github_token)  # Recreate the token generator
        
        result["Sources"] = pull_requests
    return result, merged_prs


#"""
 #   Read from list
#"""
token_file = 'tokens.txt'
token_file = '../../../../PaReco/tokens.txt'

token_list = []
with open(token_file, 'r') as f:
    for line in f.readlines():
        token_list.append(line.strip('\n'))
# print(token_list)
        
github_token = token_list
# print(github_token[0])

keyword = "https://chat.openai.com/share/"
since_date = datetime(2023,10,13)
pull_requests, merged_prs = search_pull_requests(keyword, github_token,since_date)

# if pull_requests:
#     print("Pull requests containing the keyword:")
#     for pr in pull_requests:
#         print(f"- Title: {pr['title']}, Repository: {pr['repository']}, URL: {pr['url']}")
# else:
#     print("Failed to retrieve pull requests.")
# print(pull_requests)
# Convert and write JSON object to file
with open("pr_sharing_17_02_2024.json", "w") as outfile: 
    json.dump(pull_requests, outfile)
with open("merged_pr_17_02_2024.json", "w") as outfile: 
    json.dump(merged_prs, outfile)
print("Total PRs: ", len(pull_requests['Sources']))
print("Total Merged PRs: ", len(merged_prs))
