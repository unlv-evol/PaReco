import difflib
import os
from constants import constant
from utils import helpers
from . import patch_loader as patchloader
from . import source_loader as sourceloader


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

def calc_match_percentage(results, hashes):
    # Not called anywhere at the moment
    matched_code = []
    not_matched = []
    total = 0
    matched = 0

    for h in results[0]:
        for i in h:
            total += 1
            if i['True']:
                matched += 1
                matched_code.append(hashes[h][i])
            else:
                not_matched.append(hashes[i][h])
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