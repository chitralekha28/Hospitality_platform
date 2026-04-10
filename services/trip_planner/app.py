import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

try:
    from .tasks import HospitalityTasks
except ImportError:
    from tasks import HospitalityTasks

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_PREFIX = "trip_planner_"


def _state_key(name: str) -> str:
    return f"{SESSION_PREFIX}{name}"


def _check_api_key() -> bool:
    key = os.getenv("GROQ_API_KEY", "").strip()
    return bool(key) and key != "your_groq_api_key_here"


def _fetch_destination_image(destination: str):
    try:
        query = destination.split(",")[0].strip().replace(" ", "+")
        url = f"https://source.unsplash.com/1200x500/?{query},travel,landmark"
        resp = requests.get(url, timeout=10)
        ct = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and "image" in ct:
            return Image.open(BytesIO(resp.content))
    except Exception:
        pass
    return None


def _agent_card(name: str, role: str, status: str, state: str) -> str:
    state_class = {"waiting": "waiting", "active": "active", "done": "done"}.get(state, "waiting")
    status_class = {"waiting": "status-waiting", "active": "status-active", "done": "status-done"}.get(
        state, "status-waiting"
    )
    return f"""
    <div class="agent-card {state_class}">
        <div class="agent-name">{name}</div>
        <div class="agent-role">{role}</div>
        <div class="agent-status {status_class}">{status}</div>
    </div>
    """


