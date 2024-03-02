import pandas as pd
import requests
import json
import sys
import os
from time import time
from functools import wraps
from dateutil import parser
from datetime import datetime, timedelta
import constant,common
import re

class GetOutOfLoop(Exception):
    pass

def unique(list):
    unique_list = pd.Series(list).drop_duplicates().to_list()
    return unique_list

def api_request(url, token):
    '''Takes the URL for the request and token
    Examples:
        >> apiRequest("https://github.com/linkedin", "xxxxxxxx")
    Args:
        url (String): the url for the request
        token (String): GitHub API token
    Return:
        response body of the request on json format
    '''
    header = {'Authorization': 'token %s' % token}
    response = requests.get(url, headers=header)
    try:
        json_response = json.loads(response.content)
        return json_response
    except Exception as e:
        return response

def get_response(url, token_list, ct):
    '''get content of the requested endpoint

    Args:
        url (String): url of the request
        token_list (list): GitHub API token list
        ct (int): token counter
    
    Return:
        Jsondata (object): json data 
    '''
    json_data = None

    # token_list, len_tokens = tokens()
    len_tokens = len(token_list)
    try:
        ct = ct % len_tokens
        headers = {'Authorization': 'Bearer {}'.format(token_list[ct])}
        request = requests.get(url, headers=headers)
        json_data = json.loads(request.content)
        ct += 1
    except Exception as e:
        print(e)
        print("Error in func: [get_response]...")
    return json_data, ct

def file_name(name):
    """
    file_name(name)
    Extract the file name used for storing the file
    
    Args:
        name (String): the patch retrieved from the commit api for the file
    """
    if name.startswith('.'):
        return (name[1:])
    elif '/' in name:
        return(name.split('/')[-1])
    elif '/' not in name:
        return(name)
    else: 
        sys.exit(1)


def file_dir(name):
    if name.startswith('.'):
        return (name[1])
    elif '/' in name:
        return(name.split('/')[:-1])
    elif '/' not in name:
        return ''
    else: 
        sys.exit(1)
    

def save_file(file, storageDir, fileName):
    if not os.path.exists(storageDir):
        os.makedirs(storageDir)
        f = open(storageDir + fileName, 'xb')
        f.write(file)
        f.close()
    else:
        f = open(storageDir + fileName, 'wb')
        f.write(file)
        f.close()


def get_file_type(file_path):
    '''
    Guess a file type based upon a file extension (mimetypes module)
    '''
    name = file_name(file_path)
    if name.lower() == 'requirements.txt' or name.lower() == 'requirement.txt':
        file_ext = common.FileExt.REQ_TXT
    else:
        ext = file_path.split('.')[-1]
        file_ext = None
        if ext == 'c' or ext == 'h' or ext == 'cpp':
            file_ext = common.FileExt.C
        elif ext == 'java' or ext == 'cs':
            file_ext = common.FileExt.Java
        elif ext == 'sh':
            file_ext = common.FileExt.ShellScript
        elif ext == 'pl':
            file_ext = common.FileExt.Perl
        elif ext == 'py':
            file_ext = common.FileExt.Python
        elif ext == 'php':
            file_ext = common.FileExt.PHP
        elif ext == 'rb':
            file_ext = common.FileExt.Ruby
        elif ext == 'js' or ext == 'jsx' or ext == 'ts' or ext == 'vue':
            file_ext = common.FileExt.JavaScript
        elif ext == 'scala':
            file_ext = common.FileExt.Scala
        elif ext == 'yaml' or ext == 'yml':
            file_ext = common.FileExt.yaml
        elif ext == 'ipynb':
            file_ext = common.FileExt.ipynb
        elif ext == 'json':
            file_ext = common.FileExt.JSON
        elif ext == 'kt':
            file_ext = common.FileExt.Kotlin
        elif ext == 'gradle':
            file_ext = common.FileExt.gradle
        elif ext == 'gemfile':
            file_ext = common.FileExt.GEMFILE    
        elif ext == 'xml':
            file_ext = common.FileExt.Xml
        elif ext == 'md':
            file_ext = common.FileExt.markdown
        elif ext == 'go':
            file_ext = common.FileExt.goland
        elif ext == 'css':
            file_ext = common.FileExt.CSS
        elif ext == 'html':
            file_ext = common.FileExt.html
        elif ext == 'fs':
            file_ext = common.FileExt.Fsharp
        elif ext == 'regex':
            file_ext = common.FileExt.REGEX
        elif ext == 'conf':
            file_ext = common.FileExt.conf
        else:
            file_ext = common.FileExt.Text

    return file_ext

