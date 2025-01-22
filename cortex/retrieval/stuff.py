from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from validators import url as validate_url
from pydantic import BaseModel
import os


class CategorizeRequest(BaseModel):
    summary: str
    openai_key: str
    provider_options: dict = {}


class SummarizeRequest(BaseModel):
    url: str
    openai_key: str
    provider_options: dict = {}


# TODO: support other loaders
def web_stuff_summarization( 
        url: str,
        openai_key: str,
        **kwargs
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
    # Supported various providers url here
    model = kwargs["model"] if "model" in kwargs else "gpt-4o-mini"
    llm = (
        ChatOpenAI(model=model, api_key=openai_key)
        if "openai_base" not in kwargs
        else ChatOpenAI(model=model, base_url=kwargs["openai_base"], api_key=openai_key)
    )
    chain = create_stuff_documents_chain(llm, prompt)
    loader = WebBaseLoader(url)
    docs = loader.load()
    result = chain.invoke({"context": docs})
    return result