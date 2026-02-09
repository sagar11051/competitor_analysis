# AI Startup Competitive Intelligence Analyzer

This project provides automated, AI-powered competitive intelligence for startups and developer tool companies. By analyzing a company website, it generates a comprehensive report covering the company profile, top competitors, detailed competitor analyses, and actionable strategic insights.

## What Information Does the Analysis Provide?

After running an analysis, the tool outputs the following:

### 1. Company Profile
A structured summary of the target company, including:
- **name**: Company name
- **website**: Official website URL
- **business_model**: Business model (e.g., SaaS, Open Source, Marketplace)
- **target_market**: Main customer or user segment
- **key_services**: List of main products/services
- **tech_stack**: Technologies, frameworks, or languages used
- **description**: 1-2 sentence summary of the company

### 2. Top Competitors
A ranked list of the most relevant competitors, each with:
- **name**: Competitor name
- **website**: Competitor website
- **description**: 1-2 sentence summary
- **relevance_score**: Relevance (0-1, higher is more relevant)

### 3. Competitor Analyses (Top 3)
For the top 3 competitors, a deep-dive analysis is provided, including:
- **name**: Competitor name
- **website**: URL
- **business_model**: Business model
- **target_market**: Target market
- **key_services**: List of main services/products
- **tech_stack**: Technologies used
- **description**: 1-2 sentence summary
- **features**: List of notable features
- **pricing**: Pricing information
- **integration_capabilities**: Integrations with other tools/platforms
- **messaging**: Key marketing or product messaging
- **target_audience**: Intended users/customers
- **value_propositions**: Unique value points
- **infrastructure**: Infrastructure details
- **development_patterns**: Notable development practices
- **team_size**: Team size (number, range, or unknown)
- **funding_history**: Funding rounds or history
- **market_expansion_signals**: Signs of market growth or expansion
- **blog_topics**: Main blog topics
- **seo_keywords**: SEO keywords targeted
- **thought_leadership_themes**: Themes in thought leadership content

### 4. Strategic Insights
Actionable recommendations and intelligence, including:
- **feature_gaps**: Features missing in the target company compared to competitors
- **opportunities**: Market or product opportunities
- **positioning_suggestions**: Suggestions for market positioning
- **fundraising_intel**: Fundraising tips or intelligence

## Output Format
- All fields are robust to missing data: if information is not found, fields may be `None`, an empty string, or an empty list.
- Lists may contain strings or numbers, and some fields may be a string, a list, or `None` depending on the data found.

## How It Works
1. **Company Analysis**: Scrapes and analyzes the target company's website to extract a structured profile.
2. **Competitor Search**: Identifies and ranks relevant competitors using web search and AI analysis.
3. **Competitor Analysis**: Scrapes and analyzes the top competitors' websites for detailed comparison.
4. **Insight Generation**: Synthesizes all data to generate actionable strategic insights.

## Example Usage
Run the tool and enter a company website URL when prompted. The tool will output a competitive intelligence report with all the information described above.

---

For more details, see the `src/models.py` file for the full data structure and field definitions.
