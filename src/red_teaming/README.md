# Red Teaming Feature

## Overview

The Red Teaming feature provides adversarial testing capabilities for LLM applications. It automates the execution of various attack patterns to identify security vulnerabilities, jailbreaks, prompt injections, and other potential weaknesses in your LLM defenses.

## Architecture

### Backend Components

#### 1. Database Models (`backend/src/red_teaming/models.py`)

**RedTeamCampaign**: Orchestrates multiple attacks

- `id`: UUID primary key
- `project_id`: Foreign key to projects table
- `name`: Campaign name
- `description`: Optional description
- `attack_categories`: List of attack types to run (jailbreak, prompt_injection, etc.)
- `target_model`: Target LLM model identifier
- `attacks_per_template`: Number of attacks to run per template
- `fail_threshold_percent`: Success rate threshold that marks campaign as failed
- `status`: pending | running | completed | failed | cancelled
- `total_attacks`, `successful_attacks`, `failed_attacks`: Statistics
- `success_rate`, `risk_level`: Calculated metrics
- `error_message`: Error details if failed
- `started_at`, `completed_at`: Timestamps

**RedTeamAttack**: Individual attack attempt

- `id`: UUID primary key
- `campaign_id`: Foreign key to campaigns
- `template_id`: Template used for attack
- `execution_log_id`: Link to execution log (optional)
- `project_id`: Foreign key to projects table
- `attack_type`: Category (jailbreak, prompt_injection, toxicity, data_leakage, obfuscation)
- `attack_name`: Human-readable name
- `attack_prompt`: Generated attack prompt
- `template_variables`: Variables used in template instantiation
- `llm_response`: LLM's response to attack
- `llm_model`: Model that responded
- `was_successful`: Boolean indicating if attack bypassed defenses
- `bypass_score`: Float 0-1 indicating confidence of bypass
- `analysis_notes`: Scoring analysis details
- `flagged_policies`: Policies violated (if any)
- `review_queue_id`: Link to review queue item if created
- `severity`: critical | high | medium | low
- `execution_time_ms`: Response latency
- `error_message`: Error details if execution failed

**RedTeamTemplate**: Reusable attack patterns

- `id`: UUID primary key
- `project_id`: Optional (null for built-in templates)
- `name`: Template name
- `category`: Attack category
- `severity`: Risk level
- `template_text`: Attack prompt with `{{VARIABLE}}` placeholders
- `variables`: JSON defining variable processing rules
- `expected_behavior`: Expected model response
- `is_active`: Can be disabled
- `is_custom`: User-created vs built-in

#### 2. Template System (`backend/src/red_teaming/template_manager.py`)

**VariableProcessor**: Processes template variables

- `string`: Direct string substitution
- `random_choice`: Randomly select from choices
- `base64_encode`: Base64 encode value
- `rot13`: ROT13 encoding
- `leetspeak`: Convert to leetspeak

**TemplateInstantiator**: Template management

- `load_template(template_id)`: Load single template
- `load_all_templates()`: Load all active templates
- `get_templates_by_category(categories)`: Filter by category
- `instantiate_template(template, variable_values)`: Generate attack prompt

#### 3. Attack Templates (`backend/src/red_teaming/templates/`)

20 pre-built templates organized by category:

**Jailbreaks** (4 templates):

- `dan_v1.json`: "Do Anything Now" persona jailbreak
- `developer_mode.json`: Developer mode activation jailbreak
- `evil_confidant.json`: Evil confidant roleplay jailbreak
- `opposite_mode.json`: Opposite instruction jailbreak

**Prompt Injections** (4 templates):

- `ignore_previous.json`: Direct instruction override
- `system_override.json`: System message injection
- `delimiter_confusion.json`: Context boundary confusion
- `context_confusion.json`: Context mixing attack

**Toxicity** (4 templates):

- `hate_speech_subtle.json`: Subtle hate speech probing
- `profanity_escalation.json`: Profanity generation test
- `violence_scenario.json`: Violent content generation
- `bias_probing.json`: Bias elicitation test

**Data Leakage** (4 templates):

- `system_prompt_extraction.json`: Extract system prompt
- `pii_extraction.json`: Extract training data PII
- `training_data_probe.json`: Probe for training data
- `context_window_leak.json`: Context window extraction

