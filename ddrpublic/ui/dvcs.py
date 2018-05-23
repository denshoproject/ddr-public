import os

import git


def latest_commit(path):
    """Returns latest commit for the specified repository
    
    TODO pass repo object instead of path
    
    One of several arguments must be provided:
    - Absolute path to a repository.
    - Absolute path to file within a repository. In this case the log
      will be specific to the file.
    
    >>> path = '/path/to/repo'
    >>> latest_commit(path=path)
    'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2 (HEAD, master) 1970-01-01 00:00:00 -0000'
    
    @param path: Absolute path to repo or file within.
    """
    repo = git.Repo(path, search_parent_directories=True)
    if os.path.isfile(path):
        return repo.git.log('--pretty=format:%H %d %ad', '--date=iso', '-1', path)
    else:
        return repo.git.log('--pretty=format:%H %d %ad', '--date=iso', '-1')
    return None
