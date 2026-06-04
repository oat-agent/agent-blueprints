# Agent Catalog

All **53** agent blueprints in this repository, grouped by category. Each agent has a matching benchmark suite under `benchmarks/suites/<category>/`.

`type` is the OAT factory base type: `worker` (ephemeral task agent), `review` (quality gate), or `persistent` (long-lived coordinator).


## Orchestration — team coordination (persistent) (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `context-manager` | persistent | none | Shared-memory and knowledge curator for an agent team. Builds and maintains a retrieval index over the codebase and team artifacts, distills durable facts an... |
| `orchestrator` | persistent | none | Team orchestrator that decomposes a high-level objective into a dependency-aware task graph, assigns each task to the most suitable specialist agent, dispatc... |
| `planner` | persistent | none | Implementation planner that converts a spec or feature request into a concrete engineering plan: a set of well-scoped issues organized into dependency waves,... |
| `task-router` | persistent | none | Cost-aware routing agent that classifies each incoming task (simple / standard / complex), selects the cheapest model and the most appropriate agent template... |

## Product — intake & specs (2)

| Agent | Type | PR | Description |
|---|---|---|---|
| `bug-triager` | worker | none | Triages incoming issues: reproduces or requests missing repro info, assigns severity and priority, deduplicates against existing issues, applies labels, and ... |
| `requirements-analyst` | worker | optional | Turns a vague feature idea into an unambiguous, testable specification: user stories with acceptance criteria, explicit scope and non-goals, edge cases, and ... |

## Quality — review & code health (6)

| Agent | Type | PR | Description |
|---|---|---|---|
| `code-reviewer` | review | none | Reviews a pull request diff for correctness, security, and maintainability, posting prioritized blocking vs non-blocking comments tied to specific lines, and... |
| `debugger` | worker | optional | Root-cause analysis agent that reproduces a reported bug, isolates the cause with a failing regression test, applies a minimal fix, and proves the fix by tur... |
| `dependency-upgrader` | worker | optional | Safely upgrades project dependencies: prioritizes security and outdated pins, applies upgrades incrementally, reads changelogs for breaking changes, fixes fa... |
| `refactoring-specialist` | worker | optional | Performs behavior-preserving refactors — extracting modules, removing duplication, untangling dependencies, improving naming — guarded by the existing test s... |
| `test-generator` | worker | optional | Generates meaningful unit and property tests for under-tested code, targeting real branches and edge cases (not vanity coverage), and raises measured line an... |
| `verification-agent` | review | none | Independent quality gate that takes a completed task plus its claimed result and objectively verifies it: checks file integrity, runs the build and tests, co... |

## Backend (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `api-builder` | worker | optional | REST and GraphQL API development agent specializing in API design, implementation, documentation, and testing. Handles Express, FastAPI, Spring Boot, and mod... |
| `auth-implementer` | worker | optional | Authentication and authorization implementation agent specializing in secure user management, OAuth2/OIDC flows, JWT handling, RBAC/ABAC systems, and identit... |
| `microservice-architect` | worker | optional | Microservice design and implementation agent focused on service decomposition, inter-service communication, service mesh architecture, and distributed system... |
| `queue-processor` | worker | optional | Message queue and async processing agent specializing in distributed task processing, event-driven architectures, pub/sub systems, and background job managem... |

## Frontend (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `pwa-builder` | worker | optional | Progressive Web App development agent specializing in creating app-like web experiences with service workers, offline functionality, push notifications, and ... |
| `spa-developer` | worker | optional | Single Page Application development agent specializing in modern React, Vue, and Angular applications. Handles state management, routing, component architect... |
| `static-site-generator` | worker | optional | Static site generation agent specializing in Next.js, Gatsby, Nuxt, and modern JAMstack development. Handles content management, SEO optimization, performanc... |

## UI (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `accessibility-auditor` | worker | optional | Web accessibility compliance agent that performs comprehensive accessibility audits, identifies WCAG violations, tests with assistive technologies, and provi... |
| `component-builder` | worker | optional | React, Vue, and Angular component creation agent that builds reusable UI components following modern best practices, accessibility standards, and framework c... |
| `design-system-enforcer` | worker | optional | Design system consistency agent that ensures adherence to design tokens, component usage guidelines, brand standards, and visual consistency across applicati... |
| `responsive-optimizer` | worker | optional | Responsive design and mobile optimization agent that ensures optimal user experience across all devices and screen sizes. Performs responsive testing, mobile... |

## Data (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `analytics-engineer` | worker | optional | Analytics engineering agent specializing in modern data stack implementation, dbt modeling, data warehousing, and business intelligence development. Handles ... |
| `data-quality-validator` | worker | optional | Data quality and validation agent specializing in comprehensive data testing, profiling, monitoring, and anomaly detection. Handles data quality frameworks, ... |
| `ml-pipeline-builder` | worker | optional | Machine learning pipeline development agent specializing in end-to-end ML workflows, data preprocessing, model training, evaluation, and deployment. Handles ... |

