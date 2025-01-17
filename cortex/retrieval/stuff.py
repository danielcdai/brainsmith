from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from validators import url as validate_url
from pydantic import BaseModel
import os


class SummarizeRequest(BaseModel):
    url: str
    openai_key: str


# TODO: support other loaders, other llm providers
def web_stuff_summarization( 
        url: str,
        openai_key: str
    ):
    """
    Summarize a web page using the Stuff Documents chain

    :param url: The URL of the web page to summarize
    :param openai_key: The OpenAI API key
    :return: The summary of the web page
    """
    if not validate_url(url):
        raise ValueError("Invalid URL")
    prompt = ChatPromptTemplate.from_messages(
        [("system", "Write a concise summary of the following docs:\\n\\n{context}")]
    )
    os.environ["OPENAI_API_KEY"] = openai_key
    llm = ChatOpenAI(model="gpt-4o-mini")
    chain = create_stuff_documents_chain(llm, prompt)
    loader = WebBaseLoader(url)
    docs = loader.load()
    result = chain.invoke({"context": docs})
    return result