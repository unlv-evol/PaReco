import requests
import json
from bs4 import BeautifulSoup
import re
import pandas as pd
import sys


def token_generator(tokens):

    # Define a generator function to yield tokens one at a time
    for token in tokens:
        yield token

    
def scrape_html_file(github_token):
    # Define the regex pattern to match the code block and programming language
    extract_code = r'\s*```(\w+)\n\s*(.*?)\s*```'

    data = pd.read_csv('02_15_2024_manual_data.csv')
    prs = list(data['PR_API'])
    gpt_links = list(data['ChatGPT_Link'])
    count = 0
    
    pull_requests = []
    result={}
    for pr in prs:
        sharing = {}
        conversations = []

        count = count + 1
        try:
            token_iter = token_generator(github_token)
            token = next(token_iter)
            headers = {
                "Authorization": f"token {token}",
            }
            # Make a GET request to the GitHub search API
            response = requests.get(pr, headers=headers)
            # Raise an exception for other HTTP errors
            response.raise_for_status()
            # Parse the JSON response
            data = response.json()
            # print(data.get('state'))
            # sys.exit()
            # for item in data:
            if data.get('merged_at') is None:
                state = data.get('state').upper() 
            else:
                state = "MERGED"      
            
            # Read the HTML file
            try:
                html_file = f'chat/{count}.html' 
                with open(html_file, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                gpt_script = soup.find('script', id='__NEXT_DATA__')
                gpt_html = gpt_script.get_text() if gpt_script else None
                if gpt_html:
                    gpt_data = json.loads(gpt_html)
                    server_response = gpt_data['props']['pageProps']['serverResponse']

                    # model_slug = server_response['data']['model']['slug']
                    title = server_response['data']['title']
                    
                    sharing['Title'] = title
                    sharing['URL'] = gpt_links[count-1]
                    sharing['Status'] = 200

                    temp = {}
                    for index, message in enumerate(server_response["data"]["linear_conversation"]):
                        if index > 1:
                            if index % 2 == 0:
                                # prompt = message["message"]["content"]["parts"][0]
                                print(f'Prompt: {message["message"]["content"]["parts"][0]}')
                                temp['Prompt'] = message["message"]["content"]["parts"][0]
                            else:
                                # answer = message["message"]["content"]["parts"][0]
                                print(f'Answer: {message["message"]["content"]["parts"][0]}')
                                # Find all matches in the text
                                matches = re.findall(extract_code, message["message"]["content"]["parts"][0], re.DOTALL)
                                ListOfCode = []
                                if matches:
                                    for match in matches:
                                        language, code = match
                                        coded = {
                                            "Type":  language,
                                            "Content": code.strip()
                                        }
                                        ListOfCode.append(coded)
                                temp['Answer'] = message["message"]["content"]["parts"][0]
                                temp['ListOfCode'] = ListOfCode

                                conversations.append(temp)

                                print(f"ListOfCode: {ListOfCode}")
                                print("\n........................................\n")
                                temp = {}
                sharing['Conversations'] = conversations
            except Exception as e:
                # If chat gpt link is 404, skip the PR
                print(e)
                continue

            temp_sharing = []
            temp_sharing.append(sharing)
            pull_request = {
                "Type": "pull request",
                "URL": data.get('html_url'),
                "Author": data.get('user').get('login'),
                "RepoName": data.get('html_url').split('/')[-4],
                "Number": data.get('number'),
                "Title": data.get('title'),
                "Body": data.get('body'),
                "CreatedAt": data.get('created_at'),
                "ClosedAt": data.get('closed_at'),
                "MergedAt": data.get('merged_at'),
                "UpdatedAt": data.get('updated_at'),
                "State": state,
                "Additions": data.get('additions'),
                "Deletions": data.get('deletions'),
                "ChangedFiles": data.get('changed_files'),
                "CommitsTotalCount": data.get('commits'),
                "ChatgptSharing": temp_sharing
            }
            pull_requests.append(pull_request)

        except requests.exceptions.RequestException as e:
            print("Error while trying to fetch GitHub data: ", e)
            continue
        except StopIteration:
            print("Iterated over all tokens. Recreating generator and starting again.")
            token_iter = token_generator(github_token)  # Recreate the token generator

    # print(len(prs)
    result["Sources"] = pull_requests
    return result
    
    # # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
        
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    gpt_script = soup.find('script', id='__NEXT_DATA__')
    gpt_html = gpt_script.get_text() if gpt_script else None
    if gpt_html:
        gpt_data = json.loads(gpt_html)
        server_response = gpt_data['props']['pageProps']['serverResponse']

        model_slug = server_response['data']['model']['slug']
        title = server_response['data']['title']
        conversations = []
        for index, message in enumerate(server_response["data"]["linear_conversation"]):
            if index > 1:
                if index % 2 == 0:
                    # prompt = message["message"]["content"]["parts"][0]
                    print(f'Prompt: {message["message"]["content"]["parts"][0]}')
                else:
                    # answer = message["message"]["content"]["parts"][0]
                    print(f'Answer: {message["message"]["content"]["parts"][0]}')
                    # Find all matches in the text
                    matches = re.findall(extract_code, message["message"]["content"]["parts"][0], re.DOTALL)
                    ListOfCode = []
                    if matches:
                        for match in matches:
                            language, code = match
                            coded = {
                                "Type":  language,
                                "Content": code.strip()
                            }
                            ListOfCode.append(coded)
                    print(f"ListOfCode: {ListOfCode}")
                    print("\n........................................\n")
        dialogues = [
                {"Prompt": message["message"]["content"]["parts"][0]} if index % 2 == 0 else 
                {"Answer": message["message"]["content"]["parts"][0]}
                for index, message in enumerate(server_response["data"]["linear_conversation"])
                if index > 1
            ]
        
        result_json = {
            # "model_slug": model_slug,
            "title": title,
            "items": dialogues 
            }

        # print('ChatGPT - Shared Link: ', url, '\n')
        # print(result_json)
        return result_json

#"""
 #   Read from list
#"""
token_file = 'tokens.txt'
token_file = '../../../../../PaReco/tokens.txt'

token_list = []
with open(token_file, 'r') as f:
    for line in f.readlines():
        token_list.append(line.strip('\n'))
# print(token_list)
        
github_token = token_list

pull_requests = scrape_html_file(github_token)
# Convert and write JSON object to file
with open("02_18_2024_manual_pr_sharing.json", "w") as outfile: 
    json.dump(pull_requests, outfile)