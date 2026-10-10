import os, re, time
import duckdb
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")

SCHEMA = """
Database: DuckDB. Currency: BRL (Brazilian reais).
Table gold.dim_customers(customer_id, customer_unique_id, customer_city, customer_state)
Table gold.fact_orders(order_id, customer_id, order_status, purchased_at TIMESTAMP,
  delivered_at TIMESTAMP, items_value DOUBLE, freight_value DOUBLE, paid_value DOUBLE)
Join: fact_orders.customer_id = dim_customers.customer_id
order_status values include: delivered, shipped, canceled, unavailable, invoiced, processing.
"""

BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|install|load|export|call|set)\b|read_",
    re.IGNORECASE,
)


def make_sql(question: str) -> str:
    prompt = (
        f"{SCHEMA}\nWrite ONE DuckDB SELECT query that answers the question. "
        "Use only the tables above. Return only the SQL, no explanation, no markdown.\n"
        f"Question: {question}"
    )
    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            break
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    sql = resp.text.strip()
    sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()
    return sql.rstrip(";").strip()


def is_safe(sql: str) -> bool:
    s = sql.lower().lstrip()
    return (
        (s.startswith("select") or s.startswith("with"))
        and ";" not in sql
        and not BLOCKED.search(sql)
    )


st.title("Ask the Olist data")
st.caption("Text-to-SQL over the gold layer. Read-only, gold tables only.")

question = st.text_input("Your question", placeholder="Top 5 states by revenue")

if st.button("Ask") and question:
    try:
        sql = make_sql(question)
        st.code(sql, language="sql")
        if not is_safe(sql):
            st.error("Blocked: only a single SELECT query is allowed.")
        else:
            con = duckdb.connect("data/gold_demo.duckdb", read_only=True)
            df = con.execute(f"SELECT * FROM ({sql}) LIMIT 200").df()
            st.dataframe(df)
    except Exception as e:
        st.error(f"Something went wrong: {e}")