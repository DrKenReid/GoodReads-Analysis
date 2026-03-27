"""
GoodReads Reading Stats — your reading life, analyzed. 📚
"""

import streamlit as st
import pandas as pd
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from src.analytics import (
    load_and_clean, reading_stats, reading_personality, rating_analysis,
    books_you_loved, books_you_hated, books_by_year, books_by_month,
    reading_streak, top_authors, genre_breakdown, genre_personality_tags,
    shelf_of_shame, page_stats, stats_commentary, shelf_roast,
    generate_demo_data, fun_page_facts, compare_reading_stats,
    shared_authors, comparison_commentary,
)
from src.charts import (
    rating_distribution_chart, rating_comparison_chart, books_per_year_chart,
    cumulative_reading_chart, reading_heatmap, top_authors_chart,
    genre_treemap, page_distribution_chart, page_vs_rating_chart,
    rating_difference_chart, stats_comparison_chart, shared_authors_chart,
    PLOT_CONFIG,
)

st.set_page_config(page_title="GoodReads Reading Stats", page_icon="📚", layout="wide")

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
    .comparison-card {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 1rem;
        border: 1px solid #e74c3c33;
        margin: 0.5rem 0;
    }
    .winner-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: #f39c12;
        color: #0e1117;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📚 GoodReads Reading Stats")
st.markdown("*Your reading life, analyzed.*")
st.markdown("---")

with st.expander("📋 How to get your data (& unlock genre analysis)"):
    st.markdown("""
**Basic export** (works for most features):
1. Go to [GoodReads → My Books → Import/Export](https://www.goodreads.com/review/import)
2. Click **Export Library** → download the CSV
3. Upload it here!

**Enhanced export** (unlocks genre breakdown, more accurate dates):
1. Do the basic export first
2. Run [Enhance-GoodReads-Export](https://github.com/PaulKlinger/Enhance-GoodReads-Export) on your CSV
3. This adds genre tags, read dates, and more metadata
4. Upload the enhanced CSV for the full experience!
    """)

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

# ═══════════════════════════════════════════
# QUOTES CSV DETECTION & HANDLING
# ═══════════════════════════════════════════
is_quotes_csv = "Goodreads Quote Id" in df.columns or "Quote" in df.columns

if is_quotes_csv:
    st.markdown("## 💬 Your GoodReads Quotes")
    st.info("We detected a **Quotes** export. Here's what we found!")

    total_quotes = len(df)
    st.metric("📝 Total Quotes Saved", f"{total_quotes:,}")

    # Most-quoted authors
    author_col = None
    for c in ["Author", "author", "Author Name"]:
        if c in df.columns:
            author_col = c
            break

    if author_col:
        author_counts = df[author_col].value_counts().head(15).reset_index()
        author_counts.columns = ["Author", "Quotes"]
        st.markdown("### ✍️ Most-Quoted Authors")
        fig = top_authors_chart(author_counts.rename(columns={"Quotes": "Books"}))
        fig.update_layout(title=dict(text="Most-Quoted Authors"))
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    # Tags / top tags
    tag_col = None
    for c in ["Tags", "tags", "Tag"]:
        if c in df.columns:
            tag_col = c
            break

    if tag_col:
        all_tags = {}
        for val in df[tag_col].dropna():
            for t in str(val).split(","):
                t = t.strip()
                if t:
                    all_tags[t] = all_tags.get(t, 0) + 1
        if all_tags:
            st.markdown("### 🏷️ Top Quote Tags")
            sorted_tags = sorted(all_tags.items(), key=lambda x: -x[1])[:20]
            tags_html = " ".join(
                f'<span class="genre-tag">{t} ({c})</span>' for t, c in sorted_tags
            )
            st.markdown(f'<div style="margin:8px 0;">{tags_html}</div>', unsafe_allow_html=True)

    # Random quote display
    quote_col = None
    for c in ["Quote", "quote", "Text", "text"]:
        if c in df.columns:
            quote_col = c
            break

    if quote_col:
        st.markdown("### 🎲 Random Quote")
        valid_quotes = df[quote_col].dropna()
        if len(valid_quotes) > 0:
            random_quote = valid_quotes.sample(1).iloc[0]
            author_text = ""
            if author_col and pd.notna(df.loc[valid_quotes.sample(1).index[0], author_col] if author_col in df.columns else None):
                idx = valid_quotes.sample(1, random_state=42).index[0]
                random_quote = df.loc[idx, quote_col]
                if author_col in df.columns:
                    author_text = f" — *{df.loc[idx, author_col]}*"
            st.markdown(f'> "{random_quote}"{author_text}')
            if st.button("🔄 Another quote"):
                st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; color:#555; padding:2rem;">'
        'Want the full reading analysis? Upload your <b>library export</b> instead!<br>'
        'Go to GoodReads → My Books → Import/Export → Export Library'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Validate required columns exist
