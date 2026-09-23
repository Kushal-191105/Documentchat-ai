import os
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from documents.services.vector_store import get_vector_store

def generate_answer(document_id, question, chat_history=None):
    """
    RAG Pipeline:
    1. Retrieve relevant chunks from ChromaDB for the given document_id.
    2. Pass the context and question to the LLM.
    3. Return the generated answer and the source chunks.
    """
    api_key = os.environ.get('LLM_API_KEY')
    if not api_key or api_key == 'your_llm_api_key_here':
        return {
            "answer": "Error: LLM_API_KEY is not configured in the environment variables.",
            "sources": []
        }

    try:
        # 1. Initialize Vector Store and retrieve chunks
        vector_store = get_vector_store()
        
        # We use similarity search with a metadata filter
        retrieved_docs = vector_store.similarity_search(
            query=question,
            k=5, # Number of chunks to retrieve
            filter={"document_id": str(document_id)}
        )

        # If no relevant chunks are found
        if not retrieved_docs:
            return {
                "answer": "I could not find any relevant information in the document to answer your question.",
                "sources": []
            }

        # 2. Format context
        context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])

        # 3. Prompt Template
        prompt_template = """
You are an AI Document Research Assistant. You help users answer questions based ONLY on the provided document context.

Follow these strict rules:
1. Use ONLY the provided context to answer the question. Do not use outside knowledge.
2. If the answer cannot be found in the context, say "I cannot answer this question based on the provided document." Do not try to make up an answer.
3. Be clear, concise, and helpful.
4. Use the Chat History to understand what the user is referring to if they use words like "he", "she", "it", or ask follow-up questions.

Chat History:
{chat_history}

Document Context:
{context}

Question: {question}

Answer:"""
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question", "chat_history"]
        )
        
        # 4. Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash", 
            google_api_key=api_key,
            temperature=0.0 # Low temperature for more factual answers
        )

        # 5. Generate Answer
        chain = prompt | llm
        response = chain.invoke({
            "context": context_text, 
            "question": question,
            "chat_history": chat_history or "No previous history."
        })

        answer_text = response.content
        if isinstance(answer_text, list) and len(answer_text) > 0:
            answer_text = answer_text[0].get("text", str(answer_text))
        elif not isinstance(answer_text, str):
            answer_text = str(answer_text)

        # 6. Extract source metadata (page numbers)
        sources = []
        for doc in retrieved_docs:
            # PyMuPDFLoader automatically adds 'page' to metadata (0-indexed usually)
            page_num = doc.metadata.get('page', 'Unknown')
            if isinstance(page_num, int):
                page_num += 1 # Convert to 1-indexed for user readability
                
            sources.append({
                "page": page_num,
                "snippet": doc.page_content[:200] + "..." # A brief snippet
            })

        return {
            "answer": answer_text,
            "sources": sources
        }

    except Exception as e:
        return {
            "answer": f"An error occurred during AI processing: {str(e)}",
            "sources": []
        }

def generate_answer_stream(document_id, question, chat_history=None):
    """
    RAG Pipeline that streams chunks back to the user instantly.
    """
    api_key = os.environ.get('LLM_API_KEY')
    if not api_key or api_key == 'your_llm_api_key_here':
        yield "Error: LLM_API_KEY is not configured."
        return

    try:
        vector_store = get_vector_store()
        retrieved_docs = vector_store.similarity_search(
            query=question,
            k=15, # Increased from 5 to 15 for better search accuracy in large documents
            filter={"document_id": str(document_id)}
        )

        if not retrieved_docs:
            yield "I could not find any relevant information in the document to answer your question."
            return

        # Inject the page number into the context so the AI knows where it came from
        context_chunks = []
        for doc in retrieved_docs:
            page_num = doc.metadata.get('page', 'Unknown')
            if isinstance(page_num, int):
                page_num += 1 # 1-indexed
            context_chunks.append(f"[Page {page_num}]\n{doc.page_content}")
            
        context_text = "\n\n---\n\n".join(context_chunks)
        
        prompt_template = """
You are an AI Document Research Assistant. You help users answer questions based ONLY on the provided document context.

Follow these strict rules:
1. Use ONLY the provided context to answer the question. Do not use outside knowledge.
2. If the answer cannot be found in the context, say "I cannot answer this question based on the provided document." Do not try to make up an answer.
3. Be clear, concise, and helpful.
4. ALWAYS cite the page number where you found the information. Put the page number in **bold** at the end of your sentences or paragraphs (e.g., **[Page 45]**). Use the [Page X] markers provided in the Document Context to know which page the text came from.
5. Use the Chat History to understand what the user is referring to if they use words like "he", "she", "it", or ask follow-up questions.

Chat History:
{chat_history}

Document Context:
{context}

Question: {question}

Answer:"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question", "chat_history"])
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite", 
            google_api_key=api_key,
            temperature=0.0
        )

        chain = prompt | llm
        
        # STREAM THE ANSWER!
        for chunk in chain.stream({
            "context": context_text, 
            "question": question,
            "chat_history": chat_history or "No previous history."
        }):
            text = chunk.content
            if isinstance(text, list):
                if len(text) > 0:
                    text = text[0].get("text", "")
                else:
                    text = ""
            elif not isinstance(text, str):
                text = str(text)
            
            if text:
                yield text
            
        # Finally yield the sources as a dict
        sources = []
        for doc in retrieved_docs:
            page_num = doc.metadata.get('page', 'Unknown')
            if isinstance(page_num, int):
                page_num += 1
            sources.append({"page": page_num, "snippet": doc.page_content[:200] + "..."})
            
        yield {"sources": sources}

    except Exception as e:
        yield f"\n\nAn error occurred during AI processing: {str(e)}"
