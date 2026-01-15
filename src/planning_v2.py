import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import streamlit as st
from streamlit_extras.tags import tagger_component
import os
import time
import pathlib
from datetime import timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

from project_tracker import ProjectTracker
import helper
# --- 1. SCRAPER ---
HTML_FILE = "schedule_cache.html"
TALENT_HTML = "talent_cache.html"

URL_SCHEDULE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQxy9OIle28SzGUOMwz8-jsLv1bWFl5iuZVU5E9DWwy1hUC9ni7HpZORR-Fa0WPaSzyboo229vPv5aN/pubhtml?gid=1836612665&single=true&widget=false&headers=false"
URL_TALENT = "https://docs.google.com/spreadsheets/u/0/d/e/2PACX-1vTVsigeKQiKTO5GEwF0baT3AGzxQ9NIBHJM8cju5wuBd_W5ttuFNUSxfiXFgceBJ_pFOQ1jWMvPe_Cp/pubhtml/sheet?headers=false&gid=0"


# This map follows your specific image headers
TALENT_GROUPS = {
    "IT [IT]": ["IT"],
    "Register [IT]": ["Trimble Work", "STATIC X7", "Timms", "Einstellungen Projekt-Info"],
    "Preparing [C]": ["Story Setting", "Middelling / Repetitionen - Wiederholungen", "Training / Meeting", "AV Daten"],
    "2D": ["DWG"],
    "Decken": ["Slab / Mesh / Beam / Shell / Composite"],
    "Wände": ["Wall / Wall End / Mesh / Column / Composite"],
    "Dach": ["Roof / Mesh / Shell / Column / Beam / Composite / Library"],
    "Slanted Obj. [C]": ["Wall / Slab / Column / Beam / Mesh"],
    "Türen": ["Door / Opening / Library"],
    "Fenster": ["Window / Skylight / Opening / Shell / Library"],
    "Einrichtung": ["Küche / Sanitär / Technik / Möbel Einbau"],
    "Treppe": ["Stair / Slab / Library"],
    "Geländer": ["Railing / Library"],
    "Stahl": ["Stahlkonstruktion", "Mastskelett"],
    "Leitungen": ["Pipes"],
    "Fassade": ["Complex Profiles / Shell / Morph"],
    "3D Terrain": ["Mesh / Library", "Geländemodell / Gebäudemodell [Z]"],
    "New App": ["Vektor Work", "Revit"],
    "Bemassung [Z]": ["Raster", "Masslinien / Höhenkoten", "Hotlinks / Module", "Beschriftungen/Raumstempel / Auswertungen"],
    "Layout / Partner [IT]": ["Worksheet / Layouts / Masterlayouts / Ausschnitt-Set / View-Map"],
    "Additional AC Tools [Z]": ["Issue Manager / Colission-Tool / Revision"],
    "Import- & Export-Übersetzer [C]": ["2D / Publisher-Set/ PDF/ DWG/DXF Übersetzer", "3D - PLA / IFC / BIMx Übersetzer", "PointCab, LadyBug Übersetzer", "Autodesk Übersetzer .itp/.cat"],
    "Kontrolle [C]": ["Finishing Cek List / Exporte"],
    "Add-On [C]": ["IFC Viewer", "BIMx", "Rhino", "PointCab Origin [IT]", "PointCab Plugin"],
    "Werbung [Z]": ["Fotos / Animation"],
    "Bibliotheken / Attribute [C]": ["Bibliotheken-manager / Zeichnungs-manager / Attribute", "Favoriten", "Migration Up-grade / Migration Down-grade /Template Mergen [Z]", "Layer / Layer-combinations / IFC Klassifizierungen","Graphic Overrides"],
    "BIM Cloud [IT]": ["BIM Cloud / Teamwork"]
}
# Grouping TALENT_GROUPS into Roles
ROLES = {
    "IT": {
        "IT": ["IT"],
        "Register": ["Trimble Work", "STATIC X7", "Timms", "Einstellungen Projekt-Info"],
        "Layout / Partner": ["Worksheet / Layouts / Masterlayouts / Ausschnitt-Set / View-Map"],
        "BIM Cloud": ["BIM Cloud / Teamwork"]
    },
    "C": {
        "Preparing": ["Story Setting", "Middelling / Repetitionen - Wiederholungen", "Training / Meeting", "AV Daten"],
        "Slanted Obj.": ["Wall / Slab / Column / Beam / Mesh"],
        "Import- & Export-Übersetzer": ["2D / Publisher-Set/ PDF/ DWG/DXF Übersetzer", "3D - PLA / IFC / BIMx Übersetzer", "PointCab, LadyBug Übersetzer", "Autodesk Übersetzer .itp/.cat"],
        "Kontrolle": ["Finishing Cek List / Exporte"],
        "Add-On": ["IFC Viewer", "BIMx", "Rhino", "PointCab Origin [IT]", "PointCab Plugin"],
        "Bibliotheken / Attribute": ["Bibliotheken-manager / Zeichnungs-manager / Attribute", "Favoriten", "Migration Up-grade / Migration Down-grade /Template Mergen [Z]", "Layer / Layer-combinations / IFC Klassifizierungen","Graphic Overrides"]
    },
    "Z": {
        "3D Terrain": ["Mesh / Library", "Geländemodell / Gebäudemodell [Z]"],
        "Bemassung": ["Raster", "Masslinien / Höhenkoten", "Hotlinks / Module", "Beschriftungen/Raumstempel / Auswertungen"],
        "Additional AC Tools": ["Issue Manager / Colission-Tool / Revision"],
        "Werbung": ["Fotos / Animation"]
    },
    "Staff": {
        "2D": ["DWG"],
        "Decken": ["Slab / Mesh / Beam / Shell / Composite"],
        "Wände": ["Wall / Wall End / Mesh / Column / Composite"],
        "Dach": ["Roof / Mesh / Shell / Column / Beam / Composite / Library"],
        "Türen": ["Door / Opening / Library"],
        "Fenster": ["Window / Skylight / Opening / Shell / Library"],
        "Einrichtung": ["Küche / Sanitär / Technik / Möbel Einbau"],
        "Treppe": ["Stair / Slab / Library"],
        "Geländer": ["Railing / Library"],
        "Stahl": ["Stahlkonstruktion", "Mastskelett"],
        "Leitungen": ["Pipes"],
        "Fassade": ["Complex Profiles / Shell / Morph"],
        "New App": ["Vektor Work", "Revit"]
    }
}
def get_html_content(url, filename, force_refresh=False):
    file_exists = os.path.exists(filename)
    # Check if file is older than 1 hour
    is_old = file_exists and (time.time() - os.path.getmtime(filename) > 3600)

    if not file_exists or is_old or force_refresh:
        response = requests.get(url)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        return response.text
    
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

