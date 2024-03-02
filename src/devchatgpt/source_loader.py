# sourceloader.py
#   SourceLoader class
#
# Jiyong Jang, 2012
#
import sys
import os
import time

import common
import helpers

try:
    import bitarray
except ImportError as err:
    print (err)
    sys.exit(-1)


class SourceLoader(object):

    def __init__(self):
        self._patch_list = []
        self._npatch = 0
        self._source_list = []
        self._nsource = 0
        self._match_dict = {}
        self._nmatch = 0
        self._bit_vector = bitarray.bitarray(common.bloomfilter_size)
        self._results = {}
        self._source_hashes = []
        self._patch_hashes = []

    def traverse(self, source_path, patch, fileExt):
        '''
        Traverse source files
        '''
        common.verbose_print('[+] traversing source files')
        start_time = time.time()
        self._patch_list = patch.items()
        self._npatch = patch.length()

        file_ext = fileExt
        if os.path.isfile(source_path):
            # file_ext = common.file_type(source_path)
            common.verbose_print('  [-] %s: %s' % (source_path, file_ext))
            common.verbose_print(f'Magic type :{file_ext}')
            if file_ext in range(2, 35):
                # main_type, sub_type = file_type.split('/')
                # file_ext = self._get_file_type(sub_type)
                self._process(source_path, file_ext)
        elif os.path.isdir(source_path):
            for root,dirs,files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # file_ext = common.file_type(file_path)
                    common.verbose_print('  [-] %s: %s' % (file_path, file_ext))
                    if file_ext in range(2, 35):
                        # main_type, sub_type = file_type.split('/')
                        # magic_ext = self._get_file_type(sub_type)
                        self._process(file_path, file_ext)

        elapsed_time = time.time() - start_time
        common.verbose_print('[+] %d possible matches ... %.1fs\n' % (self._nmatch, elapsed_time))
        return self._nmatch

    def _process(self, source_path, magic_ext):
        '''
        Normalize a source file and build a Bloom filter for queries
        '''
        source_file = open(source_path, 'r')
        source_orig_lines = source_file.read()
        source_file.close()

        source_norm_lines = self._normalize(source_orig_lines, magic_ext)

        self._query_bloomfilter(source_norm_lines, magic_ext)
#             source_norm_lines = re.split('\n', source_norm_lines)
#             source_orig_lines = re.split('\n', source_orig_lines)
#             self._source_list.append(common.SourceInfo(source_path, magic_ext, source_orig_lines, source_norm_lines))
#             self._nsource += 1

    def _normalize(self, source, fileExt):
        '''
        Normalize a source file
        '''
        _source = helpers.remove_comments(source, fileExt)
        # Remove whitespaces except newlines
        source = common.whitespaces_regex.sub("", _source)
        # Convert into lowercases
        return source.lower()

    def _query_bloomfilter(self, source_norm_lines, magic_ext):
        source_norm_lines = source_norm_lines.split()

        for patch_id in range(0, self._npatch):
            if len(source_norm_lines) < common.ngram_size:
                common.verbose_print('Something wrong with the file!')
                return False
            
            common.ngram_size = self._patch_list[patch_id][6]
            self._bit_vector.setall(0)
            num_ngram = len(source_norm_lines) - common.ngram_size + 1
#             print(f'num_ngram = {num_ngram}')
            is_vuln_source = False
            num_ngram_processed = 0
        
        
            for i in range(0, num_ngram):
                if num_ngram_processed > common.bloomfilter_size/common.min_mn_ratio:
    #                 common.verbose_print('      - split Bloom filters (%d n-grams)' % num_ngram_processed)
                    
                    hash_list_old = self._patch_list['old_norm_lines']
                    is_match = True
                    for h in hash_list_old:
                        if not self._bit_vector[h]:
    #                             print('No Match')
                            is_match = False
                    if is_match:
    #                         print('Matched')
                        is_vuln_source = True
                        self._match_dict[patch_id].append(self._nsource)
    #                         common.verbose_print('      - match (patch #%d : source #%d)' % (patch_id, self._nsource))
                        self._nmatch += 1
                    num_ngram_processed = 0
                    self._bit_vector.setall(0)

                ngram = ''.join(source_norm_lines[i:i+common.ngram_size])
#                 print('using size ' , common.ngram_size)
    #             print(ngram)
                hash1 = common.fnv1a_hash(ngram) & (common.bloomfilter_size-1)
                hash2 = common.djb2_hash(ngram) & (common.bloomfilter_size-1)
                hash3 = common.sdbm_hash(ngram) & (common.bloomfilter_size-1)
                self._bit_vector[hash1] = 1
                self._bit_vector[hash2] = 1
                self._bit_vector[hash3] = 1
    #             print(hash1, ' - ', hash2, ' - ', hash3, '\n')
                num_ngram_processed += 1
                self._source_hashes.append([ngram, [hash1, hash2, hash3]])

            hash_list = self._patch_list[patch_id].hash_list
            is_match = True
            i = 0
            seq = 0
            for h in hash_list:
#                 print('hash_list[h]= ', h)
                if i == 3:
                    i = 0
                    seq += 1

                if patch_id not in self._match_dict:
                    self._match_dict[patch_id] = {}

                if seq not in self._match_dict[patch_id]:
                    self._match_dict[patch_id][seq] = {}

#                 print('self._bit_vector[h] = ', self._bit_vector[h])
                if not self._bit_vector[h]:
                    is_match = False
                    self._results[h] = {}
                    self._results[h]['Match'] = False
                    self._match_dict[patch_id][seq][h] = False
                else:
                    self._results[h] = {}
                    self._results[h]['Match'] = True
                    self._match_dict[patch_id][seq][h] = True

                i += 1

    def items(self):
        return self._source_list

    def length(self):
        return self._nsource

    def match_items(self):
        return self._match_dict

    def results(self):
        return self._results

    def source_hashes(self):
        return self._source_hashes