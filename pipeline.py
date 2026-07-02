# from agents import build_reader_agent, build_search_agent,writer_chain , critic_chain

# def research_pipeline(topic:str)->dict:
#     state={}

#     #search agent working
#     print("\n" +"="*50 )

#     search_agent = build_search_agent()
#     search_result = search_agent.invoke({
#         "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}")]
#     })
#     state["search_results"] = search_result['messages'][-1].content

#     print("\n search result ",state['search_results'])

#     #reader agent working
#     print("\n"+" ="*50)
  

#     reader_agent = build_reader_agent()
#     reader_result = reader_agent.invoke({
#         "messages": [("user",
#             f"Based on the following search results about '{topic}', "
#             f"pick the most relevant URL and scrape it for deeper content.\n\n"
#             f"Search Results:\n{state['search_results'][:800]}"
#         )]
#     })

#     state['scraped_content'] = reader_result['messages'][-1].content

#     print("\nscraped content: \n", state['scraped_content'])

#     #writer chain
#     print("\n"+" ="*50)
    

#     research_combined = (
#         f"SEARCH RESULTS : \n {state['search_results']} \n\n"
#         f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
#     )

#     state["report"] = writer_chain.invoke({
#         "topic" : topic,
#         "research" : research_combined
#     })

#     print("\n Final Report\n",state['report'])

#     #critic chain
#     print("\n"+" ="*50)
    

#     state["feedback"] = critic_chain.invoke({
#         "report":state['report']
#     })

#     print("\n critic report \n", state['feedback'])

#     return state



# if __name__ == "__main__":
#     topic = input("\n Enter a research topic : ")
#     research_pipeline(topic)

from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain


def _content_to_str(content) -> str:
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)


def research_pipeline(topic: str) -> dict:
    state = {}

    # Search
    search_agent = build_search_agent()
    # langgraph create_react_agent uses "messages"
    search_result = search_agent.invoke(
        {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]}
    )
    state["search_results"] = _content_to_str(search_result["messages"][-1].content)

    # Reader
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke(
        {"messages": [("user", f"Scrape the most relevant URL from these search results about '{topic}':\n\n{state['search_results'][:800]}")]}
    )
    state["scraped_content"] = _content_to_str(reader_result["messages"][-1].content)

    # Writer
    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"SCRAPED CONTENT:\n{state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })

    # Critic
    state["feedback"] = critic_chain.invoke({"report": state["report"]})

    return state

if __name__ == "__main__":
    topic = input("Enter a research topic: ")
    research_pipeline(topic)