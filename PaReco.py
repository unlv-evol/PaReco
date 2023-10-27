import time
import pandas as pd
import src.utils.common as common
import src.utils.helpers as helpers
import src.core.data_extractor as dataloader
import src.core.classifier as classifier
import src.utils.totals as totals
import src.utils.analysis as analysis
from src.utils.helpers import divergence_date
from src.core.patch_extractor import pullrequest_patches
    
class PaReco:
    def __init__(self, params):
        self.repo_file, self.main_line, self.variant, self.diverge_date, self.cut_off_date, self.token_list = params
        self.ct = 0
        
        self.repo_data = []
        self.result_dict = {}
        
        self.len_tokens = len(self.token_list)
        self.main_dir_results= 'src/notebooks/Repos_results/' # 'Examples/Repos_results/'
        self.repo_dir_files ='src/notebooks/Repos_files/' # 'Examples/Repos_files/'
         
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
        
#     def writeResultsToCsv(self, csv_name):
#         with open(self.main_dir_results + csv_name, 'w') as f:
    
    def get_dates(self):
        self.fork_date, self.diverge_date, self.cut_off_date, self.ahead_by, self.behind_by, self.ct = divergence_date(self.main_line, self.variant, self.token_list, self.ct, self.cut_off_date, self.diverge_date)
        print(f'The divergence_date of the repository {self.variant} is {self.diverge_date} and the cut_off_date is {self.cut_off_date}.')
        print(f'The variant2 is ==>')
        print(f'\t Ahead by {self.ahead_by} patches')
        print(f'\t Behind by {self.behind_by} patches')
        print(f'Select an interval within the period [{self.diverge_date}, {self.cut_off_date}] to limit the patches being checked.')
    
    
    def extract_patches(self, chosen_diverge_date, chosen_cut_off_date):
        self.diverge_date = chosen_diverge_date
        self.cut_off_date = chosen_cut_off_date
        self.verbosePrint(f'Extracting patches between {self.diverge_date} and {self.cut_off_date}...')

        # pr_patch_ml_str = ''
        # pr_title_ml_str = ''

        pr_patch_ml, pr_title_ml, self.ct = pullrequest_patches(self.main_line, self.diverge_date, self.cut_off_date, self.token_list, self.ct)

        # at least one of the mainline or fork should have a pr with patch
        # if len(pr_patch_ml) > 0:
        #     if len(pr_patch_ml) > 1:
        #         pr_patch_ml_str = '/'.join(map(str, pr_patch_ml))
        #         pr_title_ml_str = '=/='.join(map(str, pr_title_ml))
        #     if len(pr_patch_ml) == 1:
        #         pr_patch_ml_str = pr_patch_ml[0]
        #         pr_title_ml_str = pr_title_ml[0]

#         print('pr_patch_ml:', pr_patch_ml)
#         print('pr_title_ml:', pr_title_ml)

        #------------------#
        df_data = []
        for i in range(len(pr_patch_ml)):
            df_data.append([pr_patch_ml[i], pr_title_ml[i]])

        self.df_patches = pd.DataFrame(df_data, columns = ['Patch number', 'Patch title'])

#         self.verbosePrint('Extracting finished.\n')
#         self.verbosePrint('Summary of extraction:')
        
#         self.verbosePrint(f'Variant1 {self.variant1}')
#         self.verbosePrint(f'Variant2 {self.variant2}')
#         self.verbosePrint(f'Divergence_date {self.diverge_date}')
#         self.verbosePrint(f'Least_date {self.cut_off_date}')
#         self.verbosePrint(f'Variant2 unique commits {self.ahead_by}')
#         self.verbosePrint(f'Variant1 unique commits {self.behind_by}')

#         self.verbosePrint('\nVariant1 patch details')
#         self.verbosePrint('=======================')
#         self.verbosePrint(f'Number of merged pr = {len(pr_all_merged_ml)}')
#         self.verbosePrint(f'Number of patches = {len(pr_patch_ml)}')
#         self.verbosePrint(f'Patches:: {pr_patch_ml_str}')
#         self.verbosePrint(f'Patches titles:: {pr_title_ml_str}')

        
#         self.verbosePrint('\nfork patch details')
#         self.verbosePrint('=======================')
#         self.verbosePrint(f'number of merged pr = {len(pr_all_merged_fv)}')
#         self.verbosePrint(f'number of patches = {len(pr_patch_fv)}')
#         self.verbosePrint(f'patches :: {pr_patch_fv_str}')
#         self.verbosePrint(f'patches titles:: {pr_title_fv_str}')
        
        return pr_patch_ml
    
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
            
        total_total =len(self.prs)
        
        total_mo_all += total_MO
        total_ed_all += total_ED
        total_sp_all += total_SP
        total_na_all += total_NA

        totals_list = [total_MO, total_ED, total_SP, total_CC, total_NE, total_NA, total_ERROR]

        analysis.all_class_bar(totals_list, self.repo_file, self.main_line, self.variant, True)
        
    def fetch_pullrequest_data(self):
        destination_sha, self.ct = dataloader.get_variant_sha(self.variant, self.cut_off_date, self.token_list, self.ct)
        self.ct,  self.repo_data, req, runtime = dataloader.fetch_pullrequest_data(self.main_line, self.variant, self.prs, destination_sha, self.token_list, self.ct)

