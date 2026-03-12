# bettan_agent/advanced_tools.py

from typing import Dict, List, Any, Optional
import json
from google.adk.tools import ToolContext
from .advanced_models import (
    AdvancedProBrief, AdvancedAudienceBuilder, CustomAudience, 
    LookalikeAudience, ABTestConfiguration, CreativeAsset,
    BrandGuidelines, CampaignPerformance, Platform
)

def create_advanced_audience(
    name: str, description: str, demographics_json: str, 
    geographic_json: str, interests_json: str, behaviors_json: str,
    tool_context: ToolContext
) -> str:
    """Creates an advanced audience with granular targeting options."""
    try:
        # Parse JSON inputs
        demographics = json.loads(demographics_json) if demographics_json else {}
        geographic = json.loads(geographic_json) if geographic_json else {}
        interests = json.loads(interests_json) if interests_json else {}
        behaviors = json.loads(behaviors_json) if behaviors_json else {}
        
        # Create audience builder
        audience = AdvancedAudienceBuilder(
            name=name,
            description=description,
            demographics=demographics,
            geographic=geographic,
            interests=interests,
            behaviors=behaviors
        )
        
        # Save to session state
        if "advanced_audiences" not in tool_context.state:
            tool_context.state["advanced_audiences"] = {}
        
        tool_context.state["advanced_audiences"][name] = audience.model_dump()
        
        return f"✅ Advanced audience '{name}' created successfully!\n\n**Audience Summary:**\n{_format_audience_summary(audience)}"
        
    except Exception as e:
        return f"❌ Error creating audience: {str(e)}"

def create_custom_audience(
    name: str, source_type: str, description: str,
    tool_context: ToolContext,
    website_rules_json: str = "", customer_emails: str = "",
    app_events: str = "", engagement_type: str = ""
) -> str:
    """Creates a custom audience from first-party data."""
    try:
        custom_audience = CustomAudience(
            name=name,
            source_type=source_type,
            description=description
        )
        
        # Set source-specific data
        if source_type == "website_visitors" and website_rules_json:
            custom_audience.website_rules = json.loads(website_rules_json)
        elif source_type == "customer_list" and customer_emails:
            # In production, this would be securely handled
            emails = [email.strip() for email in customer_emails.split('\n') if email.strip()]
            custom_audience.customer_data = emails
        elif source_type == "app_users" and app_events:
            custom_audience.app_events = [event.strip() for event in app_events.split(',')]
        elif source_type == "engagement" and engagement_type:
            custom_audience.engagement_type = engagement_type
        
        # Save to session state
        if "custom_audiences" not in tool_context.state:
            tool_context.state["custom_audiences"] = {}
        
        tool_context.state["custom_audiences"][name] = custom_audience.model_dump()
        
        return f"✅ Custom audience '{name}' created successfully!\n\n**Type:** {source_type}\n**Description:** {description}"
        
    except Exception as e:
        return f"❌ Error creating custom audience: {str(e)}"

def create_lookalike_audience(
    name: str, source_audience_name: str, similarity_percentage: int,
    countries: str, tool_context: ToolContext
) -> str:
    """Creates a lookalike audience based on a custom audience."""
    try:
        # Verify source audience exists
        custom_audiences = tool_context.state.get("custom_audiences", {})
        if source_audience_name not in custom_audiences:
            return f"❌ Source audience '{source_audience_name}' not found. Please create it first."
        
        countries_list = [country.strip() for country in countries.split(',')]
        
        lookalike = LookalikeAudience(
            name=name,
            source_audience=source_audience_name,
            similarity_percentage=similarity_percentage,
            countries=countries_list
        )
        
        # Save to session state
        if "lookalike_audiences" not in tool_context.state:
            tool_context.state["lookalike_audiences"] = {}
        
        tool_context.state["lookalike_audiences"][name] = lookalike.model_dump()
        
        return f"✅ Lookalike audience '{name}' created successfully!\n\n**Source:** {source_audience_name}\n**Similarity:** {similarity_percentage}%\n**Countries:** {', '.join(countries_list)}"
        
    except Exception as e:
        return f"❌ Error creating lookalike audience: {str(e)}"

