import streamlit as st
import os
from langchain_ollama.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser, BaseOutputParser
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
import uuid
from utils.helpers import load_css, render_header
import utils.templates as templates
from langchain_openai import ChatOpenAI
from utils.auth import  authenticate_user

# Load the CSS from the file
css = load_css("theme/style.css")
st.set_page_config(
    page_title="SpoKI",  # Title of the app
    page_icon="favicon.ico"     # Path to your favicon or use emojis like "🚀"
)

authenticator = authenticate_user("auth.yaml", "Secure Streamlit App")


class BooleanOutputParser(BaseOutputParser[bool]):
    """Custom boolean parser."""

    true_val: str = "YES"
    false_val: str = "NO"

    def parse(self, text: str) -> bool:
        cleaned_text = text.strip().upper()
        if cleaned_text not in (self.true_val.upper(), self.false_val.upper()):
            return cleaned_text == self.false_val.upper()
        return cleaned_text == self.true_val.upper()

    @property
    def _type(self) -> str:
        return "boolean_output_parser"


# llm settings num_ctx (Input token limit) hier setzen weil ChatOllama das sonst überschreibt
# Überlegung: Versuchen das zu cachen und gucken obs nen Unterschied macht


# Das ist das standard system prompt template für spoki, kann als grundlage genommen und angepasst werden für das system prompt template ab der 2. message
feedback_prompt = templates.feedback
feedback_all_prompt = templates.feedback_all
answer_prompt = templates.answer
feedback_aufgabe_anforderung_prompt = templates.feedback_aufgabe_anforderung
feedback_lernziel_anforderung_prompt = templates.feedback_lernziel_anforderung
feedback_lernziel_aufgabe_prompt = templates.feedback_lernziel_aufgabe
feedback_aufgabe_prompt = templates.feedback_aufgabe
feedback_lernziel_prompt = templates.feedback_lernziel


print(os.environ.get('OPENAI_API_MODEL'))


if "OPENAI_API_KEY" in os.environ:
    llm = ChatOpenAI(
        model=os.environ.get('OPENAI_API_MODEL'),
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )   
    spoki_llm = llm

    #ionos does not have correct a compatible embedding model atm
    #use this to create it via local embddings

    
    #from langchain_openai import OpenAIEmbeddings


   #embed_model = OpenAIEmbeddings(
    #    model="text-embedding-3-large",
        # With the `text-embedding-3` class
        # of models, you can specify the size
        # of the embeddings you want returned.
        # dimensions=1024
    #)



    #embed_model = OllamaEmbeddings(
        #model = os.getenv('OPENAI_API_MODEL',"nomic-embed-text")

    embed_model = OllamaEmbeddings(model="nomic-embed-text")

    persist_directory = "./data/chroma"

    


    feedback_prompt  = templates.systemprompt + "\n\n" + feedback_prompt
    feedback_all_prompt  = templates.systemprompt + "\n\n" + feedback_all_prompt
    answer_prompt  = templates.systemprompt + "\n\n" + answer_prompt
    feedback_aufgabe_anforderung_prompt  = templates.systemprompt + "\n\n" + feedback_aufgabe_anforderung_prompt
    feedback_lernziel_anforderung_prompt  = templates.systemprompt + "\n\n" + feedback_lernziel_anforderung_prompt
    feedback_lernziel_aufgabe_prompt  = templates.systemprompt + "\n\n" + feedback_lernziel_aufgabe_prompt
    feedback_aufgabe_prompt  = templates.systemprompt + "\n\n" + feedback_aufgabe_prompt
    feedback_lernziel_prompt  = templates.systemprompt + "\n\n" + feedback_lernziel_prompt

else:
    llm = ChatOllama(model="spokiv5", num_ctx=40000)
    spoki_llm = ChatOllama(model="spokiv5", num_ctx=40000, temperature=0.4)
    embed_model = OllamaEmbeddings(model="nomic-embed-text")
    persist_directory = "./data/chroma"


def generate_uuid():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    return st.session_state.thread_id


thread_id = generate_uuid()
print(thread_id)
graph_config = {"configurable": {"thread_id": thread_id}}


@st.cache_resource
def init_retriever():
    loader = DirectoryLoader("data/documents", glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=150, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)



    # Check if the database already exists

    if os.path.exists(persist_directory):
        vectorstore = Chroma(collection_name="RAG-Chroma", embedding_function=embed_model,
                             persist_directory=persist_directory)
        print("loaded existing vectorstore")
    else:
        # Create and persist the Chroma vectorstore
        vectorstore = Chroma.from_documents(documents=all_splits, collection_name="RAG-Chroma", embedding=embed_model,
                                            persist_directory=persist_directory)
        print("created new vectorstore")

    vectorstore_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    return vectorstore_retriever


retriever = init_retriever()


def clear_chat_history():
    st.session_state.messages = []
    del st.session_state.thread_id
    st.session_state['has_interacted'] = False
        


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)




