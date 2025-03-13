from langchain_anthropic import ChatAnthropic


slow_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",  # type: ignore
    temperature=0,
    max_tokens=8096,  # type: ignore
    timeout=None,
    max_retries=2,
)  # type: ignore

fast_llm = ChatAnthropic(
    model="claude-3-5-haiku-latest",  # type: ignore
    temperature=0,
    max_tokens=8096,  # type: ignore
    timeout=None,
    max_retries=2,
)  # type: ignore
