"""Tests for src/inference.py."""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analytics import load_and_clean
from src.inference import (
    books_per_year,
    bootstrap_ci,
    genre_ratings,
    rating_distribution,
    rating_vs_community,
    review_length_by_rating,
    spearman_ci,
)


def _df(ratings, avg=None, reviews=None, genres=None, dates=None):
    n = len(ratings)
    df = pd.DataFrame({
        "Title": [f"Book {i}" for i in range(n)],
        "Author": ["A"] * n,
        "My Rating": ratings,
        "Exclusive Shelf": ["read"] * n,
        "Date Read": dates or ["2024/01/01"] * n,
        "My Review": reviews or [""] * n,
    })
    if avg is not None:
        df["average_rating"] = avg
    if genres is not None:
        df["genres"] = genres
    return load_and_clean(df)


class TestBootstrap:
    def test_interval_brackets_the_estimate_and_is_reproducible(self):
        v = np.random.default_rng(1).normal(10, 2, 200)
        a = bootstrap_ci(v)
        assert a[1] < a[0] < a[2]
        assert a == bootstrap_ci(v)

    def test_interval_narrows_with_more_data(self):
        rng = np.random.default_rng(2)
        small, big = bootstrap_ci(rng.normal(0, 1, 20)), bootstrap_ci(rng.normal(0, 1, 2000))
        assert (big[2] - big[1]) < (small[2] - small[1])

    def test_too_little_data(self):
        assert np.isnan(bootstrap_ci([])[0])
        assert bootstrap_ci([3.0])[0] == 3.0 and np.isnan(bootstrap_ci([3.0])[1])


class TestSpearman:
    def test_perfect_rank_agreement(self):
        r = spearman_ci([1, 2, 3, 4, 5, 6], [10, 20, 30, 40, 50, 60])
        assert r["rho"] == pytest.approx(1.0)

    def test_unrelated_values_interval_spans_zero(self):
        rng = np.random.default_rng(3)
        r = spearman_ci(rng.normal(size=300), rng.normal(size=300))
        assert r["low"] < 0 < r["high"]


class TestDistribution:
    def test_shares_sum_to_one_and_unrated_excluded(self):
        d = rating_distribution(_df([5, 5, 4, 0, 1]))
        assert d["Books"].tolist() == [1, 0, 0, 1, 2]
        assert d["Share"].sum() == pytest.approx(1.0)


class TestReviewLength:
    def test_counts_words_without_html(self):
        res = review_length_by_rating(_df([5, 1, 3], reviews=["Fun read.", "a b c d<br/>e f", ""]))
        t = res["table"].set_index("Stars")
        assert t.loc[5, "Median words"] == 2 and t.loc[1, "Median words"] == 6
        assert res["reviewed"] == 2 and t.loc[3, "Reviews"] == 0


class TestCommunity:
    def test_by_star_and_difference(self):
        res = rating_vs_community(_df([5, 5, 1, 1], avg=["4.5", "4.3", "3.5", "3.7"]))
        t = res["by_star"].set_index("Stars")
        assert t.loc[5, "Community mean"] == pytest.approx(4.4)
        assert t.loc[1, "Community mean"] == pytest.approx(3.6)
        assert res["n"] == 4 and res["difference"]["mean"] == pytest.approx(-1.0)

    def test_no_community_data(self):
        assert rating_vs_community(_df([5, 4]))["n"] == 0


class TestGenres:
    def test_small_genres_left_out(self):
        genres = ["Fantasy|100"] * 16 + ["Horror|100"] * 3
        res = genre_ratings(_df([5] * 16 + [2] * 3, genres=genres), min_books=15)
        assert res["Genre"].tolist() == ["Fantasy"] and res.loc[0, "Books"] == 16


class TestBooksPerYear:
    def test_back_filled_years_dropped_and_current_year_marked(self):
        this_year = pd.Timestamp.now().year
        dates = ["1999/01/01"] + [f"{this_year - 1}/03/01"] * 12 + [f"{this_year}/02/01"] * 3
        out = books_per_year(_df([4] * len(dates), dates=dates))
        assert out["Year"].tolist() == [this_year - 1, this_year]
        assert out["Partial"].tolist() == [False, True]


class TestFinishDates:
    def test_rereads_count_in_their_own_years(self):
        df = _df([5, 4], dates=["2024/06/01", "2023/01/01"])
        df["read_dates"] = [",2019-03-01;,2024-06-01", None]
        out = books_per_year(df, min_books=1).set_index("Year")["Books"]
        assert out.to_dict() == {2019: 1, 2023: 1, 2024: 1}
