import asyncio
import os
import sys
import dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.file_artifact_service import FileArtifactService
from google.genai import types

# Load environment variables
dotenv.load_dotenv()

async def run_e2e_test(image_path: str):
    # Import the agent
    from persona_ad_gen import root_agent
    
    # Setup runner
    session_service = InMemorySessionService()
    # FileArtifactService expects root_dir
    artifact_service = FileArtifactService(root_dir=".adk/artifacts")
    runner = Runner(
        agent=root_agent,
        app_name="persona_ad_gen_test",
        session_service=session_service,
        artifact_service=artifact_service
    )
    
    user_id = "test_user"
    session_id = "test_session_2"
    
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
        "Conquer any trail with our durable, high-performance gear design for the wild.",
        "Inspiring and adventurous",
        # Next message will include the image
    ]
    
    print("🚀 Starting Persona Ad Gen End-to-End Test...")
    
    for i, msg in enumerate(messages):
        print(f"\n👤 User: {msg}")
        user_message = types.Content(role="user", parts=[types.Part(text=msg)])
        
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
            if event.is_final_response() and event.content:
                print(f"🤖 Agent: {event.content.parts[0].text[:200]}...")

    # Now upload the image
    print(f"\n📸 Uploading image from: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # Determine mime type from extension
    extension = image_path.split(".")[-1].lower()
    mime_type = f"image/{extension if extension != 'jpg' else 'jpeg'}"
    
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    user_message = types.Content(role="user", parts=[image_part])
    
    print("🤖 Agent (processing image)...")
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
            print(f"🤖 Agent: {event.content.parts[0].text[:200]}...")

    # Final inputs
    final_inputs = "New York and San Francisco, 25-45 both genders, interested in high-tech fitness and busy lifestyles"
    print(f"\n👤 User: {final_inputs}")
    user_message = types.Content(role="user", parts=[types.Part(text=final_inputs)])
    
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
            print(f"🤖 Agent: {event.content.parts[0].text[:200]}...")

    # Final confirmation to generate scenes
    print("\n👤 User: Yes, please generate the advertising scenes.")
    user_message = types.Content(role="user", parts=[types.Part(text="Yes, please generate the advertising scenes.")])
    
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_message):
        if event.is_final_response() and event.content:
            print(f"🤖 Agent: {event.content.parts[0].text[:200]}...")
            
    print("\n✅ Test sequence complete. Check the artifacts/ directory for generated scenes.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_persona_test.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image path '{image_path}' does not exist.")
        sys.exit(1)
        
    asyncio.run(run_e2e_test(image_path))
