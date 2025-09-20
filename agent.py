import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, Agent
from livekit.agents.llm import function_tool, ChatContext
from livekit.plugins import openai
from db import load_kb, create_help_request, add_to_kb, resolve_request

load_dotenv(dotenv_path=Path(__file__).parent / '.env.local')

class SalonAssistant(Agent):
    def __init__(self):
        kb = load_kb()
        instructions = f"""You are a helpful AI receptionist for Salon X, a fake hair salon.
Your knowledge is strictly limited to:
{kb}

Be friendly and concise. Respond only based on this knowledge.
If the user's question is not directly covered, use the escalate_to_supervisor tool with the exact question.
Do not say you don't know without using the tool."""

        llm = openai.LLM(model="llama3.1:8b").with_ollama(base_url="http://localhost:11434/v1")

        super().__init__(
            instructions=instructions,
            llm=llm,
            chat_ctx=ChatContext(),
            tools=[self.escalate_to_supervisor],
            stt=None,
            tts=None,
            vad=None,
            allow_interruptions=True
        )
        self.pending_requests = {}
        print("SalonAssistant initialized with tools:", [tool.__name__ for tool in self.tools])

    @function_tool
    async def escalate_to_supervisor(self, question: str, session_id: str = None) -> str:
        try:
            if session_id:
                self.pending_requests[session_id] = {
                    "question": question,
                    "timestamp": datetime.now(),
                    "timeout": timedelta(minutes=30)
                }
            request_id = create_help_request(question, session_id or "simulated_caller")
            print(f"Triggered help request #{request_id} for question: '{question}'")
            print(f"Simulated message to supervisor: Hey, I need help answering '{question}'.")
            return "Let me check with my supervisor and get back to you soon."
        except Exception as e:
            print(f"Error escalating: {e}")
            return "I'm having trouble right now, please try again later."

    async def process_input(self, text: str, session_id: str = "simulated_caller"):
        print(f"Received input: {text} (session_id: {session_id})")
        kb = load_kb()
        lines = kb.split('\n')
        kb_pairs = []
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('Q:'):
                question = lines[i].strip()[2:].strip()
                i += 1
                if i < len(lines) and lines[i].strip().startswith('A:'):
                    answer = lines[i].strip()[2:].strip()
                    kb_pairs.append((question, answer))
                    i += 1
                else:
                    i += 1
            else:
                i += 1
        text_lower = text.lower()
        for q, a in kb_pairs:
            if text_lower == q.lower():
                print(f"Answer: {a}")
                return
        response = await self.escalate_to_supervisor(text, session_id)
        print(response)

async def entrypoint(ctx: JobContext):
    required_env_vars = ["LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "LIVEKIT_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        return
    max_retries = 3
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            async with openai.LLM(model="llama3.1:8b").with_ollama(base_url="http://localhost:11434/v1") as llm:
                print("✓ Ollama LLM connection verified")
                break
        except Exception as e:
            print(f"✗ Ollama LLM connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print("Fatal: Could not connect to Ollama.")
                return
            await asyncio.sleep(retry_delay)
    await ctx.connect()
    print(f"Connected to room: {ctx.room}")
    assistant = SalonAssistant()
    print("Hello, this is Salon X. How can I help you today?")
    while True:
        try:
            user_input = input("Enter your question (or 'quit' to exit): ")
            if user_input.lower() == 'quit':
                break
            await assistant.process_input(user_input)
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    print("Starting Salon X Agent...")
    print("Make sure Ollama is running: ollama serve")
    print("And the model is available: ollama pull llama3.1:8b")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))