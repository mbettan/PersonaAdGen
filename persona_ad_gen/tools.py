# bettan_agent/tools.py

from typing import Dict, List, Optional, Any
import base64
import io
import os
import time
import asyncio
from pathlib import Path

from google.adk.tools import ToolContext
from .models import PersonaDrivenAdBrief, VideoAdBrief
from .sub_agents.headline_agent import generate_headlines_from_brief
import google.genai as genai
from google.cloud import storage
from google.genai.types import (
    GenerateContentConfig, Part, Image, 
    GenerateVideosSource, GenerateVideosConfig, 
    Modality, GenerateImagesConfig
)

# Models and their specific regions
# imagen-4.0-generate-001 is stable in us-central1
#EDIT_MODEL = "gemini-3.1-flash-image-preview"
EDIT_MODEL = "gemini-3-pro-image-preview"
#VIDEO_MODEL = "veo-3.1-fast-generate-001"
VIDEO_MODEL = "veo-3.1-generate-001"
VIDEO_REGION = "us-central1"
DEFAULT_REGION = "global"
MEDIA_REGION = "global"
# GCS Bucket for video output and chaining
DEFAULT_OUTPUT_BUCKET = os.environ.get("ADK_GCS_BUCKET_NAME", "your-bucket-name")
DEFAULT_OUTPUT_GCS_URI = f"gs://{DEFAULT_OUTPUT_BUCKET}/persona_ads/"

def get_genai_client(location: Optional[str] = None):
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    env_location = os.environ.get("GOOGLE_CLOUD_LOCATION", DEFAULT_REGION)
    final_location = location or env_location
    
    return genai.Client(
        vertexai=True,
        project=project_id,
        location=final_location
    )

def confirm_and_save_persona_brief(
    ideal_customer: str, core_message: str, tone_of_voice: str, 
    headlines: str, location: str, 
    demographics: str, interests: str, tool_context: ToolContext
) -> str:
    """Confirms the persona-driven brief and saves it to the session state."""
    headlines_list = [h.strip() for h in headlines.split('\n') if h.strip()]
    brief = PersonaDrivenAdBrief(
        ideal_customer=ideal_customer, 
        core_message=core_message, 
        tone_of_voice=tone_of_voice,
        headlines=headlines_list, 
        location=location, 
        demographics=demographics, 
        interests=interests
    )
    tool_context.state["confirmed_brief"] = brief.model_dump()
    
    base_image_status = "Received." if "base_image_filename" in tool_context.state else "Not yet provided."
    return f"Perfect! Brief saved. Base Image: {base_image_status}"

def confirm_and_save_brief(
    brand: str, product: str, target_location: str, target_age: str,
    target_gender: str, target_interests: str, tool_context: ToolContext
) -> str:
    """Legacy confirm function."""
    brief = VideoAdBrief(
        brand=brand, product=product, target_location=target_location,
        target_age=target_age, target_gender=target_gender, target_interests=target_interests
    )
    tool_context.state["confirmed_brief"] = brief.model_dump()
    return "Brief saved."

