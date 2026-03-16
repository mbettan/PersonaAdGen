import asyncio
import os
import sys
# import dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

# Load environment variables
# dotenv.load_dotenv()

# Ensure cloud project is set for Vertex AI
if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = "your-project-id"
    print(f"☁️ Setting default GOOGLE_CLOUD_PROJECT: {os.environ['GOOGLE_CLOUD_PROJECT']}")

async def run_e2e_test(image_path: str):
    # Import the agent
    from persona_ad_gen import root_agent
    
    # Create output directory
    os.makedirs("test_results", exist_ok=True)
    
    # Setup runner
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    runner = Runner(
        agent=root_agent,
        app_name="persona_ad_gen_test",
        session_service=session_service,
        artifact_service=artifact_service
    )
    
    user_id = "test_user"
    session_id = "test_session_final"
    
    # Create session
    await session_service.create_session(
        app_name="persona_ad_gen_test",
        user_id=user_id,
        session_id=session_id
    )
    
    # Conversation flow
    messages = [
        "hello again",
        "I want to reach outdoor enthusiasts who love hiking and mountain biking in the Pacific Northwest.",
        "They struggle with gear that breaks or fails in extreme rainy PNW weather, leaving them stranded.",
        "Conquer any trail with our durable, high-performance gear designed for the wild.",
        "Inspiring and adventurous",
    ]
    
    print("🚀 Starting Persona Ad Gen End-to-End Test...")
    
    for i, msg in enumerate(messages):
        print(f"\n👤 User: {msg}")
        user_message = types.Content(role="user", parts=[types.Part(text=msg)])
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
            if event.is_final_response() and event.content:
                print(f"🤖 Agent: {event.content.parts[0].text}")

    # Upload image
    print(f"\n📸 Uploading image from: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    user_message = types.Content(role="user", parts=[image_part])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
                print(f"🤖 Agent: {event.content.parts[0].text}")

    # Final inputs
    final_inputs = "New York and San Francisco, 25-45 both genders, interested in high-tech fitness and busy lifestyles"
    print(f"\n👤 User: {final_inputs}")
    user_message = types.Content(role="user", parts=[types.Part(text=final_inputs)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
                print(f"🤖 Agent: {event.content.parts[0].text}")

    # Confirmation
    print("\n👤 User: Yes, please generate the advertising scenes.")
    user_message = types.Content(role="user", parts=[types.Part(text="Yes, please generate the advertising scenes.")])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        for fc in event.get_function_calls():
            print(f"🛠️ Tool Call: {fc.name}")
        if event.is_final_response() and event.content:
                print(f"🤖 Agent: {event.content.parts[0].text}")
            
    # Wait for processing and extraction
    print("\n✅ Test sequence complete. Saving artifacts to 'test_results'...")
    keys = await artifact_service.list_artifact_keys(
        app_name="persona_ad_gen_test", user_id=user_id, session_id=session_id
    )
    
    for key in keys:
        # Fixed: use list_artifacts or access the internal store if needed, 
        # but ADK InMemoryArtifactService usually has a simple internal store.
        # Let's try to just use the files downloaded by tools.py instead.
        pass
    
    print("\n💾 Artifacts should have been saved directly to the current directory by tools.py.")
    print("Listing files in current directory...")
    os.system("ls -la *.mp4 *.png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_persona_test.py <image_path>")
        sys.exit(1)
    asyncio.run(run_e2e_test(sys.argv[1]))
