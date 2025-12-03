import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.retriever import create_retriever_tool

# ... (imports remain the same)

class RAGAgent:
    def __init__(self, pdf_path, tools=None, persist_directory="./chroma_db"):
        """
        Initializes the RAG Agent by loading the PDF, creating embeddings, and building the vector store.
        It then sets up an agent capable of using the provided tools plus a PDF retriever tool.
        
        Args:
            pdf_path (str): Path to the PDF file.
            tools (list, optional): List of additional tools (LangChain Tool objects) the agent can use.
            persist_directory (str, optional): Directory to save/load the vector store. Defaults to "./chroma_db".
        """
        self.pdf_path = pdf_path
        self.tools = tools or []
        self.persist_directory = persist_directory
        self.agent_executor = None
        
        if not os.path.exists(pdf_path) and (not os.path.exists(persist_directory) or not os.listdir(persist_directory)):
             # Only error if PDF is missing AND DB is missing/empty
            print(f"Error: PDF file not found at {pdf_path} and no existing DB found.")
            return

        self._initialize_agent()

    def _initialize_agent(self):
        # Note: Requires OPENAI_API_KEY environment variable to be set.
        print("Creating embeddings...")
        embeddings = OpenAIEmbeddings()
        
        vectorstore = None
        
        # Check if persistent DB exists and is not empty
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            print(f"Loading existing vectorstore from {self.persist_directory}...")
            vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=embeddings)
        else:
            print(f"Loading {self.pdf_path}...")
            if not os.path.exists(self.pdf_path):
                 raise FileNotFoundError(f"PDF not found at {self.pdf_path} and no DB exists.")
                 
            loader = PyPDFLoader(self.pdf_path)
            documents = loader.load()
            
            print("Splitting text...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_documents(documents)
            
            print(f"Creating and persisting vectorstore to {self.persist_directory}...")
            vectorstore = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=self.persist_directory)
            # Chroma automatically persists on write usually, but older versions might need .persist()
            # Modern langchain-chroma / chromadb handles it. 
        
        # Create a retriever tool
        
        # Create a retriever tool
        retriever_tool = create_retriever_tool(
            vectorstore.as_retriever(),
            "pdf_retriever",
            "Searches and returns documents regarding the content of the PDF file."
        )
        
        # Combine tools
        all_tools = [retriever_tool] + self.tools
        
        print("Initializing Agent...")
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Initialize the agent
        agent = create_openai_functions_agent(llm, all_tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

    def run_query(self, query):
        """
        Retrieves an answer for the given query using the initialized Agent.
        
        Args:
            query (str): The question to ask.
            
        Returns:
            str: The answer from the agent.
        """
        if not self.agent_executor:
            return "Agent not initialized successfully (check PDF path or API keys)."
        
        print(f"Querying: {query}")
        response = self.agent_executor.invoke({"input": query})
        return response["output"]

if __name__ == "__main__":
    # Example usage
    # Ensure you have set your OPENAI_API_KEY env variable before running.
    # os.environ["OPENAI_API_KEY"] = "sk-..."
    
    sample_pdf = "sample.pdf"
    sample_query = "What is the main topic of this document?"
    
    # Create a dummy PDF for demonstration if it doesn't exist? 
    # For now, we just check if it exists to avoid crashing.
    if os.path.exists(sample_pdf):
        agent = RAGAgent(sample_pdf)
        answer = agent.run_query(sample_query)
        print(f"\nAnswer: {answer}")
    else:
        print(f"Please place a '{sample_pdf}' in this directory to test.")
