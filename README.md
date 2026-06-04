# Agent Blueprints

Official template repository for Open Agent Teams (OAT) - specialized agent templates for automated software engineering tasks.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/oat-agent/agent-blueprints.git

# Use with OAT factory
registry := factory.NewTemplateRegistry()
registry.FetchFromRegistry("https://raw.githubusercontent.com/oat-agent/agent-blueprints/main")

# Create agent from template
factory.CreateFromTemplate(ctx, "security-auditor", map[string]interface{}{
    "task": "Audit authentication system",
    "repository": "my-repo",
})
```

> **Quality at a glance:** every template is validated against the real OAT factory
> schema and graded by a two-layer benchmark (static + behavioral). See
> [`benchmarks/`](benchmarks/README.md) and [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

## Available Templates (53 total)

### Security (3 templates)
- **security-auditor** - Comprehensive security vulnerability scanning
- **vulnerability-scanner** - Dependency and CVE scanning
- **compliance-checker** - Security compliance validation

### Performance (3 templates)
- **performance-profiler** - Application performance analysis
- **load-tester** - Load and stress testing
- **benchmark-runner** - Automated benchmarking

### Database (3 templates)
- **database-migrator** - Database migration management
- **schema-validator** - Schema validation and consistency
- **data-synchronizer** - Cross-database data synchronization

### Testing (3 templates)
- **integration-tester** - Integration test automation
- **e2e-tester** - End-to-end testing
- **chaos-engineer** - Chaos engineering and fault injection

### DevOps (4 templates)
- **ci-cd-optimizer** - CI/CD pipeline optimization
- **docker-builder** - Container image optimization
- **kubernetes-deployer** - Kubernetes deployment management
- **terraform-planner** - Infrastructure as Code planning

### UI (4 templates)
- **component-builder** - React/Vue/Angular component creation
- **accessibility-auditor** - Web accessibility compliance
- **design-system-enforcer** - Design system consistency
- **responsive-optimizer** - Responsive design and mobile optimization

### Backend (4 templates)
- **api-builder** - REST/GraphQL API development
- **microservice-architect** - Microservice design and implementation
- **auth-implementer** - Authentication and authorization
- **queue-processor** - Message queue and async processing

### Automation (4 templates)
- **workflow-automator** - Business process automation
- **data-pipeline-builder** - ETL/ELT pipeline creation
- **release-manager** - Automated release management
- **monitoring-alerter** - Monitoring and incident response

### Frontend (3 templates)
- **spa-developer** - Single Page Application development
- **static-site-generator** - Static site generation (Next.js, Gatsby)
- **pwa-builder** - Progressive Web App creation

### Data (3 templates)
- **ml-pipeline-builder** - Machine learning pipeline creation
- **analytics-engineer** - Analytics and BI development
- **data-quality-validator** - Data quality and validation

### Infrastructure (4 templates)
- **cloud-architect** - Cloud infrastructure design
- **network-optimizer** - Network configuration and optimization
- **disaster-recovery** - Backup and disaster recovery planning
- **cost-optimizer** - Cloud cost optimization and FinOps

### Documentation (3 templates)
- **api-documenter** - API documentation generation
- **readme-generator** - README automation
- **changelog-maintainer** - Changelog management

### Orchestration (4 templates) — *the autonomous-team coordination layer*
- **orchestrator** (`persistent`) - Decomposes an objective into a dependency-aware task graph and dispatches specialists
- **planner** (`persistent`) - Turns a spec into waved, independently-shippable issues with contracts
- **context-manager** (`persistent`) - Shared memory / retrieval index and decision log for the team
- **task-router** (`persistent`) - Cost-aware model + agent selection per task

### Quality (6 templates)
- **code-reviewer** (`review`) - PR review with blocking/non-blocking verdict
- **verification-agent** (`review`) - Independent pass/fail gate with evidence
- **test-generator** - Meaningful unit/property tests to raise coverage
- **debugger** - Root-cause analysis with a regression test
- **refactoring-specialist** - Behavior-preserving refactors guarded by tests
- **dependency-upgrader** - Safe, build-green dependency upgrades

### Product (2 templates)
- **requirements-analyst** - Turns ideas into testable specs with acceptance criteria
- **bug-triager** - Severity/priority triage, dedup, and routing

## Building an autonomous agent team

The original templates are all `worker`s — hands that produce artifacts. A team that
runs itself also needs **coordination** and **quality gates**, which the new
categories provide:

```
                 ┌─────────────────────────────────────────────┐
   objective ──▶ │ planner → orchestrator → task-router         │  (persistent)
                 └───────────────┬─────────────────────────────┘
                                 ▼  dispatches
        ┌────────────────────────────────────────────────────┐
        │  workers: api-builder, auth-implementer, debugger,  │
        │  refactoring-specialist, test-generator, ...        │  (worker)
        └───────────────┬────────────────────────────────────┘
                        ▼  outputs reviewed by
            code-reviewer → verification-agent                  (review)
                        ▼
                  context-manager keeps shared memory current   (persistent)
