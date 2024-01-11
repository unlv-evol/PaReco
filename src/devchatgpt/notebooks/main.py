import time
import pandas as pd
import utils.common as common
import utils.helpers as helpers
import src.core.data_extractor as dataloader
import src.core.classifier as classifier
import utils.totals as totals
import utils.analysis as analysis
import difflib
import os
import json,glob
from datetime import datetime
from constants import constant
    
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
        self.data_dir = 'src/devchatgpt/data/'
        
        # self.len_tokens = len(self.token_list)
        self.main_dir_results= 'src/devchatgpt/notebooks/Repos_results/' 
        self.repo_dir_files ='src/devchatgpt/notebooks/Repos_files/'
         
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
        print("Preparing data... please wait...")
        #1.  get projects
        df, projects, merged_pullrequest = self.get_projects();
        #2. filter projects
        project_filter, projects_clean, pull_request_clean = self.filter_projects(projects, merged_pullrequest);
        #3. fetch chatgpt data
        chatgapt_link_404 = self.fetch_chatgpt_data(df,pull_request_clean)

        #4. fetch github data
        pr_project_pair = self.fetch_github_data(pull_request_clean, chatgapt_link_404, self.token_list, self.ct)

        print("Preparing data......COMPLETED!")
        return pr_project_pair
    
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
        print("Filter projects....criteria: at least 2 developers, 100 commits, 1 review")
        # Filter `toy projects based on the following criteria
        # 1. At least 2 developers
        # 2. At least 100 commits
        # 3. At least 1 review - this is pracific to pull request.
        two_developer = []
        project_filter = []
        for project in projects:
            # constract api url
            part = project.split('github.com/')
            url = f'{part[0]}api.github.com/repos/{part[1]}/contributors'
            try:
                request = helpers.api_request(url, self.token_list[0])
                # at least 2 developers
                if len(request) > 1:
                    two_developer.append(project)

                    # at least 100 commits
                    try:
                        commits_url = f'{part[0]}api.github.com/repos/{part[1]}/commits?per_page=100'
                        fetch_commits = helpers.api_request(commits_url, self.token_list[0])
                        if len(fetch_commits) >= 100:
                            project_filter.append(project)
                    except Exception as e:
                        print("skipping...", e)
            except Exception as e:
                print(project, e)

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
                                        storage_dir = f'src/devchatgpt/notebooks/Repos_files/1/RepoData/{repo_name}/{i["Number"]}/chatgpt/'
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
        for pullrequest in pullrequests:
            # pull request to skip
            if pullrequest in skip_pr:
                # print(pullrequest)
                continue
            repo = pullrequest.split('https://github.com/')[1].split('/pull/')
            pr_nr = repo[1]
            pj_no = repo[0]
        
            pr_poject_pair[pr_nr] = {}
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
                            storage_dir = f'src/devchatgpt/notebooks/Repos_files/1/RepoData/{repo[0]}/{repo[1]}/github/'
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
        return pr_poject_pair

    
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
                                    

                                    hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'ED', added, source_hashes)

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
        # Specify the paths of the text file and the directory containing patch files
        text_files_directory = 'src/devchatgpt/notebooks/Repos_files/1/sample/241/chatgpt/'
        patch_files_directory = 'src/devchatgpt/notebooks/Repos_files/1/sample/241/github/'

        # Loop through the original text files
        for text_file_name in [file for file in os.listdir(text_files_directory) if not file.startswith('.')]:
            text_file_path = os.path.join(text_files_directory, text_file_name)

            # Read the content of the original text file
            original_text = self.read_file(text_file_path)

            # Loop through the patch files
            for patch_file_name in [file for file in os.listdir(patch_files_directory) if not file.startswith('.')]:
                patch_file_path = os.path.join(patch_files_directory, patch_file_name)

                x_patch_patch, x_patch = classifier.process_patch(patch_file_path, text_file_path, 'patch')
                

    def classify(self):
        self.verbosePrint(f'\nStarting classification for {self.main_line}, - , {self.variant}...')
        start = time.time()

        for pr_nr in self.repo_data:
            if int(pr_nr) >=0:
                try:
                    self.verbosePrint(f'Pr_nr: {pr_nr}')

                    destination_sha = self.repo_data[pr_nr]['destination_sha']

                    self.result_dict[pr_nr] = {}

                    dup_count = 1

                    for files in self.repo_data[pr_nr]['commits_data']:
                        for file in files:
                            self.result_dict[pr_nr][file] ={}
                            file_ext = helpers.get_file_type(file)

                            if len(files[file]) != 0:
                                try:
                                    if file_ext != 1:
                                        common.ngram=4
                                        fileName = ''
                                        fileDir = ''

                                        if len(files[file]) == 1:

                                            fileName = helpers.file_name(file)
                                            fileDir = helpers.file_dir(file)
                                            status = files[file][0]['status']

                                            """
                                                Get the file from the variant
                                            """
                                        new_file_dir = ''
                                        for h in fileDir:
                                            new_file_dir = f'{new_file_dir}{h}/'

                                        if self.ct == self.len_tokens:
                                            self.ct = 0
                                        destPath, destUrl_ = classifier.get_file_from_dest(self.repo_dir_files, self.variant, destination_sha, self.repo_file, file, new_file_dir, fileName, self.token_list[self.ct])
                                        self.ct += 1

                                        if status =='added':
                                            patch_lines = files[file][0]['patch']
                                            patchPath = f'{self.repo_dir_files}{self.repo_file}/{self.main_line}/{str(pr_nr)}/patches/{new_file_dir}'
                                            patchName = fileName.split('.')[0]
                                            patchPath, dup_count = classifier.save_patch(patchPath, patchName, patch_lines, dup_count)

                                            x_patch_patch, x_patch = classifier.process_patch(patchPath, destPath, 'patch')
                                            added = x_patch_patch.added()
                                            match_items_patch = x_patch.match_items()
                                            source_hashes = x_patch.source_hashes()

                                            hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'ED', added, source_hashes)

                                            hunk_classifications = []
                                            for patch_nr in hunk_matches_patch:
                                                class_buggy =''
                                                class_patch = hunk_matches_patch[patch_nr]['class']

                                                hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                                hunk_classifications.append(hunk_class)

                                            result_mod = {}
                                            result_mod['type'] = 'ADDED'
                                            result_mod['destPath'] = destPath
                                            result_mod['destUrl'] = destUrl_
                                            result_mod['patchPath'] = patchPath
                                            result_mod['processBuggy'] = ''
                                            result_mod['processPatch'] = x_patch
                                            result_mod['hunkMatchesBuggy'] = ''
                                            result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                            result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)

                                            self.result_dict[pr_nr][file]['result'] = result_mod

                                        elif status == 'removed':

                                            patch_lines = files[file][0]['patch']
                                            patchPath = f'{self.repo_dir_files}{self.repo_file}/{self.main_line}/{str(pr_nr)}/patches/{new_file_dir}'
                                            patchName = fileName.split('.')[0]
                                            patchPath, dup_count= classifier.save_patch(patchPath, patchName, patch_lines, dup_count)

                                            _class_Buggy = ''
                                            x_buggy_patch, x_buggy = classifier.process_patch(patchPath, destPath, 'buggy')
                                            match_items_buggy = x_buggy.match_items()
                                            removed = x_buggy_patch.removed()
                                            source_hashes = x_buggy.source_hashes()

                                            hunk_matches_buggy = classifier.find_hunk_matches_w_important_hash(match_items_buggy, 'MO', removed, source_hashes)

                                            hunk_classifications = []
                                            for patch_nr in hunk_matches_buggy:
                                                class_buggy = hunk_matches_buggy[patch_nr]['class']
                                                class_patch = ''

                                                hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                                hunk_classifications.append(hunk_class)

                                            result_mod = {}
                                            result_mod['type'] = 'DELETED'
                                            result_mod['destPath'] = destPath
                                            result_mod['destUrl'] = destUrl_
                                            result_mod['patchPath'] = patchPath
                                            result_mod['processBuggy'] = x_buggy
                                            result_mod['processPatch'] = ''
                                            result_mod['hunkMatchesBuggy'] = hunk_matches_buggy
                                            result_mod['hunkMatchesPatch'] = ''
                                            result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)
                                            self.result_dict[pr_nr][file]['result'] = result_mod


                                        elif status == 'modified':
                                            patch_lines = files[file][0]['patch']
                                            patchPath = f'{self.repo_dir_files}{self.repo_file}/{self.main_line}/{str(pr_nr)}/patches/{new_file_dir}'
                                            patchName = fileName.split('.')[0]
                                            patchPath, dup_count = classifier.save_patch(patchPath, patchName, patch_lines, dup_count)

                                            """
                                                Compare file before patch to current file for missed opportunities
                                            """
                                            x_buggy_patch, x_buggy = classifier.process_patch(patchPath, destPath, 'buggy')
                                            match_items_buggy = x_buggy.match_items()
                                            removed = x_buggy_patch.removed()
                                            source_hashes = x_buggy.source_hashes()

                                            hunk_matches_buggy = classifier.find_hunk_matches_w_important_hash(match_items_buggy, 'MO', removed, source_hashes)

                                            """
                                                Compare file after patch to current file for effort duplication
                                            """
                                            x_patch_patch, x_patch = classifier.process_patch(patchPath, destPath, 'patch')
                                            added = x_patch_patch.added()
                                            match_items_patch = x_patch.match_items()
                                            source_hashes = x_patch.source_hashes()

                                            hunk_matches_patch = classifier.find_hunk_matches_w_important_hash(match_items_patch, 'ED', added, source_hashes)

                                            if len(hunk_matches_buggy) != len(hunk_matches_patch):
                                                self.verbosePrint("Error \n The two sequences are not the same")
                                                self.verbosePrint(f"Seq matches buggy has length {len(hunk_matches_buggy)}")
                                                self.verbosePrint(f"Seq matches patch has length {len(hunk_matches_patch)}")
                                                continue

                                            hunk_classifications = []
                                            for patch_nr in hunk_matches_buggy:
                                                class_buggy = hunk_matches_buggy[patch_nr]['class']
                                                class_patch = hunk_matches_patch[patch_nr]['class']

                                                hunk_class = classifier.classify_hunk(class_buggy, class_patch)
                                                hunk_classifications.append(hunk_class)

                                            result_mod = {}
                                            result_mod['type'] = 'MODIFIED'
                                            result_mod['destPath'] = destPath
                                            result_mod['destUrl'] = destUrl_
                                            result_mod['patchPath'] = patchPath
                                            result_mod['processBuggy'] = x_buggy
                                            result_mod['processPatch'] = x_patch
                                            result_mod['hunkMatchesBuggy'] = hunk_matches_buggy
                                            result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                            result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)

                                            self.result_dict[pr_nr][file]['result'] = result_mod
                                    else:
                                        result_mod = {}
                                        result_mod['patchClass'] = 'OTHER EXT'
                                        self.result_dict[pr_nr][file]['result'] = result_mod

                                except Exception as e:
                                    result_mod = {}
                                    result_mod['patchClass'] = 'ERROR'
                                    self.result_dict[pr_nr][file]['result'] = result_mod
                                    print('Exception thrown is: ', e)
                                    print('File: ', file)
                            else:
                                result_mod = {}
                                self.result_dict[pr_nr][file]['result']=list()
                                if file_ext == 1:
                                    result_mod['patchClass'] = 'OTHER EXT'
                                    self.result_dict[pr_nr][file]['result'] = result_mod
                                else:
                                    result_mod['patchClass'] = 'NOT EXISTING'
                                    self.result_dict[pr_nr][file]['result'] = result_mod
                except:
                    continue
                    
        self.pr_classifications = totals.final_class(self.result_dict)     
        all_counts = totals.count_all_classifications(self.pr_classifications)
        
        end = time.time()
        duration = end-start
        self.verbosePrint(f'Classification finished.')
        self.verbosePrint(f'Classification Runtime: {duration}')
        
        common.pickleFile(f"{self.main_dir_results}{self.repo_file}_{self.main_line.split('/')[0]}_{self.main_line.split('/')[1]}_results", [self.result_dict, self.pr_classifications, all_counts, duration])

        
    def run_classification(self, pr_project_pairs):
        # self.setPrs(prs_source)
        # self.fetch_pullrequest_data()
        print('======================================================================')
        self.testClassify(pr_project_pairs)
        self.createDf()
        print('======================================================================')
