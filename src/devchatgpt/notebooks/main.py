import time
import pandas as pd
import common,helpers,classifier,totals,analysis,constant
import difflib
import os
import json,glob
from datetime import datetime
    
class PaReco:
    def __init__(self, params):
        # self.repo_file, self.main_line, self.variant, self.token_list = params
        self.token_list = params
        self.ct = 0
        self.repo_file = 1
        self.main_line = "GitHub"
        self.variant = "ChatGPT"
        self.repo_data = []
        self.result_dict = {}
        self.data_dir = 'data/'
        
        # self.len_tokens = len(self.token_list)
        self.main_dir_results= 'notebooks/Repos_results/' 
        self.repo_dir_files ='notebooks/Repos_files/'
         
        self.verbose = True
        
        self.pr_classifications = {}
        
    def setMainDirResults(self, directory):
        self.main_dir_results = directory
        
    def setRepoDirFiles(self, directory):
        self.repo_dir_files = directory
        
    def setPrs(self, prs):
        self.prs = []
        for pr in prs:
            self.prs.append(str(pr))
        
    def results(self):
        return self.result_dict

    def verboseMode(self, mode = True):
        self.verbose = mode
   
    def verbosePrint(self, text):
        if self.verbose:
            print(text)
        
    
    # def get_dates(self):
    #     self.fork_date, self.diverge_date, self.cut_off_date, self.ahead_by, self.behind_by, self.ct = divergence_date(self.main_line, self.variant, self.token_list, self.ct, self.cut_off_date, self.diverge_date)
    #     print(f'The divergence_date of the repository {self.variant} is {self.diverge_date} and the cut_off_date is {self.cut_off_date}.')
    #     print(f'The variant2 is ==>')
    #     print(f'\t Ahead by {self.ahead_by} patches')
    #     print(f'\t Behind by {self.behind_by} patches')
    #     print(f'Select an interval within the period [{self.diverge_date}, {self.cut_off_date}] to limit the patches being checked.')
    
    
    # def extract_patches(self, chosen_diverge_date, chosen_cut_off_date):
    #     self.diverge_date = chosen_diverge_date
    #     self.cut_off_date = chosen_cut_off_date
    #     self.verbosePrint(f'Extracting patches between {self.diverge_date} and {self.cut_off_date}...')

    #     pr_patch_ml, pr_title_ml, self.ct = pullrequest_patches(self.main_line, self.diverge_date, self.cut_off_date, self.token_list, self.ct)

    #     df_data = []
    #     for i in range(len(pr_patch_ml)):
    #         df_data.append([pr_patch_ml[i], pr_title_ml[i]])

    #     self.df_patches = pd.DataFrame(df_data, columns = ['Patch number', 'Patch title'])
        
    #     return pr_patch_ml
    
    def df_patches(self, nr_patches=-1):
        if nr_patches ==-1:
            return self.df_patches
        else:
            if nr_patches > self.df_patches.shape[0]:
                print(f'The dataframe contain only {self.df_patches.shape[0]} rows. Printing only {self.df_patches.shape[0]} rows.')
            return self.df_patches.head(nr_patches)
    
    def df_file_class(self, nr_patches=-1):
        if nr_patches ==-1:
            return self.df_files_classes
        else:
            if nr_patches > self.df_files_classes.shape[0]:
                print(f'The dataframe contain only {self.df_files_classes.shape[0]} rows. Printing only {self.df_files_classes.shape[0]} rows.')
            return self.df_files_classes.head(nr_patches)
        
    def df_patch_class(self, nr_patches=-1):
        if nr_patches ==-1:
            return self.df_patch_classes
        else:
            if nr_patches > self.df_patch_classes.shape[0]:
                print(f'The dataframe contain only {self.df_patch_classes.shape[0]} rows. Printing only {self.df_patch_classes.shape[0]} rows.')
            return self.df_patch_classes.head(nr_patches)
        
    def prepare_data(self): 
        try:
            print("Preparing data... please wait...")
            #1.  get projects
            df, projects, merged_pullrequest = self.get_projects();
            #2. filter projects
            project_filter, projects_clean, pull_request_clean = self.filter_projects(projects, merged_pullrequest);
            #3. fetch chatgpt data
            chatgapt_link_404 = self.fetch_chatgpt_data(df,pull_request_clean)

            #4. fetch github data
            pr_project_pair, pair_project = self.fetch_github_data(pull_request_clean, chatgapt_link_404, self.token_list, self.ct)

            print("Preparing data......COMPLETED!")
        except Exception as e:
            print(e)
        return pr_project_pair, pair_project
    
    def get_projects(self):
        print("Retrieving project details....")
        json_pattern = os.path.join(self.data_dir, '*_pr_sharings.json')
        file_list = glob.glob(json_pattern)

        dfs = []
        for file in file_list:
            with open(file) as f:
                json_data = pd.json_normalize(json.loads(f.read()))
                json_data['site'] = file.rsplit("/", 1)[-1]
            dfs.append(json_data)
        df = pd.concat(dfs)
        # print(df.head(10))

        # get merged pr url
        pull_request_merged = []
        for item in df['Sources']:
            for i in item:
                if i['State'] == 'MERGED':
                    pull_request_merged.append(i['URL'])

        # extract project name from merged pr url
        temp = []
        for pr in pull_request_merged:
            temp.append(pr.split('/pull/')[0])
        projects = helpers.unique(temp)

        print("Retrieving project details....COMPLETED!")
        return df, projects, pull_request_merged
    
    def filter_projects(self, projects, merged_pr):
        print("Filter projects....criteria: 100 commits, 1 review")
        # Filter `toy projects based on the following criteria
        # 2. At least 100 commits
        # 3. At least 1 review - this is pracific to pull request.
        # two_developer = []
        project_filter = []
        for project in projects:
            # constract api url
            part = project.split('github.com/')
            # url = f'{part[0]}api.github.com/repos/{part[1]}/contributors'
            # try:
            #     request = helpers.api_request(url, self.token_list[0])
            #     # at least 2 developers
            #     if len(request) > 1:
            #         two_developer.append(project)

            # at least 100 commits
            try:
                commits_url = f'{part[0]}api.github.com/repos/{part[1]}/commits?per_page=100'
                fetch_commits = helpers.api_request(commits_url, self.token_list[0])
                if len(fetch_commits) >= 100:
                    project_filter.append(project)
            except Exception as e:
                print("skipping...", e)
            # except Exception as e:
            #     print(project, e)

        # get the merged PRs that are part of the remainings project and perform 
        # PR specific filtering... i.e. PR should have at least 1 review
        # e.g url: https://api.github.com/repos/apache/kafka/pulls/14540/comments

        pull_request_clean = []
        for pf in project_filter:
            for pr in merged_pr:
                pr_part = pr.split('/pull/')
                if pf == pr_part[0]:
                    # at least 1 reviews
                    pf_part = pf.split('github.com/')
                    try:
                        comments_url = f"{part[0]}api.github.com/repos/{pf_part[1]}/pulls/{pr_part[1]}/reviews"
                        fetch_comments = helpers.api_request(comments_url, self.token_list[0])
                        if len(fetch_comments) >= 1:
                            pull_request_clean.append(pr)
                    except Exception as e:
                        print("skipping...", e)
        # total number of PRs that met the selection criteria 
        pull_request_clean = helpers.unique(pull_request_clean)

        # get clean projects
        temp = []
        for pr in pull_request_clean:
            temp.append(pr.split('/pull/')[0])
        projects_clean = helpers.unique(temp)

        print("Filter projects....COMPLETED")

        return project_filter, projects_clean, pull_request_clean
    
    def fetch_chatgpt_data(self, df, pull_request_clean):
        print("Fetching ChatGPT data.......")
        prompt_result = []
        pull_duration = []
        chatgapt_link_404 = []
        no_listofcode = []
        for element in df['Sources']:
            for i in element:
                # pull_title = i['Title'].lower().replace(';', '-').replace(',', '-')
                # # for bug in bugs:
                # if any([bug in pull_title for bug in bugs]):
                if i['URL'] in pull_request_clean and i['State'] == 'MERGED':
                    # print(i['State'])
                    # if i['State'] == 'MERGED':
                    # pull_request_merged.append(i['URL'])
                    mergedAt = datetime.strptime(str(i['MergedAt']), '%Y-%m-%dT%H:%M:%SZ')
                    createdAt = datetime.strptime(str(i['CreatedAt']), '%Y-%m-%dT%H:%M:%SZ')
                    pr_duration = (mergedAt - createdAt).days
                    pull_duration.append(pr_duration)
                    try:
                        count = 1
                        if i['ChatgptSharing']:
                            #print(i['URL'])
                            try:
                                conversation = i['ChatgptSharing'][0]['Conversations']
                            except:
                                chatgapt_link_404.append(i['URL'])
                    
                            for prompts in i['ChatgptSharing'][0]['Conversations']:
                                prompt_result.append(prompts['Prompt'])
                                try:
                                    code = prompts['ListOfCode']
                                    if len(code) == 0:
                                        no_listofcode.append(i['URL'])
                                except:
                                    no_listofcode.append(i['URL'])

                                for content in prompts['ListOfCode']:
                                    if content['Content']:
                                        if content['Type'] in constant.EXTENSIONS:
                                            extension = constant.EXTENSIONS[content['Type']]
                                        else:
                                            extension = "txt"
                                        # print(content['Content'])
                                        repo_name = i['RepoName'] 
                                        storage_dir = f'notebooks/Repos_files/1/RepoData/{repo_name}/{i["Number"]}/chatgpt/'
                                        if not os.path.exists(storage_dir):
                                            os.makedirs(storage_dir)
                                            path = f'{storage_dir}patch-{count}.{extension}'
                                            with open(path, 'x') as patch:
                                                patch.writelines(content['Content'])
                                        else: 
                                            count = count + 1
                                            path = f'{storage_dir}patch-{count}.{extension}'
                                            with open(path, 'x') as patch:
                                                patch.writelines(content['Content'])

                    except Exception as e:
                        print("Skipping.... ", e, i['URL'])
        print("Fetching ChatGPT data.......COMPLETED!")
        return chatgapt_link_404

    def fetch_github_data(self, pullrequests, skip_pr, token_list, ct):
        print("Fetching GITHUB data.......")
        token_length = len(token_list)
        pr_poject_pair = {}
        pair_project = {}
        for pullrequest in pullrequests:
            # pull request to skip
            if pullrequest in skip_pr:
                # print(pullrequest)
                continue
            repo = pullrequest.split('https://github.com/')[1].split('/pull/')
            pr_nr = repo[1]
            pj_no = repo[0]
        
            pr_poject_pair[pr_nr] = {}
            pair_project[pr_nr] = pj_no
            try:
                
                # get files and patches
                if ct == token_length:
                    ct = 0
                #files_merged = f'{constant.GITHUB_API_BASE_URL}{mainline}/commits/{merge_commit_sha}'
                files_merged = f'https://api.github.com/repos/{repo[0]}/pulls/{repo[1]}/files?page=1&per_page=100'
                pullrequest_files_merged, ct = helpers.get_response(files_merged, token_list, ct)
                #print(pullrequest_files_merged)
                ct += 1
                pr_data = []
                try:
                    count = 1
                    for file in  pullrequest_files_merged:
                        try:
                            patch = file['patch']
                            status = file['status']
                            storage_dir = f'notebooks/Repos_files/1/RepoData/{repo[0]}/{repo[1]}/github/'
                            if not os.path.exists(storage_dir):
                                os.makedirs(storage_dir)
                                path = f'{storage_dir}patch-{count}.patch'
                                with open(path, 'x') as file:
                                    file.writelines(patch)
                            else: 
                                count = count + 1
                                path = f'{storage_dir}patch-{count}.patch'
                                with open(path, 'x') as file:
                                    file.writelines(patch)
                            
                            files = {}
                            files['filepath'] = path
                            files['status'] =  status
                            pr_data.append(files)
                        except Exception as e:
                            print("Skipping this patch...")
                        
                except Exception as e:
                    print(e, pullrequest)
            except Exception as e:
                print("Error while trying to fetch pull request data....: ", pullrequest)
            pr_poject_pair[pr_nr][pj_no] = pr_data
        print("Fetching GITHUB data.......COMPLETED!")
        return pr_poject_pair, pair_project

    
    # def fetch_pullrequest_data(self):
    #     destination_sha, self.ct = dataloader.get_variant_sha(self.variant, self.cut_off_date, self.token_list, self.ct)
    #     self.ct,  self.repo_data, req, runtime = dataloader.fetch_pullrequest_data(self.main_line, self.variant, self.prs, destination_sha, self.token_list, self.ct)
    
    def testClassify(self, pr_project_pair):
        start = time.time()
        for pr, project in pr_project_pair.items():
            root_directory = f'src/devchatgpt/notebooks/Repos_files/1/RepoData/{project}/'
        # root_directory = f'src/devchatgpt/notebooks/Repos_files/1/RepoData/sample/'
            try:
                for pr_nr in [directory for directory in os.listdir(root_directory) if not directory.startswith('.')]:
                    # Specify the paths of the text file and the directory containing patch files
                    text_files_directory = f'{root_directory}{pr_nr}/chatgpt/'
                    patch_files_directory = f'{root_directory}{pr_nr}/github/'

                    self.result_dict[pr_nr] = {}
                    # Loop through the original text files
                    for text_file_name in [file for file in os.listdir(text_files_directory) if not file.startswith('.')]:
                        text_file_path = os.path.join(text_files_directory, text_file_name)
                        self.result_dict[pr_nr][text_file_path] = {}
                        file_ext = helpers.get_file_type(text_file_path)

                        # Read the content of the original text file
                        #original_text = self.read_file(text_file_path)

                        # Loop through the patch files
                        for patch_file_name in [file for file in os.listdir(patch_files_directory) if not file.startswith('.')]:
                            patch_file_path = os.path.join(patch_files_directory, patch_file_name)
                            try:
                                if file_ext != 1:
                                    # get status
                                    #status = status[pr][project]
                                    """
                                        Compare file before patch to current file for missed opportunities
                                    """
                                    x_buggy_patch, x_buggy = classifier.process_patch(patch_file_path, text_file_path, 'buggy')
                                    match_items_buggy = x_buggy.match_items()
                                    removed = x_buggy_patch.removed()
                                    source_hashes = x_buggy.source_hashes()

                                    hunk_matches_buggy = classifier.find_hunk_matches_w_important_hash(match_items_buggy, 'MO', removed, source_hashes)

                                    """
                                        Compare file after patch to current file for effort duplication
                                    """
                                    x_patch_patch, x_patch = classifier.process_patch(patch_file_path, text_file_path, 'patch')
                                    added = x_patch_patch.added()
                                    match_items_patch = x_patch.match_items()
                                    source_hashes = x_patch.source_hashes()

                                    #print(classifier.calc_match_percentage(match_items_patch, source_hashes))
                                    #print(hunk_matches_buggy)
                                    

                                    hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'PA', added, source_hashes)

                                    #print(hunk_matches_patch)

                                    if len(hunk_matches_buggy) != len(hunk_matches_patch):
                                        self.verbosePrint("Error \n The two sequences are not the same")
                                        self.verbosePrint(f"Seq matches buggy has length {len(hunk_matches_buggy)}")
                                        self.verbosePrint(f"Seq matches patch has length {len(hunk_matches_patch)}")
                                        print(patch_file_path)
                                        continue

                                    hunk_classifications = []
                                    for patch_nr in hunk_matches_buggy:
                                        class_buggy = hunk_matches_buggy[patch_nr]['class']
                                        class_patch = hunk_matches_patch[patch_nr]['class']

                                        hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                        hunk_classifications.append(hunk_class)

                                    result_mod = {}
                                    result_mod['type'] = 'MODIFIED'
                                    result_mod['destPath'] = text_file_path
                                    result_mod['patchPath'] = patch_file_path
                                    result_mod['processBuggy'] = x_buggy
                                    result_mod['processPatch'] = x_patch
                                    result_mod['hunkMatchesBuggy'] = hunk_matches_buggy
                                    result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                    result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)
                                else:
                                    if file_ext == 1:
                                        result_mod = {}
                                        result_mod['patchClass'] = 'OTHER EXT'
                                    else:
                                        result_mod['patchClass'] = 'NOT EXISTING'
                                        self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                            except Exception as e:
                                    result_mod = {}
                                    result_mod['patchClass'] = 'ERROR'
                                    self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                                    print('Exception thrown is: ', e)
                                    print('File: ', text_file_path)

                            self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                            # self.result_dict['result'] = result_mod
            except:
                print("Some error........")
                # print(f"Error...no pull request directory found...{pr_nr}--->{project}")
                # continue

        #print(self.result_dict)
        self.pr_classifications = totals.final_class(self.result_dict)     
        all_counts = totals.count_all_classifications(self.pr_classifications)
          
        end = time.time()
        duration = end-start
        self.verbosePrint(f'Classification finished.')
        self.verbosePrint(f'Classification Runtime: {duration}')

        common.pickleFile(f"{self.main_dir_results}{self.repo_file}_{self.main_line}_results", [self.result_dict, self.pr_classifications, all_counts, duration])

                # # Read the content of the patch file
                # patch_content = self.read_file(patch_file_path)

                # # Compare the original text with the patch
                # similarity = self.compare_text_with_patch(original_text, patch_content)

                # # Print the similarity for each patch file and original text pair
                # print(f"Similarity between {text_file_name} and patched text in {patch_file_name}: {similarity}")

    def read_file(self,file_path):
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()

    def compare_text_with_patch(self, text, patch_content):
        # Apply the patch to the original text
        # patched_text = difflib.PatchSet(patch_content).apply(text)

        # Combine the patched text into a single string
        # patched_text_combined = '\n'.join(patched_text)

        # Calculate similarity using cosine similarity or other methods
        # For simplicity, let's use the Levenshtein distance as an example
        similarity = difflib.SequenceMatcher(None, text, patch_content).ratio()

        return similarity

    def myTest(self):
        start = time.time()
        root_directory = f'src/devchatgpt/notebooks/Repos_files/1/sample/'
        try:
            for pr_nr in [directory for directory in os.listdir(root_directory) if not directory.startswith('.')]:
                # Specify the paths of the text file and the directory containing patch files
                text_files_directory = f'{root_directory}{pr_nr}/chatgpt/'
                patch_files_directory = f'{root_directory}{pr_nr}/github/'

                self.result_dict[pr_nr] = {}
                # Loop through the original text files
                for text_file_name in [file for file in os.listdir(text_files_directory) if not file.startswith('.')]:
                    text_file_path = os.path.join(text_files_directory, text_file_name)
                    self.result_dict[pr_nr][text_file_path] = {}
                    file_ext = helpers.get_file_type(text_file_path)

                    # Read the content of the original text file
                    #original_text = self.read_file(text_file_path)

                    # Loop through the patch files
                    for patch_file_name in [file for file in os.listdir(patch_files_directory) if not file.startswith('.')]:
                        patch_file_path = os.path.join(patch_files_directory, patch_file_name)
                        try:
                            if file_ext != 1:

                                x_patch_patch, x_patch = classifier.process_patch(patch_file_path, text_file_path, 'patch')
                                added = x_patch_patch.added()
                                match_items_patch = x_patch.match_items()
                                source_hashes = x_patch.source_hashes()

                                # print("ADDED: ", added)
                                # removed = x_patch_patch._only_removed
                                # print("REMOVED: ", removed)

                                hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'PA', added, source_hashes)

                                hunk_classifications = []
                                for patch_nr in hunk_matches_patch:
                                    class_buggy =''
                                    class_patch = hunk_matches_patch[patch_nr]['class']

                                    hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                    hunk_classifications.append(hunk_class)

                                result_mod = {}
                                result_mod['type'] = 'ADDED'
                                result_mod['destPath'] = text_file_path
                                #result_mod['destUrl'] = destUrl_
                                result_mod['patchPath'] = patch_file_path
                                result_mod['processBuggy'] = ''
                                result_mod['processPatch'] = x_patch
                                result_mod['hunkMatchesBuggy'] = ''
                                result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)
                                print(result_mod['patchClass'])

                                self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                            else:
                                if file_ext == 1:
                                    result_mod = {}
                                    result_mod['patchClass'] = 'OTHER EXT'
                                else:
                                    result_mod['patchClass'] = 'NOT EXISTING'
                                    self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                        except Exception as e:
                                result_mod = {}
                                result_mod['patchClass'] = 'ERROR'
                                self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                                print('Exception thrown is: ', e)
                                print('File: ', text_file_path)

                        self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                        # self.result_dict['result'] = result_mod
        except:
            print("Some error........")
            # print(f"Error...no pull request directory found...{pr_nr}--->{project}")
            # continue

        #print(self.result_dict)
        self.pr_classifications = totals.final_class(self.result_dict)     
        all_counts = totals.count_all_classifications(self.pr_classifications)
            
        end = time.time()
        duration = end-start
        self.verbosePrint(f'Classification finished.')
        self.verbosePrint(f'Classification Runtime: {duration}')

        common.pickleFile(f"{self.main_dir_results}{self.repo_file}_{self.main_line}_results", [self.result_dict, self.pr_classifications, all_counts, duration])
            

    def classify(self, pr_project_pair):
        self.verbosePrint(f'\nStarting classification for {self.main_line}, - , {self.variant}...')
        start = time.time()
        for pr_nr, project in pr_project_pair.items():
            root_directory = f'notebooks/Repos_files/1/RepoData/{project}/'

        # root_directory = f'src/devchatgpt/notebooks/Repos_files/1/sample/'
           
                # for pr_nr in [directory for directory in os.listdir(root_directory) if not directory.startswith('.')]:
            # if pr_nr != '980':
            #     continue
                # Specify the paths of the text file and the directory containing patch files
            text_files_directory = f'{root_directory}{pr_nr}/chatgpt/'
            patch_files_directory = f'{root_directory}{pr_nr}/github/'

            self.result_dict[pr_nr] = {}
            # store result for iterating through this file
            result = []
            patch_file_path =''
            # check if chatgpt directory exist
            if not os.path.exists(text_files_directory):
                # Loop through the patch files
                # print(pr_nr)
                # file_path =''
                # try:
                patch_file_names  = [file for file in os.listdir(patch_files_directory) if not file.startswith('.')]
                patch_file_path = f'{patch_files_directory}{patch_file_names[0]}'
                self.result_dict[pr_nr][patch_file_path] = {}
                # print(patch_file_path)
                result_mod = {}
                # file_path = patch_file_path
                result_mod['similarityRatio'] = ''
                result_mod['patchClass'] = 'NOT EXISTING'
                result_mod['destPath'] = patch_file_path
                result_mod['patchPath'] = patch_file_path
                result_mod['destLOC'] = patch_LOC
                result_mod['patchLOC'] = patch_LOC
                result.append(result_mod)
                self.result_dict[pr_nr][patch_file_path]['result'] = result
                continue
                # except Exception as e:
                #     print(e)
                # continue
            try:
                # Loop through the original text files
                for text_file_name in [file for file in os.listdir(text_files_directory) if not file.startswith('.')]:
                    text_file_path = os.path.join(text_files_directory, text_file_name)
                    # print(text_file_path)
                    self.result_dict[pr_nr][text_file_path] = {}
                    file_ext = helpers.get_file_type(text_file_path)
                    text_LOC = helpers.count_LOC(text_file_path)

                    # Read the content of the original text file
                    #original_text = self.read_file(text_file_path)

                    # Loop through the patch files
                    for patch_file_name in [file for file in os.listdir(patch_files_directory) if not file.startswith('.')]:
                        patch_file_path = os.path.join(patch_files_directory, patch_file_name)
                        patch_LOC = helpers.count_LOC(patch_file_path) 
                        try:
                            if file_ext > 1:
                                common.ngram_size = 1
                                
                                x_patch_patch, x_patch = classifier.process_patch(patch_file_path, text_file_path, 'patch', file_ext)
                                added = x_patch_patch.added()
                                match_items_patch = x_patch.match_items()
                                source_hashes = x_patch.source_hashes()
                                patch_hashes = x_patch_patch.hashes()

                                # print("ADDED_LINES: ", added)
                                # print("SOURCE_HASHES: ", source_hashes)
                                # print("PATCH_HASHES: ", patch_hashes)
                
                                hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'PA', added, source_hashes)
                                similarity_ratio = classifier.cal_similarity_ratio(source_hashes, added)
                                # print("SIMILARITY_RATION: ", similarity_ratio)

                                # print("HUNK_MATCHES_PATCH: ", hunk_matches_patch)
                                
                                hunk_classifications = []
                                for patch_nr in hunk_matches_patch:
                                    class_buggy =''
                                    class_patch = hunk_matches_patch[patch_nr]['class']

                                    hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                    hunk_classifications.append(hunk_class)
                                
                                # print("HUNK_CLASSIFICATION: ", hunk_classifications)

                                result_mod = {}
                                result_mod['type'] = 'ADDED'
                                result_mod['destPath'] = text_file_path
                                result_mod['destLOC'] = text_LOC
                                #result_mod['destUrl'] = destUrl_
                                result_mod['patchPath'] = patch_file_path
                                result_mod['patchLOC'] = patch_LOC
                                result_mod['processBuggy'] = ''
                                result_mod['processPatch'] = x_patch
                                result_mod['hunkMatchesBuggy'] = ''
                                result_mod['similarityRatio'] = round(similarity_ratio, 2)
                                result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)
                                #print(result_mod['patchClass'])
                                result.append(result_mod)
                                #self.result_dict[pr_nr][text_file_path]['result'] = result_mod

                            else:
                                if file_ext <= 1:
                                    result_mod = {}
                                    result_mod['similarityRatio'] = 0.0
                                    result_mod['patchClass'] = 'OTHER EXT'
                                    result_mod['destPath'] = text_file_path
                                    result_mod['destLOC'] = text_LOC
                                    result_mod['patchPath'] = patch_file_path
                                    result_mod['patchLOC'] = patch_LOC
                                    result.append(result_mod)
                                else:
                                    print(text_file_path)
                                    result_mod['similarityRatio'] = 0.0
                                    result_mod['patchClass'] = 'NOT EXISTING'
                                    result_mod['destPath'] = text_file_path
                                    result_mod['destLOC'] = text_LOC
                                    result_mod['patchPath'] = ''
                                    result.append(result_mod)
                                    #self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                        except Exception as e:
                            result_mod = {}
                            result_mod['similarityRatio'] = 0.0
                            result_mod['patchClass'] = 'ERROR'
                            result_mod['destPath'] = text_file_path
                            result_mod['destLOC'] = text_LOC
                            result_mod['patchPath'] = patch_file_path
                            result_mod['patchLOC'] = patch_LOC
                            result.append(result_mod)
                            #self.result_dict[pr_nr][text_file_path]['result'] = result_mod
                            print('Exception thrown is: ', e)
                            print('File: ', text_file_path)                        

                    self.result_dict[pr_nr][text_file_path]['result'] = result
                    # self.result_dict['result'] = result_mod
            except Exception as e:
                print("Some error........: ", e)
                # print(f"Error...no pull request directory found...{pr_nr}--->{project}")
                # continue
                # result_mod = {}
                # result_mod['similarityRatio'] = ''
                # result_mod['patchClass'] = 'ERROR'
                # result_mod['destPath'] = ''
                # result_mod['patchPath'] = patch_file_path
                # result.append(result_mod)

        # self.result_dict[pr_nr][patch_file_path]['result'] = result
        # print(self.result_dict)
        self.pr_classifications = totals.final_class(self.result_dict)     
        all_counts = totals.count_all_classifications(self.pr_classifications)

        # print(self.pr_classifications)    
        end = time.time()
        duration = end-start
        self.verbosePrint(f'Classification finished.')
        self.verbosePrint(f'Classification Runtime: {duration}')

        common.pickleFile(f"{self.main_dir_results}{self.repo_file}_{self.main_line}_results", [self.result_dict, self.pr_classifications, all_counts, duration])
            
        
