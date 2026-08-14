import pytest
from ser_pleno.utils.dates import normalize_date, parse_br_date


class TestNormalizeDate:
    def test_br_date_convertido_para_iso(self):
        assert normalize_date("13/08/2026") == "2026-08-13"

    def test_iso_e_aceito(self):
        assert normalize_date("2026-08-13") == "2026-08-13"

    def test_data_invalida_levanta_erro(self):
        with pytest.raises(ValueError):
            normalize_date("13-08-2026")

    def test_data_vazia_levanta_erro(self):
        with pytest.raises(ValueError):
            normalize_date("")

    def test_data_em_branco_levanta_erro(self):
        with pytest.raises(ValueError):
            normalize_date("   ")

    def test_nao_string_levanta_erro(self):
        with pytest.raises(ValueError):
            normalize_date(None)

    def test_traco_levanta_erro(self):
        with pytest.raises(ValueError):
            normalize_date("—")


class TestParseBrDate:
    def test_converte_br_para_iso(self):
        assert parse_br_date("13/08/2026") == "2026-08-13"

    def test_invalido_retorna_none(self):
        assert parse_br_date("13-08-2026") is None