# Test
# print(to_human_date("05.02.16")) # Output: February 5th, 2016
@st.cache_data(show_spinner="Processing Project list...")  # Cache for 1 hour
def extract_project_table_simple(html_content, max_employee_idx):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr')
    
    start_row_idx = None
    nr_col_idx = None
    server_col_idx = None

    # 1. Locate the "Nr." starting point
    for r_idx in range(max_employee_idx, len(rows)):
        cells = rows[r_idx].find_all(['td', 'th'])
        for c_idx, cell in enumerate(cells):
            if cell.get_text(strip=True) == "Nr.":
                nr_col_idx = c_idx
                start_row_idx = r_idx
                break
        if start_row_idx: break

    if start_row_idx is None:
        return pd.DataFrame()
    # 2. Locate the "Server" column width
    header_cells = rows[start_row_idx].find_all(['td', 'th'])
    for c_idx in range(nr_col_idx, len(header_cells)):
        if "Server" in header_cells[c_idx].get_text(strip=True):
            server_col_idx = c_idx + 1
            break

    start_row_idx = start_row_idx - 1
    # 3. Reconstruct a simple HTML table string for the selected area
    table_html = "<table>"
    for r_idx in range(start_row_idx, len(rows)):
        cells = rows[r_idx].find_all(['td', 'th'])
        if len(cells) > nr_col_idx:
            # Check if 'Nr.' is empty after the header row to find the end
            #if r_idx > start_row_idx and not cells[nr_col_idx].get_text(strip=True):
            #    break
            
            # Extract only the columns between Nr. and Server
            row_html = "".join([str(cells[i]) for i in range(nr_col_idx, server_col_idx + 1)])
            table_html += f"<tr>{row_html}</tr>"
    table_html += "</table>"

    # 4. Use StringIO to read with Pandas
    return pd.read_html(StringIO(table_html))[0]

