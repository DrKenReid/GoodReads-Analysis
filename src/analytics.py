"""
analytics.py — Data processing, metrics, and commentary for GoodReads Wrapped.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


def load_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean GoodReads CSV export into usable DataFrame."""
    df = df.copy()

    # Normalize column names (strip whitespace, handle common variations)
    df.columns = df.columns.str.strip()

    # Map common column name variations
    column_map = {
        "my rating": "My Rating",
        "average rating": "Average Rating",
        "number of pages": "Number of Pages",
        "year published": "Year Published",
        "original publication year": "Original Publication Year",
        "date read": "Date Read",
        "date added": "Date Added",
        "exclusive shelf": "Exclusive Shelf",
        "my review": "My Review",
        "read count": "Read Count",
        "owned copies": "Owned Copies",
    }
    lower_cols = {c.lower(): c for c in df.columns}
    for target_lower, canonical in column_map.items():
        if canonical not in df.columns and target_lower in lower_cols:
            df.rename(columns={lower_cols[target_lower]: canonical}, inplace=True)

    # Numeric columns
    for col in ["My Rating", "Average Rating", "Number of Pages", "Year Published",
                 "Original Publication Year", "Read Count", "Owned Copies"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Date columns
    for col in ["Date Read", "Date Added"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Exclusive Shelf cleanup
    if "Exclusive Shelf" in df.columns:
        df["Exclusive Shelf"] = df["Exclusive Shelf"].fillna("").str.strip().str.lower()

    # Bookshelves as list
    if "Bookshelves" in df.columns:
        df["_shelves"] = df["Bookshelves"].fillna("").str.split(",").apply(
            lambda x: [s.strip().lower() for s in x if s.strip()]
        )
    else:
        df["_shelves"] = [[] for _ in range(len(df))]

    return df


def _read_books(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to read books only."""
    if "Exclusive Shelf" in df.columns:
        return df[df["Exclusive Shelf"] == "read"].copy()
    return df.copy()


def reading_stats(df: pd.DataFrame) -> dict:
    """Key reading metrics."""
    read = _read_books(df)
    rated = read[read["My Rating"] > 0] if "My Rating" in read.columns else read

    total_books = len(read)
    total_pages = int(read["Number of Pages"].sum()) if "Number of Pages" in read.columns else 0
    avg_rating = round(rated["My Rating"].mean(), 2) if len(rated) > 0 and "My Rating" in rated.columns else 0
    avg_pages = int(read["Number of Pages"].mean()) if "Number of Pages" in read.columns and len(read) > 0 else 0
    avg_community = round(read["Average Rating"].mean(), 2) if "Average Rating" in read.columns and len(read) > 0 else 0

    # Years active
    if "Date Read" in read.columns:
        valid_dates = read["Date Read"].dropna()
        years_active = valid_dates.dt.year.nunique() if len(valid_dates) > 0 else 0
    else:
        years_active = 0

    return {
        "total_books": total_books,
        "total_pages": total_pages,
        "avg_rating": avg_rating,
        "avg_pages": avg_pages,
        "avg_community_rating": avg_community,
        "years_active": years_active,
        "rated_count": len(rated),
    }


def reading_personality(stats: dict, df: pd.DataFrame) -> tuple:
    """Determine reading personality → (title, emoji, description)."""
    read = _read_books(df)
    total = stats["total_books"]
    avg_rating = stats["avg_rating"]
    avg_pages = stats["avg_pages"]

    # Check genre diversity
    all_shelves = []
    if "_shelves" in read.columns:
        for shelves in read["_shelves"]:
            all_shelves.extend(shelves)
    unique_shelves = len(set(all_shelves) - {"read", "currently-reading", "to-read", ""})

    # Rating strictness
    rated = read[read["My Rating"] > 0] if "My Rating" in read.columns else read
    strict = avg_rating < 3.3 if avg_rating > 0 else False
    generous = avg_rating > 4.2 if avg_rating > 0 else False

    # Books per year (only meaningful with multiple years of data)
    bpy = total / max(stats["years_active"], 1) if stats["years_active"] >= 2 else 0

    if strict and stats["rated_count"] > 10:
        return ("The Critic", "🧐",
                f"Average rating: {avg_rating}. You don't hand out stars like candy. "
                "Authors have to *earn* your approval, and most of them don't.")

    if bpy > 40 and stats["years_active"] >= 2:
        return ("The Binge Reader", "📖",
                f"{int(bpy)} books per year? That's not a hobby, that's a lifestyle. "
                "Your library card has probably filed for overtime.")

    if avg_pages > 400:
        return ("The Deep Diver", "🤿",
                f"Average book length: {avg_pages} pages. You don't do novellas. "
                "If it doesn't have enough pages to stop a door, you're not interested.")

    if unique_shelves > 8:
        return ("The Eclectic", "🌈",
                f"{unique_shelves} different genres? You read like you're at a buffet — "
                "a little bit of everything, no regrets.")

    if generous:
        return ("The Enthusiast", "🌟",
                f"Average rating: {avg_rating}. You love almost everything you read. "
                "Either you have amazing taste in picking books, or you're just really nice.")

    if bpy < 8 and total < 30:
        return ("The Casual Reader", "🛋️",
                "Quality over quantity. You savor your books like a fine wine. "
                "Or you just keep forgetting to update GoodReads.")

    if total > 100:
        return ("The Completionist", "✅",
                f"{total} books tracked! You're methodical, thorough, "
                "and probably have strong opinions about library organization systems.")

    return ("The Bookworm", "📚",
            f"{total} books read with an average rating of {avg_rating}. "
            "A solid, dedicated reader. The backbone of every book club.")


def rating_analysis(df: pd.DataFrame) -> dict:
    """Rating comparisons between user and community."""
    read = _read_books(df)
    rated = read[(read["My Rating"] > 0) & (read["Average Rating"] > 0)].copy()

    if len(rated) == 0:
        return {"has_data": False}

    rated["_diff"] = rated["My Rating"] - rated["Average Rating"]

    return {
        "has_data": True,
        "avg_yours": round(rated["My Rating"].mean(), 2),
        "avg_community": round(rated["Average Rating"].mean(), 2),
        "rated_count": len(rated),
        "rating_counts": rated["My Rating"].value_counts().sort_index().to_dict(),
    }


def books_you_loved(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Books where your rating far exceeds the average."""
    read = _read_books(df)
    rated = read[(read["My Rating"] > 0) & (read["Average Rating"] > 0)].copy()
    if len(rated) == 0:
        return pd.DataFrame()
    rated["_diff"] = rated["My Rating"] - rated["Average Rating"]
    return rated.nlargest(n, "_diff")[["Title", "Author", "My Rating", "Average Rating", "_diff"]]


def books_you_hated(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Books everyone loved but you didn't."""
    read = _read_books(df)
    rated = read[(read["My Rating"] > 0) & (read["Average Rating"] > 0)].copy()
    if len(rated) == 0:
        return pd.DataFrame()
    rated["_diff"] = rated["Average Rating"] - rated["My Rating"]
    return rated.nlargest(n, "_diff")[["Title", "Author", "My Rating", "Average Rating", "_diff"]]


def books_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Books read per year."""
    read = _read_books(df)
    if "Date Read" not in read.columns:
        return pd.DataFrame()
    valid = read.dropna(subset=["Date Read"]).copy()
    if len(valid) == 0:
        return pd.DataFrame()
    valid["Year"] = valid["Date Read"].dt.year
    return valid.groupby("Year").size().reset_index(name="Books")


def books_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Books read per month×year for heatmap."""
    read = _read_books(df)
    if "Date Read" not in read.columns:
        return pd.DataFrame()
    valid = read.dropna(subset=["Date Read"]).copy()
    if len(valid) == 0:
        return pd.DataFrame()
    valid["Year"] = valid["Date Read"].dt.year
    valid["Month"] = valid["Date Read"].dt.month
    pivot = valid.groupby(["Year", "Month"]).size().reset_index(name="Books")
    return pivot


def reading_streak(df: pd.DataFrame) -> dict:
    """Calculate reading streaks (by month — most people don't read a book every day)."""
    read = _read_books(df)
    if "Date Read" not in read.columns:
        return {"current": 0, "longest": 0}
    valid = read.dropna(subset=["Date Read"]).copy()
    if len(valid) == 0:
        return {"current": 0, "longest": 0}

    # Monthly streak
    months = valid["Date Read"].dt.to_period("M").unique()
    months = sorted(months)
    if len(months) == 0:
        return {"current": 0, "longest": 0}

    longest = 1
    current = 1
    for i in range(1, len(months)):
        if months[i] == months[i - 1] + 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return {"current": current, "longest": longest}


def top_authors(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Most-read authors."""
    read = _read_books(df)
    if "Author" not in read.columns:
        return pd.DataFrame()
    counts = read["Author"].value_counts().head(n).reset_index()
    counts.columns = ["Author", "Books"]
    return counts


def genre_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Genre breakdown from bookshelves (if available)."""
    read = _read_books(df)
    if "_shelves" not in read.columns:
        return pd.DataFrame()

    skip = {"read", "currently-reading", "to-read", "owned", "favorites",
            "to-buy", "books-i-own", "default", ""}
    genre_counts = {}
    for shelves in read["_shelves"]:
        for s in shelves:
            if s not in skip and len(s) > 1:
                genre_counts[s] = genre_counts.get(s, 0) + 1

    if not genre_counts:
        return pd.DataFrame()

    result = pd.DataFrame(list(genre_counts.items()), columns=["Genre", "Count"])
    return result.sort_values("Count", ascending=False).head(30)


def genre_personality_tags(df: pd.DataFrame, n: int = 5) -> list:
    """Fun genre tags based on top shelves."""
    genres = genre_breakdown(df)
    if len(genres) == 0:
        return []

    tag_map = {
        "fiction": "📖 Fiction Fiend",
        "non-fiction": "🧠 Knowledge Seeker",
        "nonfiction": "🧠 Knowledge Seeker",
        "fantasy": "🧙 Fantasy Dweller",
        "sci-fi": "🚀 Space Cadet",
        "science-fiction": "🚀 Space Cadet",
        "romance": "💕 Hopeless Romantic",
        "mystery": "🔍 Mystery Maven",
        "thriller": "😱 Thrill Seeker",
        "horror": "👻 Nightmare Fuel",
        "history": "📜 History Buff",
        "biography": "👤 Life Story Collector",
        "self-help": "🌱 Self-Improver",
        "classics": "🎩 Classics Connoisseur",
        "poetry": "✨ Verse Lover",
        "philosophy": "🤔 Deep Thinker",
        "young-adult": "🌟 YA Devotee",
        "ya": "🌟 YA Devotee",
        "graphic-novels": "🎨 Visual Storyteller",
        "comics": "🎨 Visual Storyteller",
        "memoir": "📝 Memoir Enthusiast",
        "literary-fiction": "🎭 Literary Snob",
        "crime": "🔪 Crime Scene Investigator",
        "dystopian": "🏚️ Dystopia Tourist",
        "historical-fiction": "⚔️ Time Traveler",
    }

    tags = []
    for _, row in genres.head(n * 2).iterrows():
        genre = row["Genre"].lower()
        if genre in tag_map and tag_map[genre] not in tags:
            tags.append(tag_map[genre])
        if len(tags) >= n:
            break

    return tags


def shelf_of_shame(df: pd.DataFrame) -> dict:
    """To-read shelf analysis."""
    if "Exclusive Shelf" not in df.columns:
        return {"count": 0}

    tbr = df[df["Exclusive Shelf"] == "to-read"].copy()
    count = len(tbr)

    oldest = None
    if "Date Added" in tbr.columns and len(tbr) > 0:
        valid = tbr.dropna(subset=["Date Added"])
        if len(valid) > 0:
            oldest_row = valid.loc[valid["Date Added"].idxmin()]
            days = (datetime.now() - oldest_row["Date Added"]).days
            oldest = {
                "title": oldest_row.get("Title", "Unknown"),
                "days": days,
                "years": round(days / 365.25, 1),
            }

    return {"count": count, "oldest": oldest}


def page_stats(df: pd.DataFrame) -> dict:
    """Page count analysis."""
    read = _read_books(df)
    if "Number of Pages" not in read.columns:
        return {"has_data": False}

    pages = read["Number of Pages"].dropna()
    if len(pages) == 0:
        return {"has_data": False}

    return {
        "has_data": True,
        "mean": int(pages.mean()),
        "median": int(pages.median()),
        "min": int(pages.min()),
        "max": int(pages.max()),
        "total": int(pages.sum()),
        "shortest_title": read.loc[pages.idxmin(), "Title"] if "Title" in read.columns else "?",
        "longest_title": read.loc[pages.idxmax(), "Title"] if "Title" in read.columns else "?",
    }


def stats_commentary(stats: dict) -> str:
    """Generate fun roast text based on stats."""
    lines = []

    total = stats["total_books"]
    if total > 200:
        lines.append(f"📚 {total} books? At this point, you're basically a library with legs.")
    elif total > 100:
        lines.append(f"📚 {total} books tracked. Your bookshelf has a bookshelf.")
    elif total > 50:
        lines.append(f"📚 {total} books — solid commitment. Your Kindle is sweating.")
    elif total > 20:
        lines.append(f"📚 {total} books read. A respectable showing.")
    else:
        lines.append(f"📚 {total} books. Quality over quantity, right? ...Right?")

    pages = stats["total_pages"]
    if pages > 50000:
        lines.append(f"📄 {pages:,} total pages. That's roughly {pages // 300} average novels stacked up.")
    elif pages > 10000:
        lines.append(f"📄 {pages:,} pages turned. Your fingers deserve a vacation.")

    avg = stats["avg_pages"]
    if avg > 400:
        lines.append(f"📏 Average book: {avg} pages. You don't mess around with novellas.")
    elif avg < 200 and avg > 0:
        lines.append(f"📏 Average book: {avg} pages. Short and sweet — the book equivalent of a snack.")

    rating = stats["avg_rating"]
    if rating > 4.5:
        lines.append(f"⭐ Average rating: {rating}. Either you pick amazing books or you're just really generous.")
    elif rating < 3.0 and rating > 0:
        lines.append(f"⭐ Average rating: {rating}. Tough crowd. Do you even enjoy reading?")

    return "\n\n".join(lines)


def shelf_roast(count: int) -> str:
    """Roast the to-read backlog."""
    if count == 0:
        return "🎉 Zero books on your to-read shelf. Are you even on GoodReads?"
    elif count < 20:
        return f"📋 {count} books on your to-read shelf. That's actually... manageable? Are you okay?"
    elif count < 50:
        return f"📋 {count} books waiting. That's an optimistic reading list, not a life sentence."
    elif count < 100:
        return f"📋 {count} books on the pile. At your current pace, you'll finish these sometime around retirement."
    elif count < 200:
        return f"📋 {count} books. That's not a reading list, that's a small bookstore."
    elif count < 500:
        return f"📋 {count} books. That's not a reading list, that's a cry for help."
    else:
        return f"📋 {count} books. You've transcended reading lists. This is a literary hoard. Seek help."


def generate_demo_data() -> pd.DataFrame:
    """Generate a sample GoodReads CSV for demo mode."""
    np.random.seed(42)
    n = 85

    authors = ["Brandon Sanderson", "N.K. Jemisin", "Andy Weir", "Ursula K. Le Guin",
               "Patrick Rothfuss", "Octavia Butler", "Terry Pratchett", "Terry Pratchett",
               "Neil Gaiman", "Margaret Atwood", "Haruki Murakami", "Toni Morrison",
               "George Orwell", "Kurt Vonnegut", "Douglas Adams", "Donna Tartt",
               "Chimamanda Ngozi Adichie", "Ta-Nehisi Coates", "Yuval Noah Harari",
               "Malcolm Gladwell", "Mary Shelley", "Fyodor Dostoevsky"]

    titles = [
        "The Way of Kings", "The Fifth Season", "Project Hail Mary", "The Left Hand of Darkness",
        "The Name of the Wind", "Kindred", "Good Omens", "Going Postal", "American Gods",
        "The Handmaid's Tale", "Norwegian Wood", "Beloved", "1984", "Slaughterhouse-Five",
        "The Hitchhiker's Guide to the Galaxy", "The Secret History", "Americanah",
        "Between the World and Me", "Sapiens", "Outliers", "Frankenstein",
        "Crime and Punishment", "Mort", "Small Gods", "Reaper Man",
        "The Obelisk Gate", "The Stone Sky", "Words of Radiance", "Oathbringer",
        "Rhythm of War", "The Martian", "Artemis", "Parable of the Sower",
        "Dawn", "Anansi Boys", "Neverwhere", "The Ocean at the End of the Lane",
        "The Testaments", "Kafka on the Shore", "1Q84", "Song of Solomon",
        "The Bluest Eye", "Animal Farm", "Cat's Cradle", "Breakfast of Champions",
        "The Restaurant at the End of the Universe", "The Goldfinch", "Half of a Yellow Sun",
        "We Should All Be Feminists", "21 Lessons for the 21st Century", "Homo Deus",
        "Blink", "The Tipping Point", "The Dispossessed", "A Wizard of Earthsea",
        "The Tombs of Atuan", "Guards! Guards!", "Feet of Clay", "Night Watch",
        "Wyrd Sisters", "Equal Rites", "Jingo", "The Truth",
        "Monstrous Regiment", "Thud!", "Making Money", "Unseen Academicals",
        "Snuff", "Raising Steam", "The Color of Magic", "The Light Fantastic",
        "Sourcery", "Eric", "Interesting Times", "Maskerade",
        "Carpe Jugulum", "The Wee Free Men", "A Hat Full of Sky",
        "I Shall Wear Midnight", "The Shepherd's Crown", "Pyramids",
        "Moving Pictures", "Soul Music", "Hogfather", "The Last Continent"
    ]

    shelves_options = [
        "fiction, fantasy", "fiction, sci-fi", "non-fiction", "fiction, classics",
        "fiction, literary-fiction", "non-fiction, history", "fiction, mystery",
        "fiction, romance", "fiction, horror", "non-fiction, self-help",
        "fiction, thriller", "fiction, dystopian", "non-fiction, biography",
        "fiction, young-adult", "fiction, humor"
    ]

    start_date = datetime(2018, 1, 1)
    dates_read = [start_date + timedelta(days=int(x)) for x in
                  sorted(np.random.randint(0, 2200, size=n))]

    data = {
        "Book Id": list(range(1, n + 1)),
        "Title": [titles[i % len(titles)] for i in range(n)],
        "Author": [authors[i % len(authors)] for i in range(n)],
        "Author l-f": ["" for _ in range(n)],
        "ISBN": ["" for _ in range(n)],
        "ISBN13": ["" for _ in range(n)],
        "My Rating": np.random.choice([0, 2, 3, 3, 4, 4, 4, 5, 5, 5], size=n).tolist(),
        "Average Rating": np.round(np.random.uniform(3.2, 4.5, size=n), 2).tolist(),
        "Publisher": ["" for _ in range(n)],
        "Binding": ["Paperback" for _ in range(n)],
        "Number of Pages": np.random.choice(range(180, 900), size=n).tolist(),
        "Year Published": np.random.choice(range(1818, 2024), size=n).tolist(),
        "Original Publication Year": ["" for _ in range(n)],
        "Date Read": [d.strftime("%Y/%m/%d") for d in dates_read],
        "Date Added": [(d - timedelta(days=np.random.randint(1, 365))).strftime("%Y/%m/%d") for d in dates_read],
        "Bookshelves": [shelves_options[i % len(shelves_options)] for i in range(n)],
        "Bookshelves with positions": ["" for _ in range(n)],
        "Exclusive Shelf": ["read" for _ in range(n)],
        "My Review": ["" for _ in range(n)],
        "Spoiler": ["" for _ in range(n)],
        "Private Notes": ["" for _ in range(n)],
        "Read Count": [1 for _ in range(n)],
        "Owned Copies": [0 for _ in range(n)],
    }

    # Add some to-read books
    tbr_n = 47
    tbr_titles = [f"TBR Book {i}" for i in range(tbr_n)]
    tbr_dates_added = [start_date + timedelta(days=int(x)) for x in
                       sorted(np.random.randint(0, 2500, size=tbr_n))]
    for key in data:
        if key == "Title":
            data[key].extend(tbr_titles)
        elif key == "Author":
            data[key].extend([authors[i % len(authors)] for i in range(tbr_n)])
        elif key == "Exclusive Shelf":
            data[key].extend(["to-read" for _ in range(tbr_n)])
        elif key == "My Rating":
            data[key].extend([0 for _ in range(tbr_n)])
        elif key == "Date Read":
            data[key].extend(["" for _ in range(tbr_n)])
        elif key == "Date Added":
            data[key].extend([d.strftime("%Y/%m/%d") for d in tbr_dates_added])
        elif key == "Number of Pages":
            data[key].extend(np.random.choice(range(150, 700), size=tbr_n).tolist())
        elif key == "Book Id":
            data[key].extend(list(range(n + 1, n + tbr_n + 1)))
        elif key == "Average Rating":
            data[key].extend(np.round(np.random.uniform(3.0, 4.6, size=tbr_n), 2).tolist())
        elif key == "Bookshelves":
            data[key].extend(["to-read" for _ in range(tbr_n)])
        else:
            data[key].extend(["" for _ in range(tbr_n)])

    return pd.DataFrame(data)