feedback_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)

# Hier können wir Beispiele setzen die wir dann als bestehende Chat Messages vor dem eigentlichen Chat übergeben können.
examples = [
    {"input": "", "output": ""},
    {"input": "", "output": ""},
]

# Die Beispiele werden dann als ChatPromptTemplate formatiert.
example_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{input}"),
        ("ai", "{output}"),
    ]
)

# Hier wird das few shot prompt mit unseren Beispielen befüllt umd später als variable in dem few shot ChatPromptTemplate übergeben zu werden.
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
)

# das fertige few shot prompt template, welches wir mit unseren Beispielen befüllt haben wird vor der Chat History übergeben.
few_shot_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_prompt),
        few_shot_prompt,
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)



answer_template = ChatPromptTemplate.from_messages(
    [
        ("system", answer_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)

answer_chain = answer_template | spoki_llm | StrOutputParser()

content_check_prompt = templates.content_check

content_check_template = ChatPromptTemplate.from_messages(
    [
        ("system", content_check_prompt),
        ("human", "{question}"),
    ]
)

content_check_chain = content_check_template | spoki_llm | BooleanOutputParser()


lernziel_check_prompt = templates.lernziel_check

lernziel_check_template = ChatPromptTemplate.from_messages(
    [
        ("system", lernziel_check_prompt),
        ("human", "{question}"),
    ]
)

lernziel_check_chain = lernziel_check_template | spoki_llm | BooleanOutputParser()


anforderungssituation_check_prompt = templates.anforderungssituation_check

anforderungssituation_check_template = ChatPromptTemplate.from_messages(
    [
        ("system", anforderungssituation_check_prompt),
        ("human", "{question}"),
    ]
)

anforderungssituation_check_chain = anforderungssituation_check_template | spoki_llm | BooleanOutputParser()

feedback_all_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_all_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)



feedback_aufgabe_anforderung_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_aufgabe_anforderung_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)


feedback_lernziel_anforderung_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_lernziel_anforderung_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)



feedback_lernziel_aufgabe_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_lernziel_aufgabe_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)



feedback_aufgabe_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_aufgabe_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)

feedback_anforderungssituation_prompt = templates.feedback_anforderungssituation

feedback_anforderungssituation_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_anforderungssituation_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)



feedback_lernziel_template = ChatPromptTemplate.from_messages(
    [
        ("system", feedback_lernziel_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "{question}"),
    ]
)


# wird im graph in jedem schritt übergeben und kann von den nodes abgerufen und verändert werden.
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
        messages: list of user input and final output
        content_type: type of content
        feedback: True if exists, False if not
    """

    question: str
    generation: str
    documents: List[str]
    # durch add_messages wird jede message die im return steht unseren messages hinzugefügt
    messages: Annotated[list[AnyMessage], add_messages]
    content_type: int
    feedback: bool


# Nodes
def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    messages = state["messages"]
    st.session_state.messages.append({"role": "user", "content": question})
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question, "messages": [HumanMessage(content=question)]}


def generate_feedback(state):
    """
    Generate feedback

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATING-FEEDBACK---")
    question = state["question"]
    documents = state["documents"]
    messages = state["messages"]
    content_type = state["content_type"]
    print(f"content_type: {content_type}")
    if content_type == 1:
        feedback_chain = feedback_all_template | spoki_llm | StrOutputParser()
    elif content_type == 2:
        feedback_chain = feedback_aufgabe_anforderung_template | spoki_llm | StrOutputParser()
    elif content_type == 3:
        feedback_chain = feedback_lernziel_anforderung_template | spoki_llm | StrOutputParser()
    elif content_type == 4:
        feedback_chain = feedback_lernziel_aufgabe_template | spoki_llm | StrOutputParser()
    elif content_type == 5:
        feedback_chain = feedback_aufgabe_template | spoki_llm | StrOutputParser()
    elif content_type == 6:
        feedback_chain = feedback_anforderungssituation_template | spoki_llm | StrOutputParser()
    elif content_type == 7:
        feedback_chain = feedback_lernziel_template | spoki_llm | StrOutputParser()
    else:
        feedback_chain = feedback_template | spoki_llm | StrOutputParser()
    generation = st.write_stream(feedback_chain.stream({"context": documents, "question": question, "messages": messages}, config=graph_config))
    st.session_state.messages.append({"role": "assistant", "content": generation})
    return {"documents": documents, "generation": generation, "messages": [AIMessage(content=generation)]}


