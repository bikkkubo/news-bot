import logging
import datetime
from typing import List, Dict, Any
from src.services.llm_service import LLMService
from src.utils.logger import ExecutionLogger

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, llm_service: LLMService, execution_logger: ExecutionLogger):
        self.llm = llm_service
        self.logger = execution_logger

    def generate_report(self, stock_data: Dict[str, Any], news_items: List[Dict[str, Any]]) -> str:
        """
        Orchestrates the generation of the full markdown report.
        """
        self.logger.log("Starting report generation...")

        # 1. Thematic Analysis (New Step)
        # Identify 2-3 main themes driving the market
        themes = self._identify_themes(stock_data, news_items)
        self.logger.log(f"Identified themes: {themes}")

        # 2. Market Overview (Narrative driven by themes)
        market_section = self._generate_market_overview(stock_data, themes)
        
        # 3. News Selection & Deep Dive (Tiered)
        # Limit to top 15 for processing
        selected_news = news_items[:15]
        news_section = self._generate_news_section(selected_news, themes)
        
        # 4. Conclusion
        conclusion_section = self._generate_conclusion(stock_data, selected_news, themes)

        # 5. Assembly
        today = datetime.datetime.now().strftime("%Y年%m月%d日")
        report = f"""# 市場レポート V7.2
発行日: {today}

---

{market_section}

---

{news_section}

---

{conclusion_section}

以上
"""
        self.logger.log("Report generation completed.")
        return report

    def _identify_themes(self, stock_data: Dict[str, Any], news_items: List[Dict[str, Any]]) -> str:
        """
        Analyzes stock data and news titles to identify 2-3 main market themes.
        """
        self.logger.log("Identifying market themes...")
        
        stock_summary = "\n".join([
            f"{name}: {data['change_pct']}%"
            for name, data in stock_data.items()
        ])
        
        news_titles = "\n".join([f"- {item['title']}" for item in news_items[:20]])
        
        prompt = f"""
Analyze the following stock market moves and news headlines.
Identify the top 2-3 "Main Themes" that explain today's market movements.

Stock Moves:
{stock_summary}

News Headlines:
{news_titles}

Output Format:
1. [Theme Name]: [Brief explanation of how it drove the market]
2. [Theme Name]: [Brief explanation]
3. [Theme Name]: [Brief explanation] (Optional)

Example:
1. Inflation Fears: CPI data came in hot, pushing yields up and tech stocks down.
2. China Stimulus: Announcement of new fiscal measures boosted commodities and luxury sectors.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())

    def _generate_market_overview(self, stock_data: Dict[str, Any], themes: str) -> str:
        self.logger.log("Generating market overview...")
        
        # Format stock data for prompt
        stock_summary = "\n".join([
            f"{name}: {data['close']} (前日比: {data['change']}, {data['change_pct']}%)"
            for name, data in stock_data.items()
        ])

        prompt = f"""
Based on the following stock market data and identified themes, write a concise market overview analysis for the US and Japanese markets.
Include a table for US markets and a table for the Japanese market.

Data:
{stock_summary}

Identified Themes:
{themes}

Requirements:
- **Storytelling**: Explain the market moves using the identified themes. Connect the dots (e.g., "The drop in Nasdaq was primarily driven by Theme X...").
- Use specific market names (e.g., "ナスダック総合指数").
- Output in Markdown format.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())

    def _generate_news_section(self, news_items: List[Dict[str, Any]], themes: str) -> str:
        self.logger.log(f"Generating deep dive analysis for {len(news_items)} news items...")
        
        section_content = "## 第2章 ピックアップニュース\n\n"
        
        for i, item in enumerate(news_items, 1):
            self.logger.log(f"Processing news item {i}: {item['title']}")
            
            # Treat ALL items as MAIN THEMES (Deep Dive)
            # We focus on US Stocks/Economy or major global impact
            prompt = self._get_main_theme_prompt(item, themes, i)

            try:
                analysis = self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())
                section_content += f"{analysis}\n\n---\n\n"
            except Exception as e:
                self.logger.log(f"Error generating analysis for {item['title']}: {e}", level="ERROR")
                section_content += f"### {i}. {item['title']}\n\n*Error generating analysis.*\n\n---\n\n"

        return section_content

    def _get_main_theme_prompt(self, item: Dict[str, Any], themes: str, index: int) -> str:
        return f"""
Analyze the following news article as a **MAIN THEME** driver for the US Market/Economy.

Article Title: {item['title']}
Source: {item['source']}
Published At: {item['publishedAt']}
URL: {item['url']}
Content: {item['description']}
{item.get('content', '')}

Additional Context (from Web Search):
{item.get('search_context', 'No additional context available.')}

Identified Market Themes:
{themes}

Output Format (Markdown):
### {index}. [Translated Japanese Title] ([Published Date in JST]) **【重要テーマ】**

**企業情報**:
- **[Company Name] ([Ticker])**: [Market Cap], [Sector]
  (If macro news, write "なし（マクロ・政策ニュース）")

**ニュース概要**:
[Provide a comprehensive and detailed summary. Include ALL specific numbers, dates, percentages.
Focus on the impact on US markets/economy.]

**【その後の動き・最新アップデート】**:
[Compare dates and report subsequent stock moves/reactions.
Use specific numbers (e.g., "Stock rose 3%").]

**市場への影響（深堀り）**:
[This is the CORE section. Connect the news to the Market Themes.]
- **メカニズム解説 (Why & How)**:
  - [Explain the causal chain clearly. e.g., "Yields up -> Tech valuation down".]
  - [Explain WHY this matters now.]
- **プラス/マイナスの理由**:
  - [Logical explanation with sources.]
- **影響を受けるセクター**:
  - [Specific sectors/companies in the US market.]

**投資家への監視ポイント (Watchpoints)**:
- **[Specific Indicator/Event]**: [What to watch next. e.g., "Watch the 10-year yield crossing 4.5%..."]
- **[Scenario]**: [If X happens, expect Y...]

**出典**: {item['url']}
"""

    def _generate_conclusion(self, stock_data: Dict[str, Any], news_items: List[Dict[str, Any]], themes: str) -> str:
        self.logger.log("Generating conclusion...")
        
        # Summarize titles for context
        titles = "\n".join([f"- {item['title']}" for item in news_items])
        
        prompt = f"""
Based on the market data, identified themes, and news titles below, write a "総括" (Conclusion) section.
Summarize the overall market sentiment and key takeaways for investors.

Identified Themes:
{themes}

News Titles:
{titles}

Requirements:
- Fact-based summary.
- No personal opinions.
- Reiterate the main themes and their impact.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())
