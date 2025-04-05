from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_gigachat import GigaChat
from langgraph.graph import StateGraph, MessagesState
from langchain.tools import BaseTool
from langgraph.constants import START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

from prompts import sys_prompt
from utils import print_messages

from pydantic.v1 import Field

load_dotenv()

class LangGraphAgent:
    def __init__(self):
        self.llm = GigaChat(
            credentials=os.getenv("GIGACHAT_API_KEY"),
            scope="GIGACHAT_API_PERS",
            model="GigaChat-Pro",
            verify_ssl_certs=False,
            profanity_check=False,
            temperature=0.1
        )

        self.tools = [TavilySearchResults(max_results=5,
                                          description="Используй этот инструмент когда нужно найти что-то в интернете",
                                          tavily_api_key=os.getenv("TAVILY_API_KEY"))]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        class State(MessagesState):
            is_reasoning: bool

        self.State = State

        self.builder = StateGraph(State)
        self.builder.add_node('assistant', self.assistant)
        self.builder.add_node('tools', ToolNode(self.tools))
        self.builder.add_edge(START, 'assistant')
        self.builder.add_conditional_edges('assistant', tools_condition)
        self.builder.add_edge('tools', 'assistant')
        self.memory = MemorySaver()
        self.graph = self.builder.compile(checkpointer = self.memory)

    def assistant(self, state):
        return {
            "messages": [
                self.llm_with_tools.invoke([SystemMessage(content=sys_prompt)] + state['messages'])
            ],
            "is_reasoning": False
        }

class AgentAPI:
    def __init__(self, agent: LangGraphAgent):
        self.agent = agent
        self.app = FastAPI()

        class Query(BaseModel):
            message: str
            thread_id: str

        @self.app.post("/query")
        def query_endpoint(query: Query):
            state = self.agent.State(messages=[HumanMessage(content=query.message)], is_reasoning=False)

            try:
                result = self.agent.graph.invoke(state, {"configurable": {"thread_id": query.thread_id}})
                if 'messages' in result:
                    response = result['messages'][-1].content
                    return {"response": response}
                else:
                    raise HTTPException(status_code=500, detail="Ошибка обработки запроса")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))



agent = LangGraphAgent()
api = AgentAPI(agent)

# Запуск приложения
if __name__ == "__main__":
    m = HumanMessage(f'Куда стоит поехать этим летом?')




    for step in agent.graph.stream({"messages": m}, {"configurable": {"thread_id": 1}}):
        print(step.keys())

        # print("Результат шага:", step)

        print_messages(list(step.values())[0]['messages'])

        print("\n\n################################################################")

    print()


