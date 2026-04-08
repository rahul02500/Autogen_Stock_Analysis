import streamlit as st
import os
import yfinance as yf
from datetime import datetime
import uuid
from agents import Agents
from agent_orchestrator import orchestrate_agents
from app_config import AppConfig

# Helper to fetch sidebar metrics since we aren't touching tools.py
def fetch_sidebar_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Price": f"{info.get('currentPrice', 'N/A')} {info.get('currency', '')}",
            "Market Cap": f"{info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "N/A",
            "52W High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52W Low": info.get("fiftyTwoWeekLow", "N/A")
        }
    except Exception:
        return None

class StockAnalysisApp:
    def __init__(self):
        self.config = AppConfig()
        self.agents = Agents()

    def render_sidebar(self):
        with st.sidebar:
            st.header("🔧 Configuration")
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=os.environ.get("OPENAI_API_KEY", ""),
                help="Enter your OpenAI API key"
            )
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

            st.divider()
            st.header("📊 Quick Stock Info")
            quick_ticker = st.text_input("Enter ticker for quick view:", placeholder="e.g., AAPL")
            if quick_ticker:
                quick_ticker = quick_ticker.upper()
                metrics = fetch_sidebar_metrics(quick_ticker)
                if metrics:
                    for metric, value in metrics.items():
                        st.metric(metric, value)
                else:
                    st.error("Ticker not found.")

    def render_main_content(self):
        st.markdown('<h1 class="main-header">📈 AI Stock Analysis Platform</h1>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;"><strong>Powered by AutoGen AI Agents</strong></div>', unsafe_allow_html=True)

        user_request = st.text_input(
            "Enter your query:",
            placeholder="Should I invest in MSFT based on recent trends?",
            help="Mention stock symbol you want to analyze"
        )

        if st.button("Run Analysis", disabled=not(user_request)):
            if not os.environ.get("OPENAI_API_KEY"):
                st.error("⚠️ Please provide your OpenAI API key in the sidebar")
            else:
                with st.spinner("🤖 AI agents are analyzing..."):
                    # Initializing 4 agents (reporting, technical, strategy, user)
                    agents_tuple = self.agents.initialize_agents()
                    if all(agents_tuple):
                        analysis_data = orchestrate_agents(user_request, *agents_tuple)
                        st.session_state.analysis_results[user_request] = {
                            "timestamp": datetime.now(),
                            "result": analysis_data
                        }

        if user_request in st.session_state.analysis_results:
            st.header("📋 Analysis Results")
            st.markdown(st.session_state.analysis_results[user_request]["result"])
            st.download_button(
                label="📥 Download Report",
                data=st.session_state.analysis_results[user_request]["result"],
                file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )

    def run(self):
        self.config.setup_page()
        self.config.initialize_session_state()
        self.render_sidebar()
        self.render_main_content()

if __name__ == "__main__":
    app = StockAnalysisApp()
    app.run()
