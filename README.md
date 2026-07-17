# YT Comment Analyzer — Setup Guide

## Prerequisites

You need `python3-venv` and `python3-pip` installed. Run this in your terminal:

```bash
sudo apt install python3-pip python3-venv python3.14-venv
```

## Quick Start

```bash
cd /home/ebe/Documents/College/YT-Comment-App

# 1. Create a virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

## Deactivate venv when done

```bash
deactivate
```
