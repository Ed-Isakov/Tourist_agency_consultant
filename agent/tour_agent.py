import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic.v1 import Field
from langchain_gigachat import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.constants import START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.tools.tavily_search import TavilySearchResults

from prompts import sys_prompt
from utils import print_messages

load_dotenv()


class LangGraphAgent:
    """
    Agent that compiles a LangGraph state graph with GigaChat LLM and external tools.

    Attributes:
    -----------
    llm : GigaChat
        Language model client instance.
    tools : List[BaseTool]
        List of bound tool instances for retrieval and search.
    llm_with_tools : object
        LLM instance bound with tool invocation capabilities.
    State : subclass of MessagesState
        Custom state schema for the graph nodes.
    builder : StateGraph
        Graph builder for constructing the conversational flow.
    memory : MemorySaver
        Checkpointer for persisting graph state.
    graph : Compiled graph instance
        Executable state graph for processing messages.
    """

    def __init__(self):
        """
        Initialize LangGraphAgent, bind tools, and compile the state graph.

        Environment variables:
        ----------------------
        GIGACHAT_API_KEY : str
            API key for GigaChat.
        TAVILY_API_KEY : str
            Api key for TavilySearchResults tool.
        """
        # Initialize GigaChat LLM
        self.llm = GigaChat(
            credentials=os.getenv("GIGACHAT_API_KEY"),
            scope="GIGACHAT_API_PERS",
            model="GigaChat-Pro",
            verify_ssl_certs=False,
            profanity_check=False,
            temperature=0.3
        )

        # Define external tools
        self.tools = [
            TavilySearchResults(
                max_results=3,
                description="Искать актуальную информацию в интернете",
                tavily_api_key=os.getenv("TAVILY_API_KEY")
            )
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Define custom state
        class State(MessagesState):
            is_reasoning: bool

        self.State = State

        # Build conversational graph
        self.builder = StateGraph(State)
        self.builder.add_node('assistant', self.assistant)
        self.builder.add_node('tools', ToolNode(self.tools))
        self.builder.add_edge(START, 'assistant')
        self.builder.add_conditional_edges('assistant', tools_condition)
        self.builder.add_edge('tools', 'assistant')

        # Setup persistence
        self.memory = MemorySaver()
        self.graph = self.builder.compile(checkpointer=self.memory)

    def assistant(self, state: MessagesState) -> dict:
        """
        Graph node: invoke LLM (with tools) to process conversation state.

        Parameters:
        -----------
        state : MessagesState
            Current graph state containing message history and flags.

        Returns:
        -------
        dict
            messages: List[BaseMessage] with new assistant response
            is_reasoning: False flag indicating tool use completed
        """
        content = self.llm_with_tools.invoke(
            [SystemMessage(content=sys_prompt)] + state['messages']
        )
        return {"messages": [content], "is_reasoning": False}


class AgentAPI:
    """
    FastAPI wrapper to expose LangGraphAgent via HTTP endpoints.

    Attributes:
    -----------
    agent : LangGraphAgent
        Underlying conversational agent instance.
    app : FastAPI
        Web application instance.
    """

    def __init__(self, agent: LangGraphAgent):
        """
        Initialize API with provided agent.

        Mounts routes and binds query endpoint.
        """
        self.agent = agent
        self.app = FastAPI()

        class Query(BaseModel):
            message: str = Field(..., description="User message text")
            thread_id: str = Field(..., description="Unique conversation thread identifier")

        @self.app.post("/query")
        def query_endpoint(query: Query) -> dict:
            """
            HTTP endpoint to process user query through the agent.

            Parameters:
            -----------
            query : Query
                Parsed JSON body with `message` and `thread_id`.

            Returns:
            -------
            dict
                response: Agent-generated reply text.

            Raises:
            ------
            HTTPException(500)
                If processing or graph invocation fails.
            """
            # Initialize state for new message
            state = self.agent.State(
                messages=[HumanMessage(content=query.message)],
                is_reasoning=False
            )
            try:
                # Invoke the compiled graph flow
                result = self.agent.graph.invoke(
                    state, {"configurable": {"thread_id": query.thread_id}}
                )
                if 'messages' in result:
                    content = result['messages'][-1].content
                    print(
                        "TOTAL TOKENS (without search): ",
                        result['messages'][-1].response_metadata['token_usage']['total_tokens']
                    )
                    return {"response": content}
                raise HTTPException(status_code=500, detail="Ошибка обработки запроса")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


# Instantiate and mount API
agent = LangGraphAgent()
api = AgentAPI(agent).app

# Запуск приложения
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="0.0.0.0", port=8000)
