import os
import json
import google.generativeai as genai
from sqlalchemy.orm import Session
from models import Agent, Tool, RFP, AgentExecution, Conversation
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID

# Configure Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# NOTE: Model is now agent-specific, no global model instance

class AgentOrchestrator:
    """
    Orchestrates multiple agents for RFP processing workflow:
    1. Sales Agent - Extracts summary and objectives
    2. Technical Agent - Matches SKUs from CSV
    3. Pricing Agent - Generates pricing table
    4. Proposal Assembly Agent - Creates final proposal
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_progress(self, rfp_id: int, agent_name: str, tool_name: str = None, status: str = "running"):
        """Update RFP progress in database for real-time tracking, enforcing sequence."""
        rfp = self.db.query(RFP).filter(RFP.id == rfp_id).first()
        if rfp:
            progress = {
                "agent": agent_name,
                "tool": tool_name,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Enforce sequential progression on the backend for UI consistency
            # sales -> technical -> pricing -> proposal
            order = ["Sales Agent", "Technical Agent", "Pricing Agent", "Proposal Agent"]
            if agent_name in order:
                idx = order.index(agent_name)
                # Mark all prior stages implicitly completed if we reach a later stage
                progress["sequence"] = {
                    "sales": "completed" if idx >= 0 else None,
                    "technical": "completed" if idx >= 1 else None,
                    "pricing": "completed" if idx >= 2 else None,
                    "proposal": "completed" if idx >= 3 else None,
                }

            rfp.current_progress = progress
            self.db.commit()
            print(f"[PROGRESS] Agent: {agent_name}, Tool: {tool_name}, Status: {status}")
        
    def select_next_agent(self, current_agent: str, current_output: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use LLM to intelligently determine which agent should execute next based on:
        - Current agent that just executed
        - Output from that agent
        - Overall workflow context
        
        Returns: {
            "next_agent": agent_name or None,
            "reasoning": why this agent was selected,
            "ready": True/False if all prerequisites are met
        }
        """
        # Get all available agents
        all_agents = self.db.query(Agent).all()
        agent_info = "\n".join([
            f"- {a.name}: {a.role} - {a.system_prompt[:150]}..."
            for a in all_agents
        ])
        
        # Build routing prompt
        routing_prompt = f"""You are an intelligent workflow orchestrator for an RFP processing system.

Available Agents:
{agent_info}

Current State:
- Just executed: {current_agent}
- Agent output summary: {json.dumps(current_output, indent=2)[:500]}
- Workflow context: {json.dumps(context or {}, indent=2)[:500]}

Analyze the current state and determine:
1. Which agent should execute NEXT in the workflow?
2. Are all prerequisites for that agent satisfied?
3. If no more agents needed, workflow is complete

Standard workflow order (but use your judgment):
Sales Agent → Technical Agent → Pricing Agent → Proposal Assembly Agent

Respond with ONLY a JSON object:
{{
    "next_agent": "agent_name" or null if workflow complete,
    "reasoning": "brief explanation of why this agent",
    "ready": true/false,
    "prerequisites_missing": [] or list of what's missing
}}"""

        try:
            # Safety settings to prevent blocking
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Use Gemini for routing - use gemini-2.5-flash
            routing_model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3}, safety_settings=safety_settings)
            response = routing_model.generate_content(f"You are a workflow router. Respond ONLY with valid JSON.\\n\\n{routing_prompt}")
            result_text = response.text.strip()
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            routing_decision = json.loads(result_text)
            print(f"[ORCHESTRATOR] Routing decision: {routing_decision}")
            return routing_decision
            
        except Exception as e:
            print(f"[ORCHESTRATOR ERROR] Failed to route: {str(e)}")
            # Fallback to simple sequential routing
            agent_sequence = ["sales_agent", "technical_agent", "pricing_agent", "proposal_assembly_agent"]
            try:
                current_idx = agent_sequence.index(current_agent)
                if current_idx < len(agent_sequence) - 1:
                    return {
                        "next_agent": agent_sequence[current_idx + 1],
                        "reasoning": "Sequential fallback routing",
                        "ready": True,
                        "prerequisites_missing": []
                    }
            except:
                pass
            
            return {
                "next_agent": None,
                "reasoning": "Workflow complete or routing failed",
                "ready": False,
                "prerequisites_missing": []
            }
    
    def select_agent(self, user_message: str, available_agents: List[Agent]) -> Agent:
        """Use LLM to select the appropriate agent based on user message"""
        agent_descriptions = "\n".join([
            f"- {agent.name} (ID: {agent.id}): {agent.role} - {agent.system_prompt[:100]}..."
            for agent in available_agents
        ])
        
        selection_prompt = f"""Given the following agents and a user request, select the most appropriate agent.

Available Agents:
{agent_descriptions}

User Request: {user_message}

Respond with ONLY the agent ID number, nothing else."""

        # Safety settings to prevent blocking
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # Use Gemini for agent selection
        selection_model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.3}, safety_settings=safety_settings)
        response = selection_model.generate_content(f"You are an agent router. Select the best agent ID for the task.\\n\\n{selection_prompt}")
        
        try:
            agent_id = int(response.text.strip())
            selected_agent = next((a for a in available_agents if a.id == agent_id), None)
            return selected_agent or available_agents[0]
        except:
            return available_agents[0]
    
    def execute_agent(self, agent: Agent, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific agent with given message and context"""
        try:
            # Load agent's tools - convert string UUIDs to UUID objects
            tool_ids = [UUID(tid) if isinstance(tid, str) else tid for tid in (agent.tool_ids or [])]
            tools = self.db.query(Tool).filter(Tool.id.in_(tool_ids)).all() if tool_ids else []
            
            print(f"\n[DEBUG] Executing agent: {agent.name}")
            print(f"[DEBUG] Agent has {len(tools)} tools: {[t.name for t in tools]}")
            
            # Build tool descriptions for LLM
            tool_schemas = []
            if tools:
                for tool in tools:
                    tool_schema = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters or {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    }
                    tool_schemas.append(tool_schema)
                    print(f"[DEBUG] Tool schema added: {tool.name}")
            
            context_block = ""
            if context:
                context_block = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
            
            print(f"[DEBUG] Calling Gemini model: {agent.model}")
            print(f"[DEBUG] Tools available: {[t.name for t in tools]}")
            
            # Safety settings to prevent blocking
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Create model instance using the agent's configured model
            agent_model = genai.GenerativeModel(
                agent.model,
                generation_config={"temperature": 0.7},
                safety_settings=safety_settings
            )
            
            # Build prompt with tool information
            if tool_schemas:
                tools_description = "\\n\\nAvailable Tools:\\n"
                for tool in tools:
                    tools_description += f"- {tool.name}: {tool.description}\\n"
                    tools_description += f"  Parameters: {json.dumps(tool.parameters, indent=2)}\\n"
                
                full_prompt = (
                    f"{agent.system_prompt}"
                    f"{context_block}"
                    f"{tools_description}"
                    f"\\n\\nUser: {message}"
                    "\\n\\nIf you need to call a tool, respond with JSON: "
                    "{\\\"tool_call\\\": {\\\"name\\\": \\\"tool_name\\\", \\\"arguments\\\": {...}}}"
                    "\\nOtherwise, provide your direct response."
                )
                
                response = agent_model.generate_content(full_prompt)
            else:
                full_prompt = f"{agent.system_prompt}{context_block}\\n\\nUser: {message}"
                response = agent_model.generate_content(full_prompt)
            
            # Handle blocked responses
            try:
                response_text = response.text.strip()
            except ValueError as e:
                # Response was blocked by safety filters
                print(f"[ERROR] Gemini blocked response: {e}")
                print(f"[ERROR] Finish reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}")
                print(f"[ERROR] Safety ratings: {response.candidates[0].safety_ratings if response.candidates else 'none'}")
                
                # Return error message
                return {
                    "content": f"Error: Response blocked by safety filters. Reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}",
                    "tool_calls": [],
                    "error": True,
                    "error_details": str(e)
                }
            tool_calls_data = []
            conversation_history = full_prompt
            
            # Allow multiple sequential tool calls (max 5 iterations to prevent infinite loops)
            max_iterations = 5
            iteration = 0
            
            # Helper to map internal roles to display names
            def _display_name(role: str) -> str:
                mapping = {
                    "sales": "Sales Agent",
                    "technical": "Technical Agent",
                    "pricing": "Pricing Agent",
                    "proposal_assembly": "Proposal Agent",
                }
                return mapping.get(role, f"{role.title()} Agent")

            while iteration < max_iterations:
                iteration += 1
                
                # Check if response contains tool call
                if "\"tool_call\"" not in response_text and "{" not in response_text:
                    # No tool call detected, this is the final response
                    final_content = response_text
                    break
                
                try:
                    # Extract JSON from response (handle markdown code blocks anywhere in text)
                    clean_text = response_text
                    
                    # Check if response contains markdown code blocks
                    if "```json" in clean_text or "```" in clean_text:
                        # Extract content between ``` markers
                        parts = clean_text.split("```")
                        for i, part in enumerate(parts):
                            # Skip even indices (outside code blocks)
                            if i % 2 == 0:
                                continue
                            # Check if this is a JSON block
                            content = part.strip()
                            if content.startswith("json"):
                                content = content[4:].strip()
                            # Try to parse this as JSON
                            if "tool_call" in content:
                                clean_text = content
                                break
                    
                    # Try to parse as JSON for tool call
                    tool_call_json = json.loads(clean_text)
                    if "tool_call" in tool_call_json:
                        tool_name = tool_call_json["tool_call"]["name"]
                        tool_args = tool_call_json["tool_call"]["arguments"]
                        
                        print(f"[DEBUG] Iteration {iteration}: Executing tool: {tool_name} with args: {tool_args}")
                        
                        # Update progress before tool execution
                        if hasattr(self, 'current_rfp_id'):
                            self.update_progress(self.current_rfp_id, _display_name(agent.role), tool_name, "calling_tool")
                        
                        # Execute the tool
                        tool_result = self.execute_tool(tool_name, tool_args)
                        print(f"[DEBUG] Tool result: {tool_result}")
                        
                        tool_calls_data.append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })
                        
                        # Check if this is a PDF generation tool - stop after success
                        if tool_name in ["generate_pdf_proposal", "generate_proposal_pdf"] and tool_result.get("success"):
                            print(f"[DEBUG] PDF generated successfully, stopping iteration")
                            final_content = f"PDF proposal generated successfully. File: {tool_result.get('filename', 'N/A')}"
                            break
                        
                        # Continue conversation with tool result, allowing more tool calls
                        conversation_history += f"\\n\\nTool Result from {tool_name}: {json.dumps(tool_result)}\\n\\nIf you need to call another tool, respond with JSON. Otherwise, provide your final analysis."
                        next_response = agent_model.generate_content(conversation_history)
                        
                        # Handle blocked responses in loop
                        try:
                            response_text = next_response.text.strip()
                        except ValueError as e:
                            print(f"[ERROR] Gemini blocked continuation response: {e}")
                            final_content = f"Tool {tool_name} executed successfully, but continuation blocked by safety filters."
                            break
                    else:
                        # No tool_call key, treat as final response
                        final_content = response_text
                        break
                except json.JSONDecodeError:
                    # Not a tool call, just regular response
                    final_content = response_text
                    break
            else:
                # Max iterations reached
                final_content = response_text
            
            # Save conversation
            conversation = Conversation(
                agent_id=agent.id,
                message=message,
                response=final_content,
                tool_calls=tool_calls_data if tool_calls_data else None
            )
            self.db.add(conversation)
            self.db.commit()
            
            print(f"[DEBUG] Agent execution completed successfully")
            
            return {
                "agent_name": agent.name,
                "response": final_content,
                "tool_calls": tool_calls_data
            }
        except Exception as e:
            print(f"[ERROR] Exception in execute_agent: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool by name with given parameters"""
        tool = self.db.query(Tool).filter(Tool.name == tool_name).first()
        if not tool:
            return {"error": f"Tool {tool_name} not found"}
        
        print(f"[DEBUG] Tool type: {tool.tool_type}, Code: {tool.code}")
        
        # Check if it's an API endpoint (URL) or fallback to API type
        if tool.tool_type == "api" or tool.code.startswith("http"):
            # Call external API endpoint
            import requests
            try:
                print(f"[DEBUG] Calling API: {tool.code} with params: {parameters}")
                response = requests.post(tool.code, json=parameters, timeout=30)
                result = response.json()
                print(f"[DEBUG] API response: {result}")
                return result
            except Exception as e:
                return {"error": str(e)}
        
        elif tool.tool_type == "function":
            # Execute Python code
            try:
                local_vars = {}
                exec(tool.code, globals(), local_vars)
                if tool_name in local_vars:
                    result = local_vars[tool_name](**parameters)
                    return result
                else:
                    return {"error": f"Function {tool_name} not found in code"}
            except Exception as e:
                return {"error": str(e)}
        
        else:
            return {"error": f"Unknown tool type: {tool.tool_type}"}
    
    def run_specific_agent(self, agent_name: str, message: str, rfp_id: int = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a specific agent by name"""
        agent = self.db.query(Agent).filter(Agent.name == agent_name).first()
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        
        result = self.execute_agent(agent, message, context)
        
        if rfp_id:
            self.log_execution(rfp_id, agent.id, {"message": message, "context": context}, result, "completed")
        
        return result
    
    def process_rfp_workflow(self, rfp_id: int) -> Dict[str, Any]:
        """
        Process RFP through the complete agent workflow:
        Sales → Technical → Pricing → Proposal Assembly
        """
        rfp = self.db.query(RFP).filter(RFP.id == rfp_id).first()
        if not rfp:
            return {"error": "RFP not found"}
        
        # Store current RFP ID for tool progress tracking
        self.current_rfp_id = rfp_id
        
        results = {}
        
        # Step 1: Sales Agent
        sales_agent = self.db.query(Agent).filter(Agent.role == "sales").first()
        if sales_agent:
            self.update_progress(rfp_id, "Sales Agent", None, "starting")
            sales_result = self.execute_agent(
                sales_agent,
                f"Analyze this RFP and extract sales summary and objectives:\n\n{rfp.content}"
            )
            rfp.sales_summary = {"response": sales_result["response"], "tool_calls": sales_result.get("tool_calls")}
            results["sales"] = sales_result
            self.update_progress(rfp_id, "Sales Agent", None, "completed")
            self.log_execution(rfp_id, sales_agent.id, {"rfp_content": rfp.content}, sales_result, "completed")
        
        # Step 2: Technical Agent
        technical_agent = self.db.query(Agent).filter(Agent.role == "technical").first()
        if technical_agent and rfp.sales_summary:
            self.update_progress(rfp_id, "Technical Agent", None, "starting")
            
            # Extract requirements from sales summary to make it explicit
            sales_data = rfp.sales_summary.get("response", {})
            if isinstance(sales_data, str):
                try:
                    sales_data = json.loads(sales_data)
                except:
                    sales_data = {}
            
            requirements = sales_data.get("extracted_requirements", sales_data.get("requirements", []))
            if not requirements:
                requirements = [f"Products for {rfp.title}"]
            
            technical_message = f"""YOU HAVE ALL THE INFORMATION YOU NEED IN THE CONTEXT BELOW.

RFP Title: {rfp.title}

EXTRACTED REQUIREMENTS FROM SALES AGENT:
{json.dumps(requirements, indent=2)}

FULL SALES SUMMARY:
{json.dumps(rfp.sales_summary, indent=2)}

INSTRUCTIONS:
1. Use the extracted_requirements list above - DO NOT ask for the RFP document
2. Call match_sku_from_csv ONCE with all requirements
3. Call validate_sku for EACH matched SKU to get complete details
4. Return structured analysis with validated SKU information

Follow the two-step workflow: match → validate."""
            
            technical_result = self.execute_agent(
                technical_agent,
                technical_message,
                context={"sales_summary": rfp.sales_summary, "rfp_title": rfp.title, "extracted_requirements": requirements}
            )
            rfp.technical_matches = {"response": technical_result["response"], "tool_calls": technical_result.get("tool_calls")}
            results["technical"] = technical_result
            self.update_progress(rfp_id, "Technical Agent", None, "completed")
            self.log_execution(rfp_id, technical_agent.id, rfp.sales_summary, technical_result, "completed")
        
        # Step 3: Pricing Agent
        pricing_agent = self.db.query(Agent).filter(Agent.role == "pricing").first()
        if pricing_agent and rfp.technical_matches:
            self.update_progress(rfp_id, "Pricing Agent", None, "starting")
            pricing_result = self.execute_agent(
                pricing_agent,
                "Generate pricing table for the matched SKUs",
                context={"technical_matches": rfp.technical_matches}
            )
            # Guard against blocked/invalid LLM responses
            safe_pricing_response = pricing_result.get("response")
            if safe_pricing_response is None:
                safe_pricing_response = "Pricing agent did not return a response (model blocked or error)."
                # Normalize structure so downstream stages don't crash
                pricing_result["response"] = safe_pricing_response
                pricing_result.setdefault("tool_calls", [])

            rfp.pricing_data = {"response": safe_pricing_response, "tool_calls": pricing_result.get("tool_calls")}
            results["pricing"] = pricing_result
            self.update_progress(rfp_id, "Pricing Agent", None, "completed")
            self.log_execution(rfp_id, pricing_agent.id, rfp.technical_matches, pricing_result, "completed")
            
            # Display RFP Summary after pricing
            rfp_summary = {
                "rfp_title": rfp.title,
                "rfp_id": rfp_id,
                "sales_insights": rfp.sales_summary.get("response", "") if rfp.sales_summary else "",
                "technical_solution": rfp.technical_matches.get("response", "") if rfp.technical_matches else "",
                "pricing_summary": pricing_result.get("response", ""),
                "status": "pricing_completed"
            }
            results["rfp_summary"] = rfp_summary
            print(f"\n{'='*60}")
            print(f"RFP SUMMARY - {rfp.title}")
            print(f"{'='*60}")
            print(f"Sales Insights: {rfp_summary['sales_insights'][:200]}...")
            print(f"Technical Solution: {rfp_summary['technical_solution'][:200]}...")
            print(f"Pricing Summary: {rfp_summary['pricing_summary'][:200]}...")
            print(f"{'='*60}\n")
        
        # Step 4: Proposal Assembly Agent - Generate Draft Proposal (Human Review Required)
        proposal_agent = self.db.query(Agent).filter(Agent.role == "proposal_assembly").first()
        if proposal_agent and rfp.pricing_data:
            # Emit start progress for proposal stage so UI shows running
            self.update_progress(rfp_id, "Proposal Agent", None, "starting")
            
            # Build a comprehensive message with all prior outputs
            sales_text = rfp.sales_summary.get("response", "") if rfp.sales_summary else ""
            technical_text = rfp.technical_matches.get("response", "") if rfp.technical_matches else ""
            pricing_text = rfp.pricing_data.get("response", "") if rfp.pricing_data else ""
            
            proposal_message = f"""Create a comprehensive proposal draft for RFP: {rfp.title}

You have ALL the information you need from the previous agent analysis. DO NOT ask for the RFP document again.

USE THE FOLLOWING COMPLETED ANALYSIS:

=== SALES AGENT ANALYSIS (COMPLETED) ===
{sales_text}

=== TECHNICAL AGENT ANALYSIS (COMPLETED) ===
{technical_text}

=== PRICING AGENT ANALYSIS (COMPLETED) ===
{pricing_text}

Your task: Compile these outputs into a professional proposal draft with the following sections:
1. Executive Summary
2. Understanding of Requirements
3. Proposed Solution
4. Pricing Details
5. Payment Terms
6. Implementation Timeline
7. Terms and Conditions

DO NOT call any PDF generation tools. Generate the content in a structured format for human review."""
            
            # Generate proposal draft WITHOUT calling PDF generation tool
            proposal_result = self.execute_agent(
                proposal_agent,
                proposal_message,
                context={
                    "rfp_title": rfp.title,
                    "rfp_id": rfp_id,
                    "sales_summary": rfp.sales_summary,
                    "technical_matches": rfp.technical_matches,
                    "pricing_data": rfp.pricing_data,
                    "generate_draft_only": True
                }
            )
            
            # Compose proposal sections using prior agent outputs
            proposal_draft = self._compose_proposal_sections(
                rfp,
                llm_text=proposal_result.get("response") or ""
            )
            rfp.proposal_draft = proposal_draft
            rfp.status = "awaiting_approval"
            rfp.approval_status = "pending"
            results["proposal_draft"] = proposal_draft
            results["requires_approval"] = True
            
            self.log_execution(rfp_id, proposal_agent.id, {
                "sales": rfp.sales_summary,
                "technical": rfp.technical_matches,
                "pricing": rfp.pricing_data
            }, {"draft": proposal_draft}, "completed")
            
            print(f"\n{'='*60}")
            print(f"📋 PROPOSAL DRAFT GENERATED - AWAITING HUMAN APPROVAL")
            print(f"{'='*60}")
            print(f"RFP: {rfp.title}")
            print(f"Status: Awaiting human review and approval")
            print(f"Next Step: Review and edit the proposal, then call /rfp/{rfp_id}/approve-proposal")
            print(f"{'='*60}\n")
            
            self.log_execution(rfp_id, proposal_agent.id, {
                "sales": rfp.sales_summary,
                "technical": rfp.technical_matches,
                "pricing": rfp.pricing_data
            }, proposal_result, "completed")
            # Mark proposal stage as completed for progress endpoint
            self.update_progress(rfp_id, "Proposal Agent", None, "completed")
        
        if rfp.status not in {"awaiting_approval", "completed"}:
            rfp.status = "processed"
        self.db.commit()
        
        return results
    
    def _compose_proposal_sections(self, rfp: RFP, llm_text: str) -> Dict[str, Any]:
        """Compose proposal sections using outputs from Sales, Technical, and Pricing agents.
        Falls back to parsing LLM text if needed."""
        sales_raw = (rfp.sales_summary or {}).get("response", "")
        technical_raw = (rfp.technical_matches or {}).get("response", "")
        pricing_raw = (rfp.pricing_data or {}).get("response", "")

        # Helper function to clean and format agent outputs
        def clean_json_to_text(text: str) -> str:
            """Convert JSON-formatted agent output to clean readable text with bullet points."""
            if not text:
                return ""
            
            # Try to parse as JSON first
            try:
                data = json.loads(text)
                lines = []
                
                def format_value(val, indent=0, key_name=""):
                    prefix = "  " * indent
                    bullet = "• " if indent == 0 else "◦ " if indent == 1 else "- "
                    
                    if isinstance(val, dict):
                        # Format dictionary items
                        for k, v in val.items():
                            display_key = k.replace('_', ' ').title()
                            if isinstance(v, (list, dict)):
                                if v:  # Only show if not empty
                                    lines.append(f"{prefix}{bullet}{display_key}:")
                                    format_value(v, indent + 1, display_key)
                            else:
                                # Skip empty values and internal keys
                                if v and not k.startswith('_'):
                                    lines.append(f"{prefix}{bullet}{display_key}: {v}")
                    elif isinstance(val, list):
                        # Format list items
                        for item in val:
                            if isinstance(item, dict):
                                # For dict items in list, show as sub-sections
                                format_value(item, indent, key_name)
                            elif isinstance(item, str):
                                if item.strip():  # Only non-empty strings
                                    lines.append(f"{prefix}{bullet}{item}")
                            else:
                                format_value(item, indent, key_name)
                    else:
                        # Simple value
                        if val and str(val).strip():
                            lines.append(f"{prefix}{bullet}{val}")
                
                format_value(data)
                result = "\n".join(lines)
                # If result is still too JSON-like, add extra formatting
                if result:
                    return result
                else:
                    # Fallback to stringified version
                    return str(data)
            except Exception as e:
                # Not JSON or parsing failed, clean up the text
                text = str(text)
                # Remove JSON markers
                text = text.replace('```json', '').replace('```', '').strip()
                # Remove escaped characters
                text = text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                # If it still looks like JSON structure, try to make it readable
                if text.startswith('{') or text.startswith('['):
                    # Try to extract key-value pairs manually
                    import re
                    # Find patterns like "key": "value" or "key": [items]
                    pattern = r'"([^"]+)"\s*:\s*([^,}\]]+|\[[^\]]+\]|\{[^}]+\})'
                    matches = re.findall(pattern, text)
                    if matches:
                        formatted = []
                        for key, value in matches:
                            clean_key = key.replace('_', ' ').title()
                            clean_value = value.strip().strip('"').strip(',')
                            formatted.append(f"• {clean_key}: {clean_value}")
                        return "\n".join(formatted)
                return text

        sales = clean_json_to_text(sales_raw)
        technical = clean_json_to_text(technical_raw)
        pricing = clean_json_to_text(pricing_raw)

        # Extract specific sections from sales analysis if it's still JSON-like
        objectives_text = ""
        requirements_text = ""
        scope_text = ""
        analysis_text = ""
        
        if sales:
            try:
                # Try to parse sales data for better section extraction
                sales_data = json.loads(sales_raw) if isinstance(sales_raw, str) else sales_raw
                
                # Extract objectives
                if "objectives" in sales_data and isinstance(sales_data["objectives"], list):
                    objectives_text = "\n".join([f"• {obj}" for obj in sales_data["objectives"]])
                
                # Extract requirements
                if "requirements" in sales_data and isinstance(sales_data["requirements"], list):
                    requirements_text = "\n".join([f"• {req}" for req in sales_data["requirements"]])
                
                # Extract scope
                if "scope" in sales_data:
                    scope_text = sales_data["scope"]
                
                # Extract analysis
                if "analysis" in sales_data:
                    analysis_text = sales_data["analysis"]
                    
            except:
                # If parsing fails, use the cleaned text as-is
                pass
        
        # Basic templated composition using available outputs
        newline = "\n"
        double_newline = "\n\n"
        
        objectives_section = objectives_text if objectives_text else (sales[:800] if sales else 'Analysis pending')
        analysis_section = f"Strategic Analysis:{newline}{analysis_text[:500]}" if analysis_text else ""
        
        exec_summary = (
            f"Executive Overview for {rfp.title}{double_newline}"
            f"Key Objectives:{newline}{objectives_section}{newline}"
            f"{newline}{analysis_section}"
        ).strip()

        scope_section = scope_text if scope_text else ""
        requirements_section = requirements_text if requirements_text else (sales[:600] if sales else 'Requirements analysis in progress')
        
        understanding = (
            f"Understanding of Requirements{double_newline}"
            f"Project Scope:{newline}{scope_section}{double_newline}"
            f"Key Requirements:{newline}{requirements_section}"
        ).strip()

        pricing_details = (
            "Pricing Summary:\n\n"
            f"{pricing if pricing else 'Pricing calculation in progress'}\n"
        ).strip()

        payment_terms = (
            "Payment Terms:\n"
            "- 30% advance upon PO\n"
            "- 50% on delivery\n"
            "- 20% on completion and acceptance\n"
        ).strip()

        implementation_timeline = (
            "Implementation Timeline:\n"
            "- Week 1: Kickoff and planning\n"
            "- Weeks 2-4: Procurement and staging\n"
            "- Weeks 5-6: Delivery and installation\n"
            "- Week 7: Testing and handover\n"
        ).strip()

        terms = (
            "Terms and Conditions:\n"
            "- Validity: 30 days from proposal date\n"
            "- Delivery: As per agreed schedule\n"
            "- Warranty: 12 months standard warranty\n"
        ).strip()

        sections = {
            "title": f"Response Proposal for {rfp.title}",
            "sections": {
                "Executive Summary": exec_summary or llm_text[:800],
                "Understanding of Requirements": understanding or llm_text[:600],
                "Pricing Details": pricing_details or "",
                "Payment Terms": payment_terms,
                "Implementation Timeline": implementation_timeline,
                "Terms and Conditions": terms,
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "status": "draft",
                "editable": True
            }
        }

        # If most sections ended up blank, fallback to parser
        if not any(v for v in sections["sections"].values()):
            return self._parse_proposal_to_sections(llm_text)

        return sections

    def _parse_proposal_to_sections(self, proposal_text: str) -> Dict[str, Any]:
        """Fallback: parse freeform LLM text into sections."""
        sections = {
            "title": "Response Proposal",
            "sections": {
                "Executive Summary": "",
                "Understanding of Requirements": "",
                "Proposed Solution": "",
                "Pricing Details": "",
                "Payment Terms": "",
                "Implementation Timeline": "",
                "Terms and Conditions": ""
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "status": "draft",
                "editable": True
            }
        }
        current_section = None
        for line in (proposal_text or "").split('\n'):
            line = line.strip()
            if not line:
                continue
            for section_name in sections["sections"].keys():
                if section_name.lower() in line.lower() and (line.endswith(':') or len(line) < 50):
                    current_section = section_name
                    break
            if current_section and line and section_name.lower() not in line.lower():
                if sections["sections"][current_section]:
                    sections["sections"][current_section] += "\n" + line
                else:
                    sections["sections"][current_section] = line
        if not any(sections["sections"].values()):
            sections["sections"]["Executive Summary"] = (proposal_text or "")[:500]
            sections["sections"]["Proposed Solution"] = (proposal_text or "")[500:]
        return sections
    
    def log_execution(self, rfp_id: int, agent_id: int, input_data: Any, output_data: Any, status: str):
        """Log agent execution for tracking"""
        execution = AgentExecution(
            rfp_id=rfp_id,
            agent_id=agent_id,
            input_data=input_data,
            output_data=output_data,
            status=status,
            completed_at=datetime.utcnow() if status == "completed" else None
        )
        self.db.add(execution)
        self.db.commit()
