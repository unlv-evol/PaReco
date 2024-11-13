import difflib
import os
from src.constants import constant
from src.utils import helpers
from . import patch_loader as patchloader
from . import source_loader as sourceloader


def unified_diff(before, after):
    """
    unified_diff
    To create a unified diff file
    @before - The state of the file before changes
    @after - The state of the file after the changes
    """

    file1 = open(before).readlines()
    file2 = open(after).readlines()
    delta = difflib.unified_diff(file1, file2)
                      
    file =list()
    for line in delta:
#         if not line.startswith('---') or not line.startswith('+++'):
        file.append(line)
    return file


def save_patch(storageDir, fileName, file, dup_count):
    """
    save_patch
    To save a patch file
    
    @storageDir - The directory where to save the patch
    @fileName - The name of the file
    @file - The content of the file
    """
    patch_path = ''
    if not os.path.exists(storageDir):
        os.makedirs(storageDir)
        patch_path = f'{storageDir}{fileName}.patch'
        with open(patch_path, 'x') as patch:
            patch.writelines(file)
        # f = open(patch_path, 'x')
        # for line in file[2:]:
        #     f.write(line)
        # f.close()
        
    else:
        if not os.path.isfile(f'{storageDir}{fileName}'):
            patch_path = f'{storageDir}{fileName}.patch'
            with open(patch_path, 'x') as patch:
                patch.writelines(file)
            # f = open(patch_path, 'w')
            # for line in file[2:]:
            #     f.write(line)
            # f.close()
        else:
            patch_path = f'{storageDir}{fileName}_{dup_count}.patch'
            with open(patch_path, 'x') as patch:
                patch.writelines(file)
            # f = open(patch_path, 'w')
            # for line in file[2:]:
            #     f.write(line)
            # f.close()
            dup_count += 1
    return patch_path, dup_count
        

def process_patch(patch_path, dst_path, type_patch):
    """
    processPatch
    To process a patch
    This is done before bein able to classify the patch
    
    @patchPath - the path where the patch file is stored
    @dstPath - the path where the destination file is stored
    @typePatch - the kind of patch we are dealing with, buggy or fixed
    """
                    
    patch = patchloader.PatchLoader()
    try:
        patch.traverse(patch_path, type_patch)
    except Exception as e:
        print("Error traversing patch:....", e)
    
    source = sourceloader.SourceLoader()
    try:
        source.traverse(dst_path, patch)
    except Exception as e:
        print("Error traversing source (variant)....", e)
    
    return patch, source

def get_ext(file):
    """
    get_ext
    Extract the extension of the a file
    
    @file - the file from which to extract the file
    """
    ext = file.split['.'][-1]


def get_file_before_patch(repo_dir, mainline, sha, pair_nr, pr_nr, file, fileDir, fileName, token):
    """
    getFileBeforePatch
    Extracts the buggy file using the GitHub API
    
    @repo_dir - directory where to store the file
    @mainline - the source repository
    @sha - the commit sha-value that last changed the file == before pull request was created
    @parent - the parent commit sha-value of the commit that last changed the file
    @pr_nr - the pull request number of the patch
    @file - the file path in the repository
    @fileDir - the sub directory where to store the file
    @fileName - a name to store the file
    @token - token needed for the GitHub API
    """
    fileBeforePatchDir = f'{repo_dir}{str(pair_nr)}/{mainline}/{str(pr_nr)}/before_patch/{fileDir}'
    beforePatch_url = f'{constant.GITHUB_RAW_URL}{mainline}/{sha}/{file}'
    fileBeforePatch = helpers.api_request(beforePatch_url, token)

    try:
        helpers.save_file(fileBeforePatch.content, fileBeforePatchDir, fileName)
    except Exception as e:
        print("Could not save file before patch: ", e)
    return fileBeforePatchDir + fileName, beforePatch_url

