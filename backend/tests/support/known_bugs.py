"""Only an explicit violated bug invariant may satisfy most strict xfails."""


class KnownDefect(AssertionError):
    pass


def expect(condition, message):
    if not condition:
        raise KnownDefect(message)
