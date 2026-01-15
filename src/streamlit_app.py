import streamlit as st

# Set page config at the very beginning of main.py
st.set_page_config(page_title="Planning Dashboard", layout="wide")


pages = {
    "Dashboard": [
        #st.Page("planning_ref.py", title="Reference"),
        #st.Page("planning_v1.py", title="V1"),
        st.Page("planning_v2.py", title="V2"),
    ],
}

pg = st.navigation(pages, position="top")
pg.run()