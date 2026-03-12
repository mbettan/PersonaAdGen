# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import pathlib
import dotenv
import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from persona_ad_gen import PersonaAdGenAgent

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_agent_introduction():
    """Test that the agent provides its correct introduction."""
    agent = PersonaAdGenAgent()
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service
    )
    session = await session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )

    user_message = types.Content(role="user", parts=[types.Part(text="hello")])
    
    response_text = ""
    async for event in runner.run_async(user_id="test_user", session_id="test_session", new_message=user_message):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            break

    # The expected introduction from the agent's instructions.
    expected_introduction = (
        "Great ads connect with a real person by solving a real problem. "
        "Instead of just filling out a form, we're going to build your ad's story step-by-step. "
        "First, let's get to know your ideal customer."
    )

    assert response_text is not None, "Agent response format is not as expected."
    assert response_text.strip().startswith(expected_introduction.strip())