@st.cache_data(show_spinner="Processing Schedule...")  # Cache for 1 hour
def get_raw_data_and_colors(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    style_map = {}
    style_tag = soup.find('style')
    if style_tag:
        matches = re.findall(r'\.(s\d+)\{[^}]*background-color:(#[a-fA-F0-9]{3,6})', style_tag.text)
        style_map = {cls: color for cls, color in matches}

    table = soup.find('table')
    rows = table.find_all('tr')
    
    val_data, color_data = [], []

    for row in rows:
        v_row, c_row = [], []
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            colspan = int(cell.get('colspan', 1))
            text = cell.get_text(strip=True)
            cls = cell.get('class', [None])[0]
            color = style_map.get(cls, "#FFFFFF")
            for _ in range(colspan):
                v_row.append(text)
                c_row.append(color)
        if v_row:
            val_data.append(v_row)
            color_data.append(c_row)

    return pd.DataFrame(val_data), pd.DataFrame(color_data)

@st.cache_data(show_spinner="Processing Talent List...")
def process_talent_with_roles(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    style_tag = soup.find('style')
    
    # 1. Map CSS classes to Role names
    role_colors = {
        "#da9694": "IT", "#fabf8f": "Head Coordinator",
        "#fcd5b4": "Vice H. Coordinator", "#31869b": "Finishing Coordinator",
        "#92cddc": "Coordinator", "#ccc0da": "New Co",
        "#d9d9d9": "Trainee"
    }
    
    color_map = {}
    if style_tag:
        import re
        styles = re.findall(r'\.(s\d+)\{[^}]*background-color:(#[a-fA-F0-9]{6})', style_tag.text)
        for class_name, hex_val in styles:
            color_map[class_name] = role_colors.get(hex_val.lower(), "Staff")

    # 2. Extract Data Rows
    table = soup.find('table')
    rows = table.find_all('tr')
    headers = [cell.get_text(strip=True) for cell in rows[14].find_all(['td', 'th'])]
    
    raw_data = []
    role_list = []
    
    for row in rows[15:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) > 5:
            # Extract Text
            text_cells = [c.get_text(strip=True) for c in cells]
            
            # Extract Role from Column 3 (Index 2)
            staff_cell = cells[2]
            class_attr = staff_cell.get('class', [None])[0]
            role = color_map.get(class_attr, "Staff")
            
            if text_cells[2]: # If Staff name exists
                raw_data.append(text_cells)
                role_list.append(role)

    # 3. Assemble Dataframe
    df_raw = pd.DataFrame(raw_data)
    df_raw.columns = headers[:df_raw.shape[1]]
    #print(df_raw.head())
    
    # Apply iloc fix: Staff (2) + Date (3) + Skills (5 onwards)
    df_talent = df_raw.iloc[:, [2] + [3] + list(range(5, df_raw.shape[1]))].copy()
    #print(df_talent.head())
    
    # Add the Role column at the beginning for easy access
    df_talent.insert(1, "Role", role_list)
    
    return df_talent

# --- 2. REBUILD (Including Weekends) ---
@st.cache_data(show_spinner="Processing Project list...")  # Cache for 1 hour
def create_vertical_summary(df_summary, color_discrete_map, highlight_role=None):
    # Calculate midpoints for text placement
    df_summary['cumulative'] = df_summary['count'].cumsum()
    df_summary['midpoint'] = df_summary['cumulative'] - (df_summary['count'] / 2)
    #print(df_summary.head())
    # Create the figure
    fig_v = go.Figure()

    for i, row in df_summary.iterrows():
        role_name = row['Role']
        
        # Determine opacity: 1.0 if it's the selected role (or no role selected), 0.2 if not
        if highlight_role is None or highlight_role == "Tampilkan Semua...":
            opac = 1.0
        else:
            opac = 1.0 if role_name == highlight_role else 0.2

        fig_v.add_trace(go.Bar(
            x=[""],
            y=[row['count']],
            name=role_name,
            marker=dict(
                color=color_discrete_map.get(role_name, "#000"),
                opacity=opac,
            ),
            #hoverinfo="y+name"
            hoverinfo="skip"
        ))

        # Add Annotation (Forced text)
        fig_v.add_annotation(
            x=0,
            y=row['midpoint'],
            text=f"<b>{role_name}</b> ({row['count']})" if opac == 1.0 else "",
            showarrow=False,
            font=dict(color="black", size=13),
            bgcolor="rgba(255, 255, 255, 0.4)" if opac == 1.0 else None
        )

    fig_v.update_layout(
        barmode='stack',
        height=600,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_visible=False,
        yaxis_visible=False,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_v

def rebuild_schedule(df_v, df_c):
    # Find Anchor Date
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    start_date = None
    anchor_col = 0

    for r in range(min(15, len(df_v))):
        for c in range(min(10, len(df_v.columns))):
            match = re.search(date_pattern, str(df_v.iloc[r, c]))
            if match:
                start_date = pd.to_datetime(match.group(1), dayfirst=True)
                anchor_col = c 
                break
        if start_date: break

    if not start_date:
        return None, None, "Could not find start date."

    # Generate 14 Days Header
    work_days = ["Staff"]
    for i in range(14):
        day = start_date + timedelta(days=i)
        work_days.append(day.strftime('%a %d/%m'))

    final_rows, color_rows = [], []
    
    # Start at Row 5 (Index 4)
    for i in range(4, len(df_v)):
        name = str(df_v.iloc[i, 1]).strip() 
        
        if name and name.lower() != "none" and name != "":
            # --- THE FIX IS HERE ---
            # Get the color for the name from the same coordinates as the value
            name_color = df_c.iloc[i, 1] 
            
            # Values: [Name] + [14 days of data]
            row_vals = [name] + df_v.iloc[i, anchor_col : anchor_col + 14].tolist()
            
            # Colors: [Name Color] + [14 days of colors]
            row_cols = [name_color] + df_c.iloc[i, anchor_col : anchor_col + 14].tolist()
            
            # Padding to ensure 15 columns
            while len(row_vals) < 15: row_vals.append("")
            while len(row_cols) < 15: row_cols.append("#FFFFFF")
            
            final_rows.append(row_vals)
            color_rows.append(row_cols)

    return pd.DataFrame(final_rows, columns=work_days), pd.DataFrame(color_rows, columns=work_days), None


def apply_styles(x):
    # Set text to black and apply background colors
    style_df = pd.DataFrame('color: black; font-weight: 500;', index=x.index, columns=x.columns)
    for r in range(len(x)):
        for c in range(len(x.columns)):
            bg = st.session_state.colors.iloc[r, c]
            style_df.iloc[r, c] += f' background-color: {bg};'
    return style_df

def get_metrics_summary(df_val, df_col):
    # Adjust this hex code to the exact COLOR used in your sheet for "Day Off"
    DAY_OFF_COLOR = "#ffff00" 
    
    # Week 1: Columns 1-7 | Week 2: Columns 8-14
    # (Index 0 is the Name column)
    w1_cols = df_col.iloc[:, 1:8]
    w2_cols = df_col.iloc[:, 8:15]
    
    # Count occurrences of the color per row
    df_val['W1_Off'] = (w1_cols == DAY_OFF_COLOR).sum(axis=1)
    df_val['W2_Off'] = (w2_cols == DAY_OFF_COLOR).sum(axis=1)
    
    # Identify Free Resources (Value 0)
    # Checks if '0' exists anywhere in the 14 days for that employee
    free_resources = df_val[df_val.iloc[:, 1:15].astype(str).eq('0').any(axis=1)]['Staff'].tolist()
    
    return df_val, free_resources
def get_detailed_metrics(df_val):
    training_data = []
    free_data = []

    # Iterate through rows (employees)
    for _, row in df_val.iterrows():
        name = row["Staff"]
        emp_training_days = []
        emp_free_days = []

        # Iterate through the 14 day columns
        for col_name in df_val.columns[1:15]:
            cell_value = str(row[col_name]).strip()
            
            # Identify Training
            if "training" in cell_value.lower():
                emp_training_days.append(col_name)
            
            # Identify Value 0 (Free)
            if cell_value == "0":
                emp_free_days.append(col_name)

        if emp_training_days:
            training_data.append({"name": name, "days": emp_training_days})
        
        if emp_free_days:
            free_data.append({"name": name, "days": emp_free_days})

    return training_data, free_data

def score_skill(value):
    val = str(value).strip().lower()
    if val == 'm': return 6
    if val == 'w': return 7
    if val.isdigit(): return float(val)
    return 0

def get_mastery_score(value):
    val = str(value).strip().upper()
    mapping = {
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 
        '5.1': 6, 'M': 7, 'W': 8
    }
    return mapping.get(val, 0)

def create_stacked_skill_chart(staff_name, df_talent, talent_groups):
    # Get staff row
    row = df_talent[df_talent.iloc[:, 0] == staff_name].iloc[0]
    
    plot_data = []
    for category, sub_skills in talent_groups.items():
        for skill in sub_skills:
            if skill in df_talent.columns:
                val = row[skill]
                score = get_mastery_score(val)
                # Only include skills that have a value
                if score > 0:
                    plot_data.append({
                        "Category": category,
                        "Sub-Skill": skill,
                        "Mastery Score": score,
                        "Label": val
                    })
    
    df_plot = pd.DataFrame(plot_data)
    
    if df_plot.empty:
        return None

    # Create the Stacked Bar Chart
    fig = px.bar(
        df_plot, 
        x="Category", 
        y="Mastery Score", 
        color="Sub-Skill",
        text="Label",
        #title=f"Specialization: {staff_name}",
        # Use a diverse color palette for sub-skills
        color_discrete_sequence=px.colors.qualitative.Alphabet 
    )

    fig.update_layout(
        barmode='stack',
        bargap=0,
        xaxis={'tickangle':30, 'automargin': True}, # strongest categories first ('categoryorder':'total descending',)
        showlegend=False, # Hide legend if there are too many sub-skills
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(
            tickvals=[1, 2, 3, 4, 5, 6, 7, 8],
            ticktext=['1', '2', '3', '4', '5', '5.1', 'M', 'W'],
            title="Akumulasi Skill"
        )
    )
    
    # Add a hover template to see the full skill name
    fig.update_traces(hovertemplate="<b>%{data.name}</b><br>Level: %{text}<extra></extra>")
    
    return st.plotly_chart(fig, width='stretch')

def create_proficiency_heatmap(df_talent):
    # Force everything to string to ensure '5.1', 'M', and 'W' show up
    mastery_levels = ['1', '2', '3', '4', '5', '5.1', 'M', 'W']
    
    skills = [c for c in df_talent.columns if c != "Staff" and  c != "Role"]
    
    agg_data = []
    for level in mastery_levels:
        level_counts = []
        for skill in skills:
            # Case-insensitive count for M/W and exact match for numbers
            count = df_talent[skill].astype(str).str.strip().str.upper().eq(level.upper()).sum()
            level_counts.append(count)
        agg_data.append(level_counts)

    # Create Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=agg_data,
        x=skills,
        y=mastery_levels, # Use the explicit string labels
        colorscale='YlGnBu',
        text=agg_data,
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(title="Staff")
    ))

    fig.update_layout(
        title="<b>Distribusi Specialist</b>",
        yaxis_title="Tahapan",
        # Force the Y-axis to treat labels as discrete categories
        yaxis={'type': 'category'},
        height=600,
        margin=dict(l=50, r=50, t=100, b=150)
    )
    
    fig.update_xaxes(tickangle=-45, side="top") # Labels on top for easier reading
    
    return fig

def create_specialized_radar(selected_staff, df_talent, role_name, key=None):
    """
    key is for streamlit specific
    Creates a radar chart based on specific role groups (IT, C, Z, or Staff).
    Handles 'W'=8, 'M'=7, and numeric strings like '5.1'.
    """
    # 1. Configuration & Mapping
    # W is highest (8), M is below W (7)
    proficiency_map = {
        'W': 8.0, 'w': 8.0,
        'M': 7.0, 'm': 7.0,
        '': 0.0, None: 0.0
    }
    
    # Use the ROLES dictionary we defined previously
    # (Ensure the ROLES dict is defined in your script scope)
    target_groups = ROLES.get(role_name, {})
    
    if not target_groups:
        st.error(f"Role group '{role_name}' not found.")
        return

    # 2. Extract Staff Data
    staff_data = df_talent[df_talent['Staff'] == selected_staff]
    if staff_data.empty:
        st.warning(f"No data for {selected_staff}")
        return

    categories = []
    values = []

    # 3. Process each group in the Role
    for group_name, skills in target_groups.items():
        valid_skills = [s for s in skills if s in staff_data.columns]
        
        if valid_skills:
            skill_row = staff_data[valid_skills].iloc[0]
            numeric_vals = []
            
            for val in skill_row:
                val_str = str(val).strip()
                
                if val_str in proficiency_map:
                    numeric_vals.append(proficiency_map[val_str])
                else:
                    try:
                        # Handles 1, 2, 5.1, etc.
                        numeric_vals.append(float(val_str))
                    except ValueError:
                        numeric_vals.append(0.0)

            # Calculate average for the specific group
            avg_val = sum(numeric_vals) / len(numeric_vals) if numeric_vals else 0
            categories.append(group_name)
            values.append(avg_val)

    if not categories:
        st.info(f"No skill data available for {role_name} group.")
        return

    # 4. Close the Radar Path (append first item to end)
    plot_categories = categories + [categories[0]]
    plot_values = values + [values[0]]

    # 5. Create Plotly Figure
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=plot_values,
        theta=plot_categories,
        fill='toself',
        name=f"{selected_staff} - {role_name}",
        line=dict(color='#1f77b4', width=2),
        fillcolor='rgba(31, 119, 180, 0.3)',
        marker=dict(size=6)
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 8],  # Constant 0-8 scale
                tickvals=[1,2,3,4,5,6,7,8],
                ticktext=['1','2','3','4','5','5.1','M','W'],
                tickfont=dict(size=15,color='#FE7743',weight="bold")
            ),
            angularaxis=dict(
                tickfont=dict(size=13),
                rotation=90,
                direction="clockwise"
            )
        ),
        showlegend=False,
        height=350,
        margin=dict(l=0, r=0, t=20, b=25)
    )

    st.plotly_chart(
        fig, 
        width='stretch', 
        key=f"radar_{selected_staff}_{role_name}_{key}" # This ensures uniqueness
    )