def answer(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATING-ANSWER---")
    question = state["question"]
    documents = state["documents"]
    messages = state["messages"]
    generation = st.write_stream(answer_chain.stream({"context": documents, "question": question, "messages": messages}, config=graph_config))
    st.session_state.messages.append({"role": "assistant", "content": generation})
    return {"documents": documents, "generation": generation, "messages": [AIMessage(content=generation)]}


def check_input(state):
    """
    check input

    Args:
        state (dict): The current graph state

    Returns:
        content_type
    """
    print("---CHECKING-INPUT---")
    question = state["question"]
    aufgabe = content_check_chain.invoke({"question": question})
    lernziel = lernziel_check_chain.invoke({"question": question})
    anforderungssituation = anforderungssituation_check_chain.invoke({"question": question})
    print(f"Aufgabe: {aufgabe}")
    print(f"Lernziel: {lernziel}")
    print(f"Anforderungssituation: {anforderungssituation}")
    if aufgabe and lernziel and anforderungssituation:
        return {"content_type": 1}
    elif aufgabe and anforderungssituation:
        return {"content_type": 2}
    elif lernziel and anforderungssituation:
        return {"content_type": 3}
    elif lernziel and aufgabe:
        return {"content_type": 4}
    elif aufgabe:
        return {"content_type": 5}
    elif anforderungssituation:
        return {"content_type": 6}
    elif lernziel:
        return {"content_type": 7}
    # kann es nur aufgabe ohne lernziel oder anforderungssituation geben? -> falls ja sollt ehier noch folgendes stehen: elif aufgabe: return "generate_feedback"
    else:
        return {"content_type": 8}


def decide_output(state):
    """
    decide output

    Args:
        state (dict): The current graph state

    Returns:
        bool
    """
    # feedback_chain = feedback_template | spoki_llm | StrOutputParser()
    content_type = state["content_type"]
    if content_type is not None and content_type <= 7:
        return "generate_feedback"
    # kann es nur aufgabe ohne lernziel oder anforderungssituation geben? -> falls ja sollt ehier noch folgendes stehen: elif aufgabe: return "generate_feedback"
    else:
        return "answer"


# hier wird der eigentliche graph erstellt mit einem StateGraph welcher in jedem Schritt übergeben wird
workflow = StateGraph(GraphState)

# erst müssen die nodes hinzugefügt werden und anschließend verknüpft mit add_edge oder add_conditional_edge ; man kann auch einen langgraph agent erstellen und den agent entscheiden lassen welche node als nächstes ausgeführt werden soll -> gucke ich mir nochmal an
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("generate_feedback", generate_feedback)  # generate
workflow.add_node("answer", answer)  # answer w/o feedback
workflow.add_node("check_input", check_input)  # checks input type

# hier wird dann der eigentliche graph zusammengebaut aus den nodes die wir erstellt haben
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "check_input")
workflow.add_conditional_edges("check_input", decide_output,)
workflow.add_edge("answer", END)
workflow.add_edge("generate_feedback", END)
memory = MemorySaver()


_ = '''
das Graph compilen muss gecached werden weil sonst die chat history nicht funktioniert
'''


# nach dem compilen kann der graph wie eine normale chain benutzt werden z.B. mit .invoke oder .stream, einem anderen graph hinzugefügt oder einem agent als tool übergeben werden
@st.cache_resource
def compile_graph():
    graph = workflow.compile(checkpointer=memory)
    return graph


app = compile_graph()


# Streamlit UI
def main():
    st.title("SpoKI")

    print(f"auth status", st.session_state['authentication_status'])

    if 'has_interacted' not in st.session_state:
        st.session_state['has_interacted'] = False

    if not st.session_state['has_interacted']:
        intro_conatiner = render_header(st)

    else:
        intro_conatiner = st.empty()

    try:

        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state['authentication_status']:

        # initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []




        with st.sidebar:
            st.sidebar.button('Chat neu starten', on_click=clear_chat_history)
            authenticator.logout()
            st.write(f'Angemeldet als *{st.session_state["name"]}*')

            # Render the data privacy link
            st.markdown(
                """
                ---
                [Impressum](https://wissensnetz.dosb.de/impressum)|
                [Datenschutz](https://wissensnetz.dosb.de/datenschutz)
                """,
                unsafe_allow_html=True
            )


        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # accept user input
        if prompt := st.chat_input("Hallo, Wie kann ich helfen?"):
            st.session_state['has_interacted'] = True
            intro_conatiner.empty()


            # display user message in chat message container
            with st.chat_message("user"):
                st.write(prompt)
            # chat assistant
            with (st.chat_message("assistant")):
                input = {"question": prompt}

                #streaming und zu den messages hinzufügen passiert in generate
                app.invoke(input, config=graph_config, stream_mode="values")

                # ohne streaming
                # response = app.invoke(input, stream_mode="values")
                # st.write(response["generation"])
    elif st.session_state['authentication_status'] is False:
        st.error('Benutzername/Passwort falsch')
    elif st.session_state['authentication_status'] is None:
        st.markdown(
            """
            ---
            [Impressum](https://wissensnetz.dosb.de/impressum) | 
            [Datenschutz](https://wissensnetz.dosb.de/datenschutz)
            """,
            unsafe_allow_html=True
        )

if __name__ == '__main__':
    main()
