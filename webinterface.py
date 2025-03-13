import streamlit as st
from langgrapsupervisoragent import run_supervisor_workflow
import time
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="SilentCodingLegend",
    page_icon="🤖",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
    .stApp header {
        background-color: #0e1117;
    }
    .stMarkdown h1 {
        color: #4CAF50;
    }
    .stMarkdown h2 {
        color: #2196F3;
    }
    div[data-testid="stChatMessageContent"] {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Main title
st.title("🤖 SilentCodingLegend")

# Description
st.markdown("""
## A LangGraph Supervisor Agent

Silent Coding Legend is a specialized AI agent with expertise in:
- 💻 Python Development and Software Engineering
- 🛡️ Cybersecurity and Kali Linux
- 🔗 Blockchain, Web3, and Cryptocurrency

This advanced AI system coordinates a team of specialized agents:
- **Researcher**: For information gathering
- **Coder**: Expert at writing and debugging code
- **Analyst**: Specializes in data analysis and critical thinking

All advice follows strict ethical guidelines and focuses on constructive solutions.
""")

# Sidebar for settings and agent details
with st.sidebar:
    st.header("Settings")
    show_agents = st.checkbox("Show contributing agents", value=True)
    st.divider()
    
    st.header("Agent Details")
    with st.expander("Researcher"):
        st.write("Specializes in finding and synthesizing information.")
    
    with st.expander("Coder"):
        st.write("Expert at writing and debugging code.")
    
    with st.expander("Analyst"):
        st.write("Specializes in data analysis and critical thinking.")

# Add to sidebar
with st.sidebar:
    st.header("System Limits")
    max_conversation_length = st.slider("Max conversation length", 5, 50, 20)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "agents" in message and show_agents:
            st.caption(f"Contributing agents: {', '.join(message['agents'])}")

# Chat input
if prompt := st.chat_input("Ask something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🧠 Thinking...")
        
        # Create conversation history for context
        conversation_history = []
        for msg in st.session_state.messages[:-1]:  # Exclude the current message
            role_prefix = "User" if msg["role"] == "user" else "Assistant"
            conversation_history.append(f"{role_prefix}: {msg['content']}")
        
        # Prepare the full task with conversation history
        if conversation_history:
            full_context = "\n".join(conversation_history)
            task = f"Previous conversation:\n{full_context}\n\nCurrent request: {prompt}"
        else:
            task = prompt
        
        # Run the supervisor workflow
        try:
            result = run_supervisor_workflow(task)
            answer = result["final_answer"]
            
            # Get contributing agents
            contributing_agents = list(result["worker_results"].keys())
            
            # Display the response
            message_placeholder.markdown(answer)
            
            # Add response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer,
                "agents": contributing_agents
            })
            
            # Show contributing agents if enabled
            if show_agents and contributing_agents:
                st.caption(f"Contributing agents: {', '.join(contributing_agents)}")
                
        except Exception as e:
            message_placeholder.markdown(f"Sorry, I encountered an error: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Sorry, I encountered an error: {str(e)}",
                "agents": []
            })

# Run the Streamlit app with: streamlit run chat_interface.py