# --- 3. DISPLAY ---
st.set_page_config(page_title='Dasbor Surya Kumara Indonesia',  layout='wide', page_icon=':house:')

t1, t2, t3 = st.columns((.5,7, 1)) 
try:
    t1.image('src/assets/views/logo-icon.png', width = 80)
except:
    with t1:
        st.error("logo")
t2.title("Workforce Dashboard - Interactive Report")
with t3:
    if st.button("🔄 Request Fresh Data", type="tertiary"):
        st.cache_data.clear()
        html_schedule = get_html_content(URL_SCHEDULE, "schedule_cache.html", force_refresh=True)
        html_talent = get_html_content(URL_TALENT, "talent_cache.html", force_refresh=True)
    else:
        html_schedule = get_html_content(URL_SCHEDULE, "schedule_cache.html")
        html_talent = get_html_content(URL_TALENT, "talent_cache.html")

# Process the HTML (from disk or memory)
raw_v, raw_c = get_raw_data_and_colors(html_schedule) # Your existing schedule processor
df, colors, err = rebuild_schedule(raw_v, raw_c)

# Store in session state for styling functions
max_employee_row = len(df)
tracker = ProjectTracker(html_schedule, max_employee_row+5)

# Your specific Hex Colors
color_discrete_map = {
    "IT": "#da9694",
    "Head Coordinator": "#fabf8f",
    "Vice H. Coordinator": "#fcd5b4",
    "Finishing Coordinator": "#31869b",
    "Coordinator": "#92cddc",
    "New Co": "#ccc0da",
    "Trainee": "#d9d9d9",
    "Staff": "#eeeeee"
}# --- Initialization ---
df_talent = process_talent_with_roles(html_talent)
#print(df_talent.head(10))
df_summary = df_talent["Role"].value_counts().reset_index()
total_count = len(df_talent)-1

