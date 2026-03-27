"""Comprehensive tests for src/analytics.py."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analytics import (
    load_and_clean,
    reading_stats,
    reading_personality,
    rating_analysis,
    books_by_year,
    top_authors,
    shelf_of_shame,
    books_you_loved,
    books_you_hated,
    page_stats,
    stats_commentary,
    shelf_roast,
    books_by_month,
    reading_streak,
    genre_breakdown,
    genre_personality_tags,
    generate_demo_data,
    _read_books,
)


def _make_df(n=10, shelf="read", ratings=None, avg_ratings=None, pages=None,
             dates_read=None, dates_added=None, authors=None, titles=None,
             bookshelves=None):
    """Helper to build a GoodReads-like DataFrame."""
    if ratings is None:
        ratings = [4] * n
    if avg_ratings is None:
        avg_ratings = [3.8] * n
    if pages is None:
        pages = [300] * n
    if dates_read is None:
        base = datetime(2023, 1, 15)
        dates_read = [(base + timedelta(days=i * 30)).strftime("%Y/%m/%d") for i in range(n)]
    if dates_added is None:
        dates_added = dates_read
    if authors is None:
        authors = [f"Author {i}" for i in range(n)]
    if titles is None:
        titles = [f"Book {i}" for i in range(n)]
    if bookshelves is None:
        bookshelves = ["fiction, fantasy"] * n

    return pd.DataFrame({
        "Title": titles,
        "Author": authors,
        "My Rating": ratings,
        "Average Rating": avg_ratings,
        "Number of Pages": pages,
        "Date Read": dates_read,
        "Date Added": dates_added,
        "Exclusive Shelf": [shelf] * n,
        "My Review": [""] * n,
        "Bookshelves": bookshelves,
    })


class TestLoadAndClean:
    def test_date_parsing(self):
        df = _make_df(n=2)
        cleaned = load_and_clean(df)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["Date Read"])
        assert pd.api.types.is_datetime64_any_dtype(cleaned["Date Added"])

    def test_numeric_conversion(self):
        df = _make_df(n=2)
        df["My Rating"] = ["3", "bad"]
        cleaned = load_and_clean(df)
        assert cleaned["My Rating"].iloc[0] == 3.0
        assert pd.isna(cleaned["My Rating"].iloc[1])

    def test_shelf_normalization(self):
        df = _make_df(n=2)
        df["Exclusive Shelf"] = ["  Read ", " TO-READ "]
        cleaned = load_and_clean(df)
        assert cleaned["Exclusive Shelf"].tolist() == ["read", "to-read"]

    def test_missing_values(self):
        df = _make_df(n=2)
        df["Number of Pages"] = [None, "abc"]
        cleaned = load_and_clean(df)
        assert pd.isna(cleaned["Number of Pages"].iloc[0])
        assert pd.isna(cleaned["Number of Pages"].iloc[1])

    def test_shelves_list_created(self):
        df = _make_df(n=1, bookshelves=["fiction, fantasy, sci-fi"])
        cleaned = load_and_clean(df)
        assert "_shelves" in cleaned.columns
        assert cleaned["_shelves"].iloc[0] == ["fiction", "fantasy", "sci-fi"]

    def test_no_bookshelves_column(self):
        df = _make_df(n=1)
        df = df.drop(columns=["Bookshelves"])
        cleaned = load_and_clean(df)
        assert cleaned["_shelves"].iloc[0] == []

    def test_does_not_mutate_input(self):
        df = _make_df(n=2)
        original_cols = list(df.columns)
        load_and_clean(df)
        assert list(df.columns) == original_cols


class TestReadingStats:
    def test_basic_counts(self):
        df = load_and_clean(_make_df(n=5))
        stats = reading_stats(df)
        assert stats["total_books"] == 5
        assert stats["total_pages"] == 1500
        assert stats["avg_pages"] == 300

    def test_avg_rating_excludes_zero(self):
        df = load_and_clean(_make_df(n=3, ratings=[0, 4, 5]))
        stats = reading_stats(df)
        assert stats["avg_rating"] == 4.5
        assert stats["rated_count"] == 2

    def test_only_read_books(self):
        df1 = _make_df(n=3, shelf="read")
        df2 = _make_df(n=2, shelf="to-read")
        df = load_and_clean(pd.concat([df1, df2], ignore_index=True))
        stats = reading_stats(df)
        assert stats["total_books"] == 3

    def test_years_active(self):
        dates = ["2020/06/01", "2021/03/15", "2021/09/01"]
        df = load_and_clean(_make_df(n=3, dates_read=dates))
        stats = reading_stats(df)
        assert stats["years_active"] == 2

    def test_empty_df(self):
        """Empty DF with string-typed shelf column to avoid pandas .str accessor issue."""
        df = pd.DataFrame({
            "Title": pd.Series([], dtype=str),
            "Author": pd.Series([], dtype=str),
            "My Rating": pd.Series([], dtype=float),
            "Average Rating": pd.Series([], dtype=float),
            "Number of Pages": pd.Series([], dtype=float),
            "Date Read": pd.Series([], dtype=str),
            "Date Added": pd.Series([], dtype=str),
            "Exclusive Shelf": pd.Series([], dtype=str),
            "My Review": pd.Series([], dtype=str),
            "Bookshelves": pd.Series([], dtype=str),
        })
        cleaned = load_and_clean(df)
        stats = reading_stats(cleaned)
        assert stats["total_books"] == 0


class TestReadingPersonality:
    def _get_personality(self, **kwargs):
        df = load_and_clean(_make_df(**kwargs))
        stats = reading_stats(df)
        return reading_personality(stats, df)

    def test_critic(self):
        title, emoji, desc = self._get_personality(
            n=15, ratings=[2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2],
            dates_read=["2023/01/01"] * 15
        )
        assert title == "The Critic"

    def test_binge_reader(self):
        # 50 books in 1 year → bpy > 40
        dates = ["2023/01/01"] * 50
        title, emoji, desc = self._get_personality(
            n=50, ratings=[4]*50, dates_read=dates
        )
        assert title == "The Binge Reader"

    def test_deep_diver(self):
        title, emoji, desc = self._get_personality(
            n=5, pages=[500, 600, 450, 480, 520],
            dates_read=["2020/01/01", "2021/01/01", "2022/01/01", "2023/01/01", "2024/01/01"]
        )
        assert title == "The Deep Diver"

    def test_enthusiast(self):
        title, emoji, desc = self._get_personality(
            n=5, ratings=[5, 5, 4, 5, 5],
            dates_read=["2020/01/01", "2021/01/01", "2022/01/01", "2023/01/01", "2024/01/01"]
        )
        assert title == "The Enthusiast"

    def test_returns_tuple_of_three(self):
        result = self._get_personality(n=3)
        assert len(result) == 3
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)


class TestRatingAnalysis:
    def test_basic_analysis(self):
        df = load_and_clean(_make_df(n=3, ratings=[4, 5, 3], avg_ratings=[3.5, 4.0, 3.8]))
        result = rating_analysis(df)
        assert result["has_data"] is True
        assert result["avg_yours"] == 4.0
        assert result["rated_count"] == 3

    def test_no_rated_books(self):
        df = load_and_clean(_make_df(n=3, ratings=[0, 0, 0]))
        result = rating_analysis(df)
        assert result["has_data"] is False

    def test_rating_counts(self):
        df = load_and_clean(_make_df(n=4, ratings=[4, 4, 5, 3]))
        result = rating_analysis(df)
        assert result["rating_counts"][4] == 2
        assert result["rating_counts"][5] == 1


class TestBooksByYear:
    def test_grouping(self):
        dates = ["2022/03/01", "2022/06/15", "2023/01/01"]
        df = load_and_clean(_make_df(n=3, dates_read=dates))
        result = books_by_year(df)
        assert len(result) == 2
        row_2022 = result[result["Year"] == 2022]
        assert row_2022["Books"].iloc[0] == 2

    def test_no_dates(self):
        df = load_and_clean(_make_df(n=2, dates_read=["", ""]))
        result = books_by_year(df)
        assert len(result) == 0

    def test_only_read_books(self):
        df1 = _make_df(n=2, shelf="read", dates_read=["2023/01/01", "2023/06/01"])
        df2 = _make_df(n=1, shelf="to-read", dates_read=["2023/03/01"])
        df = load_and_clean(pd.concat([df1, df2], ignore_index=True))
        result = books_by_year(df)
        assert result["Books"].sum() == 2


class TestTopAuthors:
    def test_counting_and_sorting(self):
        authors = ["Alice", "Bob", "Alice", "Alice", "Bob"]
        df = load_and_clean(_make_df(n=5, authors=authors))
        result = top_authors(df)
        assert result.iloc[0]["Author"] == "Alice"
        assert result.iloc[0]["Books"] == 3

    def test_limit(self):
        authors = [f"Author {i}" for i in range(25)]
        df = load_and_clean(_make_df(n=25, authors=authors,
                                      ratings=[4]*25, avg_ratings=[3.8]*25,
                                      pages=[300]*25,
                                      dates_read=["2023/01/01"]*25,
                                      dates_added=["2023/01/01"]*25,
                                      bookshelves=["fiction"]*25))
        result = top_authors(df, n=10)
        assert len(result) <= 10


class TestShelfOfShame:
    def test_count(self):
        df1 = _make_df(n=3, shelf="read")
        df2 = _make_df(n=5, shelf="to-read")
        df = load_and_clean(pd.concat([df1, df2], ignore_index=True))
        result = shelf_of_shame(df)
        assert result["count"] == 5

    def test_oldest_book(self):
        df = _make_df(n=3, shelf="to-read",
                      dates_added=["2018/01/01", "2020/06/01", "2023/01/01"])
        df = load_and_clean(df)
        result = shelf_of_shame(df)
        assert result["oldest"] is not None
        assert result["oldest"]["title"] == "Book 0"

    def test_zero_tbr(self):
        df = load_and_clean(_make_df(n=3, shelf="read"))
        result = shelf_of_shame(df)
        assert result["count"] == 0


class TestBooksYouLoved:
    def test_diff_calculation(self):
        df = load_and_clean(_make_df(
            n=3,
            ratings=[5, 3, 4],
            avg_ratings=[3.0, 4.0, 3.9],
            titles=["Loved It", "Meh", "Okay"]
        ))
        result = books_you_loved(df, n=1)
        assert len(result) == 1
        assert result.iloc[0]["Title"] == "Loved It"
        assert result.iloc[0]["_diff"] == 2.0

    def test_empty_when_no_ratings(self):
        df = load_and_clean(_make_df(n=2, ratings=[0, 0]))
        result = books_you_loved(df)
        assert len(result) == 0


class TestPageStats:
    def test_basic_stats(self):
        df = load_and_clean(_make_df(n=3, pages=[100, 200, 600],
                                      titles=["Short", "Mid", "Long"]))
        result = page_stats(df)
        assert result["has_data"] is True
        assert result["min"] == 100
        assert result["max"] == 600
        assert result["total"] == 900
        assert result["shortest_title"] == "Short"
        assert result["longest_title"] == "Long"

    def test_no_pages(self):
        df = _make_df(n=2)
        df = df.drop(columns=["Number of Pages"])
        df = load_and_clean(df)
        result = page_stats(df)
        assert result["has_data"] is False


class TestStatsCommentary:
    def test_returns_string(self):
        stats = {
            "total_books": 55,
            "total_pages": 15000,
            "avg_rating": 4.0,
            "avg_pages": 280,
            "avg_community_rating": 3.9,
            "years_active": 3,
            "rated_count": 50,
        }
        result = stats_commentary(stats)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_high_books(self):
        stats = {"total_books": 250, "total_pages": 60000, "avg_rating": 4.0,
                 "avg_pages": 300, "avg_community_rating": 3.9, "years_active": 5, "rated_count": 200}
        result = stats_commentary(stats)
        assert "library" in result.lower()

    def test_low_rating(self):
        stats = {"total_books": 30, "total_pages": 8000, "avg_rating": 2.5,
                 "avg_pages": 270, "avg_community_rating": 3.9, "years_active": 3, "rated_count": 25}
        result = stats_commentary(stats)
        assert "enjoy" in result.lower() or "2.5" in result


class TestShelfRoast:
    def test_zero(self):
        assert "Zero" in shelf_roast(0) or "zero" in shelf_roast(0).lower()

    def test_small(self):
        result = shelf_roast(10)
        assert "10" in result

    def test_medium(self):
        result = shelf_roast(75)
        assert "75" in result

    def test_large(self):
        result = shelf_roast(150)
        assert "150" in result

    def test_huge(self):
        result = shelf_roast(300)
        assert "300" in result

    def test_extreme(self):
        result = shelf_roast(600)
        assert "600" in result

    def test_all_return_strings(self):
        for count in [0, 5, 25, 60, 120, 250, 500]:
            assert isinstance(shelf_roast(count), str)


class TestDemoData:
    def test_generates_dataframe(self):
        df = generate_demo_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 50

    def test_has_required_columns(self):
        df = generate_demo_data()
        for col in ["Title", "Author", "My Rating", "Average Rating",
                     "Number of Pages", "Date Read", "Exclusive Shelf"]:
            assert col in df.columns

    def test_has_tbr_books(self):
        df = generate_demo_data()
        assert (df["Exclusive Shelf"] == "to-read").sum() > 0

    def test_pipeline_integration(self):
        """Full pipeline: generate → clean → stats → personality."""
        df = generate_demo_data()
        cleaned = load_and_clean(df)
        stats = reading_stats(cleaned)
        title, emoji, desc = reading_personality(stats, cleaned)
        assert stats["total_books"] > 0
        assert isinstance(title, str)
