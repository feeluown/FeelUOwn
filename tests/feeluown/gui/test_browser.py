from unittest import mock
from feeluown.gui.browser import Browser


def test_browser_basic(app_mock, mocker, album):
    mock_r_search = mocker.patch(
        'feeluown.gui.pages.search.render', new=mock.MagicMock)
    mock_r_model = mocker.patch(
        'feeluown.gui.pages.model.render', new=mock.MagicMock)
    mocker.patch('feeluown.gui.browser.resolve', return_value=album)

    browser = Browser(app_mock)
    browser.initialize()
    browser.goto(page='/search')
    # renderer should be called once
    mock_r_search.assert_called

    browser.goto(model=album)
    mock_r_model.assert_called
    # history should be saved
    assert browser.can_back
    browser.back()
    assert browser.current_page == '/search'

    browser.forward()
    assert browser.current_page.startswith('/models/')
