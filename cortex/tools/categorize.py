from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os


def categorize_summary(summary, openai_key):
    os.environ["OPENAI_API_KEY"] = openai_key
    prompt = ChatPromptTemplate.from_template(
        "Given the following summary," 
        "categorize it into an appropriate category:\n\n"
        "Acceptable categories include: "
        "Business, Technology, Entertainment, Health, Science, Sports, Politics, "
        "Summary: {summary}\n\n"
        "Category:"
    )
    llm = ChatOpenAI(model="gpt-4o-mini")
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"summary", summary})
    return result.strip()


if __name__ == "__main__":
    summary = "As TikTok faces a potential ban in the US, "
    "creators are considering alternative platforms for maintaining their audiences and income."
    "Many creators, like Noelle Johansen and Kay Poyer, "
    "are turning to Instagram, Twitter, and newer platforms like Bluesky and Substack. "
    "Bethany Brookshire highlights the engagement differences across platforms, noting TikTok's strong community interaction. "
    "Woodstock Farm Sanctuary emphasizes TikTok's unique reach beyond typical audiences. "
    "Creators like Anna Rangos and Amanda Chavira express concerns about transitioning to platforms owned by Meta, "
    "citing past issues and policy changes. "
    "Overall, creators are preparing to pivot "
    "but acknowledge the challenges of recreating TikTok's unique environment on other platforms."
    category = categorize_summary(summary)