from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from .models import CompanyProfile, CompetitorProfile, CompetitorAnalysis, StrategicInsight, AgentState
from .prompts import CompetitiveIntelligencePrompts
from .firecrawl_service import FirecrawlService
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
import os
import json
from typing import List, Dict, Any
import re

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

# Node: Company Analysis
def company_analysis_step(state: AgentState) -> AgentState:
    firecrawl = FirecrawlService()
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=key)
    prompts = CompetitiveIntelligencePrompts()
    scraped_content = firecrawl.scrape_company_website(state.company_url)
    if not scraped_content:
        print("Failed to scrape company website.")
        return state
    messages = [
        {"role": "system", "content": prompts.COMPANY_ANALYSIS_SYSTEM},
        {"role": "user", "content": prompts.company_analysis_user(scraped_content)}
    ]
    try:
        response = llm.invoke(messages)
        cleaned_response = re.sub(r"^```json\s*|```$", "", response.content.strip(), flags=re.MULTILINE)
        company_profile = CompanyProfile(**json.loads(cleaned_response))
        state.company_profile = company_profile
    except Exception as e:
        print("Company analysis failed:", e)
    return state

# Node: Competitor Search
def competitor_search_step(state: AgentState) -> AgentState:
    import ast
    firecrawl = FirecrawlService()
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=key)
    prompts = CompetitiveIntelligencePrompts()
    if not state.company_profile:
        print("No company profile for competitor search.")
        return state
    search_results = firecrawl.search_competitors(state.company_profile.model_dump())
    candidates = json.dumps(search_results)
    kk = ast.literal_eval(candidates)
    candidates= ""
    for comp in kk:
        candidates += f"name: {comp["title"]}\n website: {comp["url"]}\n description:{comp["description"]}"
    messages = [
        {"role": "system", "content": prompts.COMPETITOR_SEARCH_SYSTEM},
        {"role": "user", "content": prompts.competitor_search_user(state.company_profile.model_dump_json(), candidates)}
    ]
    try:
        response = llm.invoke(messages)
        cleaned_response2 = re.sub(r"^```json\s*|```$", "", response.content.strip(), flags=re.MULTILINE)
        competitors = []
        for c in json.loads(cleaned_response2):
            if c["website"] is None:
                c["website"] = ""
            competitors.append(CompetitorProfile(**c))
        state.competitors = competitors
    except Exception as e:
        print("Competitor search failed:", e)
    return state

# Node: Competitor Analysis (top 3)
def competitor_analysis_step(state: AgentState) -> AgentState:
    firecrawl = FirecrawlService()
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=key)
    prompts = CompetitiveIntelligencePrompts()
    competitor_analyses = []
    for competitor in state.competitors[:3]:
        comp_content = firecrawl.scrape_competitor_website(competitor.website)
        def chunk_text_with_overlap(text, chunk_size=15000, overlap=2000):
            chunks = []
            i = 0
            while i < len(text):
                chunks.append(text[i:i+chunk_size])
                i += chunk_size - overlap
            return chunks
        def analyze_chunk(chunk, idx, total):
            # Replace with your LLM call
            messages = [
                    {"role": "system", "content": "You area helpful AI assistant help user to summarize the company analysis content below without loosing key informations like business model target market some informations about tech stack team size and any other relevent information"},
                    {"role": "user", "content": f"This is part {idx+1} of {total} of a website. Analyze and summarize the following content:{chunk}"}
                ]
            response = llm.invoke(messages)
            return f"Summary for chunk {idx+1}: {response}..."
        # Step 1: Chunk with overlap
        chunks = chunk_text_with_overlap(comp_content)
        summaries = [analyze_chunk(chunk, idx, len(chunks)) for idx, chunk in enumerate(chunks)]
        final_content = "\n\n".join(summaries)
        if not comp_content:
            continue
        messages = [
            {"role": "system", "content": prompts.COMPETITOR_ANALYSIS_SYSTEM},
            {"role": "user", "content": prompts.competitor_analysis_user(final_content)}
        ]
        try:
            response = llm.invoke(messages)
            cleaned_response = re.sub(r"^```json\s*|```$", "", response.content.strip(), flags=re.MULTILINE)
            analysis = CompetitorAnalysis(**json.loads(cleaned_response))
            competitor_analyses.append(analysis)
        except Exception as e:
            print(f"Competitor analysis failed for {competitor.name}:", e)
            continue
    state.competitor_analyses = competitor_analyses
    return state

# Node: Insight Generation
def insight_generation_step(state: AgentState) -> AgentState:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=key)
    prompts = CompetitiveIntelligencePrompts()

    try:
        messages = [
            {"role": "system", "content": prompts.INSIGHT_GENERATION_SYSTEM},
            {"role": "user", "content": prompts.insight_generation_user(
                state.company_profile.json() if state.company_profile else '{}',
                json.dumps([c.model_dump() for c in state.competitors]),
                json.dumps([a.model_dump() for a in state.competitor_analyses])
            )}
        ]
        response = llm.invoke(messages)
        cleaned = re.sub(r"^```json\s*|```$", "", response.content.strip(), flags=re.MULTILINE)
        state.strategic_insights = StrategicInsight(**json.loads(cleaned))
    except Exception as e:
        print("Insight generation failed:", e)
    return state

class Workflow:
    def __init__(self):
        # Build the workflow graph
        graph = StateGraph(AgentState)
        graph.add_node("company_analysis", company_analysis_step)
        graph.add_node("competitor_search", competitor_search_step)
        graph.add_node("competitor_analysis", competitor_analysis_step)
        graph.add_node("insight_generation", insight_generation_step)
        graph.set_entry_point("company_analysis")
        graph.add_edge("company_analysis", "competitor_search")
        graph.add_edge("competitor_search", "competitor_analysis")
        graph.add_edge("competitor_analysis", "insight_generation")
        graph.add_edge("insight_generation", END)
        self.workflow = graph.compile()

    def run(self, company_url: str) -> AgentState:
        initial_state = AgentState(company_url=company_url)
        final_state = self.workflow.invoke(initial_state)
        return final_state