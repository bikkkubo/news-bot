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

        # 1. Market Overview
        market_section = self._generate_market_overview(stock_data)
        
        # 2. News Selection & Deep Dive
        # Limit to top 15 for processing
        selected_news = news_items[:15]
        news_section = self._generate_news_section(selected_news)
        
        # 3. Conclusion
        conclusion_section = self._generate_conclusion(stock_data, selected_news)

        # 4. Assembly
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

    def _generate_market_overview(self, stock_data: Dict[str, Any]) -> str:
        self.logger.log("Generating market overview...")
        
        # Format stock data for prompt
        stock_summary = "\n".join([
            f"{name}: {data['close']} (前日比: {data['change']}, {data['change_pct']}%)"
            for name, data in stock_data.items()
        ])

        prompt = f"""
Based on the following stock market data, write a concise market overview analysis for the US and Japanese markets.
Include a table for US markets and a table for the Japanese market.

Data:
{stock_summary}

Requirements:
- Use specific market names (e.g., "ナスダック総合指数").
- Analyze the trends briefly.
- Output in Markdown format.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())

    def _generate_news_section(self, news_items: List[Dict[str, Any]]) -> str:
        self.logger.log(f"Generating deep dive analysis for {len(news_items)} news items...")
        
        section_content = "## 第2章 ピックアップニュース\n\n"
        
        for i, item in enumerate(news_items, 1):
            self.logger.log(f"Processing news item {i}: {item['title']}")
            
            # Check for duplicates (simplified logic for now, assuming collector handled exact matches)
            # In a real scenario, we might ask LLM to check semantic duplication here if needed.
            
            prompt = f"""
Analyze the following news article and generate a detailed report section.

Article Title: {item['title']}
Source: {item['source']}
Published At: {item['publishedAt']}
URL: {item['url']}
Content: {item['description']}
{item.get('content', '')}

Additional Context (from Web Search):
{item.get('search_context', 'No additional context available.')}

Output Format (Markdown):
### {i}. [Translated Japanese Title] ([Published Date in JST])

**企業情報**:
- **[Company Name] ([Ticker])**: [Market Cap], [Sector]

**ニュース概要**:
[Provide a comprehensive and detailed summary. Do NOT summarize too briefly. You MUST include ALL specific numbers, dates, percentages, and financial figures found in the text.
**CROSS-REFERENCE INSTRUCTIONS**:
- Synthesize facts from both the main article and the "Additional Context" (search results).
- If the search results contain new numbers or details not in the main article, INTEGRATE them.
- **STRICTLY EXCLUDE** any personal opinions, feelings, or "analysis" from reporters in the search results. Extract ONLY the facts (numbers, quotes, events).
- Do not omit details for brevity. The goal is to provide a "deep dive" reading experience.
- MUST embed source link like ([Source Name]({item['url']})) at the end of sentences.]

**【その後の動き・最新アップデート】**:
[Compare the "Published At" date with the information in "Additional Context".
If there are stock price movements, official statements, or market reactions that happened AFTER the original news:
- Report them here with specific numbers (e.g., "The next day, stock fell X%").
- If no new information is available, write "特になし".]

**市場への影響（深堀り）**:
[This section is CRITICAL. Do NOT be generic.
- **プラスの理由**: [Explain WHY it is positive with logic. Cite sources if available.]
- **マイナスの理由**: [Explain WHY it is negative with logic. Cite sources if available.]
- **懸念事項**: [Specific risks, e.g., regulatory hurdles, competitor moves.]
- **影響を受けるセクター/銘柄**: [List specific sectors or related companies and explain the correlation.]
- **短期・長期の影響**: [Differentiate between immediate reaction and long-term structural changes.]
**REQUIREMENT**:
- Provide LOGICAL explanations (e.g., "Revenue is up, BUT margins are down due to AI costs, so stock fell").
- If a specific analyst or report is mentioned in the search context, cite them (e.g., "According to Morgan Stanley...").]

**投資家への示唆**:
[Concrete implications based on facts]

**出典**: {item['url']}
"""
            try:
                analysis = self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())
                section_content += f"{analysis}\n\n---\n\n"
            except Exception as e:
                self.logger.log(f"Error generating analysis for {item['title']}: {e}", level="ERROR")
                section_content += f"### {i}. {item['title']}\n\n*Error generating analysis.*\n\n---\n\n"

        return section_content

    def _generate_conclusion(self, stock_data: Dict[str, Any], news_items: List[Dict[str, Any]]) -> str:
        self.logger.log("Generating conclusion...")
        
        # Summarize titles for context
        titles = "\n".join([f"- {item['title']}" for item in news_items])
        
        prompt = f"""
Based on the market data and news titles below, write a "総括" (Conclusion) section.
Summarize the overall market sentiment and key takeaways for investors.

News Titles:
{titles}

Requirements:
- Fact-based summary.
- No personal opinions.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_fact_extraction_system_prompt())
