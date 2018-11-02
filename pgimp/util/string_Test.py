from pgimp.util.string import escape_single_quotes


def test_escape_single_quotes():
    input = "'abc'"
    expected = "\\'abc\\'"

    assert expected == escape_single_quotes(input)
