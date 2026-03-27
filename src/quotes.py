"""
quotes.py — Quote loading, stats, and export generation for GoodReads Quotes.
"""

import pandas as pd
import io
import re


THEMES = {
    "Classic": {"bg": "#faf0e6", "text": "#2c1810", "accent": "#8b4513", "quote": "#5c3317"},
    "Dark": {"bg": "#1a1a2e", "text": "#e0e0e0", "accent": "#e74c3c", "quote": "#f39c12"},
    "Minimal": {"bg": "#ffffff", "text": "#000000", "accent": "#333333", "quote": "#666666"},
    "Ocean": {"bg": "#0a1628", "text": "#b0c4de", "accent": "#4682b4", "quote": "#87ceeb"},
}


def load_quotes(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize a quotes DataFrame."""
    df = df.copy()
    # Normalize column names
    col_map = {}
    for c in df.columns:
        cl = c.strip().lower()
        if "quote id" in cl:
            col_map[c] = "Quote Id"
        elif cl == "author":
            col_map[c] = "Author"
        elif cl == "book":
            col_map[c] = "Book"
        elif cl == "isbn":
            col_map[c] = "ISBN"
        elif cl in ("quote", "text"):
            col_map[c] = "Quote"
        elif cl == "tags":
            col_map[c] = "Tags"
        elif "popularity" in cl:
            col_map[c] = "Popularity"
        elif cl == "order":
            col_map[c] = "Order"
    df = df.rename(columns=col_map)

    if "Quote" in df.columns:
        df["Quote"] = df["Quote"].astype(str).str.strip().str.strip('"').str.strip('"').str.strip('"')
        df = df[df["Quote"].str.len() > 0]

    if "Author" in df.columns:
        df["Author"] = df["Author"].astype(str).str.strip()

    if "Book" in df.columns:
        df["Book"] = df["Book"].astype(str).str.strip()

    if "Popularity" in df.columns:
        df["Popularity"] = pd.to_numeric(df["Popularity"], errors="coerce").fillna(0).astype(int)

    # Add word count
    if "Quote" in df.columns:
        df["Word Count"] = df["Quote"].str.split().str.len()

    return df.reset_index(drop=True)


def quotes_stats(df: pd.DataFrame) -> dict:
    """Compute summary stats for quotes."""
    stats = {
        "total": len(df),
        "unique_authors": df["Author"].nunique() if "Author" in df.columns else 0,
        "unique_books": df["Book"].nunique() if "Book" in df.columns else 0,
        "avg_length": round(df["Word Count"].mean(), 1) if "Word Count" in df.columns else 0,
    }

    if "Popularity" in df.columns and len(df) > 0:
        idx = df["Popularity"].idxmax()
        stats["most_popular_quote"] = df.loc[idx, "Quote"]
        stats["most_popular_author"] = df.loc[idx, "Author"] if "Author" in df.columns else ""
        stats["most_popular_score"] = int(df.loc[idx, "Popularity"])
    else:
        stats["most_popular_quote"] = ""
        stats["most_popular_author"] = ""
        stats["most_popular_score"] = 0

    return stats


def quotes_by_author(df: pd.DataFrame) -> pd.DataFrame:
    if "Author" not in df.columns:
        return pd.DataFrame(columns=["Author", "Quotes"])
    counts = df["Author"].value_counts().head(20).reset_index()
    counts.columns = ["Author", "Quotes"]
    return counts


def quote_length_stats(df: pd.DataFrame) -> pd.DataFrame:
    if "Word Count" not in df.columns:
        return pd.DataFrame(columns=["Word Count"])
    return df[["Word Count"]].dropna()


def tag_counts(df: pd.DataFrame) -> pd.DataFrame:
    if "Tags" not in df.columns:
        return pd.DataFrame(columns=["Tag", "Count"])
    all_tags = {}
    for val in df["Tags"].dropna():
        for t in str(val).split(","):
            t = t.strip()
            if t and t.lower() != "nan":
                all_tags[t] = all_tags.get(t, 0) + 1
    if not all_tags:
        return pd.DataFrame(columns=["Tag", "Count"])
    result = pd.DataFrame(sorted(all_tags.items(), key=lambda x: -x[1])[:25], columns=["Tag", "Count"])
    return result


def generate_pdf(quotes_df, title="My Quotes", theme=None, font="serif",
                 include_tags=True, include_books=True):
    """Generate a styled PDF of quotes. Returns bytes."""
    from fpdf import FPDF

    if theme is None:
        theme = THEMES["Dark"]

    class QuotePDF(FPDF):
        def header(self):
            if self.page_no() > 1:
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, title, align="C")
                self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    pdf = QuotePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Parse accent color
    accent = theme.get("accent", "#e74c3c")
    try:
        ar, ag, ab = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
    except (ValueError, IndexError):
        ar, ag, ab = 231, 76, 60

    # Title page
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(ar, ag, ab)
    pdf.cell(0, 15, title, align="C")
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"{len(quotes_df)} quotes", align="C")
    pdf.ln(5)
    unique_authors = quotes_df["Author"].nunique() if "Author" in quotes_df.columns else 0
    pdf.cell(0, 10, f"{unique_authors} authors", align="C")

    # Quotes
    font_family = "Helvetica"  # fpdf2 built-in
    for _, row in quotes_df.iterrows():
        pdf.add_page()

        # Quote text
        pdf.set_font(font_family, "", 12)
        pdf.set_text_color(60, 60, 60)
        quote_text = str(row.get("Quote", ""))
        # Wrap in quotes
        pdf.multi_cell(0, 7, f'"{quote_text}"')
        pdf.ln(5)

        # Attribution
        author = str(row.get("Author", "")) if "Author" in row.index else ""
        book = str(row.get("Book", "")) if include_books and "Book" in row.index else ""
        attr_parts = [p for p in [author, book] if p and p != "nan"]
        if attr_parts:
            pdf.set_font(font_family, "I", 11)
            pdf.set_text_color(ar, ag, ab)
            pdf.cell(0, 8, f"— {', '.join(attr_parts)}")
            pdf.ln(5)

        # Tags
        if include_tags and "Tags" in row.index:
            tags = str(row.get("Tags", ""))
            if tags and tags != "nan":
                pdf.set_font(font_family, "", 9)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 6, f"Tags: {tags}")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def generate_markdown(quotes_df, title="My Quotes", include_tags=True):
    """Generate markdown text of quotes."""
    lines = [f"# {title}\n"]
    for i, (_, row) in enumerate(quotes_df.iterrows(), 1):
        quote = str(row.get("Quote", ""))
        author = str(row.get("Author", "")) if "Author" in row.index else ""
        book = str(row.get("Book", "")) if "Book" in row.index else ""
        lines.append(f"## {i}.")
        lines.append(f"> {quote}")
        attr = [p for p in [author, book] if p and p != "nan"]
        if attr:
            lines.append(f"*— {', '.join(attr)}*")
        if include_tags and "Tags" in row.index:
            tags = str(row.get("Tags", ""))
            if tags and tags != "nan":
                lines.append(f"`{tags}`")
        lines.append("")
    return "\n".join(lines)


def generate_html(quotes_df, title="My Quotes", theme_colors=None, font="serif"):
    """Generate a styled HTML page of quotes."""
    if theme_colors is None:
        theme_colors = THEMES["Dark"]
    bg = theme_colors["bg"]
    text = theme_colors["text"]
    accent = theme_colors["accent"]
    quote_color = theme_colors["quote"]
    font_family = "Georgia, 'Times New Roman', serif" if font == "serif" else "'Segoe UI', Arial, sans-serif"

    quotes_html = ""
    for _, row in quotes_df.iterrows():
        q = str(row.get("Quote", "")).replace("<", "&lt;").replace(">", "&gt;")
        author = str(row.get("Author", "")) if "Author" in row.index else ""
        book = str(row.get("Book", "")) if "Book" in row.index else ""
        attr = [p for p in [author, book] if p and p != "nan"]
        attr_str = f"— {', '.join(attr)}" if attr else ""
        tags = ""
        if "Tags" in row.index:
            t = str(row.get("Tags", ""))
            if t and t != "nan":
                tags = f'<div style="color:{accent};font-size:0.8em;margin-top:8px;">{t}</div>'
        quotes_html += f'''
        <div style="border-left:3px solid {accent};padding:16px 20px;margin:20px 0;background:rgba(255,255,255,0.03);border-radius:0 8px 8px 0;">
            <div style="color:{quote_color};font-size:1.1em;line-height:1.6;">"{q}"</div>
            <div style="color:{accent};font-style:italic;margin-top:8px;">{attr_str}</div>
            {tags}
        </div>'''

    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body style="background:{bg};color:{text};font-family:{font_family};max-width:800px;margin:0 auto;padding:40px 20px;">
<h1 style="text-align:center;color:{accent};">{title}</h1>
<p style="text-align:center;color:{text};opacity:0.6;">{len(quotes_df)} quotes</p>
{quotes_html}
</body></html>'''


def generate_text(quotes_df, title="My Quotes"):
    """Generate plain text of quotes."""
    lines = [title, "=" * len(title), ""]
    for i, (_, row) in enumerate(quotes_df.iterrows(), 1):
        quote = str(row.get("Quote", ""))
        author = str(row.get("Author", "")) if "Author" in row.index else ""
        book = str(row.get("Book", "")) if "Book" in row.index else ""
        lines.append(f"{i}. \"{quote}\"")
        attr = [p for p in [author, book] if p and p != "nan"]
        if attr:
            lines.append(f"   — {', '.join(attr)}")
        lines.append("")
    return "\n".join(lines)
