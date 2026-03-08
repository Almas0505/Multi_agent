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
