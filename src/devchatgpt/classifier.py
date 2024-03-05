import patch_loader as patchloader
import source_loader as sourceloader
import common


def process_patch(patch_path, dst_path, type_patch, file_ext):
    """
    processPatch
    To process a patch
    This is done before bein able to classify the patch
    
    @patchPath - the path where the patch file is stored
    @dstPath - the path where the destination file is stored
    @typePatch - the kind of patch we are dealing with, buggy or fixed
    """
     # reset ngram_size to 4
#     common.ngram_size = 4
    
#     patch = patchloader.PatchLoader()
#     npatch = patch.traverse(patchPath, typePatch, fileExt)

#     source = sourceloader.SourceLoader()
#     nmatch = source.traverse(dstPath, patch, fileExt)

#     # reset ngram_size to 4
# #     common.ngram_size = 4

#     return patch, source
    common.ngram_size = 1
    patch = patchloader.PatchLoader()
    try:
        npatch = patch.traverse(patch_path, type_patch, file_ext)
    except Exception as e:
        print("Error traversing patch:....", e)
    
    source = sourceloader.SourceLoader()
    try:
        nmatch = source.traverse(dst_path, patch, file_ext)
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

def calculate_match_percentage(results, hashes):
    matched_code = []
    not_matched = []
    total = 0
    matched = 0

    for h in results:
        total += 1
        if results[h]['Match']:
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
        elif _type == 'PA':
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
    if class_buggy == 'MC' and class_patch == 'PA':
        finalClass = 'PA'
    if class_buggy == 'PA' and class_patch == 'MC':
        finalClass = 'PA'
    if class_buggy == 'MC' and class_patch == 'MC':
        finalClass = 'PN'
    if class_patch == '' and class_buggy !='':
        finalClass = class_buggy
    if class_patch != '' and class_buggy =='':
        finalClass = class_patch
    if class_patch == '' and class_buggy =='':
        finalClass = 'PN'
    return finalClass


def classify_patch(hunk_classifications):
    """
    classify_patch
    To classify a patch based on the hunks
    
    @hunk_classifications - the classifications for the different hunks in the .diff of a file changed in a PR
    """

    NA_total = 0
    ED_total = 0
    
    finalClass= ''
    for i in range(len(hunk_classifications)):
        if hunk_classifications[i] =='PA':
            ED_total += 1
        elif hunk_classifications[i] =='PN':
            NA_total += 1
    
    if ED_total == 0:
        finalClass = 'PN'
    else:
        finalClass='PA'
            
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
        match_bool = False
        seq_matches[patch_nr] = {}
        seq_matches[patch_nr]['sequences'] = {}
        seq_matches[patch_nr]['class'] = ''
        for patch_seq in match_items[patch_nr]:
            seq_matches[patch_nr]['sequences'][patch_seq] = {}
            seq_matches[patch_nr]['sequences'][patch_seq]['count'] = 0
            seq_matches[patch_nr]['sequences'][patch_seq]['hash_list'] = list(match_items[patch_nr][patch_seq].keys())
            
            if seq_matches[patch_nr]['sequences'][patch_seq]['hash_list'] in test:
                seq_matches[patch_nr]['sequences'][patch_seq]['important'] = True
                important_hash_match += 1
                match_bool = True
            else:
                seq_matches[patch_nr]['sequences'][patch_seq]['important'] = False
                
            for k in match_items[patch_nr][patch_seq]:
                if match_items[patch_nr][patch_seq][k]:
                    seq_matches[patch_nr]['sequences'][patch_seq]['count'] += 1

        if match_bool:
            seq_matches[patch_nr]['class'] = _type
        else:
            seq_matches[patch_nr]['class'] = 'MC'

    # if total_important_hashes != 0:       
    #     important_hash_perc = (important_hash_match*100)/len(source_hashes) 
    # print("IMPORTANT_HASH_PER: ", important_hash_perc) 
    # pre = (important_hash_match / len(source_hashes)) * 100        
    # print("Percentage: ", pre) 
    # if test:
    #     match_bool = False
    # else:
    #     match_bool = True
        
    # for i in seq_matches:
    #     for j in seq_matches[i]['sequences']:
    #         if test:
    #             if seq_matches[i]['sequences'][j]['important'] and seq_matches[i]['sequences'][j]['count'] != 0:
    #                 match_bool = True
    #             else:
    #                 if seq_matches[i]['sequences'][j]['count'] < 1:
    #                     match_bool = False      
    #         else:
    #             if seq_matches[i]['sequences'][j]['count'] < 1:
    #                 match_bool = False
    #                 break

        # _class = ''

        # if _type == 'MO':
        #     if match_bool:
        #         _class = _type
        #     else:
        #         _class = 'MC'

        # elif _type == 'PA':
        #     if match_bool:
        #         _class = _type
        #     else:
        #         _class = 'MC'
                 
        # seq_matches[i]['class']= _class 
        
    return seq_matches

def cal_similarity_ratio(source_hashes, added_lines_hashes):

    count_matches = []
    
    for lines in added_lines_hashes:
        for line in lines:
            for each in line:
                for ngram, hash_list in source_hashes:
                    if each == ngram:
                        # print(hash_list)
                        # print(each)
                        count_matches.append(ngram)

    # count_matches = 0
    # for item in source_hashes:
    #     match = 0
    #     for h in patch_hashes:   
    #         if item[0] == patch_hashes[h]:
    #             match = 1
    #     if match == 1:
    #   
    #       count_matches += 1
    s_hashes = []         
    for ngram, hash_list in source_hashes:
        # print(ngram)
        s_hashes.append(ngram)
                
    try:
        unique_matches = list(set(count_matches))
        unique_source_hashes = list(set(s_hashes))
        # print(len(unique_matches))
        # print(len(unique_source_hashes))
        per = (len(unique_matches) / len(unique_source_hashes)) * 100 
        # if per == 100:
        #     print(unique_matches)
        #     print(unique_source_hashes)
        return per
    except:
        return 0