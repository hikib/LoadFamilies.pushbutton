import re
import os
import pathlib
from pyrevit import forms, script
from helpers import FamilyLoader

logger = script.get_logger()
# logger.set_debug_mode()

# Get directory with families
directory = forms.pick_folder("Select parent folder of families")
logger.debug('Selected parent folder: {}'.format(directory))
if directory is None:
    logger.debug('No directory selected. Calling script.exit')
    script.exit()

# Find .rfa files in directory
# Excluding backups
with_backups = [str(path) for path in pathlib.Path(directory).rglob('*.rfa')]
backup_pattern = re.compile('^.*\.\d{4}\.rfa$')
abs_paths = [i for i in with_backups if not backup_pattern.match(i)]

logger.debug('Search result for {} files: {}'.format('*.rfa', abs_paths))

# Dictionary to look up absolute paths by relative paths
rel_paths = [path.replace(directory, "..") for path in abs_paths]
logger.debug('Relative paths of files: {}'.format(rel_paths))
path_dict = dict(zip(rel_paths, abs_paths))

# User input -> Select families from directory
family_select_options = sorted(
    path_dict.keys(),
    key=lambda x: (x.count(os.sep), x))
selected_families = forms.SelectFromList.show(
    family_select_options,
    title="Select Families",
    width=500,
    button_name="Load Families",
    multiselect=True)
if selected_families is None:
    logger.debug('No families selected. Calling script.exit()')
    script.exit()
logger.debug('Selected Families: {}'.format(selected_families))

# User input -> Select loading option (load all, load certain symbols)
# Dictionary to look up FamilyLoader method by selected option
family_loading_options = {
    "Load all types": "load_all",
    "Load types by selecting individually": "load_selective"}
selected_loading_option = forms.CommandSwitchWindow.show(
    family_loading_options.keys(),
    message='Select Option:',
)
if selected_loading_option is None:
    logger.debug('No loading option selected. Calling script.exit()')
    script.exit()
logger.debug('Selected loading option: {}'.format(selected_loading_option))

# Loading selected families
for family_path in selected_families:
    family = FamilyLoader(path_dict[family_path])
    logger.debug('Loading family: {}'.format(family.name))
    loaded = family.is_loaded
    logger.debug('Family is already loaded: {}'.format(loaded))
    if not loaded:
        # Call FamilyLoad method by selected loading option
        getattr(family, family_loading_options[selected_loading_option])()