#     def run_classification(self, pr_project_pairs):
#         # self.setPrs(prs_source)
#         # self.fetch_pullrequest_data()
#         print('======================================================================')
#         self.testClassify(pr_project_pairs)
#         self.createDf()
#         print('======================================================================')
# #         self.printResults()
#         print('======================================================================')
#         self.visualizeResults()
    def run_classification(self, pr_project_pairs):
        # self.setPrs(prs_source)
        # self.fetch_pullrequest_data()
        print('======================================================================')
        self.classify(pr_project_pairs)
        self.createDf()
        print('======================================================================')
#         self.printResults()
        print('======================================================================')
        self.visualizeResults()

    def createDf(self):
        df_data_files = []
        df_data_patches = []
        for pr, files in self.result_dict.items():
            for file, result in files.items():
                for item in result['result']:
                    if item["patchClass"] in ['PA']:
                        df_data_files.append([self.main_line, self.variant, pr, file, item["destLOC"], item["patchPath"], item["patchLOC"], item["type"], item["similarityRatio"], item["patchClass"], 1])
                    else:
                        df_data_files.append([self.main_line, self.variant, pr, file, item["destLOC"], item["patchPath"], item["patchLOC"], 'None',item["similarityRatio"], item["patchClass"], 0])
                        
                if self.pr_classifications[pr]["class"] in ['PA']:
                    df_data_patches.append([self.main_line, self.variant, pr, self.pr_classifications[pr]["class"], 1])
                else:
                    df_data_patches.append([self.main_line, self.variant, pr, self.pr_classifications[pr]["class"], 0])

        self.df_files_classes = pd.DataFrame(df_data_files, columns = ['GitHub', 'ChatGPT', 'Pull Request', 'ChatGPT Patch', 'ChatGPTPatchLOC', 'GitHub Patch', 'GitHubPatchLOC', 'Operation', 'Similarity(%)','File Classification', 'Interesting'])
        self.df_files_classes = self.df_files_classes.sort_values(by =  ['Pull Request', 'Interesting'], ascending=False)
        
        self.df_patch_classes = pd.DataFrame(df_data_patches, columns = ['GitHub', 'ChatGPT', 'Pull Request', 'Patch Classification', 'Interesting'])
        self.df_patch_classes = self.df_patch_classes.sort_values(by ='Interesting', ascending=False) 
    
    def printResults(self):
        print('\nClassification results:')
        for pr in self.result_dict:
            print('\n')
            print(f'{self.main_line} -> {self.variant}')
            print(f'Pull request nr ==> {pr}')
