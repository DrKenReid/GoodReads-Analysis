"""Write the reading-analysis snapshot that kenreid.co.uk's literature page shows.

    python scripts/site_summary.py <enhanced-export.csv> <out.json> --exported YYYY-MM-DD

The site builds most of its reading figures every week from the Goodreads
RSS feed. The feed can't say how a book's Goodreads average compares with
mine, what genre it is, or what's on the to-read and did-not-finish shelves;
an export enhanced with Enhance-GoodReads-Export can. This writes those
figures, with their 95% intervals and sample sizes (src/inference.py), as a
dated snapshot: they're true as of the export and no later.
"""
import argparse
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analytics import load_and_clean, primary_genre  # noqa: E402
from src import inference as inf  # noqa: E402


def r(x, n=2):
    return None if x is None or x != x else round(float(x), n)


def summary(df: pd.DataFrame, exported: str, min_genre_books: int = 15) -> dict:
    shelves = df["Exclusive Shelf"].value_counts()
    rated = inf._rated(df)
    community = inf.rating_vs_community(df)
    genres = inf.genre_ratings(df, min_books=min_genre_books)
    # Counted by each book's top genre, so the count and the mean rating
    # beside it are about the same books (not the user's own shelves).
    counts = primary_genre(df).dropna().value_counts() if "genres" in df.columns else pd.Series(dtype=int)
    out = {
        "exported": exported,
        "shelves": {
            "read": int(shelves.get("read", 0)),
            "toRead": int(shelves.get("to-read", 0)),
            "didNotFinish": int(shelves.get("did-not-finish", 0)),
        },
        "rated": len(rated),
        "fourOrFive": r((rated["My Rating"] >= 4).mean(), 3),
        "community": None,
        "genres": [],
        "topGenre": None,
    }
    if community["n"]:
        c, d = community["correlation"], community["difference"]
        both = rated[rated["Average Rating"] > 0]
        out["community"] = {
            "books": community["n"],
            "myMean": r(both["My Rating"].mean()), "crowdMean": r(both["Average Rating"].mean()),
            "difference": r(d["mean"]), "differenceLow": r(d["low"]), "differenceHigh": r(d["high"]),
            "rho": r(c["rho"]), "rhoLow": r(c["low"]), "rhoHigh": r(c["high"]),
            "byStar": [
                {"stars": int(s["Stars"]), "books": int(s["Books"]), "mean": r(s["Community mean"]),
                 "low": r(s["Low"]), "high": r(s["High"])}
                for _, s in community["by_star"].iterrows() if s["Books"] > 0
            ],
        }
    out["genres"] = [
        {"genre": g["Genre"], "books": int(g["Books"]), "mean": r(g["Mean rating"]),
         "low": r(g["Low"]), "high": r(g["High"])}
        for _, g in genres.iterrows()
    ]
    if not counts.empty:
        out["topGenre"] = {"genre": counts.index[0], "books": int(counts.iloc[0])}
        match = genres[genres["Genre"] == counts.index[0]]
        if not match.empty:
            out["topGenre"]["mean"] = r(match.iloc[0]["Mean rating"])
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("csv")
    p.add_argument("out")
    p.add_argument("--exported", required=True, help="the date the Goodreads export was downloaded")
    p.add_argument("--min-genre-books", type=int, default=15)
    a = p.parse_args()
    data = summary(load_and_clean(pd.read_csv(a.csv)), a.exported, a.min_genre_books)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
