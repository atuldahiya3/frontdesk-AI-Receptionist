import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, Agent
from livekit.agents.llm import function_tool, ChatContext
from livekit.plugins import openai
from db import load_kb, create_help_request, add_to_kb, resolve_request, update_request_status_by_question
import difflib

load_dotenv(dotenv_path=Path(__file__).parent / '.env.local')

class SalonAssistant(Agent):
    def __init__(self):
        kb = load_kb()
        instructions = f"""You are a helpful AI receptionist for Salon X, a fake hair salon.
Your knowledge is strictly limited to:
{kb}

Be friendly and concise. Respond only based on this knowledge.
If the user's question is not directly covered (do not infer or hallucinate), you MUST use the escalate_to_supervisor tool with the exact question.
Do not say you don't know without using the tool.
After escalation, tell the user you'll follow up soon and keep the session active for follow-up."""

        llm = openai.LLM(model="llama3.1:8b").with_ollama(base_url="http://localhost:11434/v1")

        super().__init__(
            instructions=instructions,
            llm=llm,
            chat_ctx=ChatContext(),
            tools=[],
            stt=None,
            tts=None,
            vad=None,
            allow_interruptions=True
        )
        # Add tool only if not already present
        if not any(tool.__name__ == 'escalate_to_supervisor' for tool in self.tools):
            self.tools.append(self.escalate_to_supervisor)
        self.pending_requests = {}
        print("SalonAssistant initialized with tools:", [tool.__name__ for tool in self.tools])
        asyncio.create_task(self.check_timeouts())

    @function_tool
    async def escalate_to_supervisor(self, question: str, session_id: str = None) -> str:
        """Escalate a question to the supervisor when the agent cannot answer."""
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

    async def handle_supervisor_response(self, request_id: str, answer: str, session_id: str):
        """Handle supervisor's response and follow up with the customer."""
        try:
            if session_id and session_id in self.pending_requests:
                print(f"Following up with session {session_id}: {answer}")
                print(f"Hi, I got an answer to your question: {answer}")
                add_to_kb(self.pending_requests[session_id]["question"], answer)
                resolve_request(int(request_id), answer, self.pending_requests[session_id]["question"])
                del self.pending_requests[session_id]
            else:
                print(f"No session found for request_id {request_id}")
        except Exception as e:
            print(f"Error handling supervisor response: {e}")

    async def check_timeouts(self):
        """Periodically check for timed-out requests."""
        while True:
            current_time = datetime.now()
            for session_id, data in list(self.pending_requests.items()):
                if current_time - data["timestamp"] > data["timeout"]:
                    print(f"Request for session {session_id} timed out: {data['question']}")
                    update_request_status_by_question(data["question"], "Unresolved")
                    del self.pending_requests[session_id]
                    print("Sorry, I couldn't get an answer in time. Please try again later.")
            await asyncio.sleep(60)

    async def simulate_supervisor_response(self, request_id: str, session_id: str):
        """Simulate a supervisor response for testing."""
        answer = input(f"Enter supervisor response for request #{request_id}: ")
        await self.handle_supervisor_response(request_id, answer, session_id)

    async def process_input(self, text: str, session_id: str = "simulated_caller"):
        """Process user text input with improved matching."""
        print(f"Received input: {text} (session_id: {session_id})")
        kb = load_kb()
        # Parse KB
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
        print(f"DEBUG: Parsed KB pairs: {len(kb_pairs)}")
        # Exact and near-exact matching
        text_lower = text.lower()
        matched = False
        for q, a in kb_pairs:
            q_lower = q.lower()
            # Exact match
            if text_lower == q_lower:
                print(f"Answer (exact match): {a}")
                matched = True
                break
            # Near-exact match using difflib (80% similarity threshold)
            similarity = difflib.SequenceMatcher(None, text_lower, q_lower).ratio()
            if similarity > 0.8:
                print(f"Answer (near-exact match, similarity {similarity:.2f}): {a}")
                matched = True
                break
        # Fuzzy keyword matching if no exact/near-exact match
        if not matched:
            for q, a in kb_pairs:
                q_lower = q.lower()
                if any(word in text_lower for word in ['hours', 'timings', 'open', 'close', 'time']):
                    if any(word in q_lower for word in ['hours', 'timings', 'open', 'close', 'time']):
                        print(f"Answer (keyword match): {a}")
                        matched = True
                        break
                elif any(word in text_lower for word in ['service', 'offer']):
                    if any(word in q_lower for word in ['service', 'offer']):
                        print(f"Answer (keyword match): {a}")
                        matched = True
                        break
                elif any(word in text_lower for word in ['haircut', 'cut', 'price']):
                    if any(word in q_lower for word in ['haircut', 'cut', 'price']):
                        print(f"Answer (keyword match): {a}")
                        matched = True
                        break
                elif any(word in text_lower for word in ['walk', 'in', 'appointment']):
                    if any(word in q_lower for word in ['walk', 'in', 'appointment']):
                        print(f"Answer (keyword match): {a}")
                        matched = True
                        break
        if not matched:
            response = await self.escalate_to_supervisor(text, session_id)
            print(response)

async def entrypoint(ctx: JobContext):
    # Validate environment variables
    required_env_vars = ["LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "LIVEKIT_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Ensure these are set in .env.local or your environment.")
        return

    # Test Ollama connection with retries
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
                print("Fatal: Could not connect to Ollama. Ensure 'ollama serve' is running and 'llama3.1:8b' is pulled.")
                return
            print(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

    await ctx.connect()
    print(f"Connected to room: {ctx.room}")
    assistant = SalonAssistant()
    print("Hello, this is Salon X. How can I help you today?")
    # Manual input loop for text-based interaction
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