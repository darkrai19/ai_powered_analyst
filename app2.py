import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
import re
import os
import io
import plotly.express as px
import json

# --- 1. Load Credentials and Configure Page ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, OPENAI_API_KEY]):
    st.error("FATAL ERROR: Missing one or more environment variables. Please check your server configuration.")
    st.stop()

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

st.set_page_config(page_title="AI Data Analyst", page_icon="🤖", layout="wide")
st.title("🤖 AI Data Analyst")

# --- 2. Setup Cached Resources ---
@st.cache_resource
def get_db_and_engine():
    engine = create_engine(DATABASE_URL)
    db = SQLDatabase(engine)
    return db, engine

db, engine = get_db_and_engine()

@st.cache_resource
def setup_llm():
    return ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0)

llm = setup_llm()

# --- 3. Core Logic Functions ---
def polish_text_output(text: str) -> str:
    """Programmatically fixes common text formatting errors from the LLM."""
    if not text: return ""
    text = re.sub(r',([a-zA-Z])', r', \1', text)
    text = re.sub(r'\.([a-zA-Z])', r'. \1', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    return text

def run_orchestrated_analysis(user_question: str, db_object, db_engine) -> (pd.DataFrame, str):
    """This master function orchestrates the entire AI analysis process."""
    schema = db_object.get_table_info()
    planning_prompt = f"""
You are a world-class data analyst AI. Your task is to generate a JSON object with a plan.
USER QUESTION: "{user_question}"
DATABASE SCHEMA: <schema>{schema}</schema>
Follow this process:
1.  **Thought Process:** Think step-by-step.
2.  **SQL Query:** Write a SQL query. CRITICAL SQL RULE: When aggregating data over time, you MUST `SELECT` and `GROUP BY` all relevant time periods (like year and month).
3.  **Pandas Code:** If needed, write pandas code for final analysis on `df`. The result must be in `result_df`. If not needed, return an empty string.
Provide a JSON object with keys: "thought_process", "sql_query", "pandas_code".
"""
    try:
        response = llm.invoke(planning_prompt)
        plan_str = re.search(r"```json\n(.*?)\n```", response.content, re.DOTALL)
        plan_dict = json.loads(plan_str.group(1) if plan_str else response.content)
        sql_query = plan_dict.get("sql_query")
        pandas_code = plan_dict.get("pandas_code")
        thought_process = plan_dict.get("thought_process", "Analysis complete.")
        if not sql_query: return None, "The AI planner failed to generate a valid SQL query."

        with st.expander("Show AI's Execution Plan"):
            st.write(thought_process)
            st.code(sql_query, language="sql")
            if pandas_code: st.code(pandas_code, language="python")

        df = pd.read_sql_query(sql_query, db_engine)
        if pandas_code:
            exec_scope = {"df": df.copy(), "pd": pd}
            exec(pandas_code, exec_scope)
            final_df = exec_scope.get("result_df", exec_scope["df"])
        else:
            final_df = df
        if isinstance(final_df.index, pd.DatetimeIndex): final_df = final_df.reset_index()

        summary_prompt = f"""
You are a senior data analyst writing a final summary for a business report.
The user asked the following question: "{user_question}".
You have already performed the analysis, and the final data is in the following summary table:
{final_df.to_markdown()}

**YOUR TASK:**
Write an insightful, user-friendly summary of the findings based on the data.

**CRITICAL INSTRUCTIONS FOR YOUR RESPONSE:**
1.  **FORMAT:** You MUST write your entire response as a single, continuous paragraph of text. Do NOT use markdown lists, bullet points, or numbered lists (e.g., do not use '1.', '2.', or '-').
2.  **SPACING:** You MUST ensure there is a space after every single word, comma, and period. Check your output for "mergedwords". For example, an output like "sales were 100,and then..." is WRONG. The correct format is "sales were 100, and then...". An output like "thedata is..." is WRONG. The correct format is "the data is...".
3.  **CONTENT:** Explain what the data means. Do not just list the numbers from the table. Provide brief insights.

Begin the summary now.
"""
        unpolished_answer = llm.invoke(summary_prompt).content
        final_answer = polish_text_output(unpolished_answer)
        return final_df, final_answer
    except Exception as e:
        return None, f"An error occurred during analysis: {e}"

def polish_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares the final DataFrame for perfect visualization."""
    if df is None: return None
    df = df.copy()
    date_col = None
    if 'year' in df.columns and 'month' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
            df = df.sort_values(by='date').reset_index(drop=True)
            return df
        except Exception: pass
    for col in df.columns:
        if 'date' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                df = df.sort_values(by=col).reset_index(drop=True)
                return df
            except Exception: pass
    return df

def get_visualization_code(df: pd.DataFrame, user_question: str) -> str:
    """Generates beautiful, presentation-ready, and contextually appropriate Plotly code."""
    if df is None: return ""
    df_summary = f"The DataFrame has columns named {df.columns.to_list()} with data types {df.dtypes.to_dict()}."
    prompt = f"""
You are a data visualization expert specializing in Plotly Express. Your task is to write a single block of Python code to create the most appropriate chart for the user's question, using the provided DataFrame `df`.
USER QUESTION: "{user_question}"
DATAFRAME SUMMARY: {df_summary}
CHARTING GUIDELINES:
1.  **Analyze Intent & Data:** Understand the user's request.
2.  **Select Chart Type:** For trends over a continuous time series, use a **line chart (`px.line`)**. For comparing categories, use a **bar chart (`px.bar`)**.
3.  **Generate Code:** Add a descriptive title. Use the 'plotly_dark' theme. Label all axes clearly.
CRITICAL RULES:
- The code must be in a single block and use the DataFrame `df`. It MUST create a figure `fig`.
- You MUST use the exact column names from the DataFrame Summary.
- DO NOT include `import` statements or sample data.
"""
    try:
        response = llm.invoke(prompt)
        cleaned_code = re.search(r"```python\n(.*?)\n```", response.content, re.DOTALL)
        return cleaned_code.group(1).strip() if cleaned_code else response.content.strip()
    except Exception:
        return ""

# --- 4. Streamlit User Interface ---
user_question = st.text_input("Your Question:", placeholder="e.g., 'What is the 3 month rolling average for sales?'")

if st.button("Generate Insight"):
    if not user_question:
        st.warning("Please enter a question.")
    else:
        final_df, text_answer = run_orchestrated_analysis(user_question, db, engine)

        st.subheader("💡 Key Insights")
        if text_answer:
            st.markdown(text_answer)
            st.divider()
        
        if final_df is not None and not final_df.empty:
            polished_df = polish_dataframe_for_display(final_df)
            st.subheader("📊 Visualization & Data")
            if polished_df.shape[0] > 1:
                with st.spinner("Generating visualization..."):
                    viz_code = get_visualization_code(polished_df, user_question)
                if viz_code:
                    try:
                        exec_scope = {"df": polished_df, "pd": pd, "px": px}
                        exec(viz_code, exec_scope)
                        fig = exec_scope.get("fig")
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"An error occurred while rendering the visualization: {e}")
            else:
                st.info("A chart was not generated because the result is a single data point.")
            with st.expander("Show/Hide Data Table"):
                st.dataframe(polished_df)
        elif text_answer:
            st.info("The AI provided an answer, but no data table could be extracted.")
        else:
            st.error("The AI could not process your request.")