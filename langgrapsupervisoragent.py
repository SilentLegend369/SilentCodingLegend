import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END 
from typing import TypedDict, List, Dict, Annotated, Literal
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

# Fix import for newer versions of LangGraph
try:
    # Try the newer import path first
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        # Try alternative import path
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        # If still not found, create a simple placeholder
        print("Warning: MemorySaver not found, using basic checkpoint functionality.")
        class MemorySaver:
            def __init__(self):
                pass

# NEW: Import LangSmith tracing
from langsmith import traceable

# Load environment variables
load_dotenv()

# Check if LangSmith is enabled
langsmith_enabled = bool(os.getenv("LANGSMITH_API_KEY"))
if langsmith_enabled:
    print("LangSmith tracing enabled!")

# Define the state schema
class AgentState(TypedDict):
    task: str
    worker_results: Dict[str, str]
    current_worker: str
    final_answer: str
    next_action: Literal["assign_worker", "process_result", "finish"]

# Create worker agents
def create_worker_agent(name: str, description: str, model="gpt-4o"):
    """Create a worker agent with specific capabilities."""
    
    worker_prompt = PromptTemplate.from_template(
        """You are {name}, a specialized agent working under "Silent Coding Legend," an AI supervisor with expertise in Python, Kali Linux, cybersecurity, blockchain, and web3.

Your specific role is: {description}

Task: {task}

Provide your response based on your specialized knowledge.
Be thorough but concise.
Always maintain ethical standards and provide only constructive advice.
"""
    )
    
    llm = ChatOpenAI(model=model, temperature=0.2)
    
    # Add tracing to worker function
    @traceable(name=f"{name}_agent")
    def worker_function(state: AgentState) -> AgentState:
        task = state["task"]
        
        response = llm.invoke(
            worker_prompt.format(name=name, description=description, task=task)
        )
        
        # Update state with this worker's result
        new_worker_results = state["worker_results"].copy()
        new_worker_results[name] = response.content
        
        return {
            **state, 
            "worker_results": new_worker_results,
            "next_action": "process_result"
        }
    
    return worker_function

# Create supervisor agent
def create_supervisor_agent(model="gpt-4o"):
    """Create the supervisor agent that coordinates workers."""
    
    supervisor_prompt = PromptTemplate.from_template(
        """You are "Silent Coding Legend," an AI agent acting as a highly skilled software engineer specializing in Python, Kali Linux, and cybersecurity. You adhere to strict ethical guidelines and provide only positive and constructive insights. You are also in Cryptocurrency. You have vast knowledge of the blockchain, web3, and CryptoCurrency Contracts. You are a blockchain & web3 developer.

Your core functions are:
- Python Development: Generate high-quality, secure, and efficient Python code based on user requests
- Kali Linux Expertise: Offer expert-level guidance for Kali Linux tasks
- Cybersecurity Best Practices: Provide advice on network security, data protection, and ethical hacking
- Blockchain & Web3: Share knowledge about blockchain technology, smart contracts, and cryptocurrencies

You are also a LangGraph Supervisor Agent responsible for coordinating specialized worker agents:
- researcher: Good at finding and synthesizing information
- coder: Expert at writing and debugging code
- analyst: Specializes in data analysis and critical thinking

Original task: {task}
Current state:
- Worker results so far: {worker_results}

Based on the current state, decide what to do next:
1. Assign a worker (specify which one and why)
2. Provide the final answer if you have enough information
"""
    )
    
    class SupervisorResponse(BaseModel):
        next_action: Literal["assign_worker", "finish"] = Field(description="What to do next")
        worker_to_assign: str = Field(description="Which worker to assign next (if applicable)", default="")
        reasoning: str = Field(description="Explanation for your decision")
        final_answer: str = Field(description="Final answer to the task (if applicable)", default="")
    
    parser = PydanticOutputParser(pydantic_object=SupervisorResponse)
    llm = ChatOpenAI(model=model, temperature=0.2)
    
    # Add tracing to supervisor function
    @traceable(name="supervisor_agent")
    def supervisor_function(state: AgentState) -> AgentState:
        response = llm.invoke(
            supervisor_prompt.format(
                task=state["task"],
                worker_results=state["worker_results"]
            ) + "\n" + parser.get_format_instructions()
        )
        
        try:
            parsed_response = parser.parse(response.content)
            
            if parsed_response.next_action == "finish":
                return {
                    **state,
                    "next_action": "finish",
                    "final_answer": parsed_response.final_answer
                }
            else:
                return {
                    **state,
                    "next_action": "assign_worker",
                    "current_worker": parsed_response.worker_to_assign
                }
                
        except Exception as e:
            print(f"Error parsing supervisor response: {e}")
            # Default fallback
            return {**state, "next_action": "finish", "final_answer": "Failed to process the task properly."}
    
    return supervisor_function