#             print('\n')
            print('File classifications ==> ')
            for file in self.result_dict[pr]:
                if self.result_dict[pr][file]["result"]["patchClass"] in ['PA']:
                    print(f'\t {file}')
                    print(f'\t\t Operation - {self.result_dict[pr][file]["result"]["type"]}')
                    print(f'\t\t Class - {self.result_dict[pr][file]["result"]["patchClass"]}')
                else:
                    print(f'\t {file}')
                    print(f'\t\t Class - {self.result_dict[pr][file]["result"]["patchClass"]}')
            print(f'Patch classification ==> {self.pr_classifications[pr]["class"]}')
            
    def visualizeResults(self):
        
        print(f'\nBar plot of the patch classifications for {self.main_line} -> {self.variant}')
        total_PN = 0
        total_PA = 0
        total_CC = 0
        total_NE = 0
        total_ERROR = 0
        
        total_all = 0
        total_ed_all = 0
        total_na_all = 0

        for pr in self.pr_classifications:
            class_ = self.pr_classifications[pr]['class']
            if class_ == 'PA':
                total_PA += 1
            elif class_ == 'PN':
                total_PN += 1
            elif class_ == 'CC':
                total_CC += 1
            elif class_ =='NE':
                total_NE += 1
            elif class_ == 'ERROR':
                total_ERROR += 1
                
            total_mid = total_PA
            total_all += total_mid
            
        # total_total =len(self.prs)
        
        total_ed_all += total_PA
        total_na_all += total_PN

        totals_list = [total_PA, total_CC, total_NE, total_PN, total_ERROR]

        analysis.all_class_bar(totals_list, self.repo_file, self.main_line, self.variant, True)
        # analysis.all_class_pie(totals_list, self.repo_file, self.main_line, self.variant, True)
        