required_cols = ["Title", "Author"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}. Is this a GoodReads export CSV?")
    st.caption(f"Found columns: {', '.join(df.columns.tolist())}")
    st.stop()

# ═══════════════════════════════════════════
# COMPARISON MODE
# ═══════════════════════════════════════════
show_comparison = st.checkbox("⚔️ Compare with another reader")
df2 = None

if show_comparison:
    uploaded2 = st.file_uploader("Upload second reader's GoodReads CSV", type=["csv"], key="compare_upload")
    if uploaded2:
        df2 = load_and_clean(pd.read_csv(uploaded2))

if show_comparison and df2 is not None:
    # Get names from filenames or first author
    name1 = uploaded.name.replace(".csv", "").replace("_", " ").title() if uploaded else "Reader 1"
    name2 = uploaded2.name.replace(".csv", "").replace("_", " ").title() if uploaded2 else "Reader 2"

    stats1 = reading_stats(df)
    stats2 = reading_stats(df2)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## ⚔️ Head-to-Head Reading Showdown")

    # Personality cards side by side
    title1, emoji1, desc1 = reading_personality(stats1, df)
    title2, emoji2, desc2 = reading_personality(stats2, df2)

    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown(f"""
        <div class="comparison-card">
            <div style="font-size:3rem;">{emoji1}</div>
            <div style="font-size:1.5rem; font-weight:bold; color:#f39c12;">{name1}</div>
            <div style="font-size:1.1rem; color:#ccc;">{title1}</div>
            <div style="font-size:0.9rem; color:#999; margin-top:0.5rem;">{desc1}</div>
        </div>
        """, unsafe_allow_html=True)
    with pc2:
        st.markdown(f"""
        <div class="comparison-card">
            <div style="font-size:3rem;">{emoji2}</div>
            <div style="font-size:1.5rem; font-weight:bold; color:#3498db;">{name2}</div>
            <div style="font-size:1.1rem; color:#ccc;">{title2}</div>
            <div style="font-size:0.9rem; color:#999; margin-top:0.5rem;">{desc2}</div>
        </div>
        """, unsafe_allow_html=True)

    # Stats showdown
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 📊 Stats Showdown")

    comparisons = compare_reading_stats(stats1, stats2, name1, name2)
    for comp in comparisons:
        trophy = "🏆" if comp["winner"] else "🤝"
        winner_text = f'{trophy} **{comp["winner"]}**' if comp["winner"] else f"{trophy} Tie!"
        sc1, sc2, sc3 = st.columns([2, 1, 2])
        with sc1:
            st.metric(f"{name1}", comp["value1"])
        with sc2:
            st.markdown(f"**{comp['stat']}**\n\n{winner_text}")
        with sc3:
            st.metric(f"{name2}", comp["value2"])

    # Comparison chart
    st.plotly_chart(stats_comparison_chart(stats1, stats2, name1, name2),
                    use_container_width=True, config=PLOT_CONFIG)

    # Shared authors
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 📚 Shared Authors")
    shared_df = shared_authors(df, df2)
    if len(shared_df) > 0:
        st.markdown(f"You both read **{len(shared_df)}** authors in common!")
        st.plotly_chart(shared_authors_chart(shared_df, name1, name2),
                        use_container_width=True, config=PLOT_CONFIG)
    else:
        st.info("No shared authors found — you two have completely different taste! 🤷")

    # Genre overlap
    genres1 = genre_breakdown(df)
    genres2 = genre_breakdown(df2)
    if len(genres1) > 0 and len(genres2) > 0:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 🎯 Genre Overlap")
        g1_set = set(genres1["Genre"].str.lower())
        g2_set = set(genres2["Genre"].str.lower())
        overlap = g1_set & g2_set
        only1 = g1_set - g2_set
        only2 = g2_set - g1_set
        if overlap:
            overlap_html = " ".join(f'<span class="genre-tag">{g.title()}</span>' for g in sorted(overlap))
            st.markdown(f"**Shared genres:** {overlap_html}", unsafe_allow_html=True)
        if only1:
            st.markdown(f"**Only {name1}:** {', '.join(sorted(g.title() for g in list(only1)[:10]))}")
        if only2:
            st.markdown(f"**Only {name2}:** {', '.join(sorted(g.title() for g in list(only2)[:10]))}")

    # Commentary
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("## 🎤 The Verdict")
    commentary = comparison_commentary(stats1, stats2, name1, name2)
    st.markdown(f'<div class="roast-text">{commentary}</div>', unsafe_allow_html=True)

    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; color:#555; padding:2rem;">'
        'Made with ❤️ and 📚 | Upload your GoodReads export to see your own stats'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ═══════════════════════════════════════════