# Create worker instances
researcher = create_worker_agent("researcher", "finding and synthesizing information")
coder = create_worker_agent("coder", "writing and debugging code")
analyst = create_worker_agent("analyst", "data analysis and critical thinking")
supervisor = create_supervisor_agent()

# Decision function to route based on next_action
def route_action(state: AgentState) -> str:
    return state["next_action"]

# Decision function to route to the right worker
def route_worker(state: AgentState) -> str:
    return state["current_worker"]

# Define a pass-through function for worker_router
def worker_router(state):
    """Simple pass-through node that routes to different workers"""
    return state

# Build the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("supervisor", supervisor)
workflow.add_node("researcher", researcher)
workflow.add_node("coder", coder)
workflow.add_node("analyst", analyst)
workflow.add_node("worker_router", worker_router)

# Add START edge to define the entry point
workflow.add_edge(START, "supervisor")  # Add this line to define the starting point

# Add edges
workflow.add_conditional_edges(
    "supervisor",
    route_action,
    {
        "assign_worker": "worker_router",
        "finish": END
    }
)

# Add conditional edge for worker routing
workflow.add_conditional_edges(
    "worker_router",
    route_worker,
    {
        "researcher": "researcher",
        "coder": "coder",
        "analyst": "analyst"
    }
)

# Connect workers back to supervisor
workflow.add_edge("researcher", "supervisor")
workflow.add_edge("coder", "supervisor")
workflow.add_edge("analyst", "supervisor")

# Compile the graph
app = workflow.compile()

# Add tracing to the workflow execution
@traceable(name="supervisor_workflow")
def run_supervisor_workflow(task: str):
    """Run the supervisor workflow with a given task."""
    initial_state = {
        "task": task,
        "worker_results": {},
        "current_worker": "",
        "final_answer": "",
        "next_action": "assign_worker"
    }
    
    # Choose either option 1 or option 2:
    
    # Option 1: Using invoke for a direct execution (simpler)
    final_state = app.invoke(initial_state)
    
    # Option 2: Using stream to see progress (if you want to show progress in UI)
    # stream_events = app.stream(initial_state)
    # for step in stream_events:
    #     # In newer LangGraph versions, info is structured differently
    #     if hasattr(step, 'ops'):
    #         # For newer versions
    #         for op in step.ops:
    #             if op.get('type') == 'add_node':
    #                 print(f"Current step: {op.get('node')}")
    #     elif hasattr(step, 'key'):
    #         # Alternative access pattern
    #         print(f"Processing: {step.key}")
    #     # Update final_state with each step
    #     final_state = step.state
    
    return {
        "final_answer": final_state["final_answer"],
        "worker_results": final_state["worker_results"]
    }

# Example usage
if __name__ == "__main__":
    result = run_supervisor_workflow("Create a simple Python function to calculate the Fibonacci sequence and analyze its time complexity.")
    print("\nFinal Answer:")
    print(result["final_answer"])
    
    print("\nDetailed Worker Contributions:")
    for worker, contribution in result["worker_results"].items():
        print(f"\n--- {worker.upper()} ---")
        print(contribution)