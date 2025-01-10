import os
import logging
import logging.config

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language

from cortex.config import settings


log_file = f"{settings.log_dir}/split.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'default'
        }
    },
    'loggers': {
        'split_logger': {
            'handlers': ['default'],
            'level': 'INFO'
        }
    }
})
split_logger = logging.getLogger('split_logger')


known_ext_dict = {
    "cpp": Language.CPP,
    "go": Language.GO,
    "java": Language.JAVA,
    "kt": Language.KOTLIN,
    "js": Language.JS,
    "ts": Language.TS,
    "php": Language.PHP,
    "proto": Language.PROTO,
    "py": Language.PYTHON,
    "rst": Language.RST,
    "rb": Language.RUBY,
    "rs": Language.RUST,
    "scala": Language.SCALA,
    "swift": Language.SWIFT,
    "md": Language.MARKDOWN,
    "tex": Language.LATEX,
    "html": Language.HTML,
    "sol": Language.SOL,
    "cs": Language.CSHARP,
    "cob": Language.COBOL,
    "c": Language.C,
    "lua": Language.LUA,
    "pl": Language.PERL,
    "hs": Language.HASKELL
}


class Chunker:
    """
    Base class for Chunking.
    """

    @staticmethod
    def of(file_type: str, **kwargs) -> "Chunker":
        file_type = file_type.lower()
        if file_type == "pdf":
            return PdfChunker(**kwargs)
        elif file_type == "txt":
            return RecursiveCharacterChunker(**kwargs)
        elif file_type in known_ext_dict.keys():
            return CodeChunker(**kwargs)
        elif file_type == "md":
            return MarkdownChunker(**kwargs)
        elif file_type == "csv":
            return CsvChunker(**kwargs)
        else:
            return RecursiveCharacterChunker(**kwargs)

    def __init__(self, **kwargs):
        """
        :param chunk_size: max number of characters or tokens in each chunk
        :param chunk_overlap: how many characters/tokens overlap between consecutive chunks
        :param length_function: a function that determines length of text (e.g., len or a token counter)
        :param chunk_separator: a separator string or regex pattern
        """
        self.splitter = kwargs.get("splitter", "text")
        self.chunk_size = kwargs.get("chunk_size", 400)
        self.chunk_overlap = kwargs.get("chunk_overlap", 20)
        # For code splitters, the separator is dynamically determined
        # In this case, the separator would be appliyed on RecursiveCharacterTextSplitter only
        self.chunk_separator = ["\n\n", "\n", " ", ""]
        if self.splitter == "text":
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.chunk_separator,
            )
        elif self.splitter == "semantic":
            from langchain_experimental.text_splitter import SemanticChunker
            from langchain_ollama import OllamaEmbeddings
            from cortex.config import settings
            self.splitter = SemanticChunker(
                embeddings=OllamaEmbeddings(
                    base_url=settings.ollama_base_url,
                    model="nomic-embed-text:latest",
                )
            )
        else:
            raise ValueError(f"Invalid split type: {self.splitter}")

    def split(self, file_path):
        """
        Read text from `file_path` and split it into chunks.
        This method must be implemented in subclasses.
        """
        raise NotImplementedError


class RecursiveCharacterChunker(Chunker):
    """
    Character based chunker.
    Uses LangChain's RecursiveCharacterTextSplitter under the hood.
    """

    def __init__(self, **kwargs):
        super(RecursiveCharacterChunker, self).__init__(**kwargs)

    def split(self, file_path):
        """
        Do recursive character-based chunking using LangChain’s RecursiveCharacterTextSplitter.
        """
        split_logger.info(f"Splitting file: {file_path} via RecursiveChunker and {self.splitter}")
        loader = TextLoader(file_path=file_path, encoding="utf-8")
        return loader.load_and_split(text_splitter=self.splitter)


class PdfChunker(Chunker):
    """
    Chunker for PDF files.
    Uses LangChain's PDFTextSplitter under the hood.
    """

    def __init__(self, **kwargs):
        super(PdfChunker, self).__init__(**kwargs)

    def split(self, file_path):
        """
        Do PDF-based chunking using LangChain’s PDFTextSplitter.
        """
        split_logger.info(f"Splitting file: {file_path} via PdfChunker and {self.splitter}")
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        loader = PyPDFLoader(file_path)
        # Note: Simply use recursive character-based chunking for PDF files.
        #       More advanced chunking strategies can be implemented here.
        #       Currently no evidences suggests that recursive character-based chunking is not good enough
        return loader.load_and_split(text_splitter=self.splitter)
       

class CodeChunker(Chunker):
    """
    Chunker for code files.
    Supporting Python, C++, and Java.
    """

    def __init__(self, **kwargs):
        super(CodeChunker, self).__init__(**kwargs)
   
    def split(self, file_path):
        file_ext = os.path.splitext(file_path)[1].strip(".")
        split_logger.info(f"Splitting file: {file_path} via CodeChunker for language: {file_ext}")
        lan = known_ext_dict.get(file_ext)
        loader = TextLoader(file_path=file_path, encoding="utf-8")
        code_splitter = RecursiveCharacterTextSplitter.from_language(
            language=lan,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return loader.load_and_split(text_splitter=code_splitter)


class CsvChunker(Chunker):
    """
    Chunker for CSV files.
    """

    def __init__(self, **kwargs):
        self.delimiter = kwargs.get("delimiter", ",")
        self.quotechar = kwargs.get("quotechar", '"')
        self.fieldnames = kwargs.get("fieldnames", ["instructions", "context"])

        super(CsvChunker, self).__init__(**kwargs)
   
    def split(self, file_path):
        split_logger.info(f"Splitting file: {file_path} via CsvChunker and {self.splitter}")
        from langchain_community.document_loaders.csv_loader import CSVLoader
        loader = CSVLoader(
            file_path=file_path,
            csv_args={
                "delimiter": self.delimiter,
                "quotechar": self.quotechar,
                "fieldnames": self.fieldnames,
            },
        )
        return loader.load_and_split(text_splitter=self.splitter)

       
class MarkdownChunker(Chunker):
    """
    Chunker for Markdown files.
    """

    def __init__(self, **kwargs):
        self.headers_to_split_on = kwargs.get("headers_to_split_on", [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ])
        super(MarkdownChunker, self).__init__(**kwargs)
   
    def split(self, file_path):
        split_logger.info(f"Splitting file: {file_path} via MarkdownChunker and {self.splitter}")
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        # FIXME: Having trouble with dependencies related markdown loader, leave it as-is for now
        # from langchain_community.document_loaders import UnstructuredMarkdownLoader
        # loader = UnstructuredMarkdownLoader(file_path=file_path)
        loader = TextLoader(file_path=file_path, encoding="utf-8")
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on, strip_headers=False
        )
        documents = loader.load_and_split(text_splitter=markdown_splitter)
        return self.splitter.split_documents(documents=documents)