"""
Red team Celery tasks for async campaign execution.

Handles background execution of red team campaigns and quick tests.
"""
import time
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.tasks.celery_app import app
from src.database import SessionLocal
from src.red_teaming.service import RedTeamService
from src.red_teaming.template_manager import TemplateInstantiator
from src.models import RedTeamCampaign, RedTeamAttack, ExecutionLog


@app.task(bind=True, max_retries=0, queue="red_team")
def execute_campaign(self, campaign_id: str):
    """
    Execute a red team campaign asynchronously.

    Args:
        campaign_id: Campaign ID to execute
    """
    db = SessionLocal()
    service = RedTeamService(db)

    try:
        campaign = service.get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        # Update status to running
        service.update_campaign_status(campaign_id, "running")

        # Get templates for selected categories
        templates = service.instantiator.get_templates_by_category(
            campaign.attack_categories,
            campaign.project_id
        )

        if not templates:
            service.update_campaign_status(
                campaign_id,
                "failed",
                error_message="No templates found for selected categories"
            )
            return {"error": "No templates found"}

        # Execute attacks
        total_attacks = 0
        successful_attacks = 0
        failed_attacks = 0

        for template in templates:
            # Skip if campaign was cancelled
            db.refresh(campaign)
            if campaign.status == "cancelled":
                break

            # Run multiple attacks per template if configured
            for i in range(campaign.attacks_per_template):
                try:
                    # Create attack record
                    attack = service.create_attack_from_template(
                        campaign_id=campaign_id,
                        project_id=campaign.project_id,
                        template_id=template.id,
                    )

                    if not attack:
                        continue

                    # Execute the attack against LLM
                    start_time = time.time()
                    llm_response, llm_model = _execute_llm_request(
                        attack.attack_prompt,
                        campaign.target_model or "qwen2.5-1.5b-instruct",
                    )
                    execution_time_ms = int((time.time() - start_time) * 1000)

                    # Record result
                    service.record_attack_result(
                        attack_id=attack.id,
                        llm_response=llm_response,
                        llm_model=llm_model,
                        execution_time_ms=execution_time_ms,
                    )

                    total_attacks += 1
                    if attack.was_successful:
                        successful_attacks += 1
                    else:
                        failed_attacks += 1

                    # Update campaign stats periodically
                    if total_attacks % 10 == 0:
                        service.update_campaign_stats(
                            campaign_id,
                            total_attacks,
                            successful_attacks,
                            failed_attacks,
                        )

                except Exception as e:
                    print(f"Error executing attack: {e}")
                    failed_attacks += 1
                    continue

        # Final stats update
        service.update_campaign_stats(
            campaign_id,
            total_attacks,
            successful_attacks,
            failed_attacks,
        )

        # Mark as completed or failed based on threshold
        if campaign.fail_threshold_percent:
            success_rate = (successful_attacks / total_attacks *
                            100) if total_attacks > 0 else 0
            if success_rate > campaign.fail_threshold_percent:
                service.update_campaign_status(
                    campaign_id,
                    "failed",
                    error_message=f"Success rate {success_rate:.1f}% exceeded threshold {campaign.fail_threshold_percent}%"
                )
            else:
                service.update_campaign_status(campaign_id, "completed")
        else:
            service.update_campaign_status(campaign_id, "completed")

        return {
            "campaign_id": campaign_id,
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "failed_attacks": failed_attacks,
        }

    except Exception as e:
        service.update_campaign_status(
            campaign_id,
            "failed",
            error_message=str(e)
        )
        return {"error": str(e)}

    finally:
        db.close()


@app.task(bind=True, max_retries=0, queue="red_team")
def execute_quick_test(
    self,
    project_id: str,
    template_id: str,
    variable_values: Optional[Dict[str, str]] = None,
    target_model: Optional[str] = None,
):
    """
    Execute a quick single attack test.

    Args:
        project_id: Project ID
        template_id: Template ID to use
        variable_values: Optional variable overrides
        target_model: Target model identifier

    Returns:
        Test result dictionary
    """
    db = SessionLocal()
    service = RedTeamService(db)

    try:
        # Create a temporary campaign for the quick test
        campaign = service.create_campaign(
            project_id=project_id,
            user_id="system",  # System user for quick tests
            name=f"Quick Test - {datetime.utcnow().isoformat()}",
            attack_categories=["quick_test"],
            description="Quick single attack test",
            target_model=target_model,
        )

        # Create attack from template
        attack = service.create_attack_from_template(
            campaign_id=campaign.id,
            project_id=project_id,
            template_id=template_id,
            variable_values=variable_values,
        )

        if not attack:
            return {"error": "Failed to create attack from template"}

        # Execute against LLM
        start_time = time.time()
        llm_response, llm_model = _execute_llm_request(
            attack.attack_prompt,
            target_model or "qwen2.5-1.5b-instruct",
        )
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Record result
        attack = service.record_attack_result(
            attack_id=attack.id,
            llm_response=llm_response,
            llm_model=llm_model,
            execution_time_ms=execution_time_ms,
        )

        # Return result
        return {
            "attack_id": attack.id,
            "attack_name": attack.attack_name,
            "attack_type": attack.attack_type,
            "attack_prompt": attack.attack_prompt,
            "llm_response": attack.llm_response,
            "was_successful": attack.was_successful,
            "bypass_score": attack.bypass_score,
            "analysis_notes": attack.analysis_notes,
            "severity": attack.severity,
            "execution_time_ms": attack.execution_time_ms,
            "review_queue_id": attack.review_queue_id,
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()


def _execute_llm_request(prompt: str, model: str, llm_url: str = "http://host.docker.internal:1234") -> tuple[str, str]:
    """
    Execute a request against the LLM.

    Args:
        prompt: Prompt to send
        model: Model identifier
        llm_url: LLM endpoint URL (defaults to host machine's LM Studio)

    Returns:
        Tuple of (response_text, model_used)
    """
    try:
        response = httpx.post(
            f"{llm_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=30,
        )

        response.raise_for_status()
        result = response.json()

        response_text = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        model_used = result.get("model", model)

        return response_text, model_used

    except httpx.RequestError as e:
        return f"[LLM Request Error: {str(e)}]", model

    except Exception as e:
        return f"[Error: {str(e)}]", model
