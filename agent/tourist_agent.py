import operator
from typing import Annotated, List, Literal, TypedDict, Dict, Union

# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
import json

from langchain.chains.combine_documents.reduce import (
    acollapse_docs,
    split_list_of_docs,
)
from langchain_core.documents import Document
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langchain_gigachat import GigaChat
import os
from dotenv import load_dotenv
from pydantic import ValidationError
import asyncio

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from langchain_gigachat import GigaChat, GigaChatEmbeddings
from langchain_core.tools import tool

import os
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from prompts import sys_prompt, output_format

load_dotenv()

class State(MessagesState):
    is_reasoning: bool


llm = GigaChat(credentials=os.getenv("GIGACHAT_API_KEY"),
                   scope="GIGACHAT_API_PERS",
                   model="GigaChat-Pro",
                       verify_ssl_certs=False,
                 profanity_check=False,
                 temperature=0.1)

# =============== RAG Set UP [Start] ====================


# =============== TOOLS [Start] ====================
class TavilyInput(BaseModel):
    """Поисковый запрос"""
    query: str = Field(description="Текст поискового запроса")

tool = TavilySearchResults(
    max_results=5,
    args_schema=TavilyInput
)
tools = [tool]

llm_with_tools = llm.bind_tools(tools)


# =============== NODES [Start] ====================



def assistant(state: State):
    # last_mess = state["messages"][-1]
    # state["messages"][-1] = HumanMessage(last_mess.content+output_format)
    return {"messages": [llm_with_tools.invoke([SystemMessage(sys_prompt)] + state['messages'])], "is_reasoning": False}




builder = StateGraph(State)

builder.add_node('assistant', assistant)
builder.add_node('tools', ToolNode(tools))

builder.add_edge(START, 'assistant')
builder.add_conditional_edges('assistant', tools_condition)
builder.add_edge('tools', 'assistant')

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


# if __name__ == "__main__":
#     async def main():
#         # Переинициализируем глобальный семафор в рамках текущего цикла событий
#         global semaphore
#         semaphore = asyncio.Semaphore(1)
#
#         split_docs = pd.read_excel("../daily_industry.xlsx")
#         print(split_docs)
#         texts = [f"{tit}\n{date}\n{text}" for tit, text, date in zip(
#             split_docs["news_title"].tolist(),
#             split_docs["news_text"].tolist(),
#             split_docs["news_date"].tolist()
#         )]
#         print(texts)
#         print(len(texts))
#         async for step in app.astream(
#                 {"contents": texts},
#                 {"recursion_limit": 5},
#         ):
#             print(step.keys())
#
#             print("Результат шага:", step)
#             if 'report_make' in step:
#                 print("DONE")
#                 print(step['report_make']['report'])
#             print("\n\n#####################")
#
#
#
#
#
#     asyncio.run(main())

