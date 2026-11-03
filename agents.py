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
    Cite the numbered sources inline like [1], [2]. Only state facts supported by
    the research above. Do not write a Sources section; it is appended separately.
    Be detailed, factual and professional."""),
])

revision_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer revising a report based on editor feedback."),
    ("human", """Revise the report below to address every point under "Areas to Improve".
    Topic: {topic}
    Research Gathered:
    {research}
    Current Report:
    {report}
    Critic Feedback:
    {feedback}
    Keep the same structure (Introduction, Key Findings, Conclusion), keep inline [n]
    citations, and do not write a Sources section. Return only the revised report."""),
])

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
    It is a synthesis of web sources, not original research: do not penalize the
    absence of new experiments or a methodology section. Judge accuracy against its
    citations, depth, clarity, balance, and whether claims are supported.
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
revision_chain = _LazyRunnable(revision_prompt)
critic_chain = _LazyRunnable(critic_prompt)