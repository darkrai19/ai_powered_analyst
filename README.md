---

# 🧠 From Raw Data to AI-Powered Insights: Building a Full-Stack Analytics App

Welcome! This project is the result of an exciting (and at times wild) ride into building a **fully end-to-end AI data analyst**—one that turns plain English into live data insights and beautiful charts, no SQL needed.

> **Imagine:** Anyone on your team asking “What were our top-selling products this quarter?”  
> — and instantly getting back a human-friendly summary *and* a visualized chart.

---

## 🔧 Tech Stack

| Layer         | Tools & Libraries                             |
|--------------|------------------------------------------------|
| **Backend**  | Python, PostgreSQL, Star Schema Modeling       |
| **AI/ML**    | LangChain, OpenAI (GPT-4o)                     |
| **Frontend** | Streamlit                                      |
| **Infra**    | AWS EC2                                        |

---

## 🧱 Laying the Groundwork: Data Engineering First

Before AI could answer questions, the data needed to be structured and accessible:

- **Data Modeling**  
  Designed a star schema with one central fact table (`fct_order_line_items`) and supporting dimension tables (`dim_date`, `dim_product`, etc.) for efficient analytical queries.

- **Data Preparation (ETL)**  
  Cleaned and transformed raw source data, then loaded it into a PostgreSQL database ready for AI-driven exploration.

---

## 🧠 AI That Plans Before It Answers

At first, I used LangChain’s `create_sql_agent`, but complex queries like “3-month rolling sales average” quickly overwhelmed it. So I built a custom **AI Orchestrator**—more than just an agent, it’s a smart planner.

Here’s what happens when you ask it a question:

1. **Schema Discovery**  
   It inspects the live PostgreSQL schema to understand available data.

2. **Intelligent Planning**  
   It decides whether to use SQL directly or pull raw data for in-depth Python analysis with pandas.

3. **Insight Generation**  
   It runs the queries and summarizes the insights in plain language.

4. **Charting**  
   Based on the result type, it picks the right visualization (bar for categories, line for trends, etc.) and builds it using Plotly.

---

## 🤯 The Schema Overload Challenge

One unique challenge: the AI would hit token limits parsing the schema. The fix?  
A second AI acting as a **Schema Summarizer**, generating a slimmed-down “cheat sheet” for the main AI to reference—significantly boosting performance and reliability.

---

## 💡 Lessons & Takeaways

This project brought together:

- Robust data modeling and engineering
- Advanced prompt orchestration and planning
- Dynamic, conversational UI with powerful insights

It’s been one of the most rewarding builds I’ve tackled—proving how modern AI tools can unlock new ways to explore data.

---

## ❓Want to Try It?

What would *you* ask it about your data?

---