# SINGLE PLAYER MODE
# ═══════════════════════════════════════════

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

# Fun page facts
if stats["total_pages"] > 0:
    facts = fun_page_facts(stats["total_pages"])
    if facts:
        st.markdown("### 🤯 Fun Page Facts")
        for fact in facts:
            st.markdown(fact)

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

card_sections = st.multiselect(
    "Choose sections to include on your card:",
    options=["Reading Personality", "Key Stats", "Top Books", "Genre Tags", "Fun Page Facts", "Author Stats"],
    default=["Reading Personality", "Key Stats", "Top Books", "Genre Tags"],
)

# Build HTML card for display
_card_html_parts = []

# Personality
if "Reading Personality" in card_sections:
    _card_html_parts.append(f'''
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:64px;">{emoji}</div>
        <div style="font-size:24px;font-weight:bold;color:#f39c12;">{title}</div>
        <div style="font-size:14px;color:#aaa;">{description}</div>
    </div>''')

# Key Stats
if "Key Stats" in card_sections:
    _card_html_parts.append(f'''
    <div style="display:flex;justify-content:space-around;text-align:center;background:rgba(255,255,255,0.05);border-radius:8px;padding:16px;margin-bottom:20px;">
        <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["total_books"]:,}</div><div style="font-size:11px;color:#888;">Books Read</div></div>
        <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["total_pages"]:,}</div><div style="font-size:11px;color:#888;">Pages</div></div>
        <div><div style="font-size:22px;font-weight:bold;color:white;">⭐ {stats["avg_rating"]}</div><div style="font-size:11px;color:#888;">Avg Rating</div></div>
        <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["avg_pages"]:,}</div><div style="font-size:11px;color:#888;">Avg Pages</div></div>
    </div>''')

# Top Books
if "Top Books" in card_sections:
    loved_for_card = books_you_loved(df)
    if len(loved_for_card) > 0:
        books_html = ""
        for _, row in loved_for_card.head(3).iterrows():
            t = str(row.get("Title", "?"))[:50]
            a = str(row.get("Author", ""))[:30]
            books_html += f'<div style="padding:4px 0;"><span style="color:white;">{t}</span> <span style="color:#888;">— {a}</span></div>'
        _card_html_parts.append(f'''
    <div style="margin-bottom:20px;">
        <div style="font-size:12px;color:#888;margin-bottom:6px;">📖 BOOKS YOU LOVED</div>
        {books_html}
    </div>''')

# Genre Tags
if "Genre Tags" in card_sections:
    tags = genre_personality_tags(df)
    if tags:
        pills = " ".join(f'<span style="background:#e74c3c;color:white;padding:3px 10px;border-radius:12px;font-size:12px;margin:2px;display:inline-block;">{t}</span>' for t in tags[:5])
        _card_html_parts.append(f'<div style="margin-bottom:20px;">{pills}</div>')

