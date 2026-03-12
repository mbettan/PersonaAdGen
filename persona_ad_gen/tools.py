# bettan_agent/tools.py

from typing import Dict
import base64
import io
import os

from google.adk.tools import ToolContext
from .models import PersonaDrivenAdBrief, VideoAdBrief
from .sub_agents.headline_agent import generate_headlines_from_brief
import google.genai as genai
from google.genai.types import GenerateContentConfig, Part

# Use the image generation model with Google Gen AI SDK
EDIT_MODEL = "gemini-3.1-flash-image-preview"

def confirm_and_save_persona_brief(
    ideal_customer: str, core_message: str, tone_of_voice: str, 
    headlines: str, location: str, 
    demographics: str, interests: str, tool_context: ToolContext
) -> str:
    """Confirms the persona-driven brief and saves it to the session state."""
    # Parse headlines from string to list
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
    
    base_image_status = "Not yet provided."
    if "base_image_filename" in tool_context.state:
        base_image_status = f"Received ({tool_context.state['base_image_filename']})."

    confirmation_message = (
        "Perfect! Here's your complete ad story:\n\n"
        f"**The Ideal Customer:** {ideal_customer}\n\n"
        f"**The 'Aha!' Moment:** {core_message}\n\n"
        f"**Tone of Voice:** {tone_of_voice}\n\n"
        f"**Headlines ({len(headlines_list)}):**\n" +
        '\n'.join([f"• {h}" for h in headlines_list]) + "\n\n"
        f"**Location:** {location}\n"
        f"**Demographics:** {demographics}\n"
        f"**Interests:** {interests}\n\n"
        f"**Base Image:** {base_image_status}\n\n"
        "Does this capture your vision? If yes, I'll create 4 compelling advertising scenes based on this story!"
    )
    return confirmation_message

def confirm_and_save_brief(
    brand: str, product: str, target_location: str, target_age: str,
    target_gender: str, target_interests: str, tool_context: ToolContext
) -> str:
    """Legacy function - Confirms the brief and saves it to the session state."""
    brief = VideoAdBrief(
        brand=brand, product=product, target_location=target_location,
        target_age=target_age, target_gender=target_gender,
        target_interests=target_interests
    )
    tool_context.state["confirmed_brief"] = brief.model_dump()
    
    base_image_status = "Not yet provided."
    if "base_image_filename" in tool_context.state:
        base_image_status = f"Received ({tool_context.state['base_image_filename']})."

    confirmation_message = (
        "OK, I've got the following information:\n\n"
        f"Brand: {brand}\n"
        f"Product: {product}\n"
        f"Target Location: {target_location}\n"
        f"Target Age: {target_age}\n"
        f"Target Gender: {target_gender}\n"
        f"Target Interests: {target_interests}\n"
        f"Base Image: {base_image_status}\n\n"
        "Is that all correct?"
    )
    return confirmation_message