#         self.printResults()
        print('======================================================================')
        self.visualizeResults()

    def createDf(self):
        df_data_files = []
        df_data_patches = []
        for pr in self.result_dict:
            for file in self.result_dict[pr]:
                if self.result_dict[pr][file]["result"]["patchClass"] in ['ED', 'MO', 'SP']:
                    df_data_files.append([self.main_line, self.variant, pr, file, self.result_dict[pr][file]["result"]["type"], self.result_dict[pr][file]["result"]["patchClass"], 1])
                else:
                    df_data_files.append([self.main_line, self.variant, pr, file, 'None', self.result_dict[pr][file]["result"]["patchClass"], 0])
                    
            if self.pr_classifications[pr]["class"] in ['ED', 'MO', 'SP']:
                df_data_patches.append([self.main_line, self.variant, pr, self.pr_classifications[pr]["class"], 1])
            else:
                df_data_patches.append([self.main_line, self.variant, pr, self.pr_classifications[pr]["class"], 0])

        self.df_files_classes = pd.DataFrame(df_data_files, columns = ['Mainline', 'Fork', 'Pr nr', 'Filename', 'Operation', 'File classification', 'Interesting'])
        self.df_files_classes = self.df_files_classes.sort_values(by =  ['Pr nr', 'Interesting'], ascending=False)
        
        self.df_patch_classes = pd.DataFrame(df_data_patches, columns = ['Mainline', 'Fork', 'Pr nr', 'Patch classification', 'Interesting'])
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
                if self.result_dict[pr][file]["result"]["patchClass"] in ['ED', 'MO', 'SP']:
                    print(f'\t {file}')
                    print(f'\t\t Operation - {self.result_dict[pr][file]["result"]["type"]}')
                    print(f'\t\t Class - {self.result_dict[pr][file]["result"]["patchClass"]}')
                else:
                    print(f'\t {file}')
                    print(f'\t\t Class - {self.result_dict[pr][file]["result"]["patchClass"]}')
            print(f'Patch classification ==> {self.pr_classifications[pr]["class"]}')
            
    def visualizeResults(self):
        
        print(f'\nBar plot of the patch classifications for {self.main_line} -> {self.variant}')
        total_NA = 0
        total_ED = 0
        total_MO = 0
        total_CC = 0
        total_SP= 0
        total_NE = 0
        total_ERROR = 0
        
        total_all = 0
        total_mo_all = 0
        total_ed_all = 0
        total_sp_all = 0
        total_na_all = 0

        for pr in self.pr_classifications:
            class_ = self.pr_classifications[pr]['class']
            if class_ == 'ED':
                total_ED += 1
            elif class_ =='MO':
                total_MO += 1
            elif class_ == 'SP':
                total_SP += 1
            elif class_ == 'NA':
                total_NA += 1
            elif class_ == 'CC':
                total_CC += 1
            elif class_ =='NE':
                total_NE += 1
            elif class_ == 'ERROR':
                total_ERROR += 1
                
            total_mid = total_MO+ total_ED + total_SP
            total_all += total_mid
            
        # total_total =len(self.prs)
        
        total_mo_all += total_MO
        total_ed_all += total_ED
        total_sp_all += total_SP
        total_na_all += total_NA

        totals_list = [total_MO, total_ED, total_SP, total_CC, total_NE, total_NA, total_ERROR]

        analysis.all_class_bar(totals_list, self.repo_file, self.main_line, self.variant, True)
        