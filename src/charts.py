"""
charts.py — Plotly chart builders for GoodReads Reading Stats (dark theme).
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Color palette
COLORS = {
    "red": "#e74c3c",
    "blue": "#3498db",
    "green": "#2ecc71",
    "gold": "#f39c12",
    "purple": "#9b59b6",
    "teal": "#1abc9c",
}
PALETTE = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
BG_COLOR = "#0e1117"
PLOT_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
    "toImageButtonOptions": {"format": "png", "height": 700, "width": 1200, "scale": 2},
    "displaylogo": False,
}


def _base_layout(fig, title=""):
    """Apply consistent dark styling."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        title=dict(text=title, font=dict(size=20, color="#fafafa")),
        font=dict(color="#fafafa"),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def rating_distribution_chart(df: pd.DataFrame):
    """Histogram of user ratings."""
    rated = df[(df.get("Exclusive Shelf", pd.Series()) == "read") if "Exclusive Shelf" in df.columns else True]
    if "Exclusive Shelf" in df.columns:
        rated = df[df["Exclusive Shelf"] == "read"]
    rated = rated[rated["My Rating"] > 0]

    fig = px.histogram(
        rated, x="My Rating", nbins=5,
        color_discrete_sequence=[COLORS["gold"]],
        labels={"My Rating": "Your Rating", "count": "Books"},
    )
    fig.update_traces(
        hovertemplate="Rating: %{x}<br>Books: %{y}<extra></extra>"
    )
    return _base_layout(fig, "Your Rating Distribution")


def rating_comparison_chart(df: pd.DataFrame):
    """Grouped bar: your rating vs community average by rating bucket."""
    if "Exclusive Shelf" in df.columns:
        read = df[df["Exclusive Shelf"] == "read"].copy()
    else:
        read = df.copy()
    rated = read[(read["My Rating"] > 0) & (read["Average Rating"] > 0)].copy()

    if len(rated) == 0:
        return go.Figure()

    # Group by user rating
    grouped = rated.groupby("My Rating").agg(
        avg_community=("Average Rating", "mean"),
        count=("Title", "count")
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grouped["My Rating"], y=grouped["My Rating"],
        name="Your Rating", marker_color=COLORS["gold"],
        hovertemplate="Your Rating: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=grouped["My Rating"], y=grouped["avg_community"],
        name="Community Average", marker_color=COLORS["blue"],
        hovertemplate="Community Avg: %{y:.2f}<extra></extra>"
    ))
    fig.update_layout(barmode="group", xaxis_title="Your Rating", yaxis_title="Rating Value")
    return _base_layout(fig, "Your Ratings vs Community Average")


def books_per_year_chart(by_year: pd.DataFrame):
    """Bar chart of books per year."""
    if len(by_year) == 0:
        return go.Figure()
    fig = px.bar(
        by_year, x="Year", y="Books",
        color_discrete_sequence=[COLORS["red"]],
        labels={"Books": "Books Read", "Year": "Year"},
    )
    fig.update_traces(hovertemplate="Year: %{x}<br>Books: %{y}<extra></extra>")
    return _base_layout(fig, "Books Read Per Year")


def cumulative_reading_chart(df: pd.DataFrame):
    """Cumulative line chart of books read over time."""
    if "Exclusive Shelf" in df.columns:
        read = df[df["Exclusive Shelf"] == "read"].copy()
    else:
        read = df.copy()

    if "Date Read" not in read.columns:
        return go.Figure()

    valid = read.dropna(subset=["Date Read"]).sort_values("Date Read")
    if len(valid) == 0:
        return go.Figure()

    valid["Cumulative"] = range(1, len(valid) + 1)

    fig = px.line(
        valid, x="Date Read", y="Cumulative",
        color_discrete_sequence=[COLORS["green"]],
        labels={"Cumulative": "Total Books", "Date Read": "Date"},
    )
    fig.update_traces(
        hovertemplate="Date: %{x|%B %Y}<br>Total Books: %{y}<extra></extra>",
        line=dict(width=3)
    )
    return _base_layout(fig, "Cumulative Books Read")