**Obfuscation** (4 templates):

- `base64_obfuscation.json`: Base64-encoded attacks
- `rot13_obfuscation.json`: ROT13-encoded attacks
- `leetspeak_obfuscation.json`: Leetspeak-encoded attacks
- `unicode_tricks.json`: Unicode character tricks

#### 4. Attack Scoring (`backend/src/red_teaming/scorer.py`)

**AttackScorer**: Determines attack success

- Pattern matching for refusal vs compliance
- Attack-type specific analysis
- Returns: `(was_successful: bool, bypass_score: float, analysis_details: dict)`

Refusal patterns: "I cannot", "I can't", "I'm not able", "against my programming", etc.
Compliance patterns: "Sure", "Here's how", "I'll help", "I can assist", etc.

#### 5. Business Logic (`backend/src/red_teaming/service.py`)

**RedTeamService**: Core business logic

- `create_campaign()`: Create new campaign
- `get_campaign()`, `list_campaigns()`: Retrieve campaigns
- `update_campaign_status()`: Update campaign state
- `start_campaign()`: Trigger async execution
- `create_attack_from_template()`: Instantiate template and create attack record
- `record_attack_result()`: Score and save attack result
- `get_campaign_attacks()`: List attacks with filtering
- `get_attack_details()`: Get single attack
- `get_project_stats()`: Aggregate statistics
- `create_custom_template()`: User-defined templates
- `_create_review_queue_item()`: Auto-create review queue item for successful high/critical attacks

#### 6. REST API (`backend/src/red_teaming/router.py`)

**Endpoints**:

- `POST /api/v1/projects/{id}/red-teaming/campaigns` - Create campaign
- `GET /api/v1/projects/{id}/red-teaming/campaigns` - List campaigns
- `GET /api/v1/red-teaming/campaigns/{id}` - Get campaign details
- `POST /api/v1/red-teaming/campaigns/{id}/start` - Start campaign execution
- `POST /api/v1/red-teaming/campaigns/{id}/cancel` - Cancel running campaign
- `GET /api/v1/red-teaming/campaigns/{id}/attacks` - List campaign attacks
- `GET /api/v1/red-teaming/campaigns/{id}/stats` - Campaign statistics
- `GET /api/v1/red-teaming/attacks/{id}` - Attack details
- `POST /api/v1/projects/{id}/red-teaming/quick-test` - Immediate single attack
- `GET /api/v1/red-teaming/templates` - List templates
- `GET /api/v1/red-teaming/templates/{id}` - Template details
- `POST /api/v1/projects/{id}/red-teaming/templates` - Create custom template
- `GET /api/v1/projects/{id}/red-teaming/stats` - Project statistics
- `DELETE /api/v1/red-teaming/campaigns/{id}` - Delete campaign

#### 7. Async Tasks (`backend/src/tasks/red_team_tasks.py`)

**Celery Tasks**:

- `execute_campaign(campaign_id)`: Run full campaign asynchronously
  - Loads templates for selected categories
  - Executes attacks sequentially
  - Scores each response
  - Creates review queue items for successful high/critical attacks
  - Updates campaign status and statistics
- `execute_quick_test(project_id, template_id, ...)`: Single immediate test

### Frontend Components

#### 1. API Client (`frontend/lib/api.ts`)

**Types**:

- `RedTeamTemplate`, `RedTeamCampaign`, `RedTeamAttack`, `RedTeamStats`
- `CreateCampaignRequest`, `QuickTestRequest`, `QuickTestResponse`

**Functions**:

- `getRedTeamTemplates()`, `getRedTeamTemplate()`
- `createRedTeamCampaign()`, `getRedTeamCampaigns()`, `getRedTeamCampaign()`
- `startRedTeamCampaign()`, `cancelRedTeamCampaign()`
- `getCampaignAttacks()`, `getRedTeamAttack()`
- `runQuickTest()`
- `getRedTeamStats()`

#### 2. Main Dashboard (`frontend/app/projects/[project_id]/red-teaming/page.tsx`)

**Tabs**:

