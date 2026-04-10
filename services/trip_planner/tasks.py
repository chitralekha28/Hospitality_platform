
try:
    from .agents import HospitalityAgents
except ImportError:
    from agents import HospitalityAgents

class HospitalityTasks:
    """Orchestrates the collaborative work between agents."""
    
    def __init__(self):
        self.factory = HospitalityAgents()

    def generate_itinerary(self, destination: str, duration: str, budget: str):
        """Sequential hand-off: Researcher -> Writer."""
      
        research_summary = self.factory.run_researcher(destination, duration, budget)
        
      
        final_itinerary = self.factory.run_writer(research_summary, destination, duration, budget)
        
        return final_itinerary