def reading_heatmap(by_month: pd.DataFrame):
    """Month × Year heatmap."""
    if len(by_month) == 0:
        return go.Figure()

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    pivot = by_month.pivot_table(index="Year", columns="Month", values="Books", fill_value=0)
    pivot.columns = [month_names[int(c) - 1] for c in pivot.columns]

    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=[str(y) for y in pivot.index.tolist()],
        color_continuous_scale=["#1a1a2e", "#e74c3c", "#f39c12"],
        labels=dict(x="Month", y="Year", color="Books"),
        aspect="auto",
    )
    fig.update_traces(hovertemplate="Month: %{x}<br>Year: %{y}<br>Books: %{z}<extra></extra>")
    return _base_layout(fig, "Reading Heatmap")


def top_authors_chart(authors_df: pd.DataFrame):
    """Horizontal bar chart of most-read authors."""
    if len(authors_df) == 0:
        return go.Figure()

    top = authors_df.head(15)
    fig = px.bar(
        top, x="Books", y="Author", orientation="h",
        color_discrete_sequence=[COLORS["purple"]],
        labels={"Books": "Books Read", "Author": ""},
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_traces(hovertemplate="%{y}: %{x} books<extra></extra>")
    return _base_layout(fig, "Most-Read Authors")


def genre_treemap(genres_df: pd.DataFrame):
    """Treemap of genres."""
    if len(genres_df) == 0:
        return go.Figure()

    fig = px.treemap(
        genres_df, path=["Genre"], values="Count",
        color="Count",
        color_continuous_scale=["#1a1a2e", "#e74c3c", "#f39c12"],
    )
    fig.update_traces(hovertemplate="<b>%{label}</b><br>Books: %{value}<extra></extra>")
    return _base_layout(fig, "Genre Breakdown")


def page_distribution_chart(df: pd.DataFrame):
    """Histogram of page counts."""
    if "Exclusive Shelf" in df.columns:
        read = df[df["Exclusive Shelf"] == "read"].copy()
    else:
        read = df.copy()

    pages = read.dropna(subset=["Number of Pages"])
    if len(pages) == 0:
        return go.Figure()

    fig = px.histogram(
        pages, x="Number of Pages", nbins=25,
        color_discrete_sequence=[COLORS["teal"]],
        labels={"Number of Pages": "Pages", "count": "Books"},
    )
    fig.update_traces(hovertemplate="Pages: %{x}<br>Books: %{y}<extra></extra>")
    return _base_layout(fig, "Book Length Distribution")


def page_vs_rating_chart(df: pd.DataFrame):
    """Scatter plot: page count vs rating."""
    if "Exclusive Shelf" in df.columns:
        read = df[df["Exclusive Shelf"] == "read"].copy()
    else:
        read = df.copy()

    valid = read[(read["My Rating"] > 0) & (read["Number of Pages"] > 0)].dropna(
        subset=["Number of Pages", "My Rating"]
    )
    if len(valid) == 0:
        return go.Figure()

    fig = px.scatter(
        valid, x="Number of Pages", y="My Rating",
        color_discrete_sequence=[COLORS["gold"]],
        labels={"Number of Pages": "Pages", "My Rating": "Your Rating"},
        hover_data=["Title", "Author"] if "Title" in valid.columns else None,
        opacity=0.7,
        size_max=10,
    )
    return _base_layout(fig, "Does Book Length Affect Your Rating?")


def rating_difference_chart(loved: pd.DataFrame, hated: pd.DataFrame):
    """Diverging bar chart of rating differences."""
    if len(loved) == 0 and len(hated) == 0:
        return go.Figure()

    fig = go.Figure()

    if len(loved) > 0:
        fig.add_trace(go.Bar(
            y=loved["Title"], x=loved["_diff"],
            orientation="h", name="You loved more",
            marker_color=COLORS["green"],
            hovertemplate="%{y}<br>You rated +%{x:.1f} higher<extra></extra>"
        ))

    if len(hated) > 0:
        fig.add_trace(go.Bar(
            y=hated["Title"], x=-hated["_diff"],
            orientation="h", name="Community loved more",
            marker_color=COLORS["red"],
            hovertemplate="%{y}<br>Community rated +%{customdata:.1f} higher<extra></extra>",
            customdata=hated["_diff"]
        ))

    fig.update_layout(barmode="relative", yaxis=dict(autorange="reversed"),
                      xaxis_title="Rating Difference")
    return _base_layout(fig, "Your Taste vs The Crowd")


def stats_comparison_chart(stats1: dict, stats2: dict, name1: str, name2: str):
    """Grouped bar chart comparing two readers' stats."""
    categories = ["Books Read", "Total Pages (÷100)", "Avg Rating", "Avg Pages/Book"]
    vals1 = [
        stats1["total_books"],
        stats1["total_pages"] / 100,
        stats1["avg_rating"],
        stats1["avg_pages"],
    ]
    vals2 = [
        stats2["total_books"],
        stats2["total_pages"] / 100,
        stats2["avg_rating"],
        stats2["avg_pages"],
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories, y=vals1, name=name1,
        marker_color=COLORS["gold"],
        hovertemplate="%{x}: %{y:.1f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=categories, y=vals2, name=name2,
        marker_color=COLORS["blue"],
        hovertemplate="%{x}: %{y:.1f}<extra></extra>"
    ))
    fig.update_layout(barmode="group")
    return _base_layout(fig, "📊 Stats Comparison")


