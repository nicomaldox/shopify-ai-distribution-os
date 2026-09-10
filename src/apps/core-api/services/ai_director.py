import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from services.schemas import AgentState, DirectorSpec
from database.connection import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Dummy whitelist for PoC
FORBIDDEN_CLAIMS = ["cure", "guaranteed", "100%", "miracle", "magical"]

async def generate_script_node(state: AgentState) -> Dict[str, Any]:
    """Node that generates the script using with_structured_output."""
    logger.info(f"Generating script for {state['product_id']}")
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    structured_llm = llm.with_structured_output(DirectorSpec)
    
    prompt = (
        f"You are an elite TikTok/Reels creative director and professional AI video prompt engineer specializing in Wan 2.1 video diffusion models. "
        f"Target Product: {state['product_title']} (Price: {state['product_price']}). Focus on tangible physical characteristics such as texture, serum droplets, creamy lather, skin-feel, and authentic daily skincare routines without making prohibited medical claims.\n\n"
        f"PROFESSIONAL VIDEO DIFFUSION PROMPT REQUIREMENTS (4 to 6 SCENES):\n"
        f"1. Total video duration: 20 to 24 seconds across 4 to 6 scenes.\n"
        f"2. pacing_notes MUST contain 4 to 6 standalone, cinematic visual diffusion prompts (one per scene):\n"
        f"   - DO NOT USE BRACKETS OR METADATA: Do NOT write '[Medium Close-up]' or '(0s-3s)' or 'Scene 1:'. Write pure, rich descriptive natural language.\n"
        f"   - Each scene prompt MUST explicitly define:\n"
        f"     * SUBJECT & ACTION: Tangible subject and realistic physical motion (e.g. 'A manicured hand gently presses the dropper, releasing a single golden serum droplet that falls in smooth slow motion').\n"
        f"     * CAMERA MOTION: Camera movement (e.g. 'Slow macro push-in', 'Gentle steady tracking pan', 'Fixed high-angle beauty shot').\n"
        f"     * LIGHTING & MOOD: Environmental lighting (e.g. 'Soft morning sunlight from a nearby window, warm diffused glow, shallow depth of field with creamy f/1.8 bokeh').\n"
        f"     * VISUAL TEXTURE: High-fidelity details (e.g. 'Crisp glass bottle reflections, natural skin pores, glossy liquid shimmer, photorealistic 4k UGC aesthetic').\n"
        f"   - Scene Roles:\n"
        f"     * Scene 1 (The Hook): Pure aesthetic motion to stop scrolling (lifestyle, refreshing morning mist, or soft silk texture).\n"
        f"     * Scene 2 (Product Hero): Anchored to the product package, showing the bottle/tube in an elegant clean setting.\n"
        f"     * Scene 3-4 (Texture & Application): Close-up of formulation (droplets, lathering foam, or smooth application onto skin).\n"
        f"     * Scene 5 (Radiant Result): Fresh, glowing healthy skin in natural daylight.\n"
        f"     * Scene 6 (Call-to-Action Packshot): Elegant hero product presentation with gentle lighting shimmer.\n"
        f"3. visual_hook: A vivid visual motion description of the opening attention-grabber.\n"
        f"4. narration_text: Punchy voiceover script, strictly between 45 and 65 words (~18 to 22 seconds spoken duration).\n"
        f"5. ad_disclosures: MUST include '#Ad', '#Sponsored', or '#AffiliateLink'."
    )
    
    response = await structured_llm.ainvoke([HumanMessage(content=prompt)])
    
    # Enforce strict maximum of 6 scenes and clean any stray brackets
    if response and hasattr(response, "pacing_notes") and response.pacing_notes:
        cleaned_notes = []
        for note in response.pacing_notes[:6]:
            cleaned = note.replace("[", "").replace("]", "").strip()
            cleaned_notes.append(cleaned)
        response.pacing_notes = cleaned_notes
    
    # Basic token estimation if usage_metadata is stripped by with_structured_output
    estimated_tokens = int(len(str(response)) / 3) + 150 
    
    return {
        "generated_spec": response,
        "total_tokens": estimated_tokens
    }