def get_file_after_patch(repo_dir, mainline, sha, pair_nr, pr_nr, file, fileDir, fileName, token):
    fileAfterPatchDir = f'{repo_dir}{str(pair_nr)}/{mainline}/{str(pr_nr)}/after_patch/{fileDir}'
    fileAfterPatchUrl = f'{constant.GITHUB_RAW_URL}{mainline}/{sha}/{file}'
    fileAfterPatch = helpers.api_request(fileAfterPatchUrl, token)

    try:
        helpers.save_file(fileAfterPatch.content, fileAfterPatchDir, fileName)
    except Exception as e:
        print("Could not save file after patch: ", e)
    return fileAfterPatchDir + fileName, fileAfterPatchUrl

def get_file_from_dest(repo_dir, variant, sha, pair_nr, fileDir, file, fileName, token):
    destPath = f'{repo_dir}{str(pair_nr)}/{variant}/{fileDir}'
    
    if not os.path.exists(destPath):
        os.makedirs(destPath)

    dest_url = f'{constant.GITHUB_RAW_URL}{variant}/{sha}/{fileDir}{fileName}'

    destFile = helpers.api_request(dest_url, token)
    
    try:
        helpers.save_file(destFile.content, destPath, fileName)
    except Exception as e:
        print("Could not save file from upstream")
    return f'{destPath}{fileName}', dest_url
    
def calc_match_percentage(results, hashes):
    # Not called anywhere at the moment
    matched_code = []
    not_matched = []
    total = 0
    matched = 0

    for h in results:
        total += 1
        if results[h]['True']:
            matched += 1
            matched_code.append(hashes[h])
        else:
            not_matched.append(hashes[h])
    if total!= 0:
        return ((matched/total)*100)
    else:
        return 0


def find_hunk_matches(match_items, _type, important_hashes, source_hashes):
    # Not called anywhere at the moment
    """
    find_hunk_matches
    To find the different matches between two hunk using the hashed values
    
    @match_items
    @_type
    @important_hashes
    @source_hashes
    """

    seq_matches = {} 

    for patch_nr in match_items:
        seq_matches[patch_nr] = {}
        seq_matches[patch_nr]['sequences'] = {}
        seq_matches[patch_nr]['class'] = ''
        for patch_seq in match_items[patch_nr]:

            seq_matches[patch_nr]['sequences'][patch_seq] = {}
            seq_matches[patch_nr]['sequences'][patch_seq]['count'] = 0
            seq_matches[patch_nr]['sequences'][patch_seq]['hash_list'] = list(match_items[patch_nr][patch_seq].keys())
            
            for k in match_items[patch_nr][patch_seq]:
                if match_items[patch_nr][patch_seq][k]:
                    seq_matches[patch_nr]['sequences'][patch_seq]['count'] += 1
    
    match_bool = True

    for seq_nr in seq_matches:
        for seq in seq_matches[seq_nr]['sequences']:
            if seq_matches[seq_nr]['sequences'][seq]['count'] < 2:
                match_bool = False
                break
        _class = ''
        
        if _type == 'MO':
            if match_bool:
                _class = _type
            else:
                _class = 'MC'
        elif _type == 'ED':
            if match_bool:
                _class = _type
            else:
                _class = 'MC'
                
        seq_matches[seq_nr]['class']= _class        
    
    return seq_matches


def classify_hunk(class_patch, class_buggy):
    """
    classify_hunk
    To classify a hunk
    
    @class_patch
    @class_buggy
    """
    
    finalClass = ''
    if class_patch == 'ED' and class_buggy =='MO':
        finalClass = 'SP'
    if class_buggy == 'MO' and class_patch == 'MC':
        finalClass = 'MO'
    if class_buggy == 'MC' and class_patch == 'ED':
        finalClass = 'ED'
    if class_buggy == 'MC' and class_patch == 'MO':
        finalClass = 'MO'
    if class_buggy == 'ED' and class_patch == 'MC':
        finalClass = 'ED'
    if class_buggy == 'MC' and class_patch == 'MC':
        finalClass = 'NA'
    if class_patch == '' and class_buggy !='':
        finalClass = class_buggy
    if class_patch != '' and class_buggy =='':
        finalClass = class_patch
    if class_patch == '' and class_buggy =='':
        finalClass = 'NA'
    return finalClass


