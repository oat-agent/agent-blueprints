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

## Available Templates (43 total)

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

## Contributing

1. Create new template in appropriate category directory
2. Follow the schema specification
3. Update registry.yaml
4. Test with OAT factory
5. Submit PR

## License

MIT License - See LICENSE file for details