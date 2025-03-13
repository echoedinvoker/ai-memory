from ..prompts.summary_prompt import summarize_prompt
from ..models.llm_config import fast_llm, slow_llm


summary_chain = summarize_prompt | slow_llm
