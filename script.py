import re
import os

from pyrevit.framework import clr
from pyrevit import forms, revit, DB, script

from pathlib import Path, PurePath


def main():
    """
    TODO:
        - solve folder_options
        - comment all functions/classes
        - log all actions
        - raise exception to quit script
          (if nothing is selected)
        - refactor
        - keep main() ?
        - put your information (bundle?)
    """
    logger = script.get_logger()
    parent_folder = forms.pick_folder("Select parent folder of families")
    logger.debug('Selected parent folder: {}'.format(parent_folder))
    abs_paths = [str(path) for path in Path(parent_folder).rglob('*.rfa')]
    rel_paths = [path.replace(parent_folder, "..") for path in abs_paths]
    path_dict = dict(zip(rel_paths, abs_paths))

    """
    folder_options = {
        'All': sorted(rel_paths, key=lambda x: x.count(os.sep)),
        'Parent folder': [x for x in rel_paths if x.count(os.sep) == 1],
        'Sub folders': [x for x in rel_paths if x.count(os.sep) >= 1],
    }
    """

    folder_options = sorted(rel_paths, key=lambda x: x.count(os.sep))

    selection = forms.SelectFromList.show(
        folder_options,
        title="Select Families",
        #group_selector_title="Select folders",
        width=500,
        button_name="Load Families",
        multiselect=True
    )
    logger.debug('Selected Families: {}'.format(selection))

    loading_option = forms.CommandSwitchWindow.show(
        {"Load all types": "load_all",
         "Load types by selecting individually": "load_selective"},
        folder_loading.keys(),
        message='Select Option:',
    )
    logger.debug('Selected loading option: {}'.format(loading_option))

    if selection:
        for file_name in selection:
            family = FamilyLoader(path_dict[rel_paths])
            loaded = family.is_loaded
            logger.debug('Family already loaded: {}'.format(loaded))
            if not loaded:
                getattr(family, folder_loading[loading_option])()


class FamilyLoader:
    def __init__(self, path):
        self.abs_path = path
        self.name = PurePath(path).name.replace(".rfa", "")

    @property
    def is_loaded(self):
        collector = DB.FilteredElementCollector(revit.doc).OfClass(DB.Family)
        condition = (x for x in collector if x.Name == self.name)
        return next(condition, None) is not None

    def get_symbols(self):
        # DryTransaction will rollback all the changes
        symbol_list = set()
        with revit.ErrorSwallower():
            with revit.DryTransaction('Fake load'):
                ret_ref = clr.Reference[DB.Family]()
                revit.doc.LoadFamily(self.abs_path, ret_ref)
                loaded_fam = ret_ref.Value
                # get the symbols
                for sym_id in loaded_fam.GetFamilySymbolIds():
                    family_symbol = revit.doc.GetElement(sym_id)
                    family_symbol_name = revit.query.get_name(family_symbol)
                    sortable_sym = SmartSortableFamilyType(family_symbol_name)
                    logger.debug('Importable Type: {}'.format(sortable_sym))
                    symbol_list.add(sortable_sym)
                # okay. we have all the symbols.
        """
        if symbol_list == set():
            raise NoSelectionError("No family symbols were selected.")
        else:
            return symbol_list
        """
        return symbol_list

    def load_selective(self):
        # fake load the family so we can get the symbols
        options = sorted(self.get_symbols())
        # ask user for required symbol and load into current document
        if options:
            selected_symbols = forms.SelectFromList.show(
                options,
                title=self.name,
                button_name="Load Type(s)",
                multiselect=True,
                )
            logger.debug('Selected symbols are: {}'.format(selected_symbols))
            if selected_symbols:
                with revit.Transaction('Loaded {}'.format(self.name)):
                    try:
                        for symbol in selected_symbols:
                            logger.debug('Loading symbol: {}'.format(symbol))
                            revit.doc.LoadFamilySymbol(self.abs_path, symbol.type_name)
                        logger.debug('Successfully loaded all selected symbols')
                    except Exception as load_err:
                        logger.error('Error loading family symbol from {} | {}'
                                    .format(self.abs_path, load_err))
                        raise load_err

    def load_all(self):
        try:
            with revit.Transaction('Loaded {}'.format(self.name)):
                revit.doc.LoadFamily(self.abs_path)
        except Exception as load_err:
            logger.error('Error loading family symbol from {} | {}'
                        .format(self.abs_path, load_err))
            raise load_err



# define a class for family types so they can be smartly sorted
class SmartSortableFamilyType:
    def __init__(self, type_name):
        self.type_name = type_name
        self.sort_alphabetically = False
        self.number_list = [int(x) for x in re.findall(r'\d+', self.type_name)]
        if not self.number_list:
            self.sort_alphabetically = True

    def __str__(self):
        return self.type_name

    def __repr__(self):
        return '<SmartSortableFamilyType Name:{} Values:{} StringSort:{}>'\
               .format(self.type_name,
                       self.number_list,
                       self.sort_alphabetically)

    def __eq__(self, other):
        return self.type_name == other.type_name

    def __hash__(self):
        return hash(self.type_name)

    def __lt__(self, other):
        if self.sort_alphabetically or other.sort_alphabetically:
            return self.type_name < other.type_name
        else:
            return self.number_list < other.number_list



if __name__ == "__main__":
    main()