def setup_ab_test(
    test_name: str, variable_to_test: str, variations_json: str,
    duration_days: int, success_metric: str, traffic_split: str,
    tool_context: ToolContext
) -> str:
    """Sets up an A/B test configuration."""
    try:
        variations = json.loads(variations_json)
        split = [int(x.strip()) for x in traffic_split.split(',')]
        
        if sum(split) != 100:
            return "❌ Traffic split percentages must sum to 100%"
        
        ab_test = ABTestConfiguration(
            test_name=test_name,
            variable_to_test=variable_to_test,
            variations=variations,
            traffic_split=split,
            duration_days=duration_days,
            success_metric=success_metric
        )
        
        # Save to session state
        if "ab_tests" not in tool_context.state:
            tool_context.state["ab_tests"] = []
        
        tool_context.state["ab_tests"].append(ab_test.model_dump())
        
        return f"✅ A/B test '{test_name}' configured successfully!\n\n**Testing:** {variable_to_test}\n**Duration:** {duration_days} days\n**Success Metric:** {success_metric}\n**Traffic Split:** {traffic_split}"
        
    except Exception as e:
        return f"❌ Error setting up A/B test: {str(e)}"

def upload_brand_guidelines(
    primary_colors: str, secondary_colors: str, fonts: str,
    voice_guidelines: str, visual_style_notes: str,
    tool_context: ToolContext
) -> str:
    """Uploads and stores brand guidelines."""
    try:
        guidelines = BrandGuidelines(
            primary_colors=[color.strip() for color in primary_colors.split(',') if color.strip()],
            secondary_colors=[color.strip() for color in secondary_colors.split(',') if color.strip()],
            fonts=[font.strip() for font in fonts.split(',') if font.strip()],
            voice_guidelines=voice_guidelines,
            visual_style_notes=visual_style_notes
        )
        
        tool_context.state["brand_guidelines"] = guidelines.model_dump()
        
        return f"✅ Brand guidelines uploaded successfully!\n\n**Primary Colors:** {', '.join(guidelines.primary_colors)}\n**Fonts:** {', '.join(guidelines.fonts)}\n**Voice Guidelines:** {voice_guidelines[:100]}..."
        
    except Exception as e:
        return f"❌ Error uploading brand guidelines: {str(e)}"

def create_advanced_pro_brief(
    campaign_name: str, company_name: str, website_url: str,
    objective: str, product_name: str, product_description: str,
    usp: str, landing_url: str, persona: str, core_message: str,
    tone: str, primary_cta: str, platforms: str,
    tool_context: ToolContext
) -> str:
    """Creates a comprehensive Advanced Pro brief."""
    try:
        # Get existing data from session
        brand_guidelines = tool_context.state.get("brand_guidelines", {})
        custom_audiences = tool_context.state.get("custom_audiences", {})
        lookalike_audiences = tool_context.state.get("lookalike_audiences", {})
        ab_tests = tool_context.state.get("ab_tests", [])
        advanced_audiences = tool_context.state.get("advanced_audiences", {})
        
        # Create default audience if none exist
        if not advanced_audiences:
            default_audience = AdvancedAudienceBuilder(
                name="Default Audience",
                description="Auto-generated from persona description"
            )
            advanced_audiences["Default Audience"] = default_audience.model_dump()
        
        platforms_list = [p.strip().lower() for p in platforms.split(',')]
        
        brief = AdvancedProBrief(
            campaign_name=campaign_name,
            company_name=company_name,
            website_url=website_url,
            objective=objective,
            product_service_name=product_name,
            product_description=product_description,
            unique_selling_proposition=usp,
            target_landing_url=landing_url,
            target_persona_detailed=persona,
            core_message=core_message,
            tone_of_voice=tone,
            primary_cta=primary_cta,
            platforms=platforms_list,
            audience_strategy=list(advanced_audiences.values())[0],  # Use first audience
            custom_audiences=list(custom_audiences.values()),
            lookalike_audiences=list(lookalike_audiences.values()),
            ab_tests=ab_tests,
            brand_guidelines=brand_guidelines
        )
        
        tool_context.state["advanced_pro_brief"] = brief.model_dump()
        
        return _format_advanced_brief_summary(brief)
        
    except Exception as e:
        return f"❌ Error creating Advanced Pro brief: {str(e)}"

def analyze_campaign_performance(
    campaign_name: str, platform: str, impressions: int,
    clicks: int, conversions: int, spend: float,
    tool_context: ToolContext
) -> str:
    """Analyzes campaign performance and provides optimization recommendations."""
    try:
        # Calculate metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpc = (spend / clicks) if clicks > 0 else 0
        cpa = (spend / conversions) if conversions > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if ctr < 1.0:
            recommendations.append("CTR is below 1% - consider testing new headlines or images")
        if conversion_rate < 2.0:
            recommendations.append("Conversion rate is low - review landing page relevance")
        if cpc > 2.0:
            recommendations.append("CPC is high - consider refining audience targeting")
        
        performance_summary = f"""
📊 **Campaign Performance Analysis: {campaign_name}**

**Key Metrics:**
• Impressions: {impressions:,}
• Clicks: {clicks:,}
• Conversions: {conversions:,}
• CTR: {ctr:.2f}%
• CPC: ${cpc:.2f}
• CPA: ${cpa:.2f}
• Conversion Rate: {conversion_rate:.2f}%

**Optimization Recommendations:**
{chr(10).join([f"• {rec}" for rec in recommendations]) if recommendations else "• Performance looks good! Continue monitoring."}
"""
        
        return performance_summary
        
    except Exception as e:
        return f"❌ Error analyzing performance: {str(e)}"

