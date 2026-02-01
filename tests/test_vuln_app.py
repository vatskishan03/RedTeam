from examples.vuln_app import app


def test_functions_exist():
    assert callable(app.get_user_by_name)
    assert callable(app.deserialize_profile)
    assert callable(app.run_user_command)
    assert callable(app.weak_password_hash)
    assert callable(app.load_config)
    assert callable(app.read_file)


def test_weak_password_hash():
    value = app.weak_password_hash("password")
    assert isinstance(value, str)
    assert len(value) == 32
