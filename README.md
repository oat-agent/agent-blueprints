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

## Available Templates

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