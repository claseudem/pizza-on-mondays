from descriptor import build_company_description, fmt_money, fmt_num


class TestFmtMoney:
    def test_none_is_not_disponible(self):
        assert fmt_money(None) == "N/D"

    def test_nan_is_not_disponible(self):
        assert fmt_money(float("nan")) == "N/D"

    def test_trillions(self):
        assert fmt_money(2_500_000_000_000) == "2.50 T USD"

    def test_billions(self):
        assert fmt_money(3_000_000_000) == "3.00 B USD"

    def test_millions(self):
        assert fmt_money(1_500_000) == "1.50 M USD"

    def test_below_a_million_has_no_suffix(self):
        assert fmt_money(50_000) == "50,000 USD"

    def test_custom_currency(self):
        assert fmt_money(1_000_000, currency="ARS") == "1.00 M ARS"


class TestFmtNum:
    def test_none_is_not_disponible(self):
        assert fmt_num(None) == "N/D"

    def test_nan_is_not_disponible(self):
        assert fmt_num(float("nan")) == "N/D"

    def test_default_pattern(self):
        assert fmt_num(1.23456) == "1.23"

    def test_custom_pattern(self):
        assert fmt_num(0.1534, "{:.1%}") == "15.3%"


class TestBuildCompanyDescription:
    def test_minimal_info_only_has_intro_line(self):
        info = {"symbol": "XYZ", "shortName": "Xyz Corp"}
        description = build_company_description(info)
        assert description == "**Xyz Corp** (XYZ)."

    def test_full_info_includes_every_section(self):
        info = {
            "longName": "Exxon Mobil Corporation",
            "symbol": "XOM",
            "currency": "USD",
            "sector": "Energy",
            "industry": "Oil & Gas Integrated",
            "city": "Spring",
            "country": "United States",
            "fullTimeEmployees": 61000,
            "marketCap": 450_000_000_000,
            "trailingPE": 14.2,
            "forwardPE": 12.8,
            "profitMargins": 0.11,
            "returnOnEquity": 0.18,
            "revenueGrowth": 0.05,
            "debtToEquity": 20.0,
            "currentRatio": 1.3,
            "dividendYield": 3.5,
            "beta": 0.9,
            "targetMeanPrice": 130.0,
            "currentPrice": 120.0,
            "recommendationKey": "buy",
        }
        description = build_company_description(info)

        assert "Exxon Mobil Corporation** (XOM)" in description
        assert "sector **Energy**" in description
        assert "industria **Oil & Gas Integrated**" in description
        assert "Spring, United States" in description
        assert "61,000 empleados" in description
        assert "mega cap" in description
        assert "P/E de 14.2x" in description
        assert "crecimiento de utilidades" in description
        assert "margen neto de 11.0%" in description
        assert "ROE de 18.0%" in description
        assert "ingresos variaron +5.0%" in description
        assert "deuda/patrimonio de 0.20x" in description
        assert "current ratio de 1.30" in description
        assert "Dividendos" in description
        assert "beta de 0.90" in description
        assert "Analistas" in description

    def test_missing_optional_fields_are_omitted(self):
        info = {"symbol": "ABC", "shortName": "Abc Inc"}
        description = build_company_description(info)
        for label in (
            "Tamaño",
            "Valoración",
            "Rentabilidad",
            "Crecimiento",
            "Salud financiera",
            "Dividendos",
            "Riesgo de mercado",
            "Analistas",
        ):
            assert label not in description

    def test_small_cap_classification(self):
        info = {"symbol": "SML", "shortName": "Small Co", "marketCap": 500_000_000}
        assert "small cap" in build_company_description(info)

    def test_beta_above_threshold_is_more_volatile(self):
        info = {"symbol": "VOL", "shortName": "Volatile Co", "beta": 1.5}
        assert "más volátil" in build_company_description(info)

    def test_beta_below_threshold_is_less_volatile(self):
        info = {"symbol": "CLM", "shortName": "Calm Co", "beta": 0.5}
        assert "menos volátil" in build_company_description(info)