def remove_comments(source, fileExt):
    if fileExt in [common.FileExt.C, common.FileExt.Java, common.FileExt.goland, common.FileExt.CSS]:
        norm_lines = []
        for c in common.c_regex.finditer(source):
            if c.group('noncomment'):
                norm_lines.append(c.group('noncomment'))
            elif c.group('multilinecomment'):
                newlines_cnt = c.group('multilinecomment').count('\n')
                while newlines_cnt:
                    norm_lines.append('\n')
                    newlines_cnt -= 1
        source = ''.join(norm_lines)

    elif fileExt == common.FileExt.Python or fileExt == common.FileExt.conf:
        source = ''.join([c.group('noncomment') for c in common.py_regex.finditer(source) if c.group('noncomment')])
        source = ''.join(
            [c.group('noncomment') for c in common.py_multiline_1_regex.finditer(source) if c.group('noncomment')])
        source = ''.join(
            [c.group('noncomment') for c in common.py_multiline_2_regex.finditer(source) if c.group('noncomment')])
        
    elif fileExt == common.FileExt.ShellScript:
        source = ''.join(
            [c.group('noncomment') for c in common.shellscript_regex.finditer(source) if c.group('noncomment')])
        
    elif fileExt == common.FileExt.Perl:
        source = ''.join([c.group('noncomment') for c in common.perl_regex.finditer(source) if c.group('noncomment')])

    elif fileExt == common.FileExt.PHP:
        norm_lines = []
        for c in common.php_regex.finditer(source):
            if c.group('noncomment'):
                norm_lines.append(c.group('noncomment'))
            elif c.group('multilinecomment'):
                newlines_cnt = c.group('multilinecomment').count('\n')
                while newlines_cnt:
                    norm_lines.append('\n')
                    newlines_cnt -= 1
        source = ''.join(norm_lines)

    elif fileExt == common.FileExt.Ruby or fileExt == common.FileExt.GEMFILE:
        norm_lines = []
        for c in common.ruby_regex.finditer(source):
            if c.group('noncomment'):
                norm_lines.append(c.group('noncomment'))
            elif c.group('multilinecomment'):
                newlines_cnt = c.group('multilinecomment').count('\n')
                while newlines_cnt:
                    norm_lines.append('\n')
                    newlines_cnt -= 1
        source = ''.join(norm_lines)

    elif fileExt in [common.FileExt.Scala, common.FileExt.JavaScript, common.FileExt.TypeScript, common.FileExt.Kotlin, common.FileExt.gradle]:
        source = ''.join([c.group('noncomment') for c in common.js_regex.finditer(source) if c.group('noncomment')])
        source = ''.join(
            [c.group('noncomment') for c in common.js_partial_comment_regex.finditer(source) if c.group('noncomment')])
        
    elif fileExt == common.FileExt.yaml:
        source = ''.join([c.group('noncomment') for c in common.yaml_regex.finditer(source) if c.group('noncomment')])
        source = re.sub(common.yaml_double_quote_regex, "", source)
        source = re.sub(common.yaml_single_quote_regex, "", source)
    
    elif fileExt == common.FileExt.ipynb:
        json_data = json.loads(source)
        python_code = ""

        for i in json_data['cells']:
            for j in i['source']:
                if j.endswith('\n'):
                    python_code += j
                else:
                    python_code += j + '\n'

        source = ''.join([c.group('noncomment') for c in common.py_regex.finditer(python_code) if c.group('noncomment')])
        source = ''.join(
            [c.group('noncomment') for c in common.py_multiline_1_regex.finditer(source) if c.group('noncomment')])
        source = ''.join(
            [c.group('noncomment') for c in common.py_multiline_2_regex.finditer(source) if c.group('noncomment')])
        
    elif fileExt == common.FileExt.JSON:
        source = common.whitespaces_regex.sub("", source)
        source = source.lower()
#         source = source.split()
        
    elif fileExt in [common.FileExt.Xml, common.FileExt.markdown, common.FileExt.html]:
        source = ''.join([c.group('noncomment') for c in common.xml_regex.finditer(source) if c.group('noncomment')])
    return source


def timing(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kwargs, te - ts))
        return result

    return wrap

def count_LOC(file):
    # Initialize a counter for the lines of code
    line_count = 0

    # Open the file in read mode
    with open(file, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            # Increment the line count
            line_count += 1

    return line_count