
# GitHub constants
GITHUB_API_BASE_URL = "https://api.github.com/repos/"
GITHUB_BASE_URL = "https://github.com/"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/"

# common.py
# global variables
NGRAM_SIZE   = 4
CONTEXT_LINE = 10
VERBOSE_MODE = False
MAGIC_COOKIE = None
BLOOMFILTER_SIZE = 2097152
MIN_MN_RATIO = 32

BUGFIX_KEYWORDS = ['failur', 'fail', 'npe ', ' npe', 'issue', 'except', 'broken',
                   'crash', 'bug', 'differential testing', 'error', 'incorrect', 'flaw',
                   'addresssanitizer', 'hang ', ' hang', 'jsbugmon', 'leak', 'permaorange',
                   'random orange', 'intermittent', 'regression', 'test fix', 'problem',
                   'heap overflow', 'exception', 'daemon', 'stopped', 'broken', ' fault', 'race condition',
                   'deadlock', 'synchronization error', 'dangling pointer', 'null pointer', 'overflow', 'memory leak',
                   'race condition', 'restart', 'steps to reproduce', 'crash', 'assertion', 'failure', 'leak',
                   'stack trace', 'defect', 'mistake', 'fix', 'avoid',
                   'regression', 'test fix', ' hang', 'hang ', 'heap overflow', 'mozregression', 'safemode',
                   'safe mode', 'stop'
                   ]