st.session_state.df = df
st.session_state.colors = colors

st.markdown(f"#### 👩‍💼👨‍💼 {total_count} Staff")
staff_list = df_talent.iloc[:, 0].unique().tolist()
selected_staff = st.selectbox("Pencarian Detail Staff", ["Tampilkan Semua..."] + staff_list)

# Define Highlight Role
current_role = None
if selected_staff != "Tampilkan Semua...":
    current_role = df_talent[df_talent.iloc[:, 0] == selected_staff]['Role'].iloc[0]

# --- Main Layout ---
col_summary, col_main = st.columns([1, 4])

with col_summary:
    fig_v = create_vertical_summary(df_summary, color_discrete_map, highlight_role=current_role)
    st.plotly_chart(fig_v, width='stretch', config={'displayModeBar': False})

with col_main:
    if selected_staff != "Tampilkan Semua...":
        # 1. Fetch Staff Metadata
        staff_info = df_talent[df_talent['Staff'] == selected_staff].iloc[0]
        staff_role = staff_info['Role']  # e.g., "Head Coordinator"

        # 2. Logic to determine which Radar to show first
        # Map the official Role string to our ROLES dictionary keys
        # If Role is 'Head Coordinator', they likely need 'C' (Control) skills
        role_priority = "Staff"
        if "IT" in staff_role.upper():
            role_priority = "IT"
        elif "COORDINATOR" in staff_role.upper() or "HEAD" in staff_role.upper():
            role_priority = "C"
        elif "SUPPORT" in staff_role.upper():
            role_priority = "Z"

        # 3. Display Workload and Skills in Columns
        col_work, col_radar = st.columns([.7, 1])

        with col_work:
            from streamlit_avatar import avatar
            staff_profile = df_talent[
                df_talent['Staff'].str.contains(selected_staff, case=False, na=False)
            ].reset_index()
            avatar(
                [
                    {
                        "url": "https://picsum.photos/id/237/300/300",
                        "size": 40,
                        "title": f"{selected_staff} | 👦👩",
                        "caption": f"{helper.to_human_date(staff_profile['Date'][0])}  💼 {helper.count_time_since(staff_profile['Date'][0])}",
                        "key": "avatar1",
                    }
                ]
            )
            st.markdown("#### 🚀 Projects")
            # Filter projects from your ProjectTracker instance
            staff_projects = tracker.all_projects_df[
                tracker.all_projects_df['Coordinator'].str.contains(selected_staff, case=False, na=False)
            ].reset_index()

            if not staff_projects.empty:
                helper.render_project_section(staff_projects, "PROJECTS", "#ADADAD")
            else:
                st.info("No active projects.")

        with col_radar:
            st.markdown(f"#### 🕸️ {staff_role} Skill Fit")
            # This shows the radar chart most relevant to their 'Head Coordinator' role
            tabs = st.tabs(["Staff Skills", "Control (C)", "IT Systems", "Additional (Z)", "FULL"])
            
            with tabs[0]: create_specialized_radar(selected_staff, df_talent, "Staff", key="main_staff")
            with tabs[1]: create_specialized_radar(selected_staff, df_talent, "C", key="main_it")
            with tabs[2]: create_specialized_radar(selected_staff, df_talent, "IT", key="main_c")
            with tabs[3]: create_specialized_radar(selected_staff, df_talent, "Z", key="main_z")
            with tabs[4]: create_stacked_skill_chart(selected_staff, df_talent, TALENT_GROUPS)

        st.divider()

        # 4. Secondary Skills Tabs
        st.markdown("#### 🔍 Full Skill Breakdown")
    else:
        # Full Team Heatmap (if no one is selected)
        fig_heat = create_proficiency_heatmap(df_talent)
        st.plotly_chart(fig_heat, width='stretch')
