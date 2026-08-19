from agent.prompts import sub_agents_content
from agent.tools.rag_tools import rag_search

rag_query_agent={
    "name": sub_agents_content['rag']['name'],
    "description": sub_agents_content['rag']['description'],
    "system_prompt": sub_agents_content['rag']['system_prompt'],
    "tools": [rag_search]
}