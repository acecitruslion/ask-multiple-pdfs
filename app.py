import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_classic.memory import ConversationBufferMemory
# Using the absolute path instead of the shortcut
from langchain_classic.chains import ConversationalRetrievalChain

import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_vector_store(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    # Use the current multimodal embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2-preview")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

def get_conversation_chain(vector_store):
    # Use the current stable frontier model
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=vector_store.as_retriever(), 
        memory=memory
    )
    return conversation_chain

def main():
    st.set_page_config(page_title="Multi-PDF Chatbot", page_icon="🤖")
    st.header("Multi-PDF RAG Chatbot 🤖")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if user_question := st.chat_input("Ask a question about your documents:"):
        if st.session_state.conversation is None:
            st.warning("Please upload and process your PDFs in the sidebar first!")
            return
            
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.spinner("Thinking..."):
            response = st.session_state.conversation({'question': user_question})
            answer = response['answer']
            
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

    with st.sidebar:
        st.title("Menu")
        pdf_docs = st.file_uploader("Upload your PDFs", accept_multiple_files=True)
        if st.button("Process"):
            if pdf_docs:
                with st.spinner("Processing..."):
                    raw_text = get_pdf_text(pdf_docs)
                    vector_store = get_vector_store(raw_text)
                    st.session_state.conversation = get_conversation_chain(vector_store)
                    st.success("Documents processed successfully!")
            else:
                st.error("Please upload at least one PDF.")

if __name__ == "__main__":
    main()