st.divider()


if "df" in st.session_state:
    train_list, free_list = get_detailed_metrics(st.session_state.df)
    df_with_off, _ = get_metrics_summary(st.session_state.df, st.session_state.colors)


    # Layout: 3 Columns
    col1, col2, col3 = st.columns([1,3,2])

    with col1:
        st.markdown("##### 🎓 Training")
        if train_list:
            for item in train_list:
                st.info(f"**{item['name']}**\n\n" + ", ".join(item['days']))
        else:
            st.write("Tidak ada yang training.")

    with col2:
        # Grouping names by date to save space
        free_by_date = {}
        for _, row in st.session_state.df.iterrows():
            for col in st.session_state.df.columns[1:15]:
                if str(row[col]) == "0":
                    free_by_date.setdefault(col, []).append(row["Staff"])

        # Display in a compact grid
        st.markdown("##### 🟢 Free Resources")
        if free_by_date:
            for date, names in free_by_date.items():
                # Clean date (e.g., "Mon 12/05") : Names
                st.write(f"**{date}**: {', '.join(names)}")
        else:
            st.write("None")

    with col3:
        st.markdown("##### 🗓️ Quota Izin")
        for _, row in df_with_off.iterrows():
            total = row['W1_Off'] + row['W2_Off']
            if total > 0:
                label = f"{row['Staff']} ({total}/30)"
                with st.expander(label):
                    st.write(f"**Week 1:** {row['W1_Off']} days")
                    st.write(f"**Week 2:** {row['W2_Off']} days")
                    st.progress(total / 30) # Visual quota bar


#reduce top padding and app header to be transparent (check .streamlit/config.toml)
st.markdown(
    """
        <style>
                .stAppHeader {
                    background-color: rgba(255, 255, 255, 0.0);  /* Transparent background */
                    z-index: 1;
                }
                button[kind="tertiary"] {
                    z-index: 999;
                    position: relative;
                }

            .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)