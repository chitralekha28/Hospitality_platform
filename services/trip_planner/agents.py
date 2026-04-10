
import os
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )


search_tool = DuckDuckGoSearchRun()

class HospitalityAgents:
    """Specialised hospitality AI agents using LangChain."""

    def __init__(self):
        self.llm = get_llm()

    def run_researcher(self, destination: str, duration: str, budget: str) -> str:
        """Runs the Senior Travel Researcher agent."""
        prompt = f"""
        Role: Senior Travel Researcher
        Goal: Discover the very best travel options, accommodations, and local activities.
        Destination: {destination}
        Duration: {duration} days
        Budget: {budget}
        
        Instructions:
        Search for real-world details on landmarks, dining, and hotels matching the budget.
        Provide a comprehensive summary of your findings.
        """
       
        search_query = f"best {budget} budget travel activities and hotels in {destination} {duration} days"
        search_results = search_tool.run(search_query)
        
        full_prompt = f"{prompt}\n\nWeb Search Results:\n{search_results}\n\nPlease synthesize this into a structured research summary."
        response = self.llm.invoke(full_prompt)
        return response.content

    def run_writer(self, research_data: str, destination: str, duration: str, budget: str) -> str:
        """Runs the Travel Itinerary Writer agent."""
        prompt = f"""
        Role: Travel Itinerary Writer
        Goal: Craft a beautifully formatted markdown travel itinerary.
        Destination: {destination}
        Duration: {duration} days
        Budget: {budget}
        
        Context (Research Data):
        {research_data}
        
        Instructions:
        - Catchy Title
        - Vivid Intro
        - Day-by-Day (Morning, Afternoon, Evening)
        - Dining & Where to Stay
        - Travel Tips & Packing
        
        Use bolding, emojis, and clear headers to make it look premium.
        """
        response = self.llm.invoke(prompt)
        return response.content