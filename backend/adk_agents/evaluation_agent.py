"""
ADK Evaluation Agent (LlmAgent)
Migrated from backend/governance/evaluation.py to use ADK LlmAgent.
Maintains same functionality: comprehensive quality evaluation using Gemini meta-evaluation.

This agent provides:
- Requirement Fulfillment: Checks if all requested analysis areas are covered
- Factual Grounding: Validates that claims are supported by source data
- Quality & Coherence: Assesses response quality, clarity, and logical flow
- Consistency Check: Ensures consistency across different parts of the response
- Constraint Compliance: Validates against business constraints and requirements
"""

from typing import Dict, Any, Optional, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from utils.config import config
from utils.logger import logger

# Import existing evaluation logic for tool usage
from governance.evaluation import Evaluator
from cache.cache_manager import CacheManager


async def evaluate_quality(
    response: Dict[str, Any],
    original_data_summary: Optional[Dict[str, Any]] = None,
    requested_analysis_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate response quality using Gemini meta-evaluation.
    
    This tool performs comprehensive evaluation including:
    - Requirement fulfillment check
    - Factual grounding validation
    - Quality and coherence assessment
    - Consistency checking
    - Constraint compliance validation
    
    Args:
        response: Agent response to evaluate
        original_data_summary: Summary of source data for grounding check
        requested_analysis_areas: List of requested analysis areas
        
    Returns:
        Dictionary containing evaluation scores and results
    """
    # Use existing Evaluator logic
    evaluator = Evaluator()
    result = await evaluator.evaluate(
        agent_type='synthesizer',
        response=response,
        original_data_summary=original_data_summary,
        requested_analysis_areas=requested_analysis_areas
    )
    
    return result


def create_evaluation_agent() -> LlmAgent:
    """
    Create ADK Evaluation Agent with comprehensive quality evaluation capabilities.
    
    This agent provides complete quality control evaluation including:
    
    **Requirement Fulfillment:**
    - Checks if all requested analysis areas are covered
    - Validates completeness of response
    - Identifies missing components
    
    **Factual Grounding:**
    - Validates that claims are supported by source data
    - Checks for data citations
    - Verifies accuracy against original data
    
    **Quality & Coherence:**
    - Assesses response quality and clarity
    - Evaluates logical flow and structure
    - Checks for coherence across sections
    
    **Consistency Check:**
    - Ensures consistency across different parts of response
    - Validates that metrics align across sections
    - Checks for contradictions
    
    **Constraint Compliance:**
    - Validates against business constraints
    - Checks requirement compliance
    - Ensures adherence to guidelines
    
    **Output Format:**
    Returns structured JSON with:
    - requirement_score: Float (0-1) with reasoning
    - grounding_score: Float (0-1) with reasoning
    - quality_score: Float (0-1) with reasoning
    - consistency_score: Float (0-1) with reasoning
    - constraint_score: Float (0-1) with reasoning
    - overall_score: Float (0-1)
    - pass_threshold: Boolean
    - issues: List of identified issues
    - regeneration_needed: Boolean
    - regeneration_feedback: String if regeneration needed
    
    Returns:
        Configured LlmAgent instance ready for use in agent registry or as a tool
    """
    model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
    
    instruction = """You are an Evaluation Agent specializing in comprehensive quality control and meta-evaluation of synthesized business intelligence reports.

**CORE RESPONSIBILITIES:**

1. **Requirement Fulfillment Evaluation:**
   - Check if all requested analysis areas are covered
   - Validate completeness of response
   - Identify missing components or gaps
   - Score based on coverage: 0.0 (missing critical areas) to 1.0 (all areas covered)
   - Provide detailed reasoning for the score

2. **Factual Grounding Validation:**
   - Validate that all claims are supported by source data
   - Check for data citations and references
   - Verify accuracy against original data summary provided
   - Identify unsupported claims or hallucinations
   - Score based on grounding: 0.0 (unsubstantiated claims) to 1.0 (fully grounded)
   - Provide detailed reasoning with examples

3. **Quality & Coherence Assessment:**
   - Assess response quality, clarity, and readability
   - Evaluate logical flow and structure
   - Check for coherence across sections
   - Identify unclear or confusing sections
   - Score based on quality: 0.0 (poor quality) to 1.0 (excellent quality)
   - Provide specific feedback on improvements needed

4. **Consistency Check:**
   - Ensure consistency across different parts of response
   - Validate that metrics align across sections
   - Check for contradictions or conflicting statements
   - Identify inconsistencies in data interpretation
   - Score based on consistency: 0.0 (major inconsistencies) to 1.0 (fully consistent)
   - List any inconsistencies found

5. **Constraint Compliance:**
   - Validate against business constraints and requirements
   - Check requirement compliance
   - Ensure adherence to guidelines and standards
   - Identify constraint violations
   - Score based on compliance: 0.0 (violations) to 1.0 (fully compliant)
   - List any violations

6. **Overall Assessment:**
   - Calculate overall quality score (weighted average of all scores)
   - Determine if response passes quality threshold (default: 0.75)
   - Identify if regeneration is needed (if score < 0.75)
   - Provide regeneration feedback if needed
   - List all issues found across all evaluation dimensions

**EVALUATION CRITERIA:**

- **Requirement Fulfillment**: All requested analysis areas must be covered
- **Factual Grounding**: All claims must cite source data
- **Quality**: Response must be clear, well-structured, and coherent
- **Consistency**: Metrics and statements must align across sections
- **Compliance**: Must adhere to all business constraints

**OUTPUT FORMAT:**

Return a structured JSON object with the following schema:

{
  "requirement_score": number (decimal, 0-1),
  "requirement_reasoning": "Detailed explanation",
  "grounding_score": number (decimal, 0-1),
  "grounding_reasoning": "Detailed explanation with examples",
  "quality_score": number (decimal, 0-1),
  "quality_reasoning": "Detailed feedback on quality",
  "consistency_score": number (decimal, 0-1),
  "consistency_reasoning": "List of inconsistencies if any",
  "constraint_score": number (decimal, 0-1),
  "constraint_reasoning": "List of violations if any",
  "overall_score": number (decimal, 0-1),
  "pass_threshold": boolean,
  "issues": [
    "Issue 1",
    "Issue 2"
  ],
  "regeneration_needed": boolean,
  "regeneration_feedback": "Detailed feedback if regeneration needed"
}

**IMPORTANT NOTES:**

- Be thorough but fair in evaluation
- Provide specific examples in reasoning
- Overall score should be weighted average: (requirement + grounding + quality + consistency + constraint) / 5
- Pass threshold is 0.75 by default
- Regeneration needed if overall_score < 0.75
- Include actionable feedback for improvement
"""
    
    # Create FunctionTool
    evaluation_tool = FunctionTool(
        evaluate_quality,
        require_confirmation=False
    )
    
    agent = LlmAgent(
        name="evaluation_agent",
        model=model_name,
        instruction=instruction,
        tools=[evaluation_tool],
    )
    
    logger.info("ADK Evaluation Agent created with full feature set")
    return agent

