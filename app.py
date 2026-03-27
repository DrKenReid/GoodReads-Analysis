"""
GoodReads Wrapped — Spotify Wrapped, but for your reading life. 📚
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from src.analytics import (
    load_and_clean, reading_stats, reading_personality, rating_analysis,
    books_you_loved, books_you_hated, books_by_year, books_by_month,
    reading_streak, top_authors, genre_breakdown, genre_personality_tags,
    shelf_of_shame, page_stats, stats_commentary, shelf_roast,
    generate_demo_data,
)
from src.charts import (
    rating_distribution_chart, rating_comparison_chart, books_per_year_chart,
    cumulative_reading_chart, reading_heatmap, top_authors_chart,
    genre_treemap, page_distribution_chart, page_vs_rating_chart,
    rating_difference_chart, PLOT_CONFIG,
)

st.set_page_config(page_title="GoodReads Wrapped", page_icon="📚", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .personality-card {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 1rem;
        border: 1px solid #e74c3c33;
        margin: 1rem 0;
    }
    .personality-emoji { font-size: 5rem; }
    .personality-title { font-size: 2.2rem; font-weight: bold; color: #f39c12; margin: 0.5rem 0; }
    .personality-desc { font-size: 1.1rem; color: #cccccc; max-width: 600px; margin: 0 auto; }
    .section-divider {
        border: 0;
        height: 1px;
        background: linear-gradient(to right, transparent, #e74c3c44, transparent);
        margin: 3rem 0;
    }
    .roast-text { font-size: 1.05rem; color: #cccccc; line-height: 1.8; }
    .genre-tag {
        display: inline-block;
        padding: 0.4rem 1rem;
        margin: 0.3rem;
        background: #1a1a2e;
        border: 1px solid #e74c3c55;
        border-radius: 2rem;
        color: #f39c12;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📚 GoodReads Wrapped")
st.markdown("*Spotify Wrapped, but for your reading life.*")
st.markdown("---")

# Upload or demo
col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("Upload your GoodReads CSV export", type=["csv"],
                                 help="Go to GoodReads → My Books → Import/Export → Export Library")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    demo = st.button("🎮 Try Demo Mode")

df = None
if uploaded:
    df = pd.read_csv(uploaded)
elif demo or st.session_state.get("demo_mode"):
    st.session_state["demo_mode"] = True
    df = generate_demo_data()
    st.info("📖 Using demo data — upload your own CSV for the real thing!")

if df is None:
    st.markdown("### 👆 Upload your GoodReads export to get started")
    st.markdown("""
    **How to export:**
    1. Go to [GoodReads](https://www.goodreads.com/review/import)
    2. Click **Export Library** (top right)
    3. Wait for the export to complete
    4. Download the CSV and upload it here!
    """)
    st.stop()

# Process data
df = load_and_clean(df)

# Detect CSV type
is_quotes_csv = "Goodreads Quote Id" in df.columns or "Quote" in df.columns

if is_quotes_csv:
    st.warning("⚠️ This looks like a GoodReads **Quotes** export, not your library export.")
    st.info(
        "This app works best with your **library export**. To get it:\n\n"
        "1. Go to [GoodReads → My Books → Import/Export](https://www.goodreads.com/review/import)\n"
        "2. Click **Export Library**\n"
        "3. Upload the downloaded CSV here\n\n"
        "We'll show what we can with the quotes data, but ratings, reading timeline, and most features need the library export."
    )

# Validate required columns exist
required_cols = ["Title", "Author"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}. Is this a GoodReads export CSV?")
    st.caption(f"Found columns: {', '.join(df.columns.tolist())}")
    st.stop()

stats = reading_stats(df)

# ═══════════════════════════════════════════
# 1. READING PERSONALITY
# ═══════════════════════════════════════════
title, emoji, description = reading_personality(stats, df)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(f"""
<div class="personality-card">
    <div class="personality-emoji">{emoji}</div>
    <div class="personality-title">{title}</div>
    <div class="personality-desc">{description}</div>
</div>
""", unsafe_allow_html=True)

# Genre tags
tags = genre_personality_tags(df)
if tags:
    tags_html = "".join(f'<span class="genre-tag">{t}</span>' for t in tags)
    st.markdown(f'<div style="text-align:center; margin-top:1rem;">{tags_html}</div>',
                unsafe_allow_html=True)

# ═══════════════════════════════════════════
# 2. KEY STATS
# ═══════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("## 📊 Your Reading Stats")

c1, c2, c3, c4 = st.columns(4)
c1.metric("📚 Books Read", f"{stats['total_books']:,}")
c2.metric("📄 Total Pages", f"{stats['total_pages']:,}")
c3.metric("⭐ Avg Rating", f"{stats['avg_rating']}")
c4.metric("📏 Avg Pages/Book", f"{stats['avg_pages']:,}")

commentary = stats_commentary(stats)
st.markdown(f'<div class="roast-text">{commentary}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# 3. RATING ANALYSIS
# ═══════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("## ⭐ Rating Analysis")

ra = rating_analysis(df)
if ra.get("has_data"):
    rc1, rc2 = st.columns(2)
    with rc1:
        st.plotly_chart(rating_distribution_chart(df), use_container_width=True, config=PLOT_CONFIG)
    with rc2:
        st.plotly_chart(rating_comparison_chart(df), use_container_width=True, config=PLOT_CONFIG)

    # Rating difference
    diff_col1, diff_col2 = st.columns(2)
    loved = books_you_loved(df)
    hated = books_you_hated(df)

    if len(loved) > 0:
        with diff_col1:
            st.markdown("### 💚 Books You Loved More Than Everyone Else")
            for _, row in loved.iterrows():
                diff = row["_diff"]
                st.markdown(
                    f"**{row['Title']}** by {row['Author']} — "
                    f"You: ⭐{int(row['My Rating'])} | Everyone: ⭐{row['Average Rating']:.1f} "
                    f"*(+{diff:.1f})*"
                )

    if len(hated) > 0:
        with diff_col2:
            st.markdown("### 🔴 Books Everyone Loved But You Didn't")
            for _, row in hated.iterrows():
                diff = row["_diff"]
                st.markdown(
                    f"**{row['Title']}** by {row['Author']} — "
                    f"You: ⭐{int(row['My Rating'])} | Everyone: ⭐{row['Average Rating']:.1f} "
                    f"*(-{diff:.1f})*"
                )

    st.plotly_chart(rating_difference_chart(loved, hated), use_container_width=True, config=PLOT_CONFIG)
else:
    st.info("No rated books found — rate some books on GoodReads to see this section!")

# ═══════════════════════════════════════════
# 4. READING TIMELINE
# ═══════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("## 📈 Reading Timeline")

by_year = books_by_year(df)
by_month = books_by_month(df)
streak = reading_streak(df)

if len(by_year) > 0:
    tc1, tc2 = st.columns(2)
    with tc1:
        st.plotly_chart(cumulative_reading_chart(df), use_container_width=True, config=PLOT_CONFIG)
    with tc2:
        st.plotly_chart(books_per_year_chart(by_year), use_container_width=True, config=PLOT_CONFIG)

if len(by_month) > 0:
    st.plotly_chart(reading_heatmap(by_month), use_container_width=True, config=PLOT_CONFIG)

if streak["longest"] > 0:
    sc1, sc2 = st.columns(2)
    sc1.metric("🔥 Longest Reading Streak", f"{streak['longest']} months")
    sc2.metric("📅 Current Streak", f"{streak['current']} months")

# ═══════════════════════════════════════════
# 5. GENRE BREAKDOWN
# ═══════════════════════════════════════════
genres = genre_breakdown(df)
if len(genres) > 0:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 🎯 Genre Breakdown")
    st.plotly_chart(genre_treemap(genres), use_container_width=True, config=PLOT_CONFIG)

    tags = genre_personality_tags(df)
    if tags:
        pills_html = " ".join(
            f'<span style="background:#e74c3c;color:white;padding:4px 12px;border-radius:16px;margin:2px;display:inline-block;font-size:14px;">{t}</span>'
            for t in tags
        )
        st.markdown(f'<div style="margin:8px 0 12px 0;">{pills_html}</div>', unsafe_allow_html=True)
else:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 🎯 Genre Breakdown")
    st.info(
        "No genre data found. Genre analysis requires the enhanced GoodReads export.\n\n"
        "Use [Enhance-GoodReads-Export](https://github.com/PaulKlinger/Enhance-GoodReads-Export) "
        "to add genre tags to your CSV, then re-upload."
    )

# ═══════════════════════════════════════════
# 6. AUTHOR STATS
# ═══════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("## ✍️ Author Stats")

authors = top_authors(df)
if len(authors) > 0:
    st.plotly_chart(top_authors_chart(authors), use_container_width=True, config=PLOT_CONFIG)

    repeat = authors[authors["Books"] > 1]
    one_hit = authors[authors["Books"] == 1]
    ac1, ac2 = st.columns(2)
    ac1.metric("🔁 Repeat Authors", len(repeat))
    ac2.metric("1️⃣ One-Hit Authors", len(one_hit))

# ═══════════════════════════════════════════
# 7. BOOK LENGTH ANALYSIS
# ═══════════════════════════════════════════
ps = page_stats(df)
if ps.get("has_data"):
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 📖 Book Length Analysis")

    pc1, pc2 = st.columns(2)
    with pc1:
        st.plotly_chart(page_distribution_chart(df), use_container_width=True, config=PLOT_CONFIG)
    with pc2:
        st.plotly_chart(page_vs_rating_chart(df), use_container_width=True, config=PLOT_CONFIG)

    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric("📕 Shortest", f"{ps['min']} pages")
    lc2.metric("📗 Longest", f"{ps['max']} pages")
    lc3.metric("📙 Median", f"{ps['median']} pages")
    lc4.metric("📘 Average", f"{ps['mean']} pages")

    st.markdown(f"📕 **Shortest:** *{ps['shortest_title']}* ({ps['min']} pages)")
    st.markdown(f"📗 **Longest:** *{ps['longest_title']}* ({ps['max']} pages)")

# ═══════════════════════════════════════════
# 8. THE SHELF OF SHAME
# ═══════════════════════════════════════════
shame = shelf_of_shame(df)
if shame["count"] > 0:
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 💀 The Shelf of Shame")

    st.metric("📋 To-Read Backlog", f"{shame['count']} books")
    roast = shelf_roast(shame["count"])
    st.markdown(f'<div class="roast-text">{roast}</div>', unsafe_allow_html=True)

    if shame.get("oldest"):
        oldest = shame["oldest"]
        st.markdown(
            f"⏳ **Oldest unread book:** *{oldest['title']}* — "
            f"added {oldest['days']:,} days ago ({oldest['years']} years). "
            f"At this point, just admit you're never reading it."
        )

# ═══════════════════════════════════════════
# 9. READING SUMMARY CARD
# ═══════════════════════════════════════════
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("## 📸 Reading Summary Card")


def generate_summary_card(title_text, emoji_char, stats_dict, top_loved, tags_list):
    """Generate a downloadable summary card using Pillow."""
    width, height = 800, 1000
    img = Image.new("RGB", (width, height), color="#0e1117")
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 42)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 18)
        font_emoji = ImageFont.truetype("seguiemj.ttf", 60)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
        font_emoji = font_large

    # Background gradient effect (simple rectangles)
    for i in range(height):
        r = int(14 + (26 - 14) * i / height)
        g = int(17 + (26 - 17) * i / height)
        b = int(23 + (46 - 23) * i / height)
        draw.line([(0, i), (width, i)], fill=(r, g, b))

    # Border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline="#e74c3c", width=2)

    # Header
    draw.text((width // 2, 50), "📚 GoodReads Wrapped", fill="#f39c12",
              font=font_large, anchor="mt")

    # Personality
    y = 130
    draw.text((width // 2, y), emoji_char, fill="#ffffff", font=font_emoji, anchor="mt")
    y += 80
    draw.text((width // 2, y), title_text, fill="#f39c12", font=font_medium, anchor="mt")

    # Stats
    y += 60
    stat_items = [
        ("Books Read", f"{stats_dict['total_books']:,}"),
        ("Total Pages", f"{stats_dict['total_pages']:,}"),
        ("Avg Rating", f"⭐ {stats_dict['avg_rating']}"),
        ("Avg Pages/Book", f"{stats_dict['avg_pages']:,}"),
    ]

    for label, value in stat_items:
        draw.text((100, y), label, fill="#888888", font=font_small)
        draw.text((400, y), str(value), fill="#fafafa", font=font_medium)
        y += 40

    # Top books
    if len(top_loved) > 0:
        y += 30
        draw.text((100, y), "Books You Loved Most:", fill="#f39c12", font=font_medium)
        y += 35
        for _, row in top_loved.head(3).iterrows():
            title_str = str(row.get("Title", "?"))[:40]
            draw.text((120, y), f"• {title_str}", fill="#cccccc", font=font_small)
            y += 28

    # Genre tags
    if tags_list:
        y += 30
        draw.text((100, y), "Your Genres:", fill="#f39c12", font=font_medium)
        y += 35
        for tag in tags_list[:4]:
            draw.text((120, y), tag, fill="#cccccc", font=font_small)
            y += 28

    # Footer
    draw.text((width // 2, height - 40), "goodreads-wrapped.streamlit.app",
              fill="#555555", font=font_small, anchor="mt")

    return img


loved_for_card = books_you_loved(df)
card = generate_summary_card(title, emoji, stats, loved_for_card, tags)

buf = BytesIO()
card.save(buf, format="PNG")
buf.seek(0)

st.image(card, use_container_width=False, width=400)
st.download_button(
    label="📥 Download Summary Card",
    data=buf.getvalue(),
    file_name="goodreads_wrapped.png",
    mime="image/png",
)

# Footer
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center; color:#555; padding:2rem;">'
    'Made with ❤️ and 📚 | Upload your GoodReads export to see your own stats'
    '</div>',
    unsafe_allow_html=True,
)