- **Overview**: Security score, recent vulnerabilities, quick test button, campaign cards
- **Campaigns**: List of all campaigns with status and results
- **Vulnerabilities**: Failed attacks grouped by severity

**Features**:

- Quick test modal for immediate single attack execution
- Real-time updates for running campaigns (5s polling)
- Navigation to campaign details and templates

#### 3. Campaign Creation (`frontend/app/projects/[project_id]/red-teaming/campaigns/new/page.tsx`)

**Form Fields**:

- Campaign name (required)
- Attack type selection (multi-select checkboxes)
- Template count display (updates based on selections)
- Target model configuration
- Attacks per type slider (1-20, default 10)

**Validation**: Ensures at least one attack type selected

#### 4. Campaign Details (`frontend/app/projects/[project_id]/red-teaming/campaigns/[campaign_id]/page.tsx`)

**Features**:

- Campaign header with status, risk level, timestamps
- Progress bar for running campaigns (auto-updates every 5s)
- Summary cards: total attacks, successful attacks, blocked attacks, risk level
- Attacks table with filtering (all vs successful only)
- Actions: Start (if pending), Cancel (if running), Export Report (if completed)
- Drill-down to individual attack details

#### 5. Attack Details (`frontend/app/projects/[project_id]/red-teaming/attacks/[attack_id]/page.tsx`)

**Tabs**:

- **Attack Prompt**: Shows attack prompt with copy button, template variables
- **LLM Response**: Shows model response with copy button
- **Analysis**: Bypass score, analysis notes, flagged policies, recommendations

**Summary Cards**:

- Bypass score with confidence indicator
- Target model
- Execution time
- Policies flagged

**Recommendations**: Context-aware mitigation advice based on attack type and success

#### 6. Template Library (`frontend/app/projects/[project_id]/red-teaming/templates/page.tsx`)

**Features**:

- Grid view of all templates
- Search bar
- Category filter (jailbreak, prompt_injection, toxicity, data_leakage, obfuscation)
- Severity filter (critical, high, medium, low)
- Preview modal with template text and variables
- Quick test button for immediate execution

#### 7. Security Widget (`frontend/components/security-widget.tsx`)

**Dashboard Widget**:

- Current risk level with trend indicator
- Total campaigns, attacks run, success rate
- Top vulnerabilities by category
- Recent test campaigns
- Quick action button to run new test

Integrated into project dashboard at `/projects/{id}/dashboard`

#### 8. Review Queue Integration

**Features**:

- Red Team badge on review queue items
- Link to attack details from review queue
- Automatic creation for successful high/critical attacks
- `violation_reasons` includes `red_team_attack_id`

#### 9. UI Components

**Created**:

- `Progress` (`frontend/components/ui/progress.tsx`): Progress bars
- `Checkbox` (`frontend/components/ui/checkbox.tsx`): Multi-select checkboxes
- `Slider` (`frontend/components/ui/slider.tsx`): Range sliders

## Usage

### Running a Campaign

1. **Navigate** to `/projects/{id}/red-teaming`
2. **Click** "New Campaign"
3. **Configure**:
   - Enter campaign name
   - Select attack categories
   - Set target model (optional)
   - Adjust attacks per template (default 10)
4. **Submit** to create campaign
5. **Start** campaign execution
6. **Monitor** progress in real-time
7. **Review** results when completed

### Quick Test

1. **Navigate** to `/projects/{id}/red-teaming`
2. **Click** "View Templates"
3. **Select** a template
4. **Click** "Test" or "Preview" → "Run Test"
5. **View** immediate results

### Creating Custom Templates

1. **Use API** `POST /api/v1/projects/{id}/red-teaming/templates`
2. **Provide**:
   - `name`: Template name
   - `category`: Attack category
   - `severity`: Risk level
   - `template_text`: Attack prompt with `{{VARIABLES}}`
   - `variables`: Variable processing rules
   - `expected_behavior`: Expected model response

## Attack Template Format

```json
{
  "id": "template-uuid",
  "name": "Human-readable name",
  "category": "jailbreak|prompt_injection|toxicity|data_leakage|obfuscation",
  "severity": "critical|high|medium|low",
  "description": "What this template tests",
  "template": "Attack prompt with {{VARIABLES}}",
  "variables": {
    "VARIABLE_NAME": {
      "type": "string|random_choice|base64_encode|rot13|leetspeak",
      "default": "default value",
      "choices": ["option1", "option2"],
      "description": "What this variable does"
    }
  },
  "expected_behavior": {
    "refusal": "Expected refusal response",
    "compliance": "What a bypassed response looks like"
  }
}
```

