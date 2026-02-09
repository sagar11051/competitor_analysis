from dotenv import load_dotenv
from src.workflow import Workflow

load_dotenv()


def main():
    workflow = Workflow()
    print("AI Startup Competitive Intelligence Analyzer")

    while True:
        company_url = input("\n🔍 Enter your company website URL (or 'quit' to exit): ").strip()
        if company_url.lower() in {"quit", "exit"}:
            break
        if not company_url:
            continue

        result = workflow.run(company_url)
        print(f"\n📊 Competitive Intelligence Report for: {company_url}")
        print("=" * 60)
        print(result)

        # Company Profile
        if result["company_profile"]:
            print("\n🏢 Company Profile:")
            for k, v in result["company_profile"].model_dump().items():
                print(f"  {k}: {v}")
        else:
            print("\n[!] No company profile extracted.")

        # Competitors
        if result["competitors"]:
            print("\n👥 Top Competitors:")
            for i, comp in enumerate(result["competitors"], 1):
                print(f"  {i}. {comp.name} | {comp.website} | Score: {comp.relevance_score}")
                print(f"     {comp.description}")
        else:
            print("\n[!] No competitors found.")

        # Competitor Analyses
        if result["competitor_analyses"]:
            print("\n🔬 Competitor Analyses:")
            for i, analysis in enumerate(result["competitor_analyses"], 1):
                print(f"\n  {i}. {analysis.name} | {analysis.website}")
                for k, v in analysis.model_dump().items():
                    if k not in {"name", "website"}:
                        print(f"     {k}: {v}")
        else:
            print("\n[!] No competitor analyses available.")

        # Strategic Insights
        if result["strategic_insights"]:
            print("\n💡 Strategic Insights:")
            for k, v in result["strategic_insights"].model_dump().items():
                print(f"  {k}: {v}")
        else:
            print("\n[!] No strategic insights generated.")


if __name__ == "__main__":
    main()