## Database (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `data-synchronizer` | worker | optional | Data synchronization agent that handles real-time and batch data sync between heterogeneous databases, manages data transformations, handles conflict resolut... |
| `database-migrator` | worker | optional | Database migration management agent that handles schema migrations, data migrations, and rollback operations across multiple database systems. Provides safet... |
| `schema-validator` | worker | optional | Database schema validation and consistency checker that ensures schema compliance, validates constraints, checks referential integrity, and maintains data qu... |

## DevOps (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `ci-cd-optimizer` | worker | optional | CI/CD pipeline optimization agent that analyzes build performance, identifies bottlenecks, optimizes workflows, reduces build times, and improves deployment ... |
| `docker-builder` | worker | optional | Docker image building and optimization agent that creates efficient, secure, and production-ready container images. Optimizes build processes, reduces image ... |
| `kubernetes-deployer` | worker | optional | Kubernetes deployment management agent that handles application deployments, rollouts, scaling, and lifecycle management. Implements best practices for produ... |
| `terraform-planner` | worker | optional | Infrastructure as Code planning and management agent using Terraform. Analyzes infrastructure changes, generates secure and optimized plans, implements best ... |

## Infrastructure (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `cloud-architect` | worker | optional | Cloud infrastructure design and provisioning agent that creates scalable, secure, and cost-effective cloud architectures. Designs multi-cloud solutions, impl... |
| `cost-optimizer` | worker | optional | Cloud cost optimization and FinOps agent that analyzes cloud spending, identifies cost savings opportunities, and implements automated cost management strate... |
| `disaster-recovery` | worker | optional | Backup and disaster recovery planning agent that designs and implements comprehensive business continuity solutions. Creates automated backup strategies, dis... |
| `network-optimizer` | worker | optional | Network configuration and optimization agent that designs high-performance, secure, and scalable network architectures. Optimizes network performance, implem... |

## Automation (4)

| Agent | Type | PR | Description |
|---|---|---|---|
| `data-pipeline-builder` | worker | optional | ETL/ELT data pipeline creation agent that builds scalable data processing pipelines using Apache Airflow, Apache Spark, dbt, Kafka, and cloud data platforms.... |
| `monitoring-alerter` | worker | optional | Monitoring, alerting, and incident response automation agent that implements comprehensive observability solutions using Prometheus, Grafana, ELK stack, and ... |
| `release-manager` | worker | required | Automated release and deployment management agent that orchestrates software releases, manages deployment pipelines, handles rollbacks, and coordinates multi... |
| `workflow-automator` | worker | optional | Business process and workflow automation agent that designs, implements, and manages automated workflows using Apache Airflow, GitHub Actions, Zapier, and cu... |

## Testing (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `chaos-engineer` | worker | optional | Chaos engineering and fault injection agent that tests system resilience by introducing controlled failures. Validates system behavior under adverse conditio... |
| `e2e-tester` | worker | optional | End-to-end testing agent that validates complete user workflows and business scenarios across the entire application stack. Automates browser interactions, U... |
| `integration-tester` | worker | optional | Integration testing automation agent that validates component interactions, API contracts, and service dependencies. Executes comprehensive integration test ... |

## Performance (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `benchmark-runner` | worker | optional | Automated benchmarking agent that runs comprehensive performance benchmarks across different configurations, compares results against baselines, and detects ... |
| `load-tester` | worker | optional | Load testing and stress testing agent that validates application performance under various load conditions. Executes comprehensive test scenarios with config... |
| `performance-profiler` | worker | optional | Application performance profiling agent that analyzes CPU, memory, and I/O bottlenecks using various profiling tools. Generates comprehensive performance rep... |

## Security (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `compliance-checker` | worker | optional | Validates code and configuration against security compliance frameworks (SOC2, HIPAA, PCI-DSS, CIS benchmarks) and organizational policies. |
| `security-auditor` | worker | optional | Comprehensive security auditor that runs static analysis, secret scanning, and dependency vulnerability checks, then produces a prioritized report and (optio... |
| `vulnerability-scanner` | worker | optional | Dependency-focused vulnerability scanner. Inspects package manifests and lockfiles across languages, cross-references CVE databases, and produces an upgrade ... |

## Documentation (3)

| Agent | Type | PR | Description |
|---|---|---|---|
| `api-documenter` | worker | optional | Generates comprehensive API documentation from code, OpenAPI specs, and inline comments, creating interactive documentation sites. |
| `changelog-maintainer` | worker | optional | Maintains a Keep a Changelog / SemVer-compliant CHANGELOG by parsing conventional commit history and merged PRs since the last release, grouping changes, and... |
| `readme-generator` | worker | optional | Generates and maintains high-quality README and onboarding documentation by analyzing a repository's structure, build system, entry points, and public interf... |
