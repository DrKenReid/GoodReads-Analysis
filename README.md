# GoodReads Data Analysis

A comprehensive tool for analyzing your reading life — from interactive web app to deep-dive Colab notebook. Upload your GoodReads export and get personalized stats, roasts, and beautiful quote exports.

## 🚀 Live App

**[Try GoodReads Reading Stats →](https://goodreads-analysis.streamlit.app/)**

No API key needed — just upload your GoodReads CSV export and go.

> Don't have a GoodReads account? The app includes a **demo mode** with sample data.

---

## 📚 Web App Features

### Reading Stats Tab

| Feature | Description |
|---|---|
| **Reading Personality** | Get classified as "The Binge Reader", "The Critic", "The Deep Diver", etc. based on your habits |
| **Key Stats** | Total books, pages, average rating, and fun page-count comparisons (War and Peace copies, book stack height, km of pages) |
| **Rating Analysis** | Your ratings vs community average, books you loved more than everyone else, and vice versa |
| **Reading Timeline** | Cumulative reading over time, books per year, monthly heatmap, reading streaks |
| **Genre Breakdown** | Treemap of your genres with personality tags (requires [enhanced export](https://github.com/PaulKlinger/Enhance-GoodReads-Export)) |
| **Author Stats** | Most-read authors, one-hit vs repeat authors |
| **Book Length Analysis** | Page distribution, does book length affect your rating? |
| **Shelf of Shame** | Your to-read backlog count with roasts |
| **Head-to-Head Comparison** | Upload two CSVs to compare readers side-by-side |
| **Summary Card** | Customizable, downloadable summary card |

### Quotes Collection Tab

| Feature | Description |
|---|---|
| **Quote Stats** | Total quotes, unique authors/books, average length, top 5 most popular |
| **Random Quote** | Beautifully styled random quote display with shuffle |
| **Quote Insights** | Visualizations — quotes per author, length distribution, popularity, tag analysis |
| **Browse & Select** | Filter by author, book, search text, quote length. Select individual quotes for export |
| **Themed Export** | Download selected quotes as **PDF**, **Markdown**, **HTML**, or **plain text** |
| **4 Theme Presets** | Classic (cream/brown), Dark (dark bg), Minimal (black/white), Ocean (blue tones) |
| **Customization** | Custom accent color, serif/sans-serif font, sort order (author, book, length, popularity), include/exclude tags and book titles |

---

## 📋 How to Get Your Data

### Library Export (for Reading Stats)

1. Go to [GoodReads → My Books → Import/Export](https://www.goodreads.com/review/import)
2. Click **Export Library** to download your CSV
3. Upload to the app

**For genre analysis**, enrich your CSV with [Enhance-GoodReads-Export](https://github.com/PaulKlinger/Enhance-GoodReads-Export) to add genre tags and more accurate reading dates.

### Quotes Export (for Quotes Collection)

1. Go to your [GoodReads profile](https://www.goodreads.com)
2. Scroll down to the **Quotes** section
3. Click **"Your Name's Quotes"**
4. At the top right, click **"Export my Quotes"**
5. Upload to the Quotes Collection tab

---

## 🔬 Colab Notebook

The original deep-dive analysis notebook is also included for those who want to go further:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DrKenReid/GoodReads-Analysis/blob/main/Goodreads_Analysis.ipynb)

### Techniques Demonstrated

| Category | Details |
|---|---|
| **Data Wrangling** | Pandas preprocessing, date parsing, genre standardisation |
| **Visualisation** | Seaborn, Matplotlib, Plotly, animated bar-chart races |
| **NLP** | NLTK VADER sentiment analysis, word clouds, stopword filtering |
| **Classical ML** | Linear & polynomial regression, Random Forest (scikit-learn pipelines) |
| **Deep Learning** | Keras feed-forward NN, PyTorch classification with early stopping |
| **Best Practices** | Proper train/test splits, no data leakage, centralised theming |

### Example Outputs

| | |
|---|---|
| ![Animated Genre Race](img/top_genres_pages.gif) | ![Book Titles Word Cloud](img/book-titles-word-cloud.png) |
| ![Review Length vs Rating](img/review-length-vs-rating.png) | ![Genre Ratings](img/genre-ratings.png) |
| ![Reading by Week](img/reading-by-week.png) | ![Genre Word Cloud](img/genre-word-cloud.png) |

### A Note on Predictions

The ML models yield modest accuracy — by design. Book ratings and reading speed are driven more by personal context than metadata. The low R² scores illustrate why recommendation systems need collaborative filtering or deeper content features to work well.

---

## 🛠️ Running Locally

```bash
git clone https://github.com/DrKenReid/GoodReads-Analysis.git
cd GoodReads-Analysis
pip install -r requirements.txt
streamlit run app.py
```

Or with Docker:

```bash
docker build -t goodreads-analysis .
docker run -p 8501:8501 goodreads-analysis
```

## License

This project is licensed under [CC BY 4.0](LICENSE). Issues and forks welcome — just link back to this repo.
