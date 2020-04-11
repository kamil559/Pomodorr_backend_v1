from pomodorr.tools.context_processors import settings_context


def test_settings_context(request_factory):
    request = request_factory.get('/')
    context = settings_context(request)

    assert context is not None
