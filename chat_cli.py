import os
from dotenv import load_dotenv
from langgrapsupervisoragent import run_supervisor_workflow
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

load_dotenv()

def main():
    """Command-line chat interface for Silent Coding Legend."""
    print(f"{Fore.GREEN}🤖 Welcome to Silent Coding Legend!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}A LangGraph Supervisor Agent specializing in:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}💻 Python Development and Software Engineering{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🛡️ Cybersecurity and Kali Linux{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🔗 Blockchain, Web3, and Cryptocurrency{Style.RESET_ALL}")
    print("\nType 'exit' or 'quit' to end the conversation.")
    print("---------------------------------------")
    
    conversation_history = []
    
    while True:
        user_input = input(f"\n{Fore.YELLOW}You:{Style.RESET_ALL} ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print(f"\n{Fore.GREEN}Silent Coding Legend:{Style.RESET_ALL} Goodbye! Feel free to return if you need more assistance.")
            break
        
        # Add user input to history
        conversation_history.append(f"User: {user_input}")
        
        # Create a task that includes conversation history for context
        if len(conversation_history) > 1:
            full_context = "\n".join(conversation_history[:-1])
            task = f"Previous conversation:\n{full_context}\n\nCurrent request: {user_input}"
        else:
            task = user_input
        
        print(f"\n{Fore.GREEN}Silent Coding Legend is thinking...{Style.RESET_ALL}")
        
        # Run the supervisor workflow
        try:
            result = run_supervisor_workflow(task)
            answer = result["final_answer"]
            
            # Print the answer
            print(f"\n{Fore.GREEN}Silent Coding Legend:{Style.RESET_ALL} {answer}")
            
            # Add AI response to history
            conversation_history.append(f"Silent Coding Legend: {answer}")
            
            # Show details of which agents contributed
            if result["worker_results"]:
                print(f"\n{Fore.BLUE}(Specialists that contributed:{Style.RESET_ALL}")
                for worker in result["worker_results"].keys():
                    print(f"{Fore.BLUE} - {worker}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}){Style.RESET_ALL}")
        
        except Exception as e:
            print(f"\n{Fore.RED}Silent Coding Legend: Sorry, I encountered an error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()