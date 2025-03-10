import re
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage


def parse_history_file(file_path: str) -> list[BaseMessage]:
    """Parse the history.md file into a list of message objects."""
    with open(file_path, 'r') as file:
        content = file.read()

    messages = []

    # 支持 "Human:" 和 "H:" 兩種格式
    sections = re.split(r'\n\n(?=System:|Human:|AI:|H:)', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if section.startswith("System:"):
            system_content = section[7:].strip()
            if system_content:
                messages.append(SystemMessage(content=system_content))

        elif section.startswith("Human:") or section.startswith("H:"):
            if section.startswith("Human:"):
                human_content = section[6:].strip()
            else:  # H:
                human_content = section[2:].strip()

            if human_content:
                messages.append(HumanMessage(content=human_content))

        elif section.startswith("AI:"):
            ai_content = section[3:].strip()
            if ai_content:
                messages.append(AIMessage(content=ai_content))

    return messages
