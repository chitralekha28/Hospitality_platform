

import os
import sys
from dotenv import load_dotenv

try:
    from .tasks import HospitalityTasks
except ImportError:
    from tasks import HospitalityTasks

load_dotenv()

def validate_env():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key or key == "your_groq_api_key_here":
        print("\n❌  ERROR: GROQ_API_KEY is not set.")
        sys.exit(1)

def main():
    validate_env()
    print("\n" + "=" * 60)
    print("  🌍  Multi-Agent Hospitality System  (Groq + LangChain)")
    print("=" * 60)

    destination = input("\n📍 Destination [Paris, France]: ") or "Paris, France"
    duration    = input("🗓️  Duration (days) [4]: ") or "4"
    budget      = input("💰 Budget (Low/Moderate/High) [Moderate]: ") or "Moderate"

    print(f"\n✅ Planning your trip to {destination}...\n")
    
    orchestrator = HospitalityTasks()
    
    try:
        itinerary = orchestrator.generate_itinerary(destination, duration, budget)
        print("\n" + "=" * 60)
        print(f"  ✈️  FINAL ITINERARY — {destination.upper()}")
        print("=" * 60 + "\n")
        print(itinerary)
        
        filename = f"{destination.replace(' ', '_').lower()}_itinerary.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(itinerary)
        print(f"\n💾 Saved to {filename}")
        
    except Exception as exc:
        print(f"❌ Error: {exc}")

if __name__ == "__main__":
    main()
