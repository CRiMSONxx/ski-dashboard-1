from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import streamlit as st
import pandas as pd

def to_human_date(date_str):
    """
    Converts '05.02.16' (DD.MM.YY) to 'February 5th, 2016'
    """
    try:
        # 1. Parse the input string
        dt = datetime.strptime(date_str, "%d.%m.%y")
        
        # 2. Determine the day suffix (st, nd, rd, th)
        day = dt.day
        if 11 <= day <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            
        # 3. Format into a clean string
        # %B = Full Month Name, %-d = Day without leading zero, %Y = 4-digit Year
        return dt.strftime(f"%B {day}{suffix}, %Y")
    
    except (ValueError, TypeError):
        # Return original string if format is invalid
        return date_str
    
def count_time_since(date_str):
    """
    Calculates time elapsed since 'DD.MM.YY'
    Returns string like '2 years, 3 months'
    """
    if not date_str or date_str.strip() == "":
        return ""
        
    try:
        # 1. Parse the input string (DD.MM.YY)
        start_date = datetime.strptime(date_str, "%d.%m.%y")
        # 2. Get current date
        now = datetime.now()
        
        # 3. Calculate difference
        diff = relativedelta(now, start_date)
        
        # 4. Build readable string
        parts = []
        if diff.years > 0:
            parts.append(f"{diff.years} Thn")
        if diff.months > 0:
            parts.append(f"{diff.months} Bulan")
        if diff.days > 0 and diff.years == 0: # Show days only if recent
            parts.append(f"{diff.days} Hari")
            
        return " ".join(parts) if parts else "Today"
        
    except (ValueError, TypeError):
        return ""
    
# 1. Define the rendering function (Make sure this is outside your main loop)
def render_project_section(df, title, header_color):
    if df.empty:
        st.write(f"No {title.lower()} projects.")
        return

    # Build the string
    html = f"""
    <table style="width:100%; border-collapse:collapse; color:black; background-color:white; font-family:sans-serif;">
        <tr style="background-color:{header_color}; font-weight:bold; border-bottom:2px solid #ccc;">
            <th style="padding:8px; text-align:left;">Category</th>
            <th style="padding:8px; text-align:left;">Project & Data From</th>
            <th style="padding:8px; text-align:right;">Time</th>
        </tr>
    """
    for _, row in df.iterrows():
        #print(row)
        html += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:8px;">{row['Category']}</td>
            <td style="padding:8px;background-color:{row['File']}">{row['Projekt']}</td>
            <td style="padding:8px; text-align:right;">{row['Time']}</td>
        </tr>
        """
    html += "</table>"
    
    # THIS LINE IS KEY:
    st.html(html, unsafe_allow_javascript=False)