async def claims_validator_node(state: AgentState) -> Dict[str, Any]:
    """Node that uses a secondary LLM (Judge) to validate the script."""
    logger.info("Validating claims via LLM Judge")
    spec = state["generated_spec"]
    
    # Validate disclosures
    has_ad = any("#ad" in tag.lower() or "#sponsored" in tag.lower() for tag in spec.ad_disclosures)
    if not has_ad:
        spec.ad_disclosures.append("#Ad")
        
    # Secondary LLM Judge
    judge_llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    judge_prompt = (
        f"Analyze the following marketing text for forbidden claims.\n"
        f"Forbidden words: {', '.join(FORBIDDEN_CLAIMS)}\n\n"
        f"Text:\n{spec.narration_text}\n\n"
        f"Reply only with 'PASS' or 'FAIL'."
    )
    
    judge_response = await judge_llm.ainvoke([HumanMessage(content=judge_prompt)])
    judge_text = str(judge_response.content).strip().upper()
    
    # Extract usage from judge
    judge_tokens = 0
    if hasattr(judge_response, "usage_metadata") and judge_response.usage_metadata:
         judge_tokens = judge_response.usage_metadata.get("total_tokens", 50)
         
    score = 1.0000 if "PASS" in judge_text else 0.5000
    if "FAIL" in judge_text:
        logger.warning(f"LLM Judge flagged the script for {state['product_id']}")
        
    return {
        "claims_accuracy_score": score,
        "total_tokens": state.get("total_tokens", 0) + judge_tokens,
        "status": "SUCCESS" if "PASS" in judge_text else "REJECTED"
    }

async def telemetry_logger_node(state: AgentState) -> Dict[str, Any]:
    """Node that asynchronously logs telemetry to the database."""
    total_tokens = state.get("total_tokens", 0)
    estimated_cost_usd = (total_tokens / 1000.0) * 0.005
    
    try:
        import uuid
        creator_id_val = None
        if state.get("creator_id"):
            try:
                creator_id_val = uuid.UUID(str(state["creator_id"]))
            except (ValueError, AttributeError):
                creator_id_val = None

        async for db in get_db_session():
            stmt = text("""
                INSERT INTO ai_generation_logs 
                (trace_id, creator_id, product_id, total_tokens, estimated_cost_usd, latency_ms, claims_accuracy_score, status)
                VALUES 
                (:trace_id, :creator_id, :product_id, :total_tokens, :estimated_cost_usd, :latency_ms, :claims_accuracy_score, :status)
            """)
            await db.execute(stmt, {
                "trace_id": state["trace_id"],
                "creator_id": creator_id_val,
                "product_id": state["product_id"],
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost_usd,
                "latency_ms": 1500, # Static mockup for latency
                "claims_accuracy_score": state.get("claims_accuracy_score", 1.0),
                "status": state.get("status", "SUCCESS")
            })
            await db.commit()
            break
        logger.info(f"AI Telemetry Logged for Trace {state['trace_id']}")
    except Exception as e:
        logger.error(f"Failed to log AI telemetry: {e}")
        
    return {}

# Build the LangGraph
workflow = StateGraph(AgentState)
workflow.add_node("generate", generate_script_node)
workflow.add_node("validate", claims_validator_node)
workflow.add_node("log", telemetry_logger_node)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "validate")
workflow.add_edge("validate", "log")
workflow.add_edge("log", END)

ai_director_app = workflow.compile()

async def generate_script(product_title: str, product_price: str, product_id: str, creator_id: str, trace_id: str) -> DirectorSpec:
    """
    Invokes the AI Director Graph to generate a compliant video script.
    """
    initial_state = {
        "product_id": product_id,
        "creator_id": creator_id,
        "trace_id": trace_id,
        "product_title": product_title,
        "product_price": product_price,
        "total_tokens": 0
    }
    
    result = await ai_director_app.ainvoke(initial_state)
    
    spec = result.get("generated_spec")
    if not spec:
        raise Exception("Failed to generate script: Empty response")
        
    return spec
