# # from langchain.agents import create_react_agent, AgentExecutor
# # from langchain import hub
# # from langchain_openai import ChatOpenAI
# # from langchain_core.prompts import ChatPromptTemplate
# # from langchain_core.output_parsers import StrOutputParser
# # from tools import web_search, scrape_url
# # import os
# # from dotenv import load_dotenv
# # load_dotenv()

# # # Lazily construct an LLM client so importing this module doesn't require
# # # credentials or optional packages to be present.
# # def get_llm():
# #     try:
       
# #         from langchain_google_genai import ChatGoogleGenerativeAI
# #         return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
# #     except Exception:
# #         try:
# #             return ChatOpenAI(temperature=0)
# #         except Exception as e:
# #             raise RuntimeError(
# #                 "No LLM available: install langchain-groq or set OPENAI_API_KEY"
# #             ) from e


# # def build_search_agent():
# #     prompt = hub.pull("hwchase17/react")
# #     agent = create_react_agent(llm=get_llm(), tools=[web_search], prompt=prompt)
# #     return AgentExecutor(agent=agent, tools=[web_search], verbose=True, handle_parsing_errors=True)

# # def build_reader_agent():
# #     prompt = hub.pull("hwchase17/react")
# #     agent = create_react_agent(llm=get_llm(), tools=[scrape_url], prompt=prompt)
# #     return AgentExecutor(agent=agent, tools=[scrape_url], verbose=True, handle_parsing_errors=True)

# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# # from tools import web_search, scrape_url
# import os
# from dotenv import load_dotenv
# load_dotenv()

# # def get_llm():
# #     from langchain_google_genai import ChatGoogleGenerativeAI
# #     return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# # def build_search_agent():
# #     llm = get_llm()
# #     return llm.bind_tools([web_search])




# #LCEL pipeline for writer chain
# writer_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
#     ("human", """Write a detailed research report on the topic below.
#     Topic: {topic}
#     Research Gathered:
#     {research}
#     Structure the report as:
#     - Introduction
#     - Key Findings (minimum 3 well-explained points)
#     - Conclusion
#     - Sources (list all URLs found in the research)
#     Be detailed, factual and professional."""),
# ])


# class _LazyRunnable:
#     def __init__(self, prompt_template):
#         self.prompt_template = prompt_template
#         self._chain = None

#     def _init_chain(self):
#         if self._chain is None:
#             self._chain = self.prompt_template | get_llm() | StrOutputParser()

#     def invoke(self, inputs: dict):
#         self._init_chain()
#         return self._chain.invoke(inputs)


# writer_chain = _LazyRunnable(writer_prompt)

# # critic_chain

# critic_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
#     ("human", """Review the research report below and evaluate it strictly.
#     Report:
#         {report}

#         Respond in this exact format:

#         Score: X/10

#         Strengths:
#         - ...
#         - ...

#         Areas to Improve:
#         - ...
#         - ...

#         One line verdict:
#         ..."""),
# ])

# critic_chain = _LazyRunnable(critic_prompt)


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent
from tools import web_search, scrape_url
import os
from dotenv import load_dotenv
load_dotenv()

def get_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def build_search_agent():
    llm = get_llm()
    # Create an agent using langgraph
    agent = create_react_agent(llm, tools=[web_search], prompt="You are an expert search agent. Use the web_search tool to find the required information and summarize the URLs and snippets clearly.")
    return agent

def build_reader_agent():
    llm = get_llm()
    # Create an agent using langgraph
    agent = create_react_agent(llm, tools=[scrape_url], prompt="You are an expert reader and scraper. Use the scrape_url tool based on the specific URL provided, and return the relevant content found within it.")
    return agent

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.
    Topic: {topic}
    Research Gathered:
    {research}
    Structure the report as:
    - Introduction
    - Key Findings (minimum 3 well-explained points)
    - Conclusion
    - Sources (list all URLs found in the research)
    Be detailed, factual and professional."""),
])

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
    Report:
        {report}

        Respond in this exact format:

        Score: X/10

        Strengths:
        - ...
        - ...

        Areas to Improve:
        - ...
        - ...

        One line verdict:
        ..."""),
])

class _LazyRunnable:
    def __init__(self, prompt_template):
        self.prompt_template = prompt_template
        self._chain = None

    def _init_chain(self):
        if self._chain is None:
            self._chain = self.prompt_template | get_llm() | StrOutputParser()

    def invoke(self, inputs: dict):
        self._init_chain()
        return self._chain.invoke(inputs)

writer_chain = _LazyRunnable(writer_prompt)
critic_chain = _LazyRunnable(critic_prompt)