
import streamlit as st
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="PDF RAG Chatbot", page_icon="📄")

st.title("PDF RAG Chatbot")

VECTOR_DB_DIR = Path.cwd() /"vector_store" / "faiss_index"

@st.cache_resource
def load_vector_db():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return FAISS.load_local(
        str(VECTOR_DB_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

vector_db = load_vector_db()

retriever = vector_db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0
)

prompt = ChatPromptTemplate.from_template("""
Answer the question using only the provided context.
If the answer is not available in the PDF, say so.

Context:
{context}

Question:
{question}

Answer:
""")

rag_chain = prompt | llm | StrOutputParser()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask a question about your PDF")

if question:

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Generating answer..."):

            docs = retriever.invoke(question)

            context = "\n\n".join(
                doc.page_content for doc in docs
            )

            response = rag_chain.invoke({
                "context": context,
                "question": question
            })

            st.markdown(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
