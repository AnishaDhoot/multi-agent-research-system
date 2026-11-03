from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from settings import LLM_MODEL, LLM_PROVIDER

DEFAULT_MODELS = {"gemini": "gemini-2.5-flash", "groq": "openai/gpt-oss-120b"}


def get_llm():
    """Chat model for the provider chosen by LLM_PROVIDER (gemini or groq); LLM_MODEL overrides the default."""
    provider = LLM_PROVIDER
    model = LLM_MODEL or DEFAULT_MODELS.get(provider)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # The client retries 429/5xx itself (HttpRetryOptions); a timeout stops a hung call blocking a run.
        return ChatGoogleGenerativeAI(model=model, temperature=0, max_retries=3, timeout=90)
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0, max_retries=3, timeout=90)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}; use 'gemini' or 'groq'")


def structured_llm(schema):
    """get_llm() constrained to return `schema`. Groq models only support JSON-schema mode reliably."""
    llm = get_llm()
    if LLM_PROVIDER == "groq":
        return llm.with_structured_output(schema, method="json_schema")
    return llm.with_structured_output(schema)


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
        {report}"""),
])


class CriticReview(BaseModel):
    score: float = Field(ge=0, le=10, description="Overall quality from 0 to 10")
    strengths: list[str] = Field(description="Specific strengths")
    improvements: list[str] = Field(description="Specific, actionable areas to improve")
    verdict: str = Field(description="One-line verdict")

    def format(self) -> str:
        """Human-readable feedback, also fed back to the writer on revision."""
        bullets = lambda items: "\n".join(f"- {i}" for i in items)
        return (
            f"Score: {self.score:g}/10\n\nStrengths:\n{bullets(self.strengths)}\n\n"
            f"Areas to Improve:\n{bullets(self.improvements)}\n\nOne line verdict:\n{self.verdict}"
        )


class ResearchPlan(BaseModel):
    questions: list[str] = Field(description="3 to 4 distinct, self-contained web search queries")


planner_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research planner. You break a topic into focused web search queries."),
    ("human", """Break the topic below into 3 to 4 distinct search queries that together give broad,
    balanced coverage (e.g. fundamentals, current state/recent developments, challenges or criticism,
    and data/numbers). Each query must make sense on its own and be suitable for a web search engine.
    Topic: {topic}"""),
])


def plan_topic(topic: str) -> list[str]:
    """Return sub-questions for the topic. Falls back to the topic itself if planning fails."""
    try:
        plan = (planner_prompt | structured_llm(ResearchPlan)).invoke({"topic": topic})
        questions = [q.strip() for q in plan.questions if q.strip()]
    except Exception:
        questions = []
    return questions[:4] or [topic]


class _LazyRunnable:
    def __init__(self, prompt_template, schema=None):
        self.prompt_template = prompt_template
        self.schema = schema
        self._chain = None

    def _init_chain(self):
        if self._chain is None:
            if self.schema:
                self._chain = self.prompt_template | structured_llm(self.schema)
            else:
                self._chain = self.prompt_template | get_llm() | StrOutputParser()

    def invoke(self, inputs: dict):
        self._init_chain()
        return self._chain.invoke(inputs)

writer_chain = _LazyRunnable(writer_prompt)
revision_chain = _LazyRunnable(revision_prompt)
critic_chain = _LazyRunnable(critic_prompt, schema=CriticReview)