"""
This module handles the data ingestion pipeline for Clintra.
It processes documents, creates embeddings, and stores them in a vector database.
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredFileLoader
from langchain.vectorstores import Pinecone
from langchain.embeddings import HuggingFaceEmbeddings

def ingest_documents(file_path: str, pinecone_index_name: str):
    """
    Processes and ingests documents into the Pinecone vector store.
    """
    print(f"Starting ingestion for file: {file_path}")

    # 1. Load the document
    # loader = UnstructuredFileLoader(file_path)
    # documents = loader.load()
    # print(f"Loaded {len(documents)} documents.")

    # 2. Split the document into chunks
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # texts = text_splitter.split_documents(documents)
    # print(f"Split into {len(texts)} chunks.")

    # 3. Initialize embeddings
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Ingest into Pinecone
    # Pinecone.from_texts(
    #     [t.page_content for t in texts],
    #     embeddings,
    #     index_name=pinecone_index_name
    # )

    print(f"Simulated ingestion for {file_path} complete.")
    return {
        "status": "success",
        "message": f"Simulated ingestion of {file_path} into {pinecone_index_name} complete.",
        "chunks_created": 15, # mock value
    }

def clear_index(pinecone_index_name: str):
    """
    Clears all vectors from a Pinecone index.
    """
    # import pinecone
    # pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT"))
    # index = pinecone.Index(pinecone_index_name)
    # index.delete(deleteAll='true')
    print(f"Simulated clearing of index {pinecone_index_name}.")
    return {"status": "success", "message": f"Index {pinecone_index_name} cleared (simulation)."}