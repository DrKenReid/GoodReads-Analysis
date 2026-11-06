# GoodReads statistics with honest uncertainty
"""
inference.py — Estimates with 95% intervals and the sample size behind them.

The charts built from these show how sure each number is, so a difference
between two small groups doesn't look more real than it is. Intervals are
percentile bootstraps with a fixed seed (the same data gives the same
interval every run) unless a function says otherwise. Nothing here fits a
curve to make a pattern; where a relationship is measured, it's a rank
correlation (Spearman), which assumes only that the variables are ordered.
"""

import re

import numpy as np
import pandas as pd
from scipy import stats

from .analytics import _read_books, primary_genre

LEVEL = 0.95


def bootstrap_ci(values, stat=np.mean, n_boot: int = 10_000, seed: int = 0, level: float = LEVEL):
    """(estimate, low, high) for ``stat`` of ``values``. ``stat`` must take
    ``axis=`` (np.mean, np.median). Fewer than two values: no interval."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return (np.nan, np.nan, np.nan)
    if len(v) < 2:
        return (float(stat(v)), np.nan, np.nan)
    rng = np.random.default_rng(seed)
    boots = stat(v[rng.integers(0, len(v), size=(n_boot, len(v)))], axis=1)
    lo, hi = np.percentile(boots, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return (float(stat(v)), float(lo), float(hi))


def spearman_ci(x, y, n_boot: int = 5_000, seed: int = 0, level: float = LEVEL) -> dict:
    """Spearman's rho with a bootstrap interval (pairs resampled together)
    and its p-value, for paired values with NaNs dropped."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    keep = ~(np.isnan(x) | np.isnan(y))
    x, y = x[keep], y[keep]
    n = len(x)
    if n < 3:
        return {"rho": np.nan, "low": np.nan, "high": np.nan, "p": np.nan, "n": n}
    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, n, size=n)
        if np.ptp(x[i]) and np.ptp(y[i]):
            boots.append(stats.spearmanr(x[i], y[i])[0])
    lo, hi = np.percentile(boots, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return {"rho": float(rho), "low": float(lo), "high": float(hi), "p": float(p), "n": n}


def _rated(df: pd.DataFrame) -> pd.DataFrame:
    read = _read_books(df)
    return read[read["My Rating"] > 0].copy()


def rating_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Books and share at each star, among the books I rated."""
    rated = _rated(df)
    counts = rated["My Rating"].astype(int).value_counts().reindex(range(1, 6), fill_value=0)
    out = counts.rename("Books").to_frame()
    out["Share"] = out["Books"] / max(len(rated), 1)
    out.index.name = "Stars"
    return out.reset_index()


def _words(text) -> int:
    if not isinstance(text, str):
        return 0
    return len(re.sub(r"<[^>]+>", " ", text).split())


def review_length_by_rating(df: pd.DataFrame) -> dict:
    """Median review length (words) at each star, with intervals, among the
    books I rated and reviewed; and how strongly length tracks rating."""
    rated = _rated(df)
    rated["_words"] = rated["My Review"].apply(_words) if "My Review" in rated.columns else 0
    reviewed = rated[rated["_words"] > 0]
    rows = []
    for star in range(1, 6):
        w = reviewed.loc[reviewed["My Rating"] == star, "_words"]
        med, lo, hi = bootstrap_ci(w, np.median)
        rows.append({"Stars": star, "Reviews": len(w), "Median words": med, "Low": lo, "High": hi})
    return {
        "table": pd.DataFrame(rows),
        "correlation": spearman_ci(reviewed["My Rating"], reviewed["_words"]),
        "reviewed": len(reviewed),
        "rated": len(rated),
    }


def rating_vs_community(df: pd.DataFrame) -> dict:
    """How my ratings line up with each book's Goodreads average.

    ``by_star``: the mean community average of the books I gave each star,
    with intervals. ``correlation``: Spearman's rho between my rating and
    the community average. ``difference``: mean (mine minus theirs)."""
    rated = _rated(df)
    rated = rated[rated["Average Rating"] > 0]
    rows = []
    for star in range(1, 6):
        a = rated.loc[rated["My Rating"] == star, "Average Rating"]
        m, lo, hi = bootstrap_ci(a)
        rows.append({"Stars": star, "Books": len(a), "Community mean": m, "Low": lo, "High": hi})
    diff = (rated["My Rating"] - rated["Average Rating"]).to_numpy()
    d, dlo, dhi = bootstrap_ci(diff)
    return {
        "by_star": pd.DataFrame(rows),
        "correlation": spearman_ci(rated["My Rating"], rated["Average Rating"]),
        "difference": {"mean": d, "low": dlo, "high": dhi},
        "higher": int((diff > 0.5).sum()),
        "lower": int((diff < -0.5).sum()),
        "n": len(rated),
    }


def genre_ratings(df: pd.DataFrame, min_books: int = 15) -> pd.DataFrame:
    """Mean rating by each book's top genre, with intervals, for genres with
    at least ``min_books`` rated books (fewer and the interval is too wide
    to say anything). Highest mean first."""
    rated = _rated(df)
    rated["_genre"] = primary_genre(df).reindex(rated.index)
    rows = []
    for genre, g in rated.dropna(subset=["_genre"]).groupby("_genre"):
        if len(g) >= min_books:
            m, lo, hi = bootstrap_ci(g["My Rating"])
            rows.append({"Genre": genre, "Books": len(g), "Mean rating": m, "Low": lo, "High": hi})
    out = pd.DataFrame(rows, columns=["Genre", "Books", "Mean rating", "Low", "High"])
    return out.sort_values("Mean rating", ascending=False).reset_index(drop=True)


def finish_dates(df: pd.DataFrame) -> pd.Series:
    """Every finish of every read book: each reading session's end date from
    the enhanced ``read_dates`` column (``start,end;start,end``), so a
    re-read counts in the year it happened; failing that, ``Date Read``."""
    read = _read_books(df)
    dates = []
    for _, row in read.iterrows():
        rd = row.get("read_dates")
        ends = []
        if isinstance(rd, str) and rd.strip():
            ends = [s.split(",")[-1].strip() for s in rd.split(";") if s.split(",")[-1].strip()]
        if ends:
            dates.extend(pd.to_datetime(ends, errors="coerce"))
        elif pd.notna(row.get("Date Read")):
            dates.append(row["Date Read"])
    return pd.Series(dates, dtype="datetime64[ns]").dropna()


def books_per_year(df: pd.DataFrame, min_books: int = 10) -> pd.DataFrame:
    """Books finished each year, re-reads included (see finish_dates), from
    the first year with at least ``min_books`` (earlier years are
    back-filled dates, not tracking). ``Partial`` marks the current year."""
    counts = finish_dates(df).dt.year.value_counts().sort_index()
    full = counts[counts >= min_books]
    if full.empty:
        return pd.DataFrame(columns=["Year", "Books", "Partial"])
    counts = counts[counts.index >= full.index.min()]
    out = counts.rename("Books").to_frame()
    out.index.name = "Year"
    out = out.reset_index()
    out["Year"] = out["Year"].astype(int)
    out["Partial"] = out["Year"] == pd.Timestamp.now().year
    return out
