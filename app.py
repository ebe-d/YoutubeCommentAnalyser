import streamlit as st
import pandas as pd
from src.analyzer import analyze_comments

# Configure the Streamlit page layout
st.set_page_config(
    page_title="YT Sentiment Analyzer",
    page_icon="📊",
    layout="wide"
)

# App Header
st.title("📊 YouTube Comment Sentiment & Toxicity Analyzer")
st.markdown("""
Paste comments from a YouTube video below. The AI will analyze the text, calculate a sentiment score, and flag toxic language.
*Perfect for rapid audience feedback analysis.*
""")

# Input Section
st.subheader("1. Input Data")
comments_input = st.text_area(
    "Paste comments here (one comment per line):",
    height=200,
    placeholder="I loved this video!\nThis tutorial was completely useless.\nOkay, this was decent."
)

# Processing and Output Section
if st.button("Analyze Sentiment", type="primary"):
    if comments_input.strip():
        with st.spinner("Analyzing comments..."):
            # Clean and split the input data
            comments_list = [c.strip() for c in comments_input.split('\n') if c.strip()]

            # Run the ML Analyzer
            df = analyze_comments(comments_list)

            st.divider()
            st.subheader("2. Dashboard Overview")

            # Top-level metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Comments", len(df))
            col2.metric("Positive 🟢", len(df[df['Sentiment'] == 'Positive']))
            col3.metric("Negative 🔴", len(df[df['Sentiment'] == 'Negative']))
            col4.metric("Toxic Flags ⚠️", len(df[df['Toxic Flag'] == '⚠️ Yes']))

            st.divider()

            # Visualizations & Data Table
            col_chart, col_table = st.columns([1, 2])

            with col_chart:
                st.subheader("Sentiment Distribution")
                # Calculate counts for the bar chart
                sentiment_counts = df['Sentiment'].value_counts()
                st.bar_chart(sentiment_counts, color="#ff4b4b")

            with col_table:
                st.subheader("Detailed Analysis")
                # Display the pandas dataframe as an interactive table
                st.dataframe(
                    df.style.map(
                        lambda x: 'background-color: #ffcccc; color: black' if x == '⚠️ Yes' else '',
                        subset=['Toxic Flag']
                    ),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("Please paste some comments into the text box first.")
