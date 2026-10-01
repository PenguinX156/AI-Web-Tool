from browser_use import Agent
from langchain_openai import ChatOpenAI
import asyncio

async def main():
    # Since we are using Ollama, we can use ChatOpenAI with a custom base URL if Nanobot/Ollama supports OpenAI API
    # Or use a dedicated Ollama provider if available in langchain
    # For now, let's just check if the package imports correctly and the Agent can be initialized.
    print("Browser-use package imported successfully.")
    # agent = Agent(task="Search for the latest news on Ollama", llm=ChatOpenAI(model="gpt-4o"))
    # await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
