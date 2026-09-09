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
        f"You are an elite TikTok/Reels creative director producing a viral UGC beauty and skincare video. "
        f"Target Product: {state['product_title']} (Price: {state['product_price']}). Focus on physical product characteristics such as texture, serum droplets, creamy lather, skin-feel, and authentic daily skincare routines without making prohibited medical claims.\n\n"
        f"STRICT DURATION AND SCENE REQUIREMENTS (MAX 6 SCENES):\n"
        f"1. Total video length MUST be 20 to 24 seconds, divided into 4 to 6 scenes (fast pacing):\n"
        f"   - Scene 1 (0-3s): The Hook (medium_closeup). High retention line. Product is NOT shown (product_visible: false).\n"
        f"   - Scene 2 (4-8s): Core Benefit (product_closeup). Packshot/texture (product_visible: true).\n"
        f"   - Scenes 3-5 (9-19s): Experience/Demonstration (macro/b-roll). Realistic usage (3-5s per scene).\n"
        f"   - Scene 6 (20-24s): Call to Action. End-card (link_required: true).\n"
        f"2. pacing_notes MUST contain MAXIMUM 6 items (at most 6 scenes, minimum 4 scenes).\n"
        f"   Format each note as: 'Scene X (Ys-Zs): [Visual Camera & Action Prompt]'.\n"
        f"3. visual_hook MUST be a vivid visual motion description for Scene 1 (burned as text overlay for 0-3s).\n"
        f"4. narration_text MUST be punchy and concise, strictly between 45 and 65 words (~18 to 22 seconds spoken duration).\n"
        f"5. ad_disclosures MUST include '#Ad' or '#Sponsored'."
    )
    
    response = await structured_llm.ainvoke([HumanMessage(content=prompt)])
    
    # Enforce strict maximum of 6 scenes
    if response and hasattr(response, "pacing_notes") and response.pacing_notes:
        response.pacing_notes = response.pacing_notes[:6]
    
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