# Fun Page Facts
if "Fun Page Facts" in card_sections:
    page_facts_for_card = fun_page_facts(stats["total_pages"]) if stats["total_pages"] > 0 else []
    if page_facts_for_card:
        facts_html = "".join(f'<div style="padding:3px 0;color:#ccc;font-size:13px;">{f}</div>' for f in page_facts_for_card[:3])
        _card_html_parts.append(f'''
    <div style="margin-bottom:20px;">
        <div style="font-size:12px;color:#888;margin-bottom:6px;">📏 FUN FACTS</div>
        {facts_html}
    </div>''')

# Author Stats
if "Author Stats" in card_sections:
    authors_for_card = top_authors(df)
    if len(authors_for_card) > 0:
        auth_html = "".join(f'<div style="padding:3px 0;color:#ccc;">• {row["Author"]} ({row["Books"]} books)</div>' for _, row in authors_for_card.head(5).iterrows())
        _card_html_parts.append(f'''
    <div style="margin-bottom:20px;">
        <div style="font-size:12px;color:#888;margin-bottom:6px;">✍️ TOP AUTHORS</div>
        {auth_html}
    </div>''')

_card_inner = "\n".join(_card_html_parts)
_full_card_html = f'''
<div style="background:linear-gradient(135deg,#0e1117,#1a1c2e);border:2px solid #e74c3c;border-radius:16px;padding:28px;max-width:600px;margin:0 auto;font-family:sans-serif;color:white;">
    <div style="text-align:center;font-size:20px;font-weight:bold;color:#f39c12;margin-bottom:20px;">📚 GoodReads Reading Stats</div>
    {_card_inner}
    <div style="text-align:center;color:#555;font-size:11px;border-top:1px solid #333;padding-top:10px;">
        goodreads-analysis.streamlit.app
    </div>
</div>
'''

# Display card
try:
    st.html(_full_card_html)
except AttributeError:
    st.markdown(_full_card_html, unsafe_allow_html=True)

st.caption("📱 Screenshot this card to share, or download below!")

