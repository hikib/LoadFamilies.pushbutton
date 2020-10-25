import re
import pathlib
import itertools

from pyrevit import script

logger = script.get_logger()
output = script.get_output()


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
        if len(list(result)) == 0:
            logger.debug(
                'No {} files in "{}" .'.format(pattern, self.directory))
            output.print_md(
                '### No {} files in "{}" .'.format(pattern, self.directory))
            script.exit()
        self.paths.update({str(path) for path in result})
        logger.debug('Found files: {}'.format(self.paths))

    def exclude_by_pattern(self, pattern):
        self.paths = itertools.ifilterfalse(
            re.compile(pattern).match, self.paths)
        logger.debug('Files passing {} filter:{}'.format(pattern, self.paths))
