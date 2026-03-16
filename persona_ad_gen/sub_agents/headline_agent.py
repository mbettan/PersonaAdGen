# bettan_agent/sub_agents/headline_agent.py

from google.adk.tools import ToolContext
import google.genai as genai
import os

MODEL = "gemini-3-flash-preview"

async def generate_headlines_from_brief(tool_context: ToolContext) -> str:
    """
    Generates compelling headlines based on the persona-driven brief.
    """
    
    # Get the brief information from the tool context
    brief_data = tool_context.state.get("confirmed_brief", {})
    
    if not brief_data:
        return "❌ No brief found. Please complete the persona-driven brief first."
    
    ideal_customer = brief_data.get("ideal_customer", "")
    core_message = brief_data.get("core_message", "")
    tone_of_voice = brief_data.get("tone_of_voice", "")
    
    if not all([ideal_customer, core_message, tone_of_voice]):
        return "❌ Incomplete brief. Please ensure ideal customer, core message, and tone of voice are provided."
    
    print(f"🎯 Generating headlines for: {ideal_customer[:50]}...")
    print(f"📝 Core message: {core_message[:50]}...")
    print(f"🎭 Tone: {tone_of_voice}")
    
    try:
        # Get project information from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        # Initialize the client with Vertex AI configuration
        client = genai.Client(vertexai=True, project=project_id)
        
        # Create the headline generation prompt
        headline_prompt = f"""You are an expert advertising copywriter specializing in creating compelling headlines that convert.
 
Based on this persona-driven brief, generate exactly **ONE** powerful, conversion-focused headline:
 
**Ideal Customer:** {ideal_customer}
**Core Message:** {core_message}
**Tone of Voice:** {tone_of_voice}
 
Create a headline that:
1. Speaks directly to the ideal customer's pain points and desires
2. Captures the essence of the core message
3. Matches the specified tone of voice
4. Is compelling and action-oriented
5. Includes emotional triggers that resonate with the target audience
 
IMPORTANT: Only generate the headline text. Do not include any numbers, bullets, quotes, explanations, or formatting."""
        
        print(f"🤖 Calling Google Gen AI with prompt length: {len(headline_prompt)}")
        
        # Generate headlines using the same pattern as other tools
        response = client.models.generate_content(
            model=MODEL,
            contents=headline_prompt,
        )
        
        # Extract the text response
        result_text = response.text
        
        print(f"✅ LLM response received, length: {len(result_text)}")
        print(f"📝 Response preview: {result_text[:300]}...")
        
        # Parse the response to extract headlines
        headline = result_text.strip()
        # Basic cleanup: remove leading/trailing quotes or dots if any
        headline = headline.strip(' ".\n')
        
        print(f"🎯 Final headline: '{headline}'")
        
        if not headline or len(headline) < 5:
            print(f"❌ Failed to generate a quality headline.")
            print(f"📝 Full LLM response for debugging:\n{result_text}")
            return f"❌ Could not generate a quality headline. Generated response: {result_text[:500]}..."
        
        headlines = [headline]
        
        # Update the brief with generated headlines
        brief_data["headlines"] = headlines
        tool_context.state["confirmed_brief"] = brief_data
        
        # Format the response
        headline_list = f"• {headline}"
        
        return f"""✅ **Generated 1 Compelling Headline**
 
{headline_list}

**Headlines Analysis:**
• **Target Audience:** {ideal_customer}
• **Core Message:** {core_message}
• **Tone:** {tone_of_voice}

These headlines have been automatically added to your brief. You can now proceed with image generation or make any adjustments if needed.

**Next Steps:**
1. Review the generated headlines
2. Upload your base image if you haven't already
3. Proceed with creating your advertising scenes

Ready to create compelling ads that convert!"""
        
    except Exception as e:
        print(f"❌ Error in generate_headlines_from_brief: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ Error generating headlines: {str(e)}. Please try again or provide headlines manually."