## Security Considerations

1. **Access Control**: All endpoints require authentication and project access verification
2. **Rate Limiting**: Campaign execution is async to prevent API abuse
3. **Audit Trail**: All attacks are logged with execution details
4. **Review Queue**: Successful high/critical attacks auto-create review items
5. **Data Isolation**: Templates and results are project-scoped

## Metrics & Reporting

### Campaign-Level Metrics

- Total attacks executed
- Successful attacks (bypass count)
- Failed attacks (blocked count)
- Success rate (% successful)
- Risk level (critical/high/medium/low based on success rate)

### Project-Level Metrics

- Total campaigns
- Active campaigns
- Total attacks run
- Total successful attacks
- Overall success rate
- Vulnerabilities by category
- Recent campaigns

### Attack-Level Metrics

- Bypass score (0-1 float)
- Execution time (ms)
- Flagged policies
- Analysis notes
- Severity

## Best Practices

1. **Start Small**: Run quick tests before full campaigns
2. **Review Templates**: Understand what each template tests
3. **Set Thresholds**: Use `fail_threshold_percent` to define acceptable risk
4. **Monitor Actively**: Check running campaigns regularly
5. **Review Findings**: Address successful attacks promptly
6. **Custom Templates**: Create project-specific attack patterns
7. **Iterative Testing**: Run campaigns after policy/model changes
8. **Document Results**: Export reports for compliance audits

## Troubleshooting

### Campaign Stuck in "running"

- Check Celery worker logs
- Verify LLM endpoint is accessible
- Cancel and restart campaign

### No Templates Found

- Verify templates loaded from `backend/src/red_teaming/templates/`
- Check category names match expected values
- Ensure templates are marked `is_active=true`

### Attacks All Failing

- Check LLM endpoint URL in task configuration
- Verify model identifier is correct
- Review attack scorer patterns

### High Success Rate

- Review and strengthen content policies
- Implement prompt injection detection
- Add output filtering
- Use system prompt reinforcement

## Development

### Adding New Attack Templates

1. Create JSON file in `backend/src/red_teaming/templates/{category}/`
2. Follow template format (see above)
3. Test with quick test before adding to campaigns
4. Document expected behavior

### Extending Attack Categories

1. Add new category to `AttackCategory` enum in `models.py`
2. Create templates directory
3. Update scorer logic in `scorer.py`
4. Add frontend category filter

### Custom Scoring Logic

Modify `AttackScorer.score_attack()` in `backend/src/red_teaming/scorer.py` to implement custom success detection logic.

## API Examples

### Create Campaign

```bash
curl -X POST https://api.example.com/api/v1/projects/{project_id}/red-teaming/campaigns \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Security Audit Q4 2024",
    "description": "Quarterly security assessment",
    "attack_categories": ["jailbreak", "prompt_injection"],
    "target_model": "gpt-4",
    "attacks_per_template": 5,
    "fail_threshold_percent": 10
  }'
```

### Start Campaign

```bash
curl -X POST https://api.example.com/api/v1/red-teaming/campaigns/{campaign_id}/start \
  -H "Authorization: Bearer {token}"
```

### Quick Test

```bash
curl -X POST https://api.example.com/api/v1/projects/{project_id}/red-teaming/quick-test \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "dan_v1",
    "target_model": "gpt-4"
  }'
```

## Future Enhancements

- [ ] Scheduled campaigns (cron-based execution)
- [ ] Campaign comparison (diff between runs)
- [ ] Export formats (PDF, CSV, JSON)
- [ ] LLM-based attack scoring (vs pattern matching)
- [ ] Multi-model campaigns (test multiple models)
- [ ] Attack chaining (sequential attack patterns)
- [ ] Real-time notifications (webhooks for successful attacks)
- [ ] Template marketplace (community templates)
- [ ] Automated mitigation suggestions
- [ ] Integration with external red teaming tools