def classify_patch(hunk_classifications):
    """
    classify_patch
    To classify a patch based on the hunks
    
    @hunk_classifications - the classifications for the different hunks in the .diff of a file changed in a PR
    """

    NA_total = 0
    MO_total = 0
    ED_total = 0
    SP_total = 0
    
    finalClass= ''
    for i in range(len(hunk_classifications)):
        if hunk_classifications[i] =='ED':
            ED_total += 1
        elif hunk_classifications[i] =='MO':
            MO_total += 1
        elif hunk_classifications[i] =='NA':
            NA_total += 1
        elif hunk_classifications[i] =='SP':
            SP_total += 1
    
    if MO_total == 0 and ED_total == 0 and SP_total ==0:
        max_total = NA_total
        finalClass = 'NA'
    else:
        max_total = ED_total
        finalClass='ED'
        
        if max_total < MO_total:
            max_total = MO_total
            finalClass = 'MO'
        elif max_total == MO_total:
            # Possible SPLIT case if ED == MO
            finalClass='SP'
            
        if max_total <= SP_total:
            max_total = SP_total
            finalClass = 'SP'
            
    return finalClass


def find_hunk_matches_w_important_hash(match_items, _type, important_hashes, source_hashes):
    """
    find_hunk_matches_w_important_hash
    To find the different matches between two hunk using the hashed values and using the important hash feature
    
    @match_items
    @_type
    @important_hashes
    @source_hashes
    """

    seq_matches = {} 
    test = []
    for lines in important_hashes:
        for line in lines:
            for each in line:
                for ngram, hash_list in source_hashes:
                    if each in ngram:
                        test.append(hash_list)
    
    found_important_hashes = {}
    important_hash_match = 0
    total_important_hashes = len(important_hashes)
    for patch_nr in match_items:
        seq_matches[patch_nr] = {}
        seq_matches[patch_nr]['sequences'] = {}
        seq_matches[patch_nr]['class'] = ''
        for patch_seq in match_items[patch_nr]:
            seq_matches[patch_nr]['sequences'][patch_seq] = {}
            seq_matches[patch_nr]['sequences'][patch_seq]['count'] = 0
            seq_matches[patch_nr]['sequences'][patch_seq]['hash_list'] = list(match_items[patch_nr][patch_seq].keys())
            
            if seq_matches[patch_nr]['sequences'][patch_seq]['hash_list'] in test:
                seq_matches[patch_nr]['sequences'][patch_seq]['important'] = True
                important_hash_match =+ 1
            else:
                seq_matches[patch_nr]['sequences'][patch_seq]['important'] = False
                
            for k in match_items[patch_nr][patch_seq]:
                if match_items[patch_nr][patch_seq][k]:
                    seq_matches[patch_nr]['sequences'][patch_seq]['count'] += 1

    if total_important_hashes != 0:       
        important_hash_perc = (important_hash_match*100)/total_important_hashes            

    if test:
        match_bool = False
    else:
        match_bool = True
        
    for i in seq_matches:
        for j in seq_matches[i]['sequences']:
            if test:
                if seq_matches[i]['sequences'][j]['important'] and seq_matches[i]['sequences'][j]['count'] != 0:
                    match_bool = True
                else:
                    if seq_matches[i]['sequences'][j]['count'] < 2:
                        match_bool = False      
            else:
                if seq_matches[i]['sequences'][j]['count'] < 2:
                    match_bool = False
                    break

        _class = ''

        if _type == 'MO':
            if match_bool:
                _class = _type
            else:
                _class = 'MC'

        elif _type == 'ED':
            if match_bool:
                _class = _type
            else:
                _class = 'MC'
                 
        seq_matches[i]['class']= _class 
        
    return seq_matches 