def shared_authors_chart(shared_df: pd.DataFrame, name1: str, name2: str):
    """Bar chart of shared authors with book counts from each reader."""
    if len(shared_df) == 0:
        return go.Figure()

    top = shared_df.head(15)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["Author"], x=top["Books_1"], name=name1,
        orientation="h", marker_color=COLORS["gold"],
        hovertemplate="%{y}: %{x} books<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=top["Author"], x=top["Books_2"], name=name2,
        orientation="h", marker_color=COLORS["blue"],
        hovertemplate="%{y}: %{x} books<extra></extra>"
    ))
    fig.update_layout(barmode="group", yaxis=dict(autorange="reversed"))
    return _base_layout(fig, "📚 Shared Authors")


# ═══════════════════════════════════════════
# QUOTES CHARTS
# ═══════════════════════════════════════════

def quotes_per_author_chart(df: pd.DataFrame):
    """Horizontal bar chart of quotes per author."""
    fig = px.bar(
        df, y="Author", x="Quotes", orientation="h",
        color_discrete_sequence=[COLORS["gold"]],
    )
    fig.update_traces(hovertemplate="%{y}: %{x} quotes<extra></extra>")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _base_layout(fig, "✍️ Quotes per Author")


def quote_length_chart(df: pd.DataFrame):
    """Histogram of quote word counts."""
    fig = px.histogram(
        df, x="Word Count", nbins=20,
        color_discrete_sequence=[COLORS["blue"]],
        labels={"Word Count": "Words", "count": "Quotes"},
    )
    fig.update_traces(hovertemplate="Words: %{x}<br>Quotes: %{y}<extra></extra>")
    return _base_layout(fig, "📏 Quote Length Distribution")


def tags_chart(df: pd.DataFrame):
    """Bar chart of most common tags."""
    fig = px.bar(
        df, x="Count", y="Tag", orientation="h",
        color_discrete_sequence=[COLORS["teal"]],
    )
    fig.update_traces(hovertemplate="%{y}: %{x}<extra></extra>")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _base_layout(fig, "🏷️ Most Common Tags")


def popularity_chart(df: pd.DataFrame):
    """Histogram of quote popularity scores."""
    fig = px.histogram(
        df, x="Popularity", nbins=20,
        color_discrete_sequence=[COLORS["purple"]],
        labels={"Popularity": "Popularity Score", "count": "Quotes"},
    )
    fig.update_traces(hovertemplate="Popularity: %{x}<br>Quotes: %{y}<extra></extra>")
    return _base_layout(fig, "📊 Quote Popularity Distribution")
