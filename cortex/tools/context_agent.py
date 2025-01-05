from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

from cortex.config import settings


def get_context_agent_graph(embedding_name: str, api_key: str = None, model: str = "gpt-4o"):
    def _contextual_user_input(original_user_input):
        import requests
        import json

        url = "http://localhost:8000/search"

        payload = json.dumps({
            "name": embedding_name,
            "query": original_user_input,
            # TODO: Make the top k configurable
            "top_k": 3,
            "search_type": "similarity",
            "content_only": True
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        try:
            response.raise_for_status()
            content_list = response.json()
            combined_context = ", ".join([f"context {i+1}: {item}" for i, item in enumerate(content_list)])
            # rag_prompt = f"""Answer the following question based on the given context.
            # ---
            # Context: {combined_context}
            # ---
            # Question: {original_user_input}
            # ---
            # Answer: """
            return combined_context
        except Exception as err:
            print(err)
        return None


    @tool
    def get_similar_context(user_input: str):
        """Call to get the similar context related to the user input."""
        return _contextual_user_input(user_input)

    tools = [get_similar_context]
    context_node = ToolNode(tools)

    llm = ChatOpenAI(api_key=api_key, model=model).bind_tools(tools)

    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "similarity search"
        return END

    def call_model(state: MessagesState):
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    graph_builder = StateGraph(MessagesState)


    # The first argument is the unique node name
    # The second argument is the function or object that will be called whenever
    # the node is used.
    graph_builder.add_node("agent", call_model)
    graph_builder.add_node("similarity search", context_node)
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", should_continue, ["similarity search", END])
    graph_builder.add_edge("similarity search", "agent")
    graph = graph_builder.compile()
    return graph


if __name__ == "__main__":
    from IPython.display import Image

    try:
        graph = get_context_agent_graph("paul")
        image = Image(graph.get_graph().draw_mermaid_png())
        with open("logs/tool_graph.png", "wb") as f:
            f.write(image.data)
        print("Graph saved as graph.png")
    except Exception as e:
        print(f"An error occurred: {e}")

    messages_list = []

    from typing import Literal
    def stream_graph_updates(user_input: str, mode: Literal["values", "messages"] = "values"):
        messages_list.append({"role": "user", "content": user_input})
        if mode == "messages":
            ai_answer = ""
        print("AI Assistant: ", end='', flush=True)
        for chunk in graph.stream(
            {"messages": messages_list}, stream_mode=mode
        ):
            match mode:
                case "values":
                    if len(chunk["messages"]) % 2 == 0:
                        print(chunk["messages"][-1].content, end='\n', flush=True)
                        messages_list.append({"role": "assistant", "content": chunk["messages"][-1].content})
                case "messages":
                    from langchain_core.messages import AIMessageChunk
                    if len(chunk) % 2 == 0:
                        if isinstance(chunk, tuple) and len(chunk) > 0 and type(chunk[0]) == AIMessageChunk:
                            content = chunk[0].content
                            ai_answer += content
                            print(content, end='', flush=True)
                        messages_list.append({"role": "assistant", "content": ai_answer})
            # Debug only
            # print(chunk)


    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input, "messages")