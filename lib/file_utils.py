import re
import pathlib
import itertools

from pyrevit import script, forms

logger = script.get_logger()


class FileFinder:
    """

    Methods
    -------
    search(str)
        searches in the given absolute path recursively for '.rfa' files.
    """
    def __init__(self, directory):
        self.directory = directory
        self.paths = set()

    def search(self, pattern):
        result = pathlib.Path(self.directory).rglob(pattern)
        for path in result:
            logger.debug('Found file: {}'.format(path))
            self.paths.add(str(path))
        if len(self.paths) == 0:
            logger.debug(
                'No {} files in "{}" found.'.format(pattern, self.directory))
            forms.alert(
                'No {} files in "{}" found.'.format(pattern, self.directory))
            script.exit()

    def exclude_by_pattern(self, pattern):
        self.paths = itertools.ifilterfalse(
            re.compile(pattern).match, self.paths)