async def save_image_as_artifact(tool_context: ToolContext) -> Dict[str, str]:
    """
    Saves the user-provided image as a user-scoped artifact and
    stores its filename in the session state.
    """
    import json
    
    try:
        print("🔍 Starting image search in tool_context...")
        print(f"Tool context type: {type(tool_context)}")
        print(f"Tool context attributes: {[attr for attr in dir(tool_context) if not attr.startswith('_')][:20]}")
        
        # Method 1: Check user_content (this is where ADK stores user input including images)
        if hasattr(tool_context, 'user_content') and tool_context.user_content:
            print(f"User content type: {type(tool_context.user_content)}")
            
            # If user_content has parts attribute
            if hasattr(tool_context.user_content, 'parts'):
                print(f"Found user_content.parts with {len(tool_context.user_content.parts)} parts")
                for i, part in enumerate(tool_context.user_content.parts):
                    print(f"  Part {i}: type={type(part)}, has_mime_type={hasattr(part, 'mime_type')}")
                    
                    # Check for inline_data which might contain the image
                    if hasattr(part, 'inline_data'):
                        print(f"    Part {i} has inline_data")
                        if hasattr(part.inline_data, 'mime_type'):
                            print(f"    inline_data.mime_type: {part.inline_data.mime_type}")
                            if 'image' in str(part.inline_data.mime_type):
                                print(f"    ✅ Found image in part {i} inline_data!")
                                extension = str(part.inline_data.mime_type).split("/")[-1] if "/" in str(part.inline_data.mime_type) else "png"
                                artifact_filename = f"user:base_image.{extension}"
                                
                                # Save the part (which contains inline_data) as an artifact
                                await tool_context.save_artifact(filename=artifact_filename, artifact=part)
                                
                                tool_context.state["base_image_filename"] = artifact_filename
                                
                                print(f"✅ Saved uploaded image as artifact '{artifact_filename}'")
                                return {"status": "success", "message": "I've saved your image. Let's continue with the brief."}
                    
                    # Check for direct mime_type
                    if hasattr(part, 'mime_type'):
                        print(f"    mime_type: {part.mime_type}")
                        if part.mime_type and 'image' in str(part.mime_type):
                            print(f"    ✅ Found image in part {i}!")
                            extension = str(part.mime_type).split("/")[-1] if "/" in str(part.mime_type) else "png"
                            artifact_filename = f"user:base_image.{extension}"
                            
                            # Save the image as an artifact
                            await tool_context.save_artifact(filename=artifact_filename, artifact=part)
                            tool_context.state["base_image_filename"] = artifact_filename
                            
                            print(f"✅ Saved uploaded image as artifact '{artifact_filename}'")
                            return {"status": "success", "message": "I've saved your image. Let's continue with the brief."}
                    
                    # Deep inspection of part attributes
                    print(f"    Part {i} attributes: {[attr for attr in dir(part) if not attr.startswith('_')][:10]}")
            
            # Check if user_content is a Content object with parts
            if hasattr(tool_context.user_content, '__dict__'):
                print(f"User content attributes: {list(tool_context.user_content.__dict__.keys())}")
        
        # Method 2: Fallback to check prompt if user_content doesn't have the image
        if hasattr(tool_context, 'prompt') and tool_context.prompt:
            print(f"Checking prompt as fallback - type: {type(tool_context.prompt)}")
            
            if hasattr(tool_context.prompt, 'parts'):
                for i, part in enumerate(tool_context.prompt.parts):
                    if hasattr(part, 'mime_type') and part.mime_type and 'image' in str(part.mime_type):
                        print(f"    ✅ Found image in prompt part {i}!")
                        extension = str(part.mime_type).split("/")[-1] if "/" in str(part.mime_type) else "png"
                        artifact_filename = f"user:base_image.{extension}"
                        
                        await tool_context.save_artifact(filename=artifact_filename, artifact=part)
                        tool_context.state["base_image_filename"] = artifact_filename
                        
                        print(f"✅ Saved uploaded image as artifact '{artifact_filename}'")
                        return {"status": "success", "message": "I've saved your image. Let's continue with the brief."}
        
        # Method 3: Check for messages/history
        print("⚠️ Could not find image in user_content.parts, checking messages/history...")
        
        if hasattr(tool_context, 'messages'):
            print(f"Found messages attribute with type: {type(tool_context.messages)}")
            if hasattr(tool_context.messages, '__len__'):
                print(f"  Number of messages: {len(tool_context.messages)}")
        
        if hasattr(tool_context, 'history'):
            print(f"Found history attribute with type: {type(tool_context.history)}")
            if hasattr(tool_context.history, '__len__'):
                print(f"  Number of history items: {len(tool_context.history)}")
                for i, item in enumerate(reversed(tool_context.history[-3:])):  # Check last 3 items
                    print(f"  History item {i}: type={type(item)}")
                    if hasattr(item, 'parts'):
                        for j, part in enumerate(item.parts):
                            if hasattr(part, 'mime_type') and part.mime_type and 'image' in str(part.mime_type):
                                print(f"    ✅ Found image in history item {i}, part {j}!")
                                extension = str(part.mime_type).split("/")[-1] if "/" in str(part.mime_type) else "png"
                                artifact_filename = f"user:base_image.{extension}"
                                
                                await tool_context.save_artifact(filename=artifact_filename, artifact=part)
                                tool_context.state["base_image_filename"] = artifact_filename
                                
                                print(f"✅ Saved uploaded image as artifact '{artifact_filename}'")
                                return {"status": "success", "message": "I've saved your image. Let's continue with the brief."}
        
        # Method 3: Check for conversation attribute
        if hasattr(tool_context, 'conversation'):
            print(f"Found conversation attribute with type: {type(tool_context.conversation)}")
        
        # Method 4: Check for current_message
        if hasattr(tool_context, 'current_message'):
            print(f"Found current_message attribute with type: {type(tool_context.current_message)}")
            if hasattr(tool_context.current_message, 'parts'):
                for i, part in enumerate(tool_context.current_message.parts):
                    print(f"  Current message part {i}: type={type(part)}")
                    if hasattr(part, 'mime_type') and part.mime_type and 'image' in str(part.mime_type):
                        print(f"    ✅ Found image in current_message part {i}!")
                        extension = str(part.mime_type).split("/")[-1] if "/" in str(part.mime_type) else "png"
                        artifact_filename = f"user:base_image.{extension}"
                        
                        await tool_context.save_artifact(filename=artifact_filename, artifact=part)
                        tool_context.state["base_image_filename"] = artifact_filename
                        
                        print(f"✅ Saved uploaded image as artifact '{artifact_filename}'")
                        return {"status": "success", "message": "I've saved your image. Let's continue with the brief."}
        
        # Method 5: Try to access the last user input directly
        if hasattr(tool_context, 'last_user_input'):
            print(f"Found last_user_input attribute with type: {type(tool_context.last_user_input)}")
        
        # If we still haven't found the image, print all available attributes for debugging
        print("\n❌ Could not find image. Here are ALL tool_context attributes:")
        for attr in dir(tool_context):
            if not attr.startswith('_'):
                try:
                    value = getattr(tool_context, attr)
                    print(f"  {attr}: {type(value)}")
                except:
                    print(f"  {attr}: <unable to access>")
        
        return {"status": "error", "message": "No valid image data was found. The debug output above shows what was searched. Please check the terminal for details."}
    
    except Exception as e:
        print(f"❌ Error during image saving: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Sorry, I couldn't save the image. Error: {str(e)}"}

