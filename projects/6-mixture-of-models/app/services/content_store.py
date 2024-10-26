import uuid

from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List, Tuple

from langchain_core.documents import Document
from opensearchpy import OpenSearch

from services.data_loader import DataLoader
from services.embedding_service import EmbeddingService


@dataclass
class OpenSearchConfig:
    hostname: str
    port: str
    auth: Tuple[str, str]
    use_ssl: bool = True
    verify_certs: bool = False


class ContentStore:
    INDEX_NAME = "app_documents"
    SEARCH_PIPELINE_NAME = "nlp-search-pipeline"

    SEARCH_PIPELINE_SETTINGS = {
        "description": "Post processor for hybrid search (combine keyword and vector)",
        "phase_results_processors": [
            {
                "normalization-processor": {
                    "normalization": {"technique": "min_max"},
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {"weights": [0.3, 0.7]},
                    },
                }
            }
        ],
    }

    BASE_SEARCH_QUERY = {
        "_source": False,
        "fields": ["page_content", "metadata.source"],
    }

    def __init__(
        self,
        search_config: OpenSearchConfig,
        content_dir: str,
        embedding_service: EmbeddingService,
    ):
        self.content_dir = content_dir
        self.data_loader = DataLoader(content_dir)
        self.embedding_service = embedding_service
        self.search_client = self.initialize_search_client(config=search_config)

        self.ensure_search_setup()

    @cached_property
    def index_settings(self) -> Dict:
        return {
            "settings": {"index": {"number_of_shards": 4}, "index.knn": True},
            "mappings": {
                "properties": {
                    "embeddings": {
                        "type": "knn_vector",
                        "dimension": self.embedding_service.get_embedding_model_dimensions(),
                    },
                }
            },
        }

    ########
    # Setup
    ########
    def initialize_search_client(self, config: OpenSearchConfig) -> OpenSearch:
        return OpenSearch(
            hosts=[{"host": config.hostname, "port": config.port}],
            http_auth=config.auth,
            use_ssl=config.use_ssl,
            verify_certs=config.verify_certs,
        )

    def ensure_search_setup(self) -> None:
        self.ensure_index_exists()
        self.ensure_search_pipeline_exists()

    def ensure_index_exists(self) -> None:
        try:
            self.search_client.indices.get(self.INDEX_NAME)
        except:
            self.refresh_index()

    def refresh_index(self) -> None:
        try:
            self.search_client.indices.delete(self.INDEX_NAME)
        except:
            pass

        self.search_client.indices.create(self.INDEX_NAME, body=self.index_settings)
        self.load_documents_from_disk_into_index()

    def ensure_search_pipeline_exists(self) -> None:
        try:
            self.search_client.http.get(
                f"/_search/pipeline/{self.SEARCH_PIPELINE_NAME}"
            )
        except:
            self.refresh_search_pipeline()

    def refresh_search_pipeline(self) -> None:
        try:
            self.search_client.http.delete(
                f"/_search/pipeline/{self.SEARCH_PIPELINE_NAME}"
            )
        except:
            pass

        self.search_client.http.put(
            f"/_search/pipeline/{self.SEARCH_PIPELINE_NAME}",
            body=self.SEARCH_PIPELINE_SETTINGS,
        )

    ########
    # Loader
    ########
    def load_documents_from_disk_into_index(self) -> None:
        documents = self.data_loader.load_documents_from_disk()
        self.load_documents_into_index(documents)

    def load_documents_into_index(self, documents: List[Document]) -> None:
        for document in documents:
            # Todo: use bulk upload
            search_body = document.dict()
            search_body.update(
                {
                    "embedding_model": self.embedding_service.model,
                    "embeddings": self.embedding_service.get_embeddings(
                        document.page_content
                    ),
                }
            )

            self.search_client.index(
                index=self.INDEX_NAME,
                body=search_body,
                id=str(uuid.uuid1()),
                refresh=True,
            )

    def add_document(self, title: str, body: str) -> None:
        document_file_path = self.data_loader.save_document_to_disk(title, body)
        self.load_document_into_index(document_file_path)

    def load_document_into_index(self, document_file_path: str) -> None:
        documents = self.data_loader.load_document_from_disk(document_file_path)
        self.load_documents_into_index(documents)

    ########
    # Search
    ########
    def query(self, text: str, size: int = 3) -> List:
        return self.hybrid_query(text=text, size=size)

    def hybrid_query(self, text: str, size: int = 3) -> List:
        query_embeddings = self.embedding_service.get_embeddings(text)

        search_query = self.BASE_SEARCH_QUERY.copy()
        search_query.update(
            {
                "size": size,
                "query": {
                    "hybrid": {
                        "queries": [
                            {"match": {"page_content": {"query": text}}},
                            {
                                "knn": {
                                    "embeddings": {
                                        "vector": query_embeddings,
                                        "k": size,
                                    }
                                }
                            },
                        ]
                    }
                },
            }
        )

        results = self.search_client.search(
            index=self.INDEX_NAME,
            body=search_query,
            params={"search_pipeline": self.SEARCH_PIPELINE_NAME},
        )

        return results["hits"]["hits"]

    def keyword_query(self, text: str, size: int = 3) -> List:
        search_query = self.BASE_SEARCH_QUERY.copy()
        search_query.update(
            {"size": size, "query": {"match": {"page_content": {"query": text}}}}
        )

        results = self.search_client.search(index=self.INDEX_NAME, body=search_query)

        return results["hits"]["hits"]

    def vector_query(self, text: str, size: int = 3) -> List:
        query_embeddings = self.embedding_service.get_embeddings(text)

        search_query = self.BASE_SEARCH_QUERY.copy()
        search_query.update(
            {
                "size": size,
                "query": {
                    "knn": {
                        "embeddings": {
                            "vector": query_embeddings,
                            "k": size,
                        }
                    }
                },
            }
        )

        results = self.search_client.search(index=self.INDEX_NAME, body=search_query)

        return results["hits"]["hits"]

    def find_document(self, query: str) -> Dict:
        search_query = self.BASE_SEARCH_QUERY.copy()
        search_query.update(
            {"size": 1, "query": {"wildcard": {"metadata.source": f"*{query}*"}}}
        )

        results = self.search_client.search(index=self.INDEX_NAME, body=search_query)

        if not results["hits"]["hits"]:
            return {}

        hit = results["hits"]["hits"][0]

        return {
            "source": hit["fields"]["metadata.source"][0],
            "page_content": hit["fields"]["page_content"][0],
        }
