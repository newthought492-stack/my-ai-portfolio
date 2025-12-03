import pkgutil
import langchain.agents
import inspect

print(f"langchain.agents path: {langchain.agents.__path__}")

# Try to find AgentExecutor in submodules
def find_agent_executor():
    try:
        from langchain.agents import AgentExecutor
        print("Found in langchain.agents")
        return
    except ImportError:
        print("Not found in langchain.agents")

    try:
        from langchain.agents.agent import AgentExecutor
        print("Found in langchain.agents.agent")
        return
    except ImportError:
        print("Not found in langchain.agents.agent")
        
    try:
        from langchain.agents.executor import AgentExecutor
        print("Found in langchain.agents.executor")
        return
    except ImportError:
        print("Not found in langchain.agents.executor")

find_agent_executor()