async def edit_scene_image(
    base_image_filename: str, edit_prompt: str, output_filename: str, tool_context: ToolContext
) -> Dict[str, str]:
    """
    Loads a base image artifact, applies a text-based edit using Gemini model with image generation,
    and saves the result as a new image artifact.
    """
    try:
        print(f"🎨 Editing image '{base_image_filename}' for scene '{output_filename}'...")
        
        # Load the base image artifact
        # We try to load the provided filename, but also fallback to the base_image_filename in state
        # in case the agent is using a generic name like 'input_file_0.png'
        base_image_part = await tool_context.load_artifact(filename=base_image_filename)
        
        if not base_image_part and "base_image_filename" in tool_context.state:
            fallback_filename = tool_context.state["base_image_filename"]
            print(f"⚠️ Could not load artifact '{base_image_filename}', trying fallback '{fallback_filename}' from state...")
            base_image_part = await tool_context.load_artifact(filename=fallback_filename)
            
        if not base_image_part:
            # Last resort: try to find ANY image artifact if we're stuck
            print("⚠️ Could not load artifact from state, checking for any available image artifacts...")
            # This is a bit of a hack but helps recovery
            if "input_file_0.png" != base_image_filename:
                 base_image_part = await tool_context.load_artifact(filename="input_file_0.png")

        if not base_image_part:
            raise ValueError(f"Could not load base image artifact: {base_image_filename}. I tried fallback names but none were found.")

        # Debug: Check what type of object we got from load_artifact
        print(f"Base image part type: {type(base_image_part)}")
        print(f"Base image part attributes: {[attr for attr in dir(base_image_part) if not attr.startswith('_')][:10]}")
        
        # Use Google Gen AI SDK for image generation
        # The base_image_part should already be a google.genai.types.Part
        if not hasattr(base_image_part, 'inline_data') or not base_image_part.inline_data:
            raise ValueError("Could not extract image data from loaded artifact")
        
        print(f"✅ Using google.genai.Part with mime_type: {base_image_part.inline_data.mime_type}")
        
        # Get project information from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        # Initialize the client with Vertex AI configuration following the official documentation
        client = genai.Client(vertexai=True, project=project_id)
        
        # Create the content properly structured for the API
        from google.genai.types import Content, Part
        
        # Ensure we create a proper Part object for the text
        text_part = Part(text=edit_prompt)
        
        # Create a single Content object with both image and text parts
        # Use the proper structure that the API expects
        content = Content(
            role="user",
            parts=[base_image_part, text_part]
        )
        
        # Configure for image generation using the patterns from the documentation
        config = GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            candidate_count=1,
            temperature=0.7,
            max_output_tokens=1024,
            safety_settings=[
                {"method": "PROBABILITY"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT"},
                {"threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )
        
        print(f"🔧 About to call generate_content with:")
        print(f"   Model: {EDIT_MODEL}")
        print(f"   Project: {project_id}")
        print(f"   Content parts: {len(content.parts)}")
        print(f"   Response modalities: {config.response_modalities}")
        
        # Execute the API call for image generation using the official pattern
        # Pass the content directly, not as a list
        try:
            response = client.models.generate_content(
                model=EDIT_MODEL,
                contents=content,
                config=config
            )
            print(f"✅ API call successful, response type: {type(response)}")
        except Exception as api_error:
            print(f"❌ API call failed with error: {api_error}")
            print(f"   Error type: {type(api_error)}")
            raise api_error
        
        # Process the response to extract both text and image
        generated_text = ""
        generated_image_part = None
        
        if response.candidates and response.candidates[0].content.parts:
            print(f"🔍 Processing {len(response.candidates[0].content.parts)} response parts...")
            
            for i, part in enumerate(response.candidates[0].content.parts):
                print(f"   Part {i} type: {type(part)}")
                
                # Extract text content
                if hasattr(part, 'text') and part.text:
                    generated_text += part.text
                    print(f"   📝 Found text: {part.text[:100]}...")
                
                # Extract image content
                if hasattr(part, 'inline_data') and part.inline_data:
                    if 'image' in str(part.inline_data.mime_type):
                        generated_image_part = part
                        print(f"   🖼️ Found generated image with mime_type: {part.inline_data.mime_type}")
        
        # Save the generated image as an artifact if we got one
        if generated_image_part:
            try:
                await tool_context.save_artifact(filename=output_filename, artifact=generated_image_part)
                print(f"✅ Saved generated image as artifact '{output_filename}'")
                
                return {
                    "status": "success", 
                    "description": generated_text or "Image generated successfully",
                    "image_filename": output_filename,
                    "message": f"Generated and saved image for {output_filename}. You can view it in the ADK web interface under artifacts."
                }
            except Exception as save_error:
                print(f"❌ Error saving generated image: {save_error}")
                return {
                    "status": "partial_success",
                    "description": generated_text or "Image was generated but could not be saved",
                    "message": f"Generated image for {output_filename} but failed to save: {str(save_error)}"
                }
        
        # If we only got text (no image generated)
        if generated_text:
            print(f"✅ Generated text description for '{output_filename}': {generated_text[:100]}...")
            return {
                "status": "text_only", 
                "description": generated_text, 
                "message": f"Generated text description for {output_filename} (no image was produced)"
            }
        
        # If no response was generated, check for blocking
        print(f"⚠️ No content found in response")
        if hasattr(response, 'prompt_feedbacks'):
            for feedback in response.prompt_feedbacks:
                print(f"Block Reason: {feedback.block_reason}")
                if hasattr(feedback, 'safety_ratings'):
                    for rating in feedback.safety_ratings:
                        print(rating)
        
        return {"status": "error", "message": f"Could not generate content for {output_filename}. No text or image content found in response."}
        
    except Exception as e:
        print(f"❌ Error during image editing: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"Sorry, I couldn't edit the image for {output_filename}. Error: {str(e)}"}

async def generate_headlines(tool_context: ToolContext) -> str:
    """
    Generates compelling headlines using the headline agent based on the persona-driven brief.
    """
    print("🎯 Starting headline generation...")
    result = await generate_headlines_from_brief(tool_context)
    print(f"✅ Headlines generation finished with result: {result[:200]}...")
    return result

async def create_persona_brief_without_headlines(
    ideal_customer: str, core_message: str, tone_of_voice: str, 
    location: str, demographics: str, interests: str, 
    tool_context: ToolContext
) -> str:
    """
    Creates a persona-driven brief, saves it, and then immediately
    triggers headline generation.
    """
    # Create brief with empty headlines initially
    brief = PersonaDrivenAdBrief(
        ideal_customer=ideal_customer,
        core_message=core_message,
        tone_of_voice=tone_of_voice,
        headlines=[],  # Will be populated by headline generation
        location=location,
        demographics=demographics,
        interests=interests
    )
    tool_context.state["confirmed_brief"] = brief.model_dump()
    
    print("✅ Persona brief created and saved. Immediately generating headlines...")
    
    # Directly call the headline generation function
    headline_result = await generate_headlines(tool_context)
    
    # Return the result from the headline generation
    return headline_result
