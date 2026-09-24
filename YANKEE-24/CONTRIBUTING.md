# Contributing to 55d9czt4sg-ui/YANKEE-24

Thank you for your interest in contributing! This document outlines how to report issues, propose features, and work with the team.

## Reporting Issues

### Before You Report
- Check existing issues to avoid duplicates
- Provide as much detail as possible
- Use the appropriate issue template

### Issue Templates
We have templates to streamline reporting:
- **Bug Report**: Use for unexpected behavior or crashes
- **Feature Request**: Use for new functionality suggestions
- **Documentation**: Use for doc improvements

### Severity & Priority

Issues are prioritized by **severity**:

| Level | Definition |
|-------|-----------|
| **P0 - CRITICAL** | Security vulnerabilities, complete outages, data loss risks |
| **P1 - HIGH** | Core functionality broken, significant performance regression (>20%), critical dependency updates |
| **P2 - MEDIUM** | Feature requests, minor bugs, code quality improvements |
| **P3 - LOW** | Documentation enhancements, nice-to-have optimizations, chores |

## Ownership Model

The repository is organized by functional area:

| Area | Responsibility |
|------|-----------------|
| **Infrastructure & CI/CD** | GitHub Actions, automation, build pipeline |
| **Feature Development** | Core functionality, feature implementation |
| **Documentation** | Setup guides, API docs, usage examples |
| **Testing & QA** | Test coverage, validation, quality assurance |
| **Security & Dependencies** | npm audit, vulnerability scanning, dependency updates |

## Issue Workflow

1. **Intake**: New issues are labeled and assessed
2. **Triage**: Team reviews and assigns priority/owner
3. **Development**: Owner works on fix/feature
4. **Review**: Changes are reviewed for quality
5. **Release**: Merged and included in next release

## Working with Pull Requests

- Link related issues in PR description
- Provide clear explanation of changes
- Request review from appropriate owner
- Ensure all CI checks pass before merge

## Labels

We use labels to organize work:

**Priority Labels**
- `priority:critical` (P0)
- `priority:high` (P1)
- `priority:medium` (P2)
- `priority:low` (P3)

**Type Labels**
- `type:bug` - Bug fix
- `type:feature` - New feature
- `type:documentation` - Docs only
- `type:chore` - Maintenance, tooling

**Status Labels**
- `status:blocked` - Cannot proceed
- `status:in-progress` - Currently being worked on
- `status:review` - Awaiting review

**Area Labels**
- `area:ci-cd` - Infrastructure/automation
- `area:testing` - Tests/QA
- `area:docs` - Documentation

## Response SLAs

We aim to respond to issues within:
- **P0/CRITICAL**: 4 hours
- **P1/HIGH**: 24 hours
- **P2/MEDIUM**: 2-3 days
- **P3/LOW**: As capacity allows

## Code Standards

- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Run linters before submitting

## Questions?

If you have questions, please:
1. Check existing issues and docs
2. File a new issue with `type:documentation` label
3. Contact the relevant area owner

Thank you for contributing!
