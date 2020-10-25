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
        if result is None:
            logger.debug(
                'No {} files in "{}" .'.format(pattern, self.directory))
            output.print_md(
                '### No {} files in "{}" .'.format(pattern, self.directory))
            script.exit()
        for path in result:
            logger.debug('Found file: {}'.format(path))
            self.paths.add(str(path))

    def exclude_by_pattern(self, pattern):
        self.paths = itertools.ifilterfalse(
            re.compile(pattern).match, self.paths)