async def save_image_as_artifact(tool_context: ToolContext) -> Dict[str, str]:
    """Saves the user-provided image as an artifact."""
    try:
        parts = []
        if hasattr(tool_context, 'user_content') and hasattr(tool_context.user_content, 'parts'):
            parts = tool_context.user_content.parts
        elif hasattr(tool_context, 'history'):
            for item in reversed(tool_context.history[-3:]):
                if hasattr(item, 'parts'):
                    parts.extend(item.parts)
        
        for part in parts:
            mime = getattr(part, 'mime_type', None) or (part.inline_data.mime_type if hasattr(part, 'inline_data') else None)
            if mime and 'image' in str(mime):
                ext = str(mime).split("/")[-1] if "/" in str(mime) else "png"
                name = f"user:base_image.{ext}"
                await tool_context.save_artifact(filename=name, artifact=part)
                tool_context.state["base_image_filename"] = name
                return {"status": "success", "message": "Saved image."}
        return {"status": "error", "message": "No image found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def edit_scene_image(
    tool_context: ToolContext, edit_prompt: str, output_filename: str,
    reference_image_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Applies a text-based edit to an image using Gemini 3.1 Flash Image.
    Uses reference_image_filename if provided, otherwise falls back to base_image_filename.
    """
    try:
        # Determine the anchor image
        if reference_image_filename:
            anchor_image_filename = reference_image_filename
            print(f"🔗 Using sequential reference image: {anchor_image_filename}")
        elif "base_image_filename" in tool_context.state:
            anchor_image_filename = tool_context.state["base_image_filename"]
            print(f"⚓ Using base anchor image: {anchor_image_filename}")
        else:
            print("⚠️ No reference or base image found. Falling back to default.")
            anchor_image_filename = "user:base_image.png"
        
        # Load the anchor image artifact
        anchor_image_part = await tool_context.load_artifact(filename=anchor_image_filename)
        
        # RESILIENCE: Auto-discovery if specific artifact is missing
        if not anchor_image_part:
            print(f"🔍 Artifact '{anchor_image_filename}' not found. Attempting auto-discovery...")
            # 1. Try input_file_0.png as a standard adk fallback
            anchor_image_part = await tool_context.load_artifact(filename="input_file_0.png")
            
            # 2. Scan user_content and history for any image part
            if not anchor_image_part:
                parts = []
                if hasattr(tool_context, 'user_content') and hasattr(tool_context.user_content, 'parts'):
                    parts = tool_context.user_content.parts
                elif hasattr(tool_context, 'history'):
                    # Walk backwards through history to find the most recent image
                    for item in reversed(tool_context.history):
                        if hasattr(item, 'parts'):
                            parts.extend(item.parts)
                
                for part in parts:
                    if not part:
                        continue
                        
                    # Safely check for mime type across all possible part structures
                    mime = getattr(part, 'mime_type', None)
                    if not mime:
                        inline_data = getattr(part, 'inline_data', None)
                        if inline_data:
                            mime = getattr(inline_data, 'mime_type', None)
                    if not mime:
                        file_data = getattr(part, 'file_data', None)
                        if file_data:
                            mime = getattr(file_data, 'mime_type', None)
                        
                    if mime and 'image' in str(mime):
                        anchor_image_part = part
                        print(f"✨ Auto-discovered image part with mime '{mime}'.")
                        # Proactively save it for future stability if not already set
                        if "base_image_filename" not in tool_context.state:
                            await tool_context.save_artifact(filename="user:base_image.png", artifact=part)
                            tool_context.state["base_image_filename"] = "user:base_image.png"
                        break

        if not anchor_image_part:
            raise Exception(f"Failed to load or discover anchor image artifact. Please ensure an image is uploaded.")

        client = get_genai_client(location=MEDIA_REGION)
        
        # Hardcoded 'No Text' policy to ensure reliability regardless of agent instruction
        no_text_instruction = "IMPORTANT: Ensure there is absolutely NO text, writing, subtitles, or graphic overlays in the generated image. The output must be purely visual."
        
        # Multimodal request to Gemini
        response = client.models.generate_content(
            model=EDIT_MODEL,
            contents=[
                anchor_image_part,
                Part(text=f"Modify this image based on the following scene description: {edit_prompt}. {no_text_instruction} Ensure visual continuity with the character and environment in the provided image.")
            ],
            config=GenerateContentConfig(
                response_modalities=[Modality.TEXT, Modality.IMAGE],
                temperature=0.7
            )
        )
        
        generated_image_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and "image" in part.inline_data.mime_type:
                generated_image_part = part
                break
        
        if not generated_image_part:
            raise Exception("Gemini returned a response but no image part was found.")

        # Save the result
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / output_filename
        
        # Save locally
        with open(output_path, "wb") as f:
            f.write(generated_image_part.inline_data.data)
            
        # Save as artifact
        await tool_context.save_artifact(filename=output_filename, artifact=generated_image_part)
            
        print(f"✅ Saved reference-based scene to {output_path}")
        
        # Automatically trigger video generation (Image-to-Video)
        try:
             video_filename = output_filename.replace(".png", ".mp4")
             await generate_video_ad(tool_context, edit_prompt, video_filename, image_bytes=generated_image_part.inline_data.data)
        except Exception as ve:
             print(f"⚠️ Video generation trigger failed for {video_filename}: {ve}")

        return {
            "status": "success",
            "image_filename": output_filename,
            "local_path": str(output_path.absolute())
        }

    except Exception as e:
        print(f"❌ Error during reference-based image generation: {e}")
        return {"status": "error", "message": str(e)}

async def generate_video_ad(
    ctx: ToolContext, prompt: str, output_filename: str, 
    image_bytes: Optional[bytes] = None,
    reference_video_uri: Optional[str] = None
) -> str:
    """
    Generates or extends a video using Veo 3.1 in us-central1.
    - If reference_video_uri is provided, it performs 'Video Extension' (exactly 7s).
    - If image_bytes are provided, it performs 'Image-to-Video' (8s).
    - Otherwise, it performs 'Text-to-Video' (8s).
    - Outputs are stored in GCS to facilitate chaining.
    """
    client = get_genai_client(location=VIDEO_REGION)
    
    is_extension = bool(reference_video_uri or ctx.state.get("latest_video_uri"))
    
    # Logic for extension chaining
    active_ref_uri = reference_video_uri or ctx.state.get("latest_video_uri")
    
    gen_type = "Video-Extension" if is_extension else ("Image-to-Video" if image_bytes else "Text-to-Video")
    
    # Enforce NO TEXT rule in video prompts
    no_text_instruction = " Ensure there is NO text, writing, subtitles, or graphic overlays in the video. The output must be purely visual."
    final_prompt = prompt + no_text_instruction
    
    print(f"🎬 Generating {gen_type} creative: {output_filename} via {VIDEO_MODEL}...")
    
    source_args = {"prompt": final_prompt}
    if is_extension:
        source_args["video"] = genai.types.Video(uri=active_ref_uri, mime_type="video/mp4")
    elif image_bytes:
        source_args["image"] = Image(image_bytes=image_bytes, mime_type="image/png")

    # Extension requires exactly 7 seconds per docs. Initial can be 8.
    duration = 7 if is_extension else 8
    
    # Ensure unique GCS folder for this ad sequence to avoid collisions
    session_id = ctx.state.get("session_id", "default")
    gcs_uri = f"{DEFAULT_OUTPUT_GCS_URI}{session_id}/"

    operation = client.models.generate_videos(
        model=VIDEO_MODEL,
        source=GenerateVideosSource(**source_args),
        config=GenerateVideosConfig(
            duration_seconds=duration, 
            resolution="720p",
            output_gcs_uri=gcs_uri
        )
    )
    
    print(f"   Operation ID: {operation.name}")
    
    # Poll for completion
    while not operation.done:
        await asyncio.sleep(20)
        operation = client.operations.get(operation)
    
    if operation.error:
        raise Exception(f"Video generation failed: {operation.error}")
        
    if not operation.result or not operation.result.generated_videos:
        raise Exception("No video generated in the final response.")
        
    video = operation.result.generated_videos[0].video
    
    # Store the URI for next extension
    if video.uri:
        ctx.state["latest_video_uri"] = video.uri
        print(f"🔗 Chaining URI stored: {video.uri}")

    # Save the video bytes locally for immediate inspection
    if video.video_bytes:
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        final_path = output_dir / output_filename
        with open(final_path, "wb") as f:
            f.write(video.video_bytes)
        print(f"✅ Video artifact persisted locally to: {final_path}")
        return str(final_path.absolute())
    
    # If no bytes returned, download from GCS
    if video.uri:
        try:
            print(f"📥 Downloading video from GCS: {video.uri}...")
            storage_client = storage.Client()
            path_parts = video.uri.replace("gs://", "").split("/", 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            final_path = output_dir / output_filename
            blob.download_to_filename(final_path)
            
            print(f"✅ Video artifact downloaded and persisted locally to: {final_path}")
            return str(final_path.absolute())
        except Exception as de:
            print(f"⚠️ GCS download failed for {video.uri}: {de}")
            return video.uri

    raise Exception(f"Video generation succeeded but both 'video_bytes' and 'uri' are empty for {output_filename}.")

async def generate_headlines(tool_context: ToolContext) -> str:
    """Generates headlines using global model for optimal reasoning."""
    print("🎯 Initiating headline generation...")
    return await generate_headlines_from_brief(tool_context)

async def create_persona_brief_without_headlines(
    ideal_customer: str, core_message: str, tone_of_voice: str, 
    location: str, demographics: str, interests: str, tool_context: ToolContext
) -> str:
    """Orchestrates brief creation and subsequent headline generation."""
    brief = PersonaDrivenAdBrief(
        ideal_customer=ideal_customer, 
        core_message=core_message, 
        tone_of_voice=tone_of_voice,
        headlines=[], 
        location=location, 
        demographics=demographics, 
        interests=interests
    )
    tool_context.state["confirmed_brief"] = brief.model_dump()
    return await generate_headlines(tool_context)
