import os
from rag_agent import RAGAgent
from rag_api_service import read_financial_data

def run_audit():
    pdf_path = "sample.pdf"
    
    if not os.path.exists(pdf_path):
        print("sample.pdf not found. Please run setup_data.py first.")
        return

    print("Initializing Audit Agent...")
    # Initialize agent with the financial tool
    tools = [read_financial_data]
    agent = RAGAgent(pdf_path, tools=tools)
    
    query = (
        "Perform a financial audit:\n"
        "1. Find the 'Budget Forecast for Q1' from the document.\n"
        "2. Retrieve the 'Actual Q1 Revenue' using the financial tool.\n"
        "3. Compare them and state if the company met its Q1 revenue target."
    )
    
    print(f"\nAudit Query:\n{query}\n")
    print("-" * 50)
    
    try:
        response = agent.run_query(query)
        print(f"Audit Result:\n{response}")
    except Exception as e:
        print(f"Audit Failed: {e}")
        print("\nNote: Ensure OPENAI_API_KEY is set in your environment.")

if __name__ == "__main__":
    run_audit()
