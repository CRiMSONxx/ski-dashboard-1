import re
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import helper

class ProjectTracker:
    def __init__(self, html_content, max_employee_idx):
        self.html_content = html_content
        self.max_employee_idx = max_employee_idx
        self.color_map = {}
        self.categories = {
            'PROJECT SELESAI': [],
            'ON PROGRESS': [],
            'REGISTER & POINT': [],
            'DOWNLOAD': [],
            'AUFTRAG': []
        }
        self._process_data()

    @staticmethod
    def format_date(date_str):
        if not date_str or date_str == "":
            return ""
        # Handle the specific 05.02.16 format
        return helper.to_human_date(date_str)
    def _process_data(self):
        """Parses HTML and populates the categories dictionary."""
        soup = BeautifulSoup(self.html_content, 'html.parser')
        
        # 1. Build Color Map
        style_tag = soup.find('style')
        if style_tag:
            styles = re.findall(r'\.(s\d+)\{[^}]*background-color:(#[a-fA-F0-9]{6})', style_tag.text)
            self.color_map = {class_name: hex_val for class_name, hex_val in styles}

        table = soup.find('table')
        if not table:
            return
        rows = table.find_all('tr')
        
        # 2. Extract Virtual Rows
        raw_data = []
        for r_idx in range(self.max_employee_idx, len(rows)):
            cells = rows[r_idx].find_all(['td', 'th'])
            virtual_row = []
            for cell in cells:
                colspan = int(cell.get('colspan', 1))
                text = cell.get_text(strip=True)
                class_attr = cell.get('class', [None])[0]
                bg_color = self.color_map.get(class_attr, "#ffffff")
                for _ in range(colspan):
                    virtual_row.append({'text': text, 'color': bg_color})
            
            if virtual_row:
                while len(virtual_row) <= 15: # Padded to match your highest index (15)
                    virtual_row.append({'text': '', 'color': '#ffffff'})
                raw_data.append(virtual_row)

        # 3. Categorize
        current_cat = None
        for row in raw_data:
            row_text = " ".join([c['text'] for c in row if c['text']]).upper()
            
            if "SELESAI" in row_text or "PROJECT DONE" in row_text:
                current_cat = 'PROJECT SELESAI'
                continue
            elif "ON PROGRESS" in row_text:
                current_cat = 'ON PROGRESS'
                continue
            elif "REGISTER" in row_text or "POINT" in row_text:
                current_cat = 'REGISTER & POINT'
                continue
            elif "DOWNLOAD" in row_text:
                current_cat = 'DOWNLOAD'
                continue
            elif "AUFTRAG" in row_text:
                current_cat = 'AUFTRAG'
                continue
            
            nr_val = row[2]['text']
            if nr_val and nr_val.lower() != "nr." and current_cat:
                self.categories[current_cat].append(row)

    def get_category_df(self, category_name):
        """Returns a standard DataFrame for a specific category."""
        rows = self.categories.get(category_name, [])
        if not rows:
            return pd.DataFrame()
        
        data = []
        for r in rows:
            data.append({
                "Category": category_name,
                "Nr.": r[2]['text'],
                "Projekt": r[5]['text'], 
                "to Bali": r[7]['text'],
                "to Swiss": r[8]['text'],
                "Time": r[9]['text'],
                "Priority": r[10]['text'],
                "Coordinator": r[11]['text'],
                "File": r[12]['color'],
                "over time": r[13]['text'],
                "over date": r[14]['text'],
                "Server": r[15]['text'] 
            })
        return pd.DataFrame(data)

    @property
    def all_projects_df(self):
        """Access a single DataFrame containing all projects from all categories."""
        all_dfs = [self.get_category_df(cat) for cat in self.categories.keys()]
        return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

    def display_in_streamlit(self):
        """Renders the styled tables in Streamlit."""
        order = ['PROJECT SELESAI', 'ON PROGRESS', 'REGISTER & POINT', 'DOWNLOAD', 'AUFTRAG']
        for cat_name in order:
            rows = self.categories[cat_name]
            if not rows:
                continue

            text_list = []
            color_list = []
            for r in rows:
                text_list.append({
                    "Nr.": r[2]['text'],
                    "Projekt": r[5]['text'], 
                    "to Bali": r[7]['text'],
                    "to Swiss": r[8]['text'],
                    "Time": r[9]['text'],
                    "Priority": r[10]['text'],
                    "Coordinator": r[11]['text'],
                    "File": r[12]['color'],
                    "over time": r[13]['text'],
                    "over date": r[14]['text'],
                    "Server": r[15]['text'] 
                })
                color_list.append([
                    r[0]['color'], r[2]['color'], r[5]['color'], 
                    r[6]['color'], r[7]['color'], r[8]['color'],
                    r[12]['color'], r[12]['color'],r[13]['color'], r[14]['color'], 
                    r[15]['color']
                ])

            df = pd.DataFrame(text_list)
            st.markdown(f"###### 📋 {cat_name}")
            
            styled_df = df.style.apply(
                lambda x: [f"background-color: {c}; color: black;" for c in color_list[x.name]], 
                axis=1
            )
            
            st.dataframe(
                styled_df, 
                width='stretch', 
                hide_index=True,
                column_config={"Projekt": st.column_config.Column(width=250)}
            )