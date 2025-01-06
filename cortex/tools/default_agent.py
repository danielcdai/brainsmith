from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


def get_default_agent_graph(api_key: str = None, model: str = "gpt-4o", base_url: str = None):
    graph_builder = StateGraph(State)

    from langchain_openai import ChatOpenAI

    if base_url:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            base_url=base_url,
            model=model
        )
    else:
        llm = ChatOpenAI(api_key=api_key, model=model)


    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    graph = graph_builder.compile()
    return graph


if __name__ == "__main__":
    def stream_graph_updates(user_input: str):
        graph = get_default_agent_graph()
        for event in graph.stream({"messages": [("user", user_input)]}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)


    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break