def _apply_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #0e1117;
}
[data-testid="stSidebar"] {
    background: #161b27;
    border-right: 1px solid #2a2f3e;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0e1117; }
::-webkit-scrollbar-thumb { background: #3a4060; border-radius: 3px; }

.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #f97316 0%, #ec4899 50%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.2;
    margin-bottom: 0.3rem;
}
.hero-subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

.sidebar-section {
    color: #f97316;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}

.budget-low { background:#1a3a1a; color:#4ade80; border:1px solid #16a34a; }
.budget-mod { background:#1a2a3f; color:#60a5fa; border:1px solid #2563eb; }
.budget-high { background:#3a1a2a; color:#f472b6; border:1px solid #db2777; }
.budget-pill {
    display: inline-block;
    padding: 0.2rem 0.8rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.4rem;
}

.agent-card {
    background: #161b27;
    border: 1px solid #2a2f3e;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    transition: all 0.3s ease;
}
.agent-card.active { border-color: #f97316; box-shadow: 0 0 12px rgba(249,115,22,0.2); }
.agent-card.done { border-color: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.15); }
.agent-card.waiting { border-color: #2a2f3e; opacity: 0.6; }
.agent-name { font-weight: 700; color: #f9fafb; font-size: 0.95rem; }
.agent-role { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.agent-status { font-size: 0.82rem; margin-top: 0.5rem; }
.status-waiting { color: #6b7280; }
.status-active { color: #f97316; }
.status-done { color: #22c55e; }

.stProgress > div > div { background: linear-gradient(90deg, #f97316, #ec4899) !important; }

.itinerary-box {
    background: #161b27;
    border: 1px solid #2a2f3e;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    line-height: 1.8;
}
.itinerary-box h1, .itinerary-box h2 { color: #f97316 !important; }
.itinerary-box h3 { color: #ec4899 !important; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #f97316, #ec4899) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.5rem !important;
}

.placeholder {
    text-align: center;
    padding: 5rem 2rem;
    color: #374151;
}
.placeholder-text { font-size: 1.1rem; }

.api-warn {
    background: #2d1a00;
    border: 1px solid #f97316;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: #fed7aa;
    font-size: 0.9rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _ensure_session_state() -> None:
    defaults = {
        "result": None,
        "running": False,
        "error": None,
        "last_dest": "",
    }
    for key, value in defaults.items():
        session_key = _state_key(key)
        if session_key not in st.session_state:
            st.session_state[session_key] = value


def render_app() -> None:
    _apply_styles()
    _ensure_session_state()

    with st.sidebar:
        st.markdown("### Trip Configuration")
        st.divider()

        if _check_api_key():
            st.success("GroqCloud API key detected")
        else:
            st.markdown(
                """
                <div class="api-warn">
                    <b>GROQ_API_KEY not set</b><br>
                    Create a <code>.env</code> file with your key from
                    <a href="https://console.groq.com" target="_blank">console.groq.com</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown('<div class="sidebar-section">Destination</div>', unsafe_allow_html=True)
        destination_input = st.text_input(
            "Where are you going?",
            value="Paris, France",
            placeholder="e.g. Kyoto, Japan",
            label_visibility="collapsed",
            key=_state_key("destination_input"),
        )

        st.markdown('<div class="sidebar-section">Duration</div>', unsafe_allow_html=True)
        duration_input = st.slider(
            "Trip length (days)",
            min_value=1,
            max_value=21,
            value=5,
            key=_state_key("duration_input"),
        )

        st.markdown('<div class="sidebar-section">Budget Level</div>', unsafe_allow_html=True)
        budget_choice = st.radio(
            "Budget",
            ["Low", "Moderate", "High"],
            index=1,
            label_visibility="collapsed",
            key=_state_key("budget_choice"),
        )

        pill_class = {"Low": "budget-low", "Moderate": "budget-mod", "High": "budget-high"}[budget_choice]
        st.markdown(f'<div class="budget-pill {pill_class}">{budget_choice} Budget</div>', unsafe_allow_html=True)

        st.divider()
        generate_btn = st.button(
            "Generate My Itinerary",
            type="primary",
            use_container_width=True,
            disabled=st.session_state[_state_key("running")] or not _check_api_key(),
            key=_state_key("generate_btn"),
        )

        st.markdown(
            """
            <div style="color:#4b5563; font-size:0.75rem; margin-top:1rem; text-align:center;">
                Powered by <b>Llama 3.3 70B</b><br>via <b>GroqCloud</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    logo_path = os.path.join(BASE_DIR, "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)

    st.markdown('<div class="hero-title">Multi-Agent Hospitality Planner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Powered by AI Researcher & Writer Agents via GroqCloud - crafting your perfect trip</div>',
        unsafe_allow_html=True,
    )

    if generate_btn and destination_input.strip():
        st.session_state[_state_key("result")] = None
        st.session_state[_state_key("error")] = None
        st.session_state[_state_key("running")] = True
        st.session_state[_state_key("last_dest")] = destination_input

        with st.spinner("Fetching destination photo..."):
            img_obj = _fetch_destination_image(destination_input)
        if img_obj:
            st.image(img_obj, caption=destination_input, use_container_width=True)

        st.divider()
        st.markdown("### Agent Activity")

        col_r, col_w = st.columns(2)
        with col_r:
            researcher_slot = st.empty()
        with col_w:
            writer_slot = st.empty()

        progress_bar = st.progress(0, text="Initialising agents...")
        status_slot = st.empty()

        def render_cards(r_state, r_status, w_state, w_status):
            researcher_slot.markdown(
                _agent_card("Senior Travel Researcher", "Searches the web for destination intel", r_status, r_state),
                unsafe_allow_html=True,
            )
            writer_slot.markdown(
                _agent_card("Travel Itinerary Writer", "Crafts your polished markdown itinerary", w_status, w_state),
                unsafe_allow_html=True,
            )

        render_cards("waiting", "Waiting to start...", "waiting", "Waiting for research...")

        try:
            tasks_orchestrator = HospitalityTasks()

            progress_bar.progress(10, text="Researcher gathering data...")
            render_cards("active", "Searching the web...", "waiting", "Waiting for research...")
            status_slot.info(f"Phase 1 / 2: Researcher is analysing {destination_input}...")

            research_output = tasks_orchestrator.factory.run_researcher(
                destination_input,
                str(duration_input),
                budget_choice,
            )

            progress_bar.progress(60, text="Writer crafting your itinerary...")
            render_cards("done", "Research complete!", "active", "Writing itinerary...")
            status_slot.info("Phase 2 / 2: Writer is building a day-by-day itinerary...")

            final_output = tasks_orchestrator.factory.run_writer(
                research_output,
                destination_input,
                str(duration_input),
                budget_choice,
            )

            st.session_state[_state_key("result")] = final_output
            progress_bar.progress(100, text="Done!")
            render_cards("done", "Research complete!", "done", "Itinerary written!")
            status_slot.success("Your itinerary is ready.")
        except Exception as exc:
            st.session_state[_state_key("error")] = str(exc)
            progress_bar.empty()
            status_slot.empty()
        finally:
            st.session_state[_state_key("running")] = False

    if st.session_state[_state_key("result")]:
        res_text = st.session_state[_state_key("result")]
        dest_name = st.session_state[_state_key("last_dest")]

        st.divider()
        st.markdown(f"### Your Itinerary for {dest_name}")
        st.markdown('<div class="itinerary-box">', unsafe_allow_html=True)
        st.markdown(res_text)
        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()

        safe_fname = dest_name.lower().replace(", ", "_").replace(" ", "_").replace("'", "")
        st.download_button(
            label="Download Itinerary (Markdown)",
            data=res_text,
            file_name=f"{safe_fname}_itinerary.md",
            mime="text/markdown",
            use_container_width=True,
            key=_state_key("download_btn"),
        )
    elif st.session_state[_state_key("error")]:
        st.error(f"An error occurred:\n\n{st.session_state[_state_key('error')]}")
    else:
        st.markdown(
            """
            <div class="placeholder">
                <div class="placeholder-text">
                    Configure your trip in the sidebar and click<br>
                    <b>Generate My Itinerary</b> to let the AI agents get to work!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    st.set_page_config(
        page_title="Hospitality AI Planner | GroqCloud",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_app()
