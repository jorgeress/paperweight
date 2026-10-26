from paperweight.provenance.text_match import contains_value, is_same_value


def test_value_matches_whole_tokens_ignoring_case_and_accents():
    assert contains_value("28013 MADRID", "madrid")
    assert contains_value("29001 Málaga", "MALAGA")
    assert contains_value("75008 Paris, France", "paris france")


def test_partial_token_does_not_match():
    assert not contains_value("MADRIDISTA FC", "MADRID")
    assert not contains_value("PARIS", "PARIS FRANCE")


def test_empty_value_never_matches():
    assert not contains_value("28013 MADRID", "  ")


def test_same_value_normalizes():
    assert is_same_value("São Paulo", "SAO PAULO")
    assert not is_same_value("Madrid", "Madrid Centro")
