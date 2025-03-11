from ..models.llm_config import summary_llm
from ..prompts.summary_prompt import summarize_prompt


summary_chain = summarize_prompt | summary_llm
