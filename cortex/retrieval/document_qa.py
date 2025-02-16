import os
import tempfile
import shutil
from pathlib import Path
from IPython.display import Markdown, display

# Docling imports
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption, SimplePipeline

# LangChain imports
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


def get_document_format(file_path) -> InputFormat:
    """Determine the document format based on file extension"""
    try:
        file_path = str(file_path)
        extension = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.pdf': InputFormat.PDF,
            '.docx': InputFormat.DOCX,
            '.doc': InputFormat.DOCX,
            '.pptx': InputFormat.PPTX,
            '.html': InputFormat.HTML,
            '.htm': InputFormat.HTML
        }
        return format_map.get(extension, None)
    except:
        return "Unsupported document format: {str(e)}"

def convert_document_to_markdown(doc_path) -> str:
    """Convert document to markdown using simplified pipeline"""
    try:
        # Convert to absolute path string
        input_path = os.path.abspath(str(doc_path))
        print(f"Converting document: {doc_path}")
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy input file to temp directory
            temp_input = os.path.join(temp_dir, os.path.basename(input_path))
            shutil.copy2(input_path, temp_input)
            # Configure pipeline options
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False # Disable OCR temporarily
            pipeline_options.do_table_structure = True
            # Create converter with minimal options
            converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.DOCX,
                    InputFormat.HTML,
                    InputFormat.PPTX,
                ],
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                    ),
                    InputFormat.DOCX: WordFormatOption(
                        pipeline_cls=SimplePipeline
                    )
                }
            )

            # Convert document
            print("Starting conversion...")
            conv_result = converter.convert(temp_input)
            if not conv_result or not conv_result.document:
                raise ValueError(f"Failed to convert document: {doc_path}")
            # Export to markdown
            print("Exporting to markdown...")
            md = conv_result.document.export_to_markdown()

            # Create output path
            output_dir = os.path.dirname(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            md_path = os.path.join(output_dir, f"{base_name}_converted.md")

            # Write markdown file
            print(f"Writing markdown to: {base_name}_converted.md")
            with open(md_path, "w", encoding="utf-8") as fp:
                fp.write(md)
            return md_path
    except:
        return f"Error converting document: {doc_path}"


def setup_qa_chain(markdown_path: Path, embeddings_model_name:str = "nomic-embed-text:latest", model_name: str = "deepseek-r1:14b-qwen-distill-q8_0"):
    """Set up the QA chain for document processing"""
    # Load and split the document
    loader = UnstructuredMarkdownLoader(str(markdown_path))
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_documents(documents)
    # Create embeddings and vector store
    embeddings = OllamaEmbeddings(model=embeddings_model_name)
    vectorstore = FAISS.from_documents(texts, embeddings)
    # Initialize LLM
    llm = OllamaLLM(
        model=model_name,
        temperature=0
    )
    # Set up conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    # Build a prompt to rephrase a follow-up question given the chat history.
    rephrase_system_prompt = (
        "Given the chat history and the follow-up question, reformulate the question "
        "into a standalone question that can be understood without the conversation context."
    )
    rephrase_prompt = ChatPromptTemplate.from_messages([
        ("system", rephrase_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    # Create a history-aware retriever that uses the LLM to rephrase the question.
    history_aware_retriever = create_history_aware_retriever(llm, retriever, rephrase_prompt)

    # Build a prompt to answer the question using retrieved documents.
    qa_system_prompt = (
        "You are an assistant that answers questions based on the provided context. "
        "Use the context below to answer the question. If you don't know the answer, say so."
        "\n\n{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    # Create a chain that will combine retrieved documents (using a "stuff" approach) with your LLM.
    doc_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Compose the retrieval chain.
    qa_chain = create_retrieval_chain(
        history_aware_retriever,
        doc_chain,
    )
    chat_history = memory.load_memory_variables({})["chat_history"]
    return qa_chain, chat_history


def ask_question(qa_chain, question: str, chat_history: str = ""):
    """Ask a question and display the answer"""
    result = qa_chain.invoke({"input": question, "chat_history": chat_history})
    display(Markdown(f"**Question:** {question}\n\n**Answer:** {result['answer']}"))


if __name__ == "__main__":
    # Process a document
    doc_path = Path("paul_graham_essay.pdf")
    # Check format and process
    doc_format = get_document_format(doc_path)
    if doc_format:
        md_path = convert_document_to_markdown(doc_path)
        qa_chain, chat_history = setup_qa_chain(md_path)
        # Example questions
        questions = [
            "1. Why did the author want to get rich?",
            "2. What are some important things the author learned at Interleaf?",
            "3. Why did the author drop out of art school?",
            "4. What was the author's first company?",
            "5. What made the author leave Y Combinator?",
            "6. Why did the author go to Italy?",
            "7. What advice does the author give to aspiring entrepreneurs?",
            "8. What kinds of projects have the author pursued in his career?",
            "9. Why did the author switch art schools?",
            "10. Who is Rtm?",
        ]
        for question in questions:
            ask_question(qa_chain, question, chat_history)
    else:
        print(f"Unsupported document format: {doc_path.suffix}")
