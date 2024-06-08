# import json

import uuid

import chromadb
from chromadb.config import Settings

from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader

from langchain_text_splitters import CharacterTextSplitter

from services.fs_utils import save_document_to_disk as save_document_to_disk


class VectorStore:
    def __init__(
        self,
        chroma_hostname: str,
        chroma_port: str,
        content_dir: str,
        embedding_function,
    ):
        self.chroma_hostname = chroma_hostname
        self.chroma_port = chroma_port
        self.content_dir = content_dir
        self.embedding_function = embedding_function

        self.directory_loader = DirectoryLoader(self.content_dir, glob="**/*.txt")
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

        self.chroma_client = chromadb.HttpClient(
            host=self.chroma_hostname,
            port=self.chroma_port,
            settings=Settings(allow_reset=True),
        )

        self.collection_name = "app_collection"
        self.ensure_collection_exists()

    def ensure_collection_exists(self):
        try:
            self.chroma_collection = self.chroma_client.get_collection(
                self.collection_name
            )
        except:
            self.refresh_collection()

    def refresh_collection(self):
        self.chroma_client.reset()

        self.chroma_collection = self.chroma_client.create_collection(
            self.collection_name
        )

        self.load_docs_from_disk_into_collection()

    def load_docs_from_disk_into_collection(self):
        documents = self.directory_loader.load()
        docs = self.text_splitter.split_documents(documents)
        self.load_docs_into_collection(docs)

    def load_docs_into_collection(self, docs):
        for doc in docs:
            self.chroma_collection.add(
                ids=[str(uuid.uuid1())],
                metadatas=doc.metadata,
                documents=doc.page_content,
                embeddings=self.embedding_function(doc.page_content),
            )

    def add_document(self, title: str, body: str):
        document_file_path = save_document_to_disk(
            directory_path=self.content_dir, title=title, body=body
        )
        self.load_document_into_collection(document_file_path)

    def load_document_into_collection(self, document_file_path: str):
        text_loader = TextLoader(document_file_path)
        document = text_loader.load()
        docs = self.text_splitter.split_documents(document)

        self.load_docs_into_collection(docs)

    def query_with_text(self, text: str, max_number_of_docs: int = 1):
        query_embeddings = self.embedding_function.embed_query(text)
        response = self.chroma_collection.query(
            query_embeddings=query_embeddings, n_results=max_number_of_docs
        )

        return response