# Generate downloadable PNG version with Pillow (no emoji, clean text)
try:
    CARD_W = 900
    PAD = 30

    # Load fonts
    _fonts = {}
    for fname, fsize in [("title", 28), ("sub", 20), ("body", 16), ("small", 13)]:
        for fpath in [
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if fname == 'title' else ''}.ttf",
            f"C:/Windows/Fonts/{'arialbd.ttf' if fname == 'title' else 'arial.ttf'}",
        ]:
            try:
                _fonts[fname] = ImageFont.truetype(fpath, fsize)
                break
            except (OSError, IOError):
                continue
        if fname not in _fonts:
            _fonts[fname] = ImageFont.load_default(size=fsize)

    # Calculate height
    cy = PAD + 40  # header
    if "Reading Personality" in card_sections:
        cy += 70
    if "Key Stats" in card_sections:
        cy += 4 * 35 + 30
    if "Top Books" in card_sections and len(loved_for_card) > 0:
        cy += 25 + min(len(loved_for_card), 3) * 28
    if "Genre Tags" in card_sections and tags:
        cy += 45
    if "Fun Page Facts" in card_sections and page_facts_for_card:
        cy += 25 + min(len(page_facts_for_card), 3) * 28
    if "Author Stats" in card_sections and len(authors_for_card) > 0:
        cy += 25 + min(len(authors_for_card), 5) * 28
    cy += 50  # footer
    CARD_H = max(cy, 300)

    _img = Image.new("RGB", (CARD_W, CARD_H), color=(14, 17, 23))
    _draw = ImageDraw.Draw(_img)

    # Gradient
    for _i in range(CARD_H):
        _r = int(14 + (26 - 14) * _i / CARD_H)
        _g = int(17 + (28 - 17) * _i / CARD_H)
        _b = int(23 + (46 - 23) * _i / CARD_H)
        _draw.line([(0, _i), (CARD_W, _i)], fill=(_r, _g, _b))

    _draw.rounded_rectangle([(8, 8), (CARD_W - 8, CARD_H - 8)], radius=16, outline="#e74c3c", width=2)

    # Header
    _draw.text((CARD_W // 2, PAD), "GoodReads Reading Stats", fill="#f39c12", font=_fonts["title"], anchor="mt")
    _y = PAD + 50

    # Personality (text only — no emoji in PNG)
    if "Reading Personality" in card_sections:
        _draw.text((CARD_W // 2, _y), title, fill="#f39c12", font=_fonts["title"], anchor="mt")
        _y += 35
        desc_short = description[:80] + "..." if len(description) > 80 else description
        _draw.text((CARD_W // 2, _y), desc_short, fill="#aaaaaa", font=_fonts["small"], anchor="mt")
        _y += 35

    # Key Stats
    if "Key Stats" in card_sections:
        for lbl, val in [("Books Read", f"{stats['total_books']:,}"), ("Total Pages", f"{stats['total_pages']:,}"),
                          ("Avg Rating", f"{stats['avg_rating']}"), ("Avg Pages/Book", f"{stats['avg_pages']:,}")]:
            _draw.text((PAD + 40, _y), lbl, fill="#888888", font=_fonts["body"])
            _draw.text((CARD_W - PAD - 40, _y), val, fill="white", font=_fonts["body"], anchor="rt")
            _y += 35
        _y += 10

    # Top Books
    if "Top Books" in card_sections and len(loved_for_card) > 0:
        _draw.text((PAD + 40, _y), "BOOKS YOU LOVED", fill="#888888", font=_fonts["small"])
        _y += 25
        for _, _row in loved_for_card.head(3).iterrows():
            _t = str(_row.get("Title", "?"))[:50]
            _draw.text((PAD + 50, _y), f"- {_t}", fill="#cccccc", font=_fonts["body"])
            _y += 28

    # Genre Tags
    if "Genre Tags" in card_sections and tags:
        tag_str = " | ".join(tags[:5])
        _draw.text((CARD_W // 2, _y + 10), tag_str, fill="#e74c3c", font=_fonts["body"], anchor="mt")
        _y += 45

    # Fun Facts
    if "Fun Page Facts" in card_sections and page_facts_for_card:
        _draw.text((PAD + 40, _y), "FUN FACTS", fill="#888888", font=_fonts["small"])
        _y += 25
        for _fact in page_facts_for_card[:3]:
            _clean = _fact.replace("**", "").replace("*", "")
            import re as _re
            _clean = _re.sub(r'[\U00010000-\U0010ffff]', '', _clean).strip()
            if len(_clean) > 75:
                _clean = _clean[:72] + "..."
            _draw.text((PAD + 50, _y), _clean, fill="#cccccc", font=_fonts["small"])
            _y += 28

    # Authors
    if "Author Stats" in card_sections and len(authors_for_card) > 0:
        _draw.text((PAD + 40, _y), "TOP AUTHORS", fill="#888888", font=_fonts["small"])
        _y += 25
        for _, _row in authors_for_card.head(5).iterrows():
            _draw.text((PAD + 50, _y), f"- {_row['Author']} ({_row['Books']} books)", fill="#cccccc", font=_fonts["body"])
            _y += 28

    # Footer
    _draw.text((CARD_W // 2, CARD_H - 30), "goodreads-analysis.streamlit.app", fill="#555555", font=_fonts["small"], anchor="mt")

    _buf = BytesIO()
    _img.save(_buf, format="PNG")
    _card_fname = f"goodreads_stats.png"

    col_dl_l, col_dl_c, col_dl_r = st.columns([1, 2, 1])
    with col_dl_c:
        st.download_button(
            label="📥 Download Summary Card (PNG)",
            data=_buf.getvalue(),
            file_name=_card_fname,
            mime="image/png",
        )
except Exception as e:
    st.caption(f"📷 To save this card, take a screenshot.")

# Footer
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center; color:#555; padding:2rem;">'
    'Made with ❤️ and 📚 | Upload your GoodReads export to see your own stats'
    '</div>',
    unsafe_allow_html=True,
)
