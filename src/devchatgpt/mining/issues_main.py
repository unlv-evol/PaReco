import requests
import time
import re
import json
from datetime import datetime

def token_generator(tokens):

    # Define a generator function to yield tokens one at a time
    for token in tokens:
        yield token

def search_issues(keyword, github_token, since=None):

    url = f"https://api.github.com/search/issues?q='{keyword}'+type:issue"
    per_page = 100  # Number of items per page
    
    if since:
        since_str = datetime.strftime(since, "%Y-%m-%dT%H:%M:%SZ")
        url += f"+created:>={since_str}"
    
    print(url)
    
    # Regular expression pattern to match shared links
    pattern = r"https:\/\/chat\.openai\.com\/share\/[a-zA-Z0-9-]{36}"
    
    
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
            result = {}
            issues = []

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

                issue = {
                    "Type": "issue",
                    "URL": item.get('html_url'),
                    "Author": item.get('user').get('login'),
                    "RepoName": item.get('repository_url').split('/repos/')[-1],
                    "Number": item.get('number'),
                    "Title": item.get('title'),
                    "Body": body_text,
                    "CreatedAt": item.get('created_at'),
                    "ClosedAt": item.get('closed_at'),
                    "UpdatedAt": item.get('updated_at'),
                    "State": item.get('state').upper(),
                    "ChatgptSharing": matches
                }
                issues.append(issue)
                
            result["Sources"] = issues

            # Check if there are more pages of results
            if 'next' in response.links:
                url = response.links['next']['url']  # Get the URL of the next page
            else:
                break  # No more pages, exit the loop
        except requests.exceptions.RequestException as e:
            print("Error while trying to fetch GitHub data:", e)
            continue
        except StopIteration:
            print("Iterated over all tokens. Recreating generator and starting again.")
            token_iter = token_generator(github_token)  # Recreate the token generator
    
    return result


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
issues = search_issues(keyword, github_token,since_date)

# if issues:
#     print("Pull requests containing the keyword:")
#     for pr in issues:
#         print(f"- Title: {pr['title']}, Repository: {pr['repository']}, URL: {pr['url']}")
# else:
#     print("Failed to retrieve pull requests.")
# print(issues)
# Convert and write JSON object to file
with open("issues_sharing.json", "w") as outfile: 
    json.dump(issues, outfile)
print(len(issues['Sources']))