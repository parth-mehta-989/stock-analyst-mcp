"""Tests for FA runners: ratio_runner, dcf_runner, forecast_runner."""

import pytest

from stock_analyst.fa.ratio_runner import run_ratios
from stock_analyst.fa.dcf_runner import run_dcf
from stock_analyst.fa.forecast_runner import run_forecast
from stock_analyst.fa.ratio_calculator import safe_divide, FinancialRatioCalculator
from stock_analyst.fa.dcf_valuation import DCFModel
from stock_analyst.fa.forecast_builder import ForecastBuilder, simple_linear_regression


class TestSafeDivide:
    def test_normal(self):
        assert safe_divide(10, 2) == 5.0

    def test_zero_denominator(self):
        assert safe_divide(10, 0) == 0.0

    def test_none_denominator(self):
        assert safe_divide(10, None) == 0.0

    def test_custom_default(self):
        assert safe_divide(10, 0, default=-1) == -1


class TestRatioCalculator:
    @pytest.fixture
    def calc(self):
        data = {
            "income_statement": {
                "revenue": 250e9, "cost_of_goods_sold": 180e9,
                "operating_income": 50e9, "net_income": 40e9,
                "interest_expense": 1e9, "ebitda": 55e9,
            },
            "balance_sheet": {
                "total_equity": 100e9, "total_assets": 200e9,
                "current_assets": 80e9, "current_liabilities": 60e9,
                "inventory": 5e9, "cash_and_equivalents": 30e9,
                "total_debt": 10e9, "accounts_receivable": 25e9,
            },
            "cash_flow": {"operating_cash_flow": 60e9},
            "market_data": {
                "market_cap": 12e12, "share_price": 3500,
                "shares_outstanding": 3.6e9, "earnings_growth_rate": 0.10,
            },
        }
        return FinancialRatioCalculator(data)

    def test_profitability(self, calc):
        ratios = calc.calculate_profitability()
        assert ratios["roe"]["value"] == pytest.approx(0.4, rel=0.01)
        assert ratios["net_margin"]["value"] == pytest.approx(0.16, rel=0.01)

    def test_liquidity(self, calc):
        ratios = calc.calculate_liquidity()
        assert ratios["current_ratio"]["value"] == pytest.approx(1.33, rel=0.01)

    def test_leverage(self, calc):
        ratios = calc.calculate_leverage()
        assert ratios["debt_to_equity"]["value"] == pytest.approx(0.1, rel=0.01)

    def test_efficiency(self, calc):
        ratios = calc.calculate_efficiency()
        assert ratios["asset_turnover"]["value"] == pytest.approx(1.25, rel=0.01)

    def test_valuation(self, calc):
        ratios = calc.calculate_valuation()
        assert ratios["pe_ratio"]["value"] > 0

    def test_calculate_all(self, calc):
        calc.calculate_all()
        assert "profitability" in calc.results
        assert "valuation" in calc.results

    def test_to_json(self, calc):
        calc.calculate_all()
        result = calc.to_json()
        assert "categories" in result

    def test_interpret_ratio(self, calc):
        interp = calc.interpret_ratio("roe", 0.30)
        assert isinstance(interp, str)
        assert len(interp) > 0


class TestRunRatios:
    def test_returns_dict(self):
        data = {
            "income_statement": {"revenue": 100, "cost_of_goods_sold": 60, "operating_income": 20, "net_income": 15, "interest_expense": 2, "ebitda": 25},
            "balance_sheet": {"total_equity": 50, "total_assets": 100, "current_assets": 40, "current_liabilities": 30, "inventory": 5, "cash_and_equivalents": 10, "total_debt": 20, "accounts_receivable": 8},
            "cash_flow": {"operating_cash_flow": 18},
            "market_data": {"market_cap": 500, "share_price": 50, "shares_outstanding": 10, "earnings_growth_rate": 0.05},
        }
        result = run_ratios(data)
        assert "categories" in result


