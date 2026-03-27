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
    quotes_per_author_chart, quote_length_chart, tags_chart, popularity_chart,
    PLOT_CONFIG,
)
from src.quotes import (
    load_quotes, quotes_stats, quotes_by_author, quote_length_stats,
    tag_counts, generate_pdf, generate_markdown, generate_html, generate_text,
    THEMES,
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
    .quote-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #e74c3c33;
        border-left: 4px solid #f39c12;
        border-radius: 0 1rem 1rem 0;
        padding: 2rem 2.5rem;
        margin: 1.5rem 0;
        font-family: Georgia, 'Times New Roman', serif;
    }
    .quote-card .quote-text {
        font-size: 1.3rem;
        color: #e0e0e0;
        line-height: 1.8;
        font-style: italic;
    }
    .quote-card .quote-attr {
        margin-top: 1rem;
        color: #f39c12;
        font-size: 1rem;
        font-style: normal;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 📚 GoodReads Reading Stats")
st.markdown("*Your reading life, analyzed.*")
st.markdown("---")

# ═══════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════
tab_reading, tab_quotes = st.tabs(["📚 Reading Stats", "💬 Quotes Collection"])

# ═══════════════════════════════════════════
# TAB 1: READING STATS (all original content)
# ═══════════════════════════════════════════
with tab_reading:
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
                                     help="Go to GoodReads → My Books → Import/Export → Export Library",
                                     key="reading_upload")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        demo = st.button("🎮 Try Demo Mode", key="reading_demo")

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
    else:
        # Process data
        df = load_and_clean(df)

        # ═══════════════════════════════════════════
        # QUOTES CSV DETECTION & HANDLING
        # ═══════════════════════════════════════════
        is_quotes_csv = "Goodreads Quote Id" in df.columns or ("Quote" in df.columns and "Title" not in df.columns)

        if is_quotes_csv:
            st.markdown("## 💬 Your GoodReads Quotes")
            st.info("We detected a **Quotes** export — head over to the **💬 Quotes Collection** tab for the full experience!")

            if "Quote" in df.columns:
                st.session_state["quotes_from_reading_tab"] = df

        else:
            # Validate required columns exist
            required_cols = ["Title", "Author"]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}. Is this a GoodReads export CSV?")
                st.caption(f"Found columns: {', '.join(df.columns.tolist())}")
            else:
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
                    name1 = uploaded.name.replace(".csv", "").replace("_", " ").title() if uploaded else "Reader 1"
                    name2 = uploaded2.name.replace(".csv", "").replace("_", " ").title() if uploaded2 else "Reader 2"

                    stats1 = reading_stats(df)
                    stats2 = reading_stats(df2)

                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## ⚔️ Head-to-Head Reading Showdown")

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

                    st.plotly_chart(stats_comparison_chart(stats1, stats2, name1, name2),
                                    use_container_width=True, config=PLOT_CONFIG)

                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## 📚 Shared Authors")
                    shared_df = shared_authors(df, df2)
                    if len(shared_df) > 0:
                        st.markdown(f"You both read **{len(shared_df)}** authors in common!")
                        st.plotly_chart(shared_authors_chart(shared_df, name1, name2),
                                        use_container_width=True, config=PLOT_CONFIG)
                    else:
                        st.info("No shared authors found — you two have completely different taste! 🤷")

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

                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## 🎤 The Verdict")
                    commentary = comparison_commentary(stats1, stats2, name1, name2)
                    st.markdown(f'<div class="roast-text">{commentary}</div>', unsafe_allow_html=True)

                else:
                    # ═══════════════════════════════════════════
                    # SINGLE PLAYER MODE
                    # ═══════════════════════════════════════════
                    stats = reading_stats(df)

                    # 1. READING PERSONALITY
                    title, emoji, description = reading_personality(stats, df)

                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="personality-card">
                        <div class="personality-emoji">{emoji}</div>
                        <div class="personality-title">{title}</div>
                        <div class="personality-desc">{description}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    tags = genre_personality_tags(df)
                    if tags:
                        tags_html = "".join(f'<span class="genre-tag">{t}</span>' for t in tags)
                        st.markdown(f'<div style="text-align:center; margin-top:1rem;">{tags_html}</div>',
                                    unsafe_allow_html=True)

                    # 2. KEY STATS
                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## 📊 Your Reading Stats")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("📚 Books Read", f"{stats['total_books']:,}")
                    c2.metric("📄 Total Pages", f"{stats['total_pages']:,}")
                    c3.metric("⭐ Avg Rating", f"{stats['avg_rating']}")
                    c4.metric("📏 Avg Pages/Book", f"{stats['avg_pages']:,}")

                    commentary = stats_commentary(stats)
                    st.markdown(f'<div class="roast-text">{commentary}</div>', unsafe_allow_html=True)

                    if stats["total_pages"] > 0:
                        facts = fun_page_facts(stats["total_pages"])
                        if facts:
                            st.markdown("### 🤯 Fun Page Facts")
                            for fact in facts:
                                st.markdown(fact)

                    # 3. RATING ANALYSIS
                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## ⭐ Rating Analysis")

                    ra = rating_analysis(df)
                    if ra.get("has_data"):
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            st.plotly_chart(rating_distribution_chart(df), use_container_width=True, config=PLOT_CONFIG)
                        with rc2:
                            st.plotly_chart(rating_comparison_chart(df), use_container_width=True, config=PLOT_CONFIG)

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

                    # 4. READING TIMELINE
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

                    # 5. GENRE BREAKDOWN
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

                    # 6. AUTHOR STATS
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

                    # 7. BOOK LENGTH ANALYSIS
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

                    # 8. THE SHELF OF SHAME
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

                    # 9. READING SUMMARY CARD
                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    st.markdown("## 📸 Reading Summary Card")

                    card_sections = st.multiselect(
                        "Choose sections to include on your card:",
                        options=["Reading Personality", "Key Stats", "Top Books", "Genre Tags", "Fun Page Facts", "Author Stats"],
                        default=["Reading Personality", "Key Stats", "Top Books", "Genre Tags"],
                    )

                    _card_html_parts = []

                    if "Reading Personality" in card_sections:
                        _card_html_parts.append(f'''
                        <div style="text-align:center;margin-bottom:20px;">
                            <div style="font-size:64px;">{emoji}</div>
                            <div style="font-size:24px;font-weight:bold;color:#f39c12;">{title}</div>
                            <div style="font-size:14px;color:#aaa;">{description}</div>
                        </div>''')

                    if "Key Stats" in card_sections:
                        _card_html_parts.append(f'''
                        <div style="display:flex;justify-content:space-around;text-align:center;background:rgba(255,255,255,0.05);border-radius:8px;padding:16px;margin-bottom:20px;">
                            <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["total_books"]:,}</div><div style="font-size:11px;color:#888;">Books Read</div></div>
                            <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["total_pages"]:,}</div><div style="font-size:11px;color:#888;">Pages</div></div>
                            <div><div style="font-size:22px;font-weight:bold;color:white;">⭐ {stats["avg_rating"]}</div><div style="font-size:11px;color:#888;">Avg Rating</div></div>
                            <div><div style="font-size:22px;font-weight:bold;color:white;">{stats["avg_pages"]:,}</div><div style="font-size:11px;color:#888;">Avg Pages</div></div>
                        </div>''')

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

                    if "Genre Tags" in card_sections:
                        tags = genre_personality_tags(df)
                        if tags:
                            pills = " ".join(f'<span style="background:#e74c3c;color:white;padding:3px 10px;border-radius:12px;font-size:12px;margin:2px;display:inline-block;">{t}</span>' for t in tags[:5])
                            _card_html_parts.append(f'<div style="margin-bottom:20px;">{pills}</div>')

                    if "Fun Page Facts" in card_sections:
                        page_facts_for_card = fun_page_facts(stats["total_pages"]) if stats["total_pages"] > 0 else []
                        if page_facts_for_card:
                            facts_html = "".join(f'<div style="padding:3px 0;color:#ccc;font-size:13px;">{f}</div>' for f in page_facts_for_card[:3])
                            _card_html_parts.append(f'''
                        <div style="margin-bottom:20px;">
                            <div style="font-size:12px;color:#888;margin-bottom:6px;">📏 FUN FACTS</div>
                            {facts_html}
                        </div>''')

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

                    import streamlit.components.v1 as components

                    _download_card_html = f'''
                    <html>
                    <head>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
                    <style>
                    body {{ margin: 0; padding: 0; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
                    .card {{
                        background: linear-gradient(135deg, #0e1117, #1a1c2e);
                        border: 2px solid #e74c3c;
                        border-radius: 16px;
                        padding: 28px;
                        max-width: 600px;
                        margin: 0 auto;
                        color: white;
                    }}
                    .card-header {{ text-align: center; font-size: 20px; font-weight: bold; color: #f39c12; margin-bottom: 20px; }}
                    .download-btn {{
                        display: block;
                        margin: 16px auto 0;
                        padding: 10px 24px;
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 15px;
                        cursor: pointer;
                        font-weight: bold;
                    }}
                    .download-btn:hover {{ background: #c0392b; }}
                    </style>
                    </head>
                    <body>
                    <div id="capture-card" class="card">
                        <div class="card-header">📚 GoodReads Reading Stats</div>
                        {_card_inner}
                        <div style="text-align:center;color:#555;font-size:11px;border-top:1px solid #333;padding-top:10px;margin-top:10px;">
                            goodreads-analysis.streamlit.app
                        </div>
                    </div>
                    <button class="download-btn" onclick="downloadCard()">📥 Download Summary Card</button>
                    <script>
                    function downloadCard() {{
                        const card = document.getElementById('capture-card');
                        html2canvas(card, {{
                            backgroundColor: '#0e1117',
                            scale: 2,
                            useCORS: true,
                            logging: false,
                        }}).then(canvas => {{
                            const link = document.createElement('a');
                            link.download = 'goodreads_reading_stats.png';
                            link.href = canvas.toDataURL('image/png');
                            link.click();
                        }});
                    }}
                    </script>
                    </body>
                    </html>
                    '''

                    _component_h = 350
                    if "Reading Personality" in card_sections: _component_h += 120
                    if "Key Stats" in card_sections: _component_h += 140
                    if "Top Books" in card_sections: _component_h += 120
                    if "Genre Tags" in card_sections: _component_h += 60
                    if "Fun Page Facts" in card_sections: _component_h += 120
                    if "Author Stats" in card_sections: _component_h += 180

                    components.html(_download_card_html, height=_component_h, scrolling=False)

    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; color:#555; padding:2rem;">'
        'Made with ❤️ and 📚 | Upload your GoodReads export to see your own stats'
        '</div>',
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════
# TAB 2: QUOTES COLLECTION
# ═══════════════════════════════════════════
with tab_quotes:
    with st.expander("📋 How to export your GoodReads quotes"):
        st.markdown("""
**To get your quotes from GoodReads:**
1. Go to [goodreads.com](https://www.goodreads.com)
2. Click **My Quotes** (in the navigation or your profile)
3. Scroll to the very bottom of your quotes page
4. Click **Export Quotes** to download a CSV
5. Upload it here!
        """)

    # Check if quotes were detected from the reading tab
    has_reading_tab_quotes = "quotes_from_reading_tab" in st.session_state

    qcol1, qcol2 = st.columns([3, 1])
    with qcol1:
        quotes_uploaded = st.file_uploader(
            "Upload your GoodReads Quotes CSV",
            type=["csv"],
            help="Export from GoodReads → My Quotes → Export Quotes",
            key="quotes_upload",
        )
    with qcol2:
        st.markdown("<br>", unsafe_allow_html=True)
        quotes_demo = st.button("🎮 Try Demo Quotes", key="quotes_demo")

    if has_reading_tab_quotes and not quotes_uploaded:
        st.info("💡 We detected a quotes CSV in the Reading Stats tab — you can use it here!")
        if st.button("📋 Use quotes from Reading tab"):
            st.session_state["use_reading_quotes"] = True

    # Load quotes data
    qdf = None
    if quotes_uploaded:
        qdf = load_quotes(pd.read_csv(quotes_uploaded))
    elif quotes_demo or st.session_state.get("quotes_demo_mode"):
        st.session_state["quotes_demo_mode"] = True
        try:
            demo_url = "https://raw.githubusercontent.com/DrKenReid/GoodReads-Quotes-PDF/main/data/goodreads_quotes_export.csv"
            qdf = load_quotes(pd.read_csv(demo_url))
            st.info("📖 Using demo quotes data — upload your own for the real thing!")
        except Exception:
            st.warning("Couldn't load demo data — try uploading your own CSV!")
    elif st.session_state.get("use_reading_quotes") and has_reading_tab_quotes:
        qdf = load_quotes(st.session_state["quotes_from_reading_tab"])

    if qdf is None or len(qdf) == 0:
        st.markdown("### 👆 Upload your GoodReads quotes export to get started")
        st.markdown("Or click **Try Demo Quotes** to see what it looks like!")
    else:
        # ═══════════════════════════════════════════
        # QUOTES STATS
        # ═══════════════════════════════════════════
        qs = quotes_stats(qdf)

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 📊 Quotes Stats")

        qm1, qm2, qm3, qm4 = st.columns(4)
        qm1.metric("📝 Total Quotes", f"{qs['total']:,}")
        qm2.metric("✍️ Unique Authors", f"{qs['unique_authors']:,}")
        qm3.metric("📚 Unique Books", f"{qs['unique_books']:,}")
        qm4.metric("📏 Avg Words/Quote", f"{qs['avg_length']}")

        if qs["most_popular_quote"]:
            st.markdown("### 🏆 Most Popular Quote")
            pop_quote = qs["most_popular_quote"][:300]
            pop_author = qs["most_popular_author"]
            st.markdown(f"""
            <div class="quote-card">
                <div class="quote-text">"{pop_quote}"</div>
                <div class="quote-attr">— {pop_author} (popularity: {qs['most_popular_score']:,})</div>
            </div>
            """, unsafe_allow_html=True)

        # ═══════════════════════════════════════════
        # RANDOM QUOTE
        # ═══════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 🎲 Random Quote")

        if "quote_idx" not in st.session_state:
            st.session_state["quote_idx"] = random.randint(0, len(qdf) - 1)

        if st.button("🔄 Show Another", key="shuffle_quote"):
            st.session_state["quote_idx"] = random.randint(0, len(qdf) - 1)

        ridx = st.session_state["quote_idx"] % len(qdf)
        rrow = qdf.iloc[ridx]
        rquote = str(rrow.get("Quote", ""))
        rauthor = str(rrow.get("Author", "")) if "Author" in rrow.index else ""
        rbook = str(rrow.get("Book", "")) if "Book" in rrow.index else ""
        rattr_parts = [p for p in [rauthor, rbook] if p and p != "nan"]
        rattr = f"— {', '.join(rattr_parts)}" if rattr_parts else ""

        st.markdown(f"""
        <div class="quote-card">
            <div class="quote-text">"{rquote}"</div>
            <div class="quote-attr">{rattr}</div>
        </div>
        """, unsafe_allow_html=True)

        # ═══════════════════════════════════════════
        # BROWSE & FILTER QUOTES
        # ═══════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 🔍 Browse & Select Quotes")

        # Filters
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            all_authors = sorted(qdf["Author"].dropna().unique().tolist()) if "Author" in qdf.columns else []
            filter_authors = st.multiselect("Filter by Author", all_authors, key="q_filter_author")
        with fcol2:
            all_books = sorted(qdf["Book"].dropna().unique().tolist()) if "Book" in qdf.columns else []
            filter_books = st.multiselect("Filter by Book", all_books, key="q_filter_book")
        with fcol3:
            search_text = st.text_input("Search quotes", key="q_search")

        filtered = qdf.copy()
        if filter_authors:
            filtered = filtered[filtered["Author"].isin(filter_authors)]
        if filter_books:
            filtered = filtered[filtered["Book"].isin(filter_books)]
        if search_text:
            mask = filtered["Quote"].str.contains(search_text, case=False, na=False)
            if "Author" in filtered.columns:
                mask = mask | filtered["Author"].str.contains(search_text, case=False, na=False)
            if "Tags" in filtered.columns:
                mask = mask | filtered["Tags"].astype(str).str.contains(search_text, case=False, na=False)
            filtered = filtered[mask]

        st.markdown(f"**{len(filtered)}** quotes shown")

        # Select all / deselect all
        sel_col1, sel_col2, _ = st.columns([1, 1, 4])
        with sel_col1:
            if st.button("✅ Select All", key="q_select_all"):
                st.session_state["q_selected"] = set(filtered.index.tolist())
        with sel_col2:
            if st.button("❌ Deselect All", key="q_deselect_all"):
                st.session_state["q_selected"] = set()

        if "q_selected" not in st.session_state:
            st.session_state["q_selected"] = set(filtered.index.tolist())

        # Display table with selection
        display_cols = [c for c in ["Quote", "Author", "Book", "Tags", "Popularity"] if c in filtered.columns]
        if display_cols:
            # Truncate quote text for display
            display_df = filtered[display_cols].copy()
            if "Quote" in display_df.columns:
                display_df["Quote"] = display_df["Quote"].str[:100] + display_df["Quote"].apply(lambda x: "..." if len(str(x)) > 100 else "")

            edited_df = st.data_editor(
                display_df,
                column_config={
                    "Quote": st.column_config.TextColumn("Quote", width="large"),
                },
                use_container_width=True,
                hide_index=True,
                key="quotes_table",
            )

        # ═══════════════════════════════════════════
        # VISUALIZATIONS
        # ═══════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 📈 Visualizations")

        # Quotes per author
        author_data = quotes_by_author(qdf)
        if len(author_data) > 0:
            st.plotly_chart(quotes_per_author_chart(author_data), use_container_width=True, config=PLOT_CONFIG)

        viz1, viz2 = st.columns(2)

        # Quote length distribution
        length_data = quote_length_stats(qdf)
        if len(length_data) > 0:
            with viz1:
                st.plotly_chart(quote_length_chart(length_data), use_container_width=True, config=PLOT_CONFIG)

        # Popularity distribution
        if "Popularity" in qdf.columns and qdf["Popularity"].sum() > 0:
            with viz2:
                st.plotly_chart(popularity_chart(qdf), use_container_width=True, config=PLOT_CONFIG)

        # Tags chart
        tc = tag_counts(qdf)
        if len(tc) > 0:
            st.plotly_chart(tags_chart(tc), use_container_width=True, config=PLOT_CONFIG)

        # ═══════════════════════════════════════════
        # EXPORT / DOWNLOAD
        # ═══════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("## 📥 Export Quotes")

        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            export_title = st.text_input("Export title", value="My GoodReads Quotes", key="export_title")
            theme_name = st.selectbox("Theme preset", list(THEMES.keys()), key="export_theme")
            accent_color = st.color_picker("Accent color", value=THEMES[theme_name]["accent"], key="export_accent")
            font_style = st.radio("Font style", ["Serif", "Sans-Serif"], horizontal=True, key="export_font")

        with exp_col2:
            include_tags = st.checkbox("Include tags", value=True, key="export_tags")
            include_books = st.checkbox("Include book titles", value=True, key="export_books")
            include_popularity = st.checkbox("Include popularity scores", value=False, key="export_pop")
            use_selected_only = st.checkbox("Export selected/filtered quotes only", value=False, key="export_selected")

        # Build theme with custom accent
        export_theme = THEMES[theme_name].copy()
        export_theme["accent"] = accent_color

        # Choose which quotes to export
        export_df = filtered if use_selected_only else qdf

        st.markdown(f"**Exporting {len(export_df)} quotes**")

        dl1, dl2, dl3, dl4 = st.columns(4)

        with dl1:
            try:
                pdf_bytes = generate_pdf(
                    export_df, title=export_title, theme=export_theme,
                    font=font_style.lower().replace("-", ""),
                    include_tags=include_tags, include_books=include_books,
                )
                st.download_button("📄 Download PDF", pdf_bytes, "quotes.pdf", "application/pdf", key="dl_pdf")
            except ImportError:
                st.warning("Install `fpdf2` for PDF export")

        with dl2:
            md_text = generate_markdown(export_df, title=export_title, include_tags=include_tags)
            st.download_button("📝 Download Markdown", md_text, "quotes.md", "text/markdown", key="dl_md")

        with dl3:
            html_text = generate_html(
                export_df, title=export_title, theme_colors=export_theme,
                font="serif" if font_style == "Serif" else "sans-serif",
            )
            st.download_button("🌐 Download HTML", html_text, "quotes.html", "text/html", key="dl_html")

        with dl4:
            txt_text = generate_text(export_df, title=export_title)
            st.download_button("📋 Download Text", txt_text, "quotes.txt", "text/plain", key="dl_txt")

    # Footer
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; color:#555; padding:2rem;">'
        'Made with ❤️ and 📚 | Your quotes, beautifully organized'
        '</div>',
        unsafe_allow_html=True,
    )
