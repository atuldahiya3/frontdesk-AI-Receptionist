import asyncio
from livekit.agents import JobContext, WorkerOptions, cli

async def entrypoint(ctx: JobContext):
    print("Starting Salon X Agent...")
    await ctx.connect()
    print("Connected to room:", ctx.room)
    print("Hello, this is Salon X.")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))