class TestDCFModel:
    @pytest.fixture
    def model(self):
        m = DCFModel()
        m.set_historical_financials({
            "revenue": [200e9, 230e9, 250e9],
            "net_debt": -20e9,
            "shares_outstanding": 3.6e9,
        })
        m.set_assumptions({
            "projection_years": 5,
            "terminal_growth_rate": 0.025,
            "exit_ev_ebitda_multiple": 12.0,
            "terminal_ebitda_margin": 0.20,
            "wacc_inputs": {
                "risk_free_rate": 0.07, "equity_risk_premium": 0.06,
                "beta": 0.7, "cost_of_debt": 0.09, "tax_rate": 0.25,
                "debt_weight": 0.30, "equity_weight": 0.70,
            },
        })
        return m

    def test_wacc(self, model):
        wacc = model.calculate_wacc()
        assert 0.05 < wacc < 0.20

    def test_project_cash_flows(self, model):
        model.calculate_wacc()
        rev, fcf = model.project_cash_flows()
        assert len(rev) == 5
        assert all(r > 0 for r in rev)

    def test_full_valuation(self, model):
        result = model.run_full_valuation()
        assert "wacc" in result
        assert "value_per_share" in result

    def test_sensitivity(self, model):
        model.run_full_valuation()
        sa = model.sensitivity_analysis()
        assert "share_price_table" in sa

    def test_no_revenue_raises(self):
        m = DCFModel()
        m.set_historical_financials({"revenue": []})
        m.set_assumptions({"wacc_inputs": {}})
        m.calculate_wacc()
        with pytest.raises(ValueError):
            m.project_cash_flows()


class TestRunDcf:
    def test_returns_dict(self, config):
        data = {
            "historical": {"revenue": [100, 110, 120], "net_debt": 10, "shares_outstanding": 100},
            "assumptions": {
                "projection_years": 5, "terminal_growth_rate": 0.025,
                "exit_ev_ebitda_multiple": 12, "terminal_ebitda_margin": 0.2,
                "wacc_inputs": {"risk_free_rate": 0.07, "equity_risk_premium": 0.06, "beta": 1.0, "cost_of_debt": 0.09, "tax_rate": 0.25, "debt_weight": 0.3, "equity_weight": 0.7},
            },
        }
        result = run_dcf(data, config)
        assert "wacc" in result
        assert "value_per_share" in result


class TestSimpleLinearRegression:
    def test_perfect_line(self):
        slope, intercept, r2 = simple_linear_regression([1, 2, 3], [2, 4, 6])
        assert slope == pytest.approx(2.0)
        assert intercept == pytest.approx(0.0)
        assert r2 == pytest.approx(1.0)

    def test_too_few_points(self):
        assert simple_linear_regression([1], [2]) == (0.0, 0.0, 0.0)


class TestForecastBuilder:
    @pytest.fixture
    def builder(self):
        return ForecastBuilder({
            "forecast_periods": 12,
            "historical_periods": [{"revenue": 200e9}, {"revenue": 230e9}, {"revenue": 250e9}],
            "assumptions": {"revenue_growth_rate": 0.08, "gross_margin": 0.4, "opex_pct_revenue": 0.25},
            "scenarios": {
                "base": {"growth_adjustment": 0.0, "margin_adjustment": 0.0},
                "bull": {"growth_adjustment": 0.05, "margin_adjustment": 0.02},
                "bear": {"growth_adjustment": -0.05, "margin_adjustment": -0.02},
            },
        })

    def test_trend_analysis(self, builder):
        result = builder.analyze_trends()
        assert result["trend"]["direction"] == "upward"
        assert result["average_growth_rate"] > 0

    def test_base_forecast(self, builder):
        result = builder.build_driver_based_forecast("base")
        assert result["scenario"] == "base"
        assert len(result["forecast_periods"]) == 12

    def test_bull_forecast(self, builder):
        result = builder.build_driver_based_forecast("bull")
        assert result["growth_rate"] > 0.08

    def test_run_full_forecast(self, builder):
        result = builder.run_full_forecast(scenarios=["base", "bull", "bear"])
        assert "trend_analysis" in result
        assert "scenario_comparison" in result


class TestRunForecast:
    def test_returns_dict(self, config):
        data = {
            "forecast_periods": 12,
            "historical_periods": [{"revenue": 100}, {"revenue": 110}],
            "assumptions": {"revenue_growth_rate": 0.05, "gross_margin": 0.4, "opex_pct_revenue": 0.25},
            "scenarios": {
                "base": {"growth_adjustment": 0.0, "margin_adjustment": 0.0},
            },
        }
        result = run_forecast(data, config)
        assert "trend" in result or "scenarios" in result
