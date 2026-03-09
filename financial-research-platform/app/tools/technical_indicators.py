"""Technical analysis indicators tool using pandas-ta."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from loguru import logger

try:
    import pandas_ta as ta  # type: ignore
    _TA_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TA_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MPL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MPL_AVAILABLE = False

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NUMPY_AVAILABLE = False

from app.config import settings


class TechnicalIndicatorsTool:
    """Calculate technical indicators and generate price charts."""

    def calculate_indicators(self, price_data: dict) -> dict:
        """Calculate RSI, MACD, Bollinger Bands, SMA and EMA from price_data dict."""
        try:
            df = self._to_dataframe(price_data)
            result: dict = {}

            if _TA_AVAILABLE and not df.empty:
                df.ta.rsi(append=True)
                df.ta.macd(append=True)
                df.ta.bbands(append=True)
                df.ta.sma(length=50, append=True)
                df.ta.sma(length=200, append=True)
                df.ta.ema(length=20, append=True)

                latest = df.iloc[-1]
                result = {
                    "rsi": self._safe(latest, "RSI_14"),
                    "macd": self._safe(latest, "MACD_12_26_9"),
                    "macd_signal": self._safe(latest, "MACDs_12_26_9"),
                    "macd_hist": self._safe(latest, "MACDh_12_26_9"),
                    "bb_upper": self._safe(latest, "BBU_5_2.0"),
                    "bb_middle": self._safe(latest, "BBM_5_2.0"),
                    "bb_lower": self._safe(latest, "BBL_5_2.0"),
                    "sma_50": self._safe(latest, "SMA_50"),
                    "sma_200": self._safe(latest, "SMA_200"),
                    "ema_20": self._safe(latest, "EMA_20"),
                    "current_price": price_data["close"][-1] if price_data.get("close") else None,
                }
            else:
                result = self._mock_indicators()

            return result
        except Exception as exc:
            logger.warning(f"calculate_indicators failed: {exc}")
            return self._mock_indicators()

    def find_support_resistance(self, price_data: dict) -> dict:
        """Identify key support and resistance price levels."""
        try:
            closes = price_data.get("close", [])
            if len(closes) < 20:
                return self._mock_support_resistance()

            closes_series = pd.Series(closes)
            highs = closes_series.nlargest(5).round(2).tolist()
            lows = closes_series.nsmallest(5).round(2).tolist()
            return {
                "resistance_levels": sorted(highs, reverse=True),
                "support_levels": sorted(lows),
            }
        except Exception as exc:
            logger.warning(f"find_support_resistance failed: {exc}")
            return self._mock_support_resistance()

    def generate_chart(self, price_data: dict, ticker: str) -> str:
        """Generate and save a price chart PNG; return the file path."""
        charts_dir = Path(settings.CHARTS_DIR)
        charts_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(charts_dir / f"{ticker}_chart.png")

        if not _MPL_AVAILABLE:
            logger.warning("matplotlib not available; skipping chart generation")
            return output_path

        try:
            dates = price_data.get("dates", [])
            closes = price_data.get("close", [])
            if not closes:
                return output_path

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(range(len(closes)), closes, linewidth=1.5, color="#2196F3", label="Close")
            ax.set_title(f"{ticker} – Price Chart", fontsize=16, fontweight="bold")
            ax.set_xlabel("Trading Days")
            ax.set_ylabel("Price (USD)")
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Annotate with date labels at regular intervals
            if dates:
                step = max(1, len(dates) // 6)
                tick_positions = list(range(0, len(dates), step))
                ax.set_xticks(tick_positions)
                ax.set_xticklabels([dates[i] for i in tick_positions], rotation=45, ha="right")

            plt.tight_layout()
            plt.savefig(output_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            logger.info(f"Chart saved to {output_path}")
        except Exception as exc:
            logger.warning(f"Chart generation failed: {exc}")

        return output_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _to_dataframe(self, price_data: dict) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "open": price_data.get("open", []),
                "high": price_data.get("high", []),
                "low": price_data.get("low", []),
                "close": price_data.get("close", []),
                "volume": price_data.get("volume", []),
            }
        )
        df.columns = [c.lower() for c in df.columns]
        return df

    @staticmethod
    def _safe(series: "pd.Series", col: str):
        try:
            val = series[col]
            return None if pd.isna(val) else round(float(val), 4)
        except (KeyError, TypeError):
            return None

    def _mock_indicators(self) -> dict:
        return {
            "rsi": 55.3,
            "macd": 1.25,
            "macd_signal": 0.98,
            "macd_hist": 0.27,
            "bb_upper": 185.0,
            "bb_middle": 175.0,
            "bb_lower": 165.0,
            "sma_50": 172.5,
            "sma_200": 160.0,
            "ema_20": 174.0,
            "current_price": 175.0,
        }

    def _mock_support_resistance(self) -> dict:
        return {
            "resistance_levels": [185.0, 190.0, 195.0, 200.0, 210.0],
            "support_levels": [165.0, 160.0, 155.0, 150.0, 140.0],
        }

    # ------------------------------------------------------------------
    # New Phase 2 methods
    # ------------------------------------------------------------------

    def compute_all(self, ticker: str, period: str = "1y") -> dict:
        """Fetch OHLCV, compute all indicators, and return a comprehensive dict.

        Computes RSI(14), MACD, Bollinger Bands(20), SMA20, SMA50, Volume SMA20,
        support/resistance levels. Returns last 60 data points for chart efficiency.
        """
        try:
            from app.tools.yfinance_tool import YFinanceTool
            price_data = YFinanceTool().get_historical_prices(ticker, period)
            closes = price_data.get("close", [])
            volumes = price_data.get("volume", [])

            if not closes or len(closes) < 20:
                return self._mock_compute_all()

            if not _NUMPY_AVAILABLE:
                return self._mock_compute_all()

            closes_arr = np.array(closes, dtype=float)
            volumes_arr = np.array(volumes, dtype=float)

            # --- RSI(14) ---
            rsi_arr = self._compute_rsi(closes_arr, period=14)

            # --- MACD: EMA12 - EMA26; signal = EMA9(MACD) ---
            ema12 = self._ema(closes_arr, 12)
            ema26 = self._ema(closes_arr, 26)
            macd_line = ema12 - ema26
            signal_line = self._ema(macd_line, 9)
            histogram = macd_line - signal_line

            # --- Bollinger Bands (20-period SMA ± 2 std) ---
            sma20_arr = self._sma(closes_arr, 20)
            std20 = self._rolling_std(closes_arr, 20)
            bb_upper_arr = sma20_arr + 2 * std20
            bb_lower_arr = sma20_arr - 2 * std20

            # --- SMA50 ---
            sma50_arr = self._sma(closes_arr, 50)

            # --- Volume SMA20 ---
            vol_sma20_arr = self._sma(volumes_arr, 20)

            # --- Support / Resistance (last 20 closes) ---
            recent_closes = closes_arr[-20:]
            support = float(np.min(recent_closes))
            resistance = float(np.max(recent_closes))

            # Trim to last 60 points
            n = min(60, len(closes_arr))
            dates_trimmed = price_data.get("dates", [])[-n:]
            closes_trimmed = closes_arr[-n:].tolist()
            volumes_trimmed = volumes_arr[-n:].tolist()

            def _last(arr):
                a = np.array(arr, dtype=float)
                valid = a[~np.isnan(a)]
                return round(float(valid[-1]), 4) if len(valid) > 0 else None

            return {
                "ticker": ticker,
                "dates": dates_trimmed,
                "close": closes_trimmed,
                "volume": volumes_trimmed,
                "rsi": _last(rsi_arr[-n:]),
                "macd": _last(macd_line[-n:]),
                "signal_line": _last(signal_line[-n:]),
                "macd_histogram": _last(histogram[-n:]),
                "bb_upper": _last(bb_upper_arr[-n:]),
                "bb_middle": _last(sma20_arr[-n:]),
                "bb_lower": _last(bb_lower_arr[-n:]),
                "sma20": _last(sma20_arr[-n:]),
                "sma50": _last(sma50_arr[-n:]),
                "volume_sma20": _last(vol_sma20_arr[-n:]),
                "support": round(support, 4),
                "resistance": round(resistance, 4),
                "current_price": round(float(closes_arr[-1]), 4),
            }
        except Exception as exc:
            logger.warning(f"compute_all failed for {ticker}: {exc}")
            return self._mock_compute_all()

    def generate_chart_from_indicators(self, ticker: str, indicators_data: dict) -> str:
        """Generate a 3-panel chart (Price+BB, Volume, RSI) and save to /tmp/{ticker}_chart.png."""
        output_path = f"/tmp/{ticker}_chart.png"

        if not _MPL_AVAILABLE:
            logger.warning("matplotlib not available; skipping chart generation")
            return ""

        try:
            closes = indicators_data.get("close", [])
            volumes = indicators_data.get("volume", [])
            dates = indicators_data.get("dates", [])

            if not closes:
                return ""

            x = list(range(len(closes)))

            fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1, 1]})

            # --- Top panel: Price + Bollinger Bands + SMA ---
            ax1 = axes[0]
            ax1.plot(x, closes, color="#2196F3", linewidth=1.5, label="Close")

            bb_upper = indicators_data.get("bb_upper")
            bb_lower = indicators_data.get("bb_lower")
            bb_middle = indicators_data.get("bb_middle")

            # Bollinger Band values from compute_all are scalars (last-bar values).
            # Represent them as horizontal reference lines rather than full arrays.
            if bb_upper is not None and bb_lower is not None:
                if isinstance(bb_upper, (int, float)) and isinstance(bb_lower, (int, float)):
                    # Scalar: draw horizontal reference bands
                    ax1.axhline(bb_upper, color="orange", linewidth=0.8, linestyle=":", label=f"BB Upper {bb_upper:.1f}")
                    ax1.axhline(bb_lower, color="orange", linewidth=0.8, linestyle=":", label=f"BB Lower {bb_lower:.1f}")
                    ax1.fill_between(x, [bb_lower] * len(closes), [bb_upper] * len(closes), alpha=0.08, color="orange")
                else:
                    bb_u = list(bb_upper)
                    bb_l = list(bb_lower)
                    ax1.fill_between(x, bb_l, bb_u, alpha=0.15, color="orange", label="BB Band")
            if bb_middle is not None:
                if isinstance(bb_middle, (int, float)):
                    ax1.axhline(bb_middle, color="orange", linewidth=0.8, linestyle="--", label=f"BB Middle {bb_middle:.1f}")
                else:
                    ax1.plot(x, list(bb_middle), color="orange", linewidth=0.8, linestyle="--", label="BB Middle")

            sma20 = indicators_data.get("sma20")
            sma50 = indicators_data.get("sma50")
            if sma20 is not None:
                ax1.axhline(sma20, color="green", linewidth=0.9, linestyle="--",
                            label=f"SMA20 {sma20:.1f}")
            if sma50 is not None:
                ax1.axhline(sma50, color="red", linewidth=0.9, linestyle="--",
                            label=f"SMA50 {sma50:.1f}")

            ax1.set_title(f"{ticker} – Technical Analysis", fontsize=14, fontweight="bold")
            ax1.set_ylabel("Price (USD)")
            ax1.legend(fontsize=7, loc="upper left")
            ax1.grid(True, alpha=0.3)

            # --- Middle panel: Volume ---
            ax2 = axes[1]
            ax2.bar(x, volumes, color="#90CAF9", width=0.8)
            ax2.set_ylabel("Volume")
            ax2.grid(True, alpha=0.3)

            # --- Bottom panel: RSI ---
            ax3 = axes[2]
            rsi_val = indicators_data.get("rsi")
            if rsi_val is not None:
                ax3.axhline(rsi_val, color="#FF5722", linewidth=1.2,
                            label=f"RSI {rsi_val:.1f}")
            ax3.axhline(70, color="red", linewidth=0.8, linestyle="--", alpha=0.7)
            ax3.axhline(30, color="green", linewidth=0.8, linestyle="--", alpha=0.7)
            ax3.fill_between(x, [70] * len(closes), [100] * len(closes), alpha=0.05, color="red")
            ax3.fill_between(x, [0] * len(closes), [30] * len(closes), alpha=0.05, color="green")
            ax3.set_ylim(0, 100)
            ax3.set_ylabel("RSI")
            ax3.legend(fontsize=7)
            ax3.grid(True, alpha=0.3)

            if dates:
                step = max(1, len(dates) // 6)
                tick_positions = list(range(0, len(dates), step))
                ax3.set_xticks(tick_positions)
                ax3.set_xticklabels([dates[i] for i in tick_positions], rotation=45, ha="right")

            plt.tight_layout()
            plt.savefig(output_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            logger.info(f"Technical chart saved to {output_path}")
            return output_path
        except Exception as exc:
            logger.warning(f"Technical chart generation failed for {ticker}: {exc}")
            return ""

    @staticmethod
    def get_trend_signal(indicators_data: dict) -> str:
        """Return BULLISH, BEARISH, or NEUTRAL based on RSI, MACD, SMA alignment."""
        rsi = indicators_data.get("rsi") or 50
        macd = indicators_data.get("macd") or 0
        signal = indicators_data.get("signal_line") or 0
        close = indicators_data.get("current_price") or 0
        sma20 = indicators_data.get("sma20") or 0
        sma50 = indicators_data.get("sma50") or 0

        bullish = rsi > 50 and macd > signal and close > sma20 > sma50
        bearish = rsi < 50 and macd < signal and close < sma20 < sma50

        if bullish:
            return "BULLISH"
        if bearish:
            return "BEARISH"
        return "NEUTRAL"

    # --- Numpy-based indicator helpers ---

    @staticmethod
    def _ema(arr: "np.ndarray", span: int) -> "np.ndarray":
        """Exponential moving average."""
        result = np.full_like(arr, np.nan, dtype=float)
        k = 2.0 / (span + 1)
        result[span - 1] = np.mean(arr[:span])
        for i in range(span, len(arr)):
            result[i] = arr[i] * k + result[i - 1] * (1 - k)
        return result

    @staticmethod
    def _sma(arr: "np.ndarray", window: int) -> "np.ndarray":
        result = np.full_like(arr, np.nan, dtype=float)
        for i in range(window - 1, len(arr)):
            result[i] = np.mean(arr[i - window + 1:i + 1])
        return result

    @staticmethod
    def _rolling_std(arr: "np.ndarray", window: int) -> "np.ndarray":
        result = np.full_like(arr, np.nan, dtype=float)
        for i in range(window - 1, len(arr)):
            result[i] = np.std(arr[i - window + 1:i + 1], ddof=0)
        return result

    def _compute_rsi(self, arr: "np.ndarray", period: int = 14) -> "np.ndarray":
        """Standard Wilder RSI."""
        result = np.full_like(arr, np.nan, dtype=float)
        if len(arr) < period + 1:
            return result
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        for i in range(period, len(arr)):
            idx = i - 1
            avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
            avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
            result[i] = 100 - 100 / (1 + rs)
        return result

    def _mock_compute_all(self) -> dict:
        return {
            "ticker": "MOCK",
            "dates": [],
            "close": [175.0],
            "volume": [50_000_000],
            "rsi": 55.3,
            "macd": 1.25,
            "signal_line": 0.98,
            "macd_histogram": 0.27,
            "bb_upper": 185.0,
            "bb_middle": 175.0,
            "bb_lower": 165.0,
            "sma20": 174.0,
            "sma50": 172.5,
            "volume_sma20": 50_000_000,
            "support": 165.0,
            "resistance": 185.0,
            "current_price": 175.0,
        }


# Alias for new agent usage
TechnicalIndicators = TechnicalIndicatorsTool
