from src.modulus import detect_modulus


def test_detects_modulo_100000():
    result = detect_modulus("Give your answer modulo 100000.")

    assert result.success is True
    assert result.modulus == 100000
    assert result.source == "modulo"
    assert result.matched_text == "modulo 100000"


def test_detects_mod_10_power_5():
    result = detect_modulus("Return the result mod 10^5.")

    assert result.success is True
    assert result.modulus == 100000
    assert result.source == "mod"
    assert result.matched_text == "mod 10^5"


def test_detects_mod_5_power_7():
    result = detect_modulus("Report the answer mod 5^7.")

    assert result.success is True
    assert result.modulus == 78125
    assert result.source == "mod"
    assert result.matched_text == "mod 5^7"


def test_detects_remainder_when_divided_by():
    result = detect_modulus("Find the remainder when divided by 99991.")

    assert result.success is True
    assert result.modulus == 99991
    assert result.source == "remainder_when_divided_by"
    assert result.matched_text == "remainder when divided by 99991"


def test_detects_final_answer_range_instruction():
    result = detect_modulus("The final answer should be in [0, 99999].")

    assert result.success is True
    assert result.modulus == 100000
    assert result.source == "final_answer_range"
    assert result.matched_text == "final answer should be in [0, 99999]"
    assert "used fixed normalization modulus for required final answer range" in result.notes


def test_returns_failure_when_no_modulus_instruction_exists():
    result = detect_modulus("Compute the exact number of lattice paths.")

    assert result.success is False
    assert result.modulus is None
    assert result.source == "none"
    assert result.matched_text is None
    assert "no modulus instruction detected" in result.notes