```

`requirements-analyst` and `bug-triager` feed work in at the top; the review agents
gate work on the way out.

## Template Schema

Each template follows the OAT AgentTemplate specification:

```yaml
apiVersion: agents.oat.dev/v1
kind: AgentTemplate
metadata:
  name: template-name
  version: 1.0.0
  author: author-name
spec:
  capabilities:
    tools: []      # Required tools
    apis: []       # API integrations
    models: {}     # AI models
  resources:       # Resource requirements
  prompt:          # Agent instructions
  behavior:        # Execution behavior
  success:         # Success conditions
```

## Integration with OAT

This repository contains ONLY template definitions. The OAT factory (in the main open-agent-teams repo) fetches and instantiates these templates.

## Benchmark

Templates are evaluated by a two-layer harness in [`benchmarks/`](benchmarks/README.md):

- **Layer 1 — static validation** scores every template (0–100) against the *real*
  OAT factory rules (`internal/factory/validator.go`): allowed `base.type`
  (`worker`/`review`/`persistent`), required metadata, valid tool version
  constraints, memory format, `pr_creation` enum, `{task` placeholder, plus
  registry↔filesystem consistency and benchmark-suite coverage.
- **Layer 2 — behavioral scoring** grades the *output* an agent produces for a
  scenario against a domain-specific, weighted rubric (with hard `critical` gates
  for safety invariants like "no leaked secrets" and "build still passes").

```bash
pip install -r benchmarks/requirements.txt

python -m benchmarks.framework.cli validate                 # score all templates
python -m benchmarks.framework.cli validate --min-score 80 --fail-on major   # CI gate
python -m benchmarks.framework.cli lint-suites --strict     # validate the suites
python -m benchmarks.framework.cli score \
  --suite benchmarks/suites/security/security-auditor.benchmark.yaml \
  --outputs benchmarks/sample-runs/security-auditor-pass
```

Every template has a matching suite in `benchmarks/suites/<category>/`.

## Documentation

- [`docs/AGENT_CATALOG.md`](docs/AGENT_CATALOG.md) - all 53 agents, grouped, with roles and factory types
- [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) - how the benchmark works and how to run it
- [`benchmarks/README.md`](benchmarks/README.md) - full benchmark methodology and check reference
- [`benchmarks/schema/benchmark-suite.schema.yaml`](benchmarks/schema/benchmark-suite.schema.yaml) - suite file format

## Contributing

1. Create the template in the appropriate category directory (`templates/<category>/`)
2. Follow the schema specification (and keep `base.type` ∈ `worker`/`review`/`persistent`)
3. Add an entry to `registry.yaml`
4. Add a matching benchmark suite under `benchmarks/suites/<category>/`
5. Run `python -m benchmarks.framework.cli validate --fail-on major` and `lint-suites --strict`
6. Submit a PR

## License

MIT License - See LICENSE file for details