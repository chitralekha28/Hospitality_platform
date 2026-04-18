import os
import sys

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.hospitality_creator.app import render_app as render_hospitality_creator
from services.trip_planner.app import render_app as render_trip_planner

st.set_page_config(page_title="AI Travel + Hospitality", layout="wide", initial_sidebar_state="expanded")

st.title("Hospitality Platform - CI/CD Test Successful")
st.caption("Use the tabs below to switch between your Trip Planner and Hospitality Creator projects.")

trip_tab, hospitality_tab = st.tabs(["Trip Planner", "Hospitality Creator"])

with trip_tab:
    render_trip_planner()

with hospitality_tab:
    render_hospitality_creator()