#     def fetchRepoData(self):
#         print(self.prs)
#         for pr in self.prs:
#             print(pr)
#             self.repo_data.append(self.fetchPrData(pr))

    def classify(self):
        self.verbosePrint(f'\nStarting classification for {self.main_line}, - , {self.variant}...')
        start = time.time()

        for pr_nr in self.repo_data:
            if int(pr_nr) >=0:
                try:
                    self.verbosePrint(f'Pr_nr: {pr_nr}')

                    destination_sha = self.repo_data[pr_nr]['destination_sha']
                    merged_commit_sha = self.repo_data[pr_nr]['merge_commit_sha']
                    commit_before_sha = self.repo_data[pr_nr]['commit_sha_before']

                    self.result_dict[pr_nr] = {}

                    dup_count = 1

                    for files in self.repo_data[pr_nr]['commits_data']:
                        for file in files:
                            self.result_dict[pr_nr][file] ={}
                            file_ext = helpers.get_file_type(file)
                            # self.verbosePrint(f"\nThe File extension is: {file_ext}")

                            # emptyFilePath = ''

                            # if file_ext == 2:
                            #     emptyFilePath = 'EmptyFiles/EmptyC.c'
                            # elif file_ext == 3:
                            #     emptyFilePath = 'EmptyFiles/EmptyJava.java'
                            # elif file_ext == 4:
                            #     emptyFilePath = 'EmptyFiles/EmptyShell.sh'
                            # elif file_ext == 5:
                            #     emptyFilePath = 'EmptyFiles/EmptyPython.py'
                            # elif file_ext == 6:
                            #     emptyFilePath = 'EmptyFiles/EmptyPerl.pl'
                            # elif file_ext == 7:
                            #     emptyFilePath = 'EmptyFiles/EmptyPHP.php'
                            # elif file_ext == 8:
                            #     emptyFilePath = 'EmptyFiles/EmptyRuby.rb'

                            if len(files[file]) != 0:
                                try:
                                    if file_ext != 1:
                                        common.ngram=4
                                        # parent = ''
                                        # sha =''
                                        fileName = ''
                                        fileDir = ''

                                        if len(files[file]) == 1:
                                            # parent = files[file][0]['parent_sha']
                                            # sha = files[file][0]['commit_sha']
                                            fileName = helpers.file_name(file)
                                            fileDir = helpers.file_dir(file)
                                            status = files[file][0]['status']

                                            """
                                                Get the file from the variant
                                            """
                                        new_file_dir = ''
                                        for h in fileDir:
                                            new_file_dir = new_file_dir + h + '/'

                                        if self.ct == self.len_tokens:
                                            self.ct = 0
                                        destPath, destUrl_ = classifier.get_file_from_dest(self.repo_dir_files, self.variant, destination_sha, self.repo_file, file, new_file_dir, fileName, self.token_list[self.ct])
                                        self.ct += 1

                                        if status =='added':
                                            # """
                                            #     Get the file after the patch from the main_line
                                            # """
                                            # if self.ct == self.len_tokens:
                                            #     self.ct = 0
                                            # fileAfterPatchDir, fileAfterPatchUrlAdd_= classifier.get_file_after_patch(self.repo_dir_files, self.main_line, merged_commit_sha, self.repo_file, pr_nr, file, new_file_dir, fileName, self.token_list[self.ct])
                                            # self.ct += 1

                                            # """
                                            #     Create the patch file in unified diff format
                                            # """
                                            # patch_lines = classifier.unified_diff(emptyFilePath, fileAfterPatchDir)
                                            patch_lines = files[file][0]['patch']
                                            patchPath = self.repo_dir_files + self.repo_file + '/' + self.main_line + '/' + str(pr_nr) +  '/patches/' + new_file_dir
                                            patchName = fileName.split('.')[0]
                                            patchPath, dup_count = classifier.save_patch(patchPath, patchName, patch_lines, dup_count)

                                            _class_patch = ''
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
                                            # result_mod['fileAfterPatchUrl'] = fileAfterPatchUrlAdd_
                                            # result_mod['fileBeforePatchUrl'] =  ''
                                            result_mod['patchPath'] = patchPath
                                            result_mod['processBuggy'] = ''
                                            result_mod['processPatch'] = x_patch
                                            result_mod['hunkMatchesBuggy'] = ''
                                            result_mod['hunkMatchesPatch'] = hunk_matches_patch
                                            result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)

                                            self.result_dict[pr_nr][file]['result'] = result_mod

                                        elif status == 'removed':
                                            # """
                                            #     Get the file before the patch from the main_line
                                            # """
                                            # if self.ct == self.len_tokens:
                                            #     self.ct = 0
                                            # fileBeforePatchDir, fileBeforePatchUrlRem_= classifier.get_file_before_patch(self.repo_dir_files, self.main_line, commit_before_sha, self.repo_file, pr_nr, file, new_file_dir, fileName, self.token_list[self.ct])
                                            # self.ct += 1

                                            # """
                                            #     Create the patch file in unified diff format
                                            # """
                                            #patch_lines = classifier.unified_diff(fileBeforePatchDir, emptyFilePath)
                                            patch_lines = files[file][0]['patch']
                                            patchPath = self.repo_dir_files + self.repo_file + '/' + self.main_line + '/' + str(pr_nr) + '/patches/' + new_file_dir
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
                                            # result_mod['fileAfterPatchUrl'] = ''
                                            # result_mod['fileBeforePatchUrl'] =  fileBeforePatchUrlRem_
                                            result_mod['patchPath'] = patchPath
                                            result_mod['processBuggy'] = x_buggy
                                            result_mod['processPatch'] = ''
                                            result_mod['hunkMatchesBuggy'] = hunk_matches_buggy
                                            result_mod['hunkMatchesPatch'] = ''
                                            result_mod['patchClass'] = classifier.classify_patch(hunk_classifications)
                                            self.result_dict[pr_nr][file]['result'] = result_mod


                                        elif status == 'modified':
                                            # """
                                            #     Get the file before the patch from the main_line
                                            # """
                                            # if self.ct == self.len_tokens:
                                            #     self.ct = 0
                                            # fileBeforePatchDir, fileBeforePatchUrlMod_ = classifier.get_file_before_patch(self.repo_dir_files, self.main_line, commit_before_sha, self.repo_file, pr_nr, file, new_file_dir, fileName, self.token_list[self.ct])
                                            # self.ct += 1

                                            # """
                                            #     Get the file after the patch from the main_line
                                            # """
                                            # if self.ct == self.len_tokens:
                                            #     self.ct = 0
                                            # fileAfterPatchDir, fileAfterPatchUrlMod_ = classifier.get_file_after_patch(self.repo_dir_files, self.main_line, merged_commit_sha, self.repo_file, pr_nr, file, new_file_dir, fileName, self.token_list[self.ct])
                                            # self.ct += 1

                                            # """
                                            #     Create the patch file in unified diff format
                                            # """
                                            # patch_lines = classifier.unified_diff(fileBeforePatchDir, fileAfterPatchDir)
                                            patch_lines = files[file][0]['patch']
                                            patchPath = f'{self.repo_dir_files}{self.repo_file}/{self.main_line}/{str(pr_nr)}/patches/{new_file_dir}'
                                            patchName = fileName.split('.')[0]
                                            patchPath, dup_count = classifier.save_patch(patchPath, patchName, patch_lines, dup_count)

                                            """
                                                Compare file before patch to current file for missed opportunities
                                            """
                                            _class_Buggy = ''
                                            x_buggy_patch, x_buggy = classifier.process_patch(patchPath, destPath, 'buggy')
                                            match_items_buggy = x_buggy.match_items()
                                            removed = x_buggy_patch.removed()
                                            source_hashes = x_buggy.source_hashes()

                                            hunk_matches_buggy = classifier.find_hunk_matches_w_important_hash(match_items_buggy, 'MO', removed, source_hashes)

                                            """
                                                Compare file after patch to current file for effort duplication
                                            """
                                            _class_patch = ''
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
                                            # result_mod['fileAfterPatchUrl'] = fileAfterPatchUrlMod_
                                            # result_mod['fileBeforePatchUrl'] =  fileBeforePatchUrlMod_
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
                                self.result_dict[pr_nr][file]['results']=list()
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
        
        common.pickleFile(self.main_dir_results + self.repo_file + '_' + self.main_line.split('/')[0] + '_' + self.main_line.split('/')[1] + '_results', [self.result_dict, self.pr_classifications, all_counts, duration])

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
        
    def run_classification(self, prs_source):
        self.setPrs(prs_source)
        self.fetch_pullrequest_data()
        print('======================================================================')
        self.classify()
        self.createDf()
        print('======================================================================')
#         self.printResults()
        print('======================================================================')
        self.visualizeResults()