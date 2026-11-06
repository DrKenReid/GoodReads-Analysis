"""Draw the reading figures from a GoodReads export, each with its uncertainty.

    python scripts/make_figures.py <export.csv> <out-dir> [--theme dark|light] [--font FILE ...] [--size WxH]

Writes PNGs (1080 px wide) to <out-dir>, one per question, and prints the
numbers behind each so a caption can quote them:

    rating_distribution.png    how many books got each star
    review_length.png          median review length at each star, 95% intervals
    vs_community.png           the crowd's average for the books I gave each star
    genre_ratings.png          mean rating by each book's top genre, 95% intervals
    books_per_year.png         books finished each year

vs_community and genre_ratings need the columns the Enhance-GoodReads-Export
tool adds (average_rating, genres); without them they are skipped. Error bars
are percentile-bootstrap 95% intervals (src/inference.py). Every bar or point
is labelled with the number of books behind it: an interval on three books
is wide for a reason.
"""
import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.analytics import load_and_clean  # noqa: E402
from src import inference as inf  # noqa: E402

THEMES = {
    "dark": {"bg": "#1a1a1a", "ink": "#e2e2e2", "muted": "#a8a099", "grid": "#333333",
             "a": "#ff9696", "b": "#ffe89e", "c": "#7fc8f8"},
    "light": {"bg": "#ffffff", "ink": "#252525", "muted": "#6b6560", "grid": "#e5e1dc",
              "a": "#c53030", "b": "#b7791f", "c": "#2b6cb0"},
}
STAR = "★"


def setup(theme: dict, fonts: list) -> None:
    family = None
    for f in fonts or []:
        font_manager.fontManager.addfont(f)
        family = family or font_manager.FontProperties(fname=f).get_name()
    plt.rcParams.update({
        "figure.facecolor": theme["bg"], "axes.facecolor": theme["bg"],
        "savefig.facecolor": theme["bg"], "text.color": theme["ink"],
        "axes.labelcolor": theme["ink"], "xtick.color": theme["muted"],
        "ytick.color": theme["muted"], "axes.edgecolor": theme["grid"],
        "grid.color": theme["grid"], "font.size": 17, "axes.labelsize": 18,
        "xtick.labelsize": 16, "ytick.labelsize": 16, "axes.spines.top": False,
        "axes.spines.right": False,
    })
    if family:
        plt.rcParams["font.family"] = [family, "DejaVu Sans"]   # DejaVu has the star


# Figure size in inches at DPI. The default makes 1080 px wide charts for a
# page; --size 6.4x5.2 keeps the same type on a smaller canvas, so labels stay
# legible when the chart is shrunk onto a phone-sized slide.
SIZE = [9.0, 7.5]
DPI = 120


def new(h: float = None):
    w, default_h = SIZE
    fig, ax = plt.subplots(figsize=(w, (h or 7.5) * default_h / 7.5), dpi=DPI)
    ax.grid(axis="y", linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, out: str, name: str) -> None:
    fig.tight_layout()
    fig.savefig(os.path.join(out, name))
    plt.close(fig)
    print(f"wrote {name}")


def fig_distribution(df, out, t):
    d = inf.rating_distribution(df)
    fig, ax = new()
    ax.bar(d["Stars"], d["Books"], color=t["a"], width=0.65)
    for _, r in d.iterrows():
        ax.text(r["Stars"], r["Books"], f"{r['Share']:.0%}", ha="center", va="bottom", color=t["ink"])
    ax.set_xticks(d["Stars"], [f"{s} {STAR}" for s in d["Stars"]])
    ax.set_ylabel("Books")
    save(fig, out, "rating_distribution.png")
    print(d.to_string(index=False))


def fig_review_length(df, out, t):
    res = inf.review_length_by_rating(df)
    d = res["table"][res["table"]["Reviews"] > 0]
    fig, ax = new()
    err = [d["Median words"] - d["Low"], d["High"] - d["Median words"]]
    ax.errorbar(d["Stars"], d["Median words"], yerr=err, fmt="o", markersize=11, color=t["a"],
                ecolor=t["ink"], elinewidth=2, capsize=8)
    for _, r in d.iterrows():
        ax.annotate(f"n={int(r['Reviews'])}", (r["Stars"], r["High"] if r["High"] == r["High"] else r["Median words"]),
                    textcoords="offset points", xytext=(0, 10), ha="center", color=t["muted"], fontsize=14)
    ax.set_xticks(range(1, 6), [f"{s} {STAR}" for s in range(1, 6)])
    ax.set_xlim(0.5, 5.5)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Median review length (words)")
    save(fig, out, "review_length.png")
    c = res["correlation"]
    print(d.to_string(index=False))
    print(f"Spearman rho {c['rho']:.2f} (95% CI {c['low']:.2f} to {c['high']:.2f}), p = {c['p']:.3g}, n = {c['n']} reviews of {res['rated']} rated")


def fig_community(df, out, t):
    res = inf.rating_vs_community(df)
    if res["n"] == 0:
        print("vs_community: no average_rating column (run Enhance-GoodReads-Export); skipped")
        return
    d = res["by_star"][res["by_star"]["Books"] > 0]
    fig, ax = new()
    err = [d["Community mean"] - d["Low"], d["High"] - d["Community mean"]]
    ax.errorbar(d["Stars"], d["Community mean"], yerr=err, fmt="o", markersize=11, color=t["c"],
                ecolor=t["ink"], elinewidth=2, capsize=8)
    for _, r in d.iterrows():
        ax.annotate(f"n={int(r['Books'])}", (r["Stars"], r["High"] if r["High"] == r["High"] else r["Community mean"]),
                    textcoords="offset points", xytext=(0, 10), ha="center", color=t["muted"], fontsize=14)
    ax.set_xticks(range(1, 6), [f"{s} {STAR}" for s in range(1, 6)])
    ax.set_xlim(0.5, 5.5)
    ax.set_xlabel("My rating")
    ax.set_ylabel("Goodreads average of those books")
    save(fig, out, "vs_community.png")
    c, dd = res["correlation"], res["difference"]
    print(d.to_string(index=False))
    print(f"Spearman rho {c['rho']:.2f} (95% CI {c['low']:.2f} to {c['high']:.2f}), p = {c['p']:.3g}, n = {c['n']}")
    print(f"mine minus theirs: {dd['mean']:+.2f} stars (95% CI {dd['low']:+.2f} to {dd['high']:+.2f}); "
          f"{res['higher']} books over half a star higher, {res['lower']} over half a star lower")


def fig_genres(df, out, t, min_books):
    d = inf.genre_ratings(df, min_books=min_books)
    if d.empty:
        print("genre_ratings: no genres column, or no genre with enough books; skipped")
        return
    d = d.iloc[::-1]
    fig, ax = new(h=max(5.5, 0.62 * len(d) + 1.6))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", linewidth=0.8)
    err = [d["Mean rating"] - d["Low"], d["High"] - d["Mean rating"]]
    ax.errorbar(d["Mean rating"], range(len(d)), xerr=err, fmt="o", markersize=10, color=t["b"],
                ecolor=t["ink"], elinewidth=2, capsize=6)
    ax.set_yticks(range(len(d)), [f"{g}  (n={n})" for g, n in zip(d["Genre"], d["Books"])])
    overall = inf._rated(df)["My Rating"].mean()
    ax.axvline(overall, color=t["muted"], linestyle="--", linewidth=1.5)
    ax.set_xlabel("My mean rating")
    save(fig, out, "genre_ratings.png")
    print(d.iloc[::-1].to_string(index=False))
    print(f"overall mean {overall:.2f}")


def fig_years(df, out, t):
    d = inf.books_per_year(df)
    fig, ax = new()
    colors = [t["muted"] if p else t["a"] for p in d["Partial"]]
    ax.bar(d["Year"].astype(str), d["Books"], color=colors, width=0.65)
    small = SIZE[0] < 8          # a slide-sized chart: tilt the years, keep labels short
    for i, r in d.iterrows():
        ax.text(i, r["Books"], str(int(r["Books"])) + ("" if small or not r["Partial"] else " so far"), ha="center",
                va="bottom", color=t["ink"], fontsize=15)
    if small:
        ax.tick_params(axis="x", labelrotation=45)
    ax.set_ylabel("Books finished (grey: this year so far)" if small else "Books finished")
    save(fig, out, "books_per_year.png")
    print(d.to_string(index=False))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("csv")
    p.add_argument("out")
    p.add_argument("--theme", choices=THEMES, default="dark")
    p.add_argument("--size", default="9x7.5", help="figure size in inches, WxH (default 9x7.5, 1080 px wide)")
    p.add_argument("--font", action="append", help="TTF/OTF to use (repeatable; the first sets the family)")
    p.add_argument("--min-genre-books", type=int, default=15)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t = THEMES[a.theme]
    SIZE[:] = [float(x) for x in a.size.lower().split("x")]
    globals()["DPI"] = round(1080 / SIZE[0])
    setup(t, a.font)
    df = load_and_clean(pd.read_csv(a.csv))
    fig_distribution(df, a.out, t)
    fig_review_length(df, a.out, t)
    fig_community(df, a.out, t)
    fig_genres(df, a.out, t, a.min_genre_books)
    fig_years(df, a.out, t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
