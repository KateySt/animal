import asyncio
import ssl
import sys
from contextlib import AsyncExitStack
from uuid import UUID

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from livekit.agents import (
    Agent,
    AgentSession,
    ConversationItemAddedEvent,
    FunctionToolsExecutedEvent,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
)
from livekit.agents.utils import http_context as lk_http_context
from livekit.agents.voice.room_io import TextInputEvent
from livekit.plugins import anthropic as lk_anthropic
from livekit.plugins import deepgram as lk_deepgram
from livekit.plugins import elevenlabs as lk_elevenlabs
from livekit.plugins import silero as lk_silero

from app.core.config import get_anthropic_config, get_livekit_config, get_speech_config
from app.core.prompts import SYSTEM_PROMPT
from app.db.session import get_session_factory
from app.livekit_worker.db import worker_db_engine
from app.livekit_worker.dependencies import get_chat_session_service
from app.livekit_worker.persistence import (
    ConversationPersistenceWorker,
    _conversation_item_to_row,
    _function_tools_executed_to_rows,
    hydrate_chat_context,
)
from app.livekit_worker.tools import build_invoices_function_tool, build_web_search_function_tool


async def entrypoint(ctx: JobContext):
    session_id = UUID(ctx.job.metadata)
    await ctx.connect()
    shutdown_event = asyncio.Event()

    async def on_shutdown(_: str):
        shutdown_event.set()

    ctx.add_shutdown_callback(on_shutdown)

    async with AsyncExitStack() as stack:
        engine = await stack.enter_async_context(worker_db_engine())
        session_factory = get_session_factory(engine)

        db_session = await stack.enter_async_context(session_factory())
        persistence_db_session = await stack.enter_async_context(session_factory())

        session_service = get_chat_session_service(db_session)
        persistence_service = get_chat_session_service(persistence_db_session)

        chat_session = await session_service.get_session_with_user(session_id)
        user = chat_session.user

        chat_ctx = await hydrate_chat_context(session_service, chat_session)
        agent = Agent(
            instructions=SYSTEM_PROMPT,
            chat_ctx=chat_ctx,
            tools=[build_invoices_function_tool(db_session, user), build_web_search_function_tool()],
        )

        anthropic_config = get_anthropic_config()
        speech_config = get_speech_config()

        agent_session = AgentSession(
            stt=lk_deepgram.STT(
                model=speech_config.DEEPGRAM_MODEL,
                api_key=speech_config.DEEPGRAM_API_KEY
            ),
            llm=lk_anthropic.LLM(
                model=anthropic_config.ANTHROPIC_MODEL,
                api_key=anthropic_config.ANTHROPIC_API_KEY,
                max_tokens=anthropic_config.ANTHROPIC_MAX_TOKEN,
            ),
            tts=lk_elevenlabs.TTS(
                voice_id=speech_config.ELEVENLABS_VOICE_ID,
                model=speech_config.ELEVENLABS_MODEL,
                api_key=speech_config.ELEVENLABS_API_KEY,
            ),
            vad=ctx.proc.userdata["vad"]
        )

        worker = ConversationPersistenceWorker(persistence_service, session_id)

        @agent_session.on("conversation_item_added")
        def on_conversation_item_added(event: ConversationItemAddedEvent) -> None:
            row = _conversation_item_to_row(event.item)
            if row is not None:
                worker.enqueue(row)

        @agent_session.on("function_tools_executed")
        def on_function_tools_executed(event: FunctionToolsExecutedEvent) -> None:
            for row in _function_tools_executed_to_rows(event):
                worker.enqueue(row)

        stack.push_async_callback(worker.aclose)

        await agent_session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                text_enabled=True,
                audio_enabled=True,
                text_input_cb=text_only_reply_cb
            ),
            room_output_options=RoomOutputOptions(transcription_enabled=True, audio_enabled=True),
        )

        await shutdown_event.wait()

# to answer text only
async def text_only_reply_cb(session: AgentSession, ev: TextInputEvent) -> None:
    async with session._claim_user_turn():
        session.output.set_audio_enabled(False)
        try:
            await session.generate_reply(user_input=ev.text)
        finally:
            session.output.set_audio_enabled(True)


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = lk_silero.VAD.load()
    ssl_context = ssl.create_default_context()
    lk_http_context._create_ssl_context = lambda: ssl_context


def main() -> None:
    config = get_livekit_config()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name=config.LIVEKIT_AGENT_NAME,
            ws_url=config.LIVEKIT_URL,
            api_key=config.LIVEKIT_API_KEY,
            api_secret=config.LIVEKIT_API_SECRET,
        )
    )


if __name__ == "__main__":
    main()
