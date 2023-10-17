def test_load_env_vars_using_pytest_env() -> None:
    """
    Using pytest_env and pytest.ini
    :return: None
    """
    import os
    assert 'super duper test env test test' == os.environ.get('TEST_ENV')
    assert 'djangoProject.settings' == os.environ.get('DJANGO_SETTINGS_MODULE')
    