def generate_responsive_ad_assets(
    headlines: str, descriptions: str, images: str,
    tool_context: ToolContext
) -> str:
    """Generates assets optimized for responsive ad formats."""
    try:
        headlines_list = [h.strip() for h in headlines.split('\n') if h.strip()]
        descriptions_list = [d.strip() for d in descriptions.split('\n') if d.strip()]
        images_list = [img.strip() for img in images.split('\n') if img.strip()]
        
        if len(headlines_list) > 15:
            return "❌ Maximum 15 headlines allowed for responsive ads"
        if len(descriptions_list) > 4:
            return "❌ Maximum 4 descriptions allowed for responsive ads"
        
        # Validate character limits
        for i, headline in enumerate(headlines_list):
            if len(headline) > 30:
                return f"❌ Headline {i+1} exceeds 30 character limit: '{headline}'"
        
        for i, desc in enumerate(descriptions_list):
            if len(desc) > 90:
                return f"❌ Description {i+1} exceeds 90 character limit: '{desc}'"
        
        asset_summary = f"""
✅ **Responsive Ad Assets Generated**

**Headlines ({len(headlines_list)}/15):**
{chr(10).join([f"{i+1}. {h} ({len(h)} chars)" for i, h in enumerate(headlines_list)])}

**Descriptions ({len(descriptions_list)}/4):**
{chr(10).join([f"{i+1}. {d} ({len(d)} chars)" for i, d in enumerate(descriptions_list)])}

**Images ({len(images_list)}):**
{chr(10).join([f"• {img}" for img in images_list])}

**Platform Optimization:**
• Google Responsive Search Ads: Ready ✅
• Google Responsive Display Ads: Ready ✅
• Meta Dynamic Ads: Ready ✅
"""
        
        # Save assets to session
        tool_context.state["responsive_assets"] = {
            "headlines": headlines_list,
            "descriptions": descriptions_list,
            "images": images_list
        }
        
        return asset_summary
        
    except Exception as e:
        return f"❌ Error generating responsive assets: {str(e)}"

# Helper functions
def _format_audience_summary(audience: AdvancedAudienceBuilder) -> str:
    """Formats audience summary for display."""
    summary_parts = []
    
    if audience.demographics.age_min or audience.demographics.age_max:
        age_range = f"{audience.demographics.age_min or 'Any'}-{audience.demographics.age_max or 'Any'}"
        summary_parts.append(f"Age: {age_range}")
    
    if audience.geographic.countries:
        summary_parts.append(f"Countries: {', '.join(audience.geographic.countries[:3])}{'...' if len(audience.geographic.countries) > 3 else ''}")
    
    if audience.interests.broad_categories:
        summary_parts.append(f"Interests: {', '.join(audience.interests.broad_categories[:3])}{'...' if len(audience.interests.broad_categories) > 3 else ''}")
    
    if audience.work.industries:
        summary_parts.append(f"Industries: {', '.join(audience.work.industries[:3])}{'...' if len(audience.work.industries) > 3 else ''}")
    
    return '\n'.join([f"• {part}" for part in summary_parts]) if summary_parts else "• Broad targeting (AI-optimized)"

def _format_advanced_brief_summary(brief: AdvancedProBrief) -> str:
    """Formats the advanced brief summary for display."""
    return f"""
🎯 **Advanced Pro Campaign Brief Created**

**Campaign Foundation:**
• Name: {brief.campaign_name}
• Company: {brief.company_name}
• Objective: {brief.objective.value.title()}
• Product: {brief.product_service_name}

**Strategic Messaging:**
• Core Message: {brief.core_message}
• Tone: {brief.tone_of_voice.value.title()}
• Primary CTA: {brief.primary_cta.value}

**Targeting Strategy:**
• Audience: {brief.audience_strategy.name}
• Custom Audiences: {len(brief.custom_audiences)}
• Lookalike Audiences: {len(brief.lookalike_audiences)}

**Campaign Configuration:**
• Platforms: {', '.join([p.title() for p in brief.platforms])}
• A/B Tests: {len(brief.ab_tests)}
• Brand Guidelines: {'✅ Configured' if brief.brand_guidelines else '❌ Not set'}

**Next Steps:**
1. Review and approve the brief configuration
2. Upload creative assets (images, videos, logos)
3. Launch A/B tests for optimization
4. Monitor performance and iterate

Ready to generate your advanced advertising campaign!
"""
