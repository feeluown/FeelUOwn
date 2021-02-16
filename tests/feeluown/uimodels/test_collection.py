from unittest import mock

from feeluown.collection import Collection, LIBRARY_FILENAME
from feeluown.uimodels.collection import CollectionUiManager
from feeluown.gui.widgets.collections import CollectionsModel


def new_collection(path):
    path.touch()
    coll = Collection(str(path))
    coll.load()
    return coll


def test_predefined_collection_should_on_top(tmp_path, app_mock, mocker):
    mock_add = mocker.patch.object(CollectionUiManager, 'add')
    mock_init = mocker.patch.object(CollectionsModel, '__init__')
    mock_init.return_value = None
    mgr = CollectionUiManager(app_mock)

    coll1 = new_collection(tmp_path / '1.fuo')
    coll2 = new_collection(tmp_path / '2.fuo')
    coll_library = new_collection(tmp_path / LIBRARY_FILENAME)

    app_mock.coll_mgr.scan.return_value = [coll1, coll_library, coll2]
    mgr.initialize()

    mock_add.assert_has_calls([
        mock.call(coll_library),
        mock.call(coll1),
        mock.call(coll2),
    ])
