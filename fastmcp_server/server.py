import os
import re

from dotenv import load_dotenv
from fastmcp import FastMCP, mcp_config
from langchain_community.document_loaders.firecrawl import FireCrawlLoader
from langchain_community.retrievers import PineconeHybridSearchRetriever
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import openai
from pinecone_text.sparse import BM25Encoder
from supabase import Client, create_client
import yfinance as yf

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

mcp = FastMCP("SearchAI")

@mcp.tool
def web_crawl_tool(query: str) -> str:
    """
    Search the web for the query using DuckDuckGo, crawl the top result with FireCrawl, and return the crawled content as text.
    """
    print(f"[SERVER] web_crawl_tool called with query: {query}")
    try:
        search_tool = DuckDuckGoSearchResults()
        search_results = search_tool.run(query)
        if not search_results or not isinstance(search_results, list) or not search_results[0].get('link'):
            return str(search_results)
        top_url = search_results[0]['link']
        print(f"[SERVER] Crawling top URL: {top_url}")
        loader = FireCrawlLoader(url=top_url, api_key=FIRECRAWL_API_KEY)
        docs = loader.load()
        if not docs:
            return f"No content found for {top_url}"
        return docs[0].page_content[:4000]  # Truncate to avoid overlong responses
    except Exception as e:
        return str(f"Error in web_crawl_tool: {e}")

@mcp.tool
def yahoo_finance_tool(ticker: str) -> str:
    """
    Fetch the latest price for a given ticker using yfinance.
    """
    print(f"[SERVER] yahoo_finance_tool called with ticker: {ticker}")
    try:
        ticker_obj = yf.Ticker(ticker)
        price = ticker_obj.fast_info['last_price'] if hasattr(ticker_obj, 'fast_info') and 'last_price' in ticker_obj.fast_info else None
        if price is None:
            # fallback to regular info
            price = ticker_obj.info.get('regularMarketPrice')
        if price is None:
            return f"Could not fetch price for {ticker}"
        return f"Latest price for {ticker}: {price}"
    except Exception as e:
        return str(f"Error in yahoo_finance_tool: {e}")
    
@mcp.tool
def embedder_tool(text: str) -> str:
    """
    Embed the text for hybrid search (semantic + keyword) using PineconeHybridSearchRetriever.
    """
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        bm25_encoder = BM25Encoder().default()
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("searchai")
        retriever = PineconeHybridSearchRetriever(
            embeddings=embedder,
            sparse_encoder=bm25_encoder,
            index=index
        )
        retriever.add_texts([text])
        return str("Embedded text into Pinecone for hybrid search.")
    except Exception as e:
        return str(f"Error in embedder_tool: {e}")

@mcp.tool
def similarity_search_tool(query: str) -> str:
    """
    Perform a hybrid search (semantic + keyword) for the query using PineconeHybridSearchRetriever.
    Returns the most similar documents as a string.
    """
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        bm25_encoder = BM25Encoder().default()
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("searchai")
        retriever = PineconeHybridSearchRetriever(
            embeddings=embedder,
            sparse_encoder=bm25_encoder,
            index=index
        )
        docs = retriever.invoke(query)
        if not docs:
            return str("No similar documents found.")
        return str("\n\n".join(doc.page_content for doc in docs))
    except Exception as e:
        return str(f"Error in similarity_search_tool: {e}")
    
@mcp.tool
def hello_tool(query: str) -> str:
    print(f"[SERVER] hello_tool called with query: {query}")
    return "hello from mcp"

if __name__ == "__main__":
    mcp.run(transport="http")