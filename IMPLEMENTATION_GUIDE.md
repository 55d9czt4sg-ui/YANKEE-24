# 🎯 GitHub Issues Priority Implementation Guide

**Status**: Ready for team implementation  
**Generated**: 2026-09-28  
**Author**: Automated priority review  

## Context

The repository has 25 open issues requiring triage and prioritization. This guide provides exact steps to implement the priority framework.

---

## Step 1: Create Priority Labels

Run these commands in `tradesdontlie/tradingview-mcp`:

```bash
# Create priority level labels
gh label create "priority:critical" --color "8B0000" --description "P0: Critical - 4hr response SLA"
gh label create "priority:high"     --color "FF4500" --description "P1: High - 24hr response SLA"  
gh label create "priority:medium"   --color "FFD700" --description "P2: Medium - 2-3 day response SLA"
gh label create "priority:low"      --color "90EE90" --description "P3: Low - As capacity allows"
```

---

## Step 2: Apply Priority Labels to Issues

### 🔴 CRITICAL Priority (6 issues)

```bash
# Data loss, security, and platform stability risks
gh issue edit 542 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "bug"
gh issue edit 540 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "bug"
gh issue edit 541 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "security"
gh issue edit 513 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "bug"
gh issue edit 496 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "bug"
gh issue edit 527 --repo tradesdontlie/tradingview-mcp --add-label "priority:critical" --add-label "bug"
```

### 🟠 HIGH Priority (5 issues)

```bash
# Stability and production blockers
gh issue edit 497 --repo tradesdontlie/tradingview-mcp --add-label "priority:high" --add-label "bug"
gh issue edit 484 --repo tradesdontlie/tradingview-mcp --add-label "priority:high" --add-label "bug"
gh issue edit 489 --repo tradesdontlie/tradingview-mcp --add-label "priority:high" --add-label "bug"
gh issue edit 529 --repo tradesdontlie/tradingview-mcp --add-label "priority:high" --add-label "bug"
gh issue edit 546 --repo tradesdontlie/tradingview-mcp --add-label "priority:high"
```

### 🟡 MEDIUM Priority (6 issues)

```bash
# Scalability and UX improvements
gh issue edit 488 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "bug"
gh issue edit 494 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "bug"
gh issue edit 501 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "bug"
gh issue edit 476 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "bug"
gh issue edit 477 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "bug"
gh issue edit 512 --repo tradesdontlie/tradingview-mcp --add-label "priority:medium" --add-label "enhancement"
```

### ⚪ LOW Priority (2 issues)

```bash
# Documentation and incomplete issues
gh issue edit 483 --repo tradesdontlie/tradingview-mcp --add-label "priority:low" --add-label "documentation"
gh issue edit 531 --repo tradesdontlie/tradingview-mcp --add-label "priority:low"
```

---

## Step 3: Create Milestone "Sprint 1: Critical Fixes"

```bash
gh api repos/tradesdontlie/tradingview-mcp/milestones \
  -X POST \
  -f title="Sprint 1: Critical Fixes" \
  -f description="6 critical issues for immediate action. Data loss prevention, security, platform stability. Target: This week. Effort: 11 days"
```

Then assign critical issues to milestone 1:

```bash
for issue in 542 540 541 513 496 527; do
  gh api repos/tradesdontlie/tradingview-mcp/issues/$issue \
    -X PATCH \
    -f milestone=1
done
```

---

## Step 4: Assign Issues to Owners

### Critical Path Assignments

| Issue | Title | Owner | Priority |
|-------|-------|-------|----------|
| **#541** | Privacy leak (Pine source) | Security Lead | 🔴 TODAY |
| **#540** | API returns wrong data | Core API Owner | 🔴 THIS WEEK |
| **#527** | Alert deletion bug | Core API Owner | 🔴 THIS WEEK |
| **#513** | Script overwrite | Editor Owner | 🔴 THIS WEEK |
| **#542** | Session continuity | Platform Lead | 🔴 THIS WEEK |
| **#496** | MSIX crash | Windows Build Lead | 🔴 NEXT WEEK |

**Owner assignment example:**

```bash
# Assign #541 to security team member (replace "username" with actual GitHub username)
gh issue edit 541 --repo tradesdontlie/tradingview-mcp --assignee username
```

---

## Step 5: Create GitHub Project Board (Optional but Recommended)

Create a new GitHub Project with columns:
- Backlog
- Ready (Sprint 1 critical issues)
- In Progress
- Review
- Done

Add all 6 critical issues to the "Ready" column.

---

## Step 6: Communicate to Team

Create a team announcement or post that includes:

```
🚨 PRIORITY REVIEW COMPLETE

25 open issues have been triaged and prioritized:
- 🔴 6 CRITICAL issues (this week)
- 🟠 5 HIGH issues (week 2)
- 🟡 6 MEDIUM issues (backlog)
- ⚪ 2 LOW issues (polish)

CRITICAL PATH (START THIS WEEK):
#541 Privacy leak → Security Lead
#540 Wrong data → Core API Owner
#527 Alert deletion → Core API Owner
#513 Script overwrite → Editor Owner
#542 Session loss → Platform Lead
#496 MSIX crash → Windows Build Lead (planning starts now)

See PRIORITY_TRACKER.md for full details.
```

---

## Step 7: Track Progress

### Weekly Sync Agenda

1. **Monday**: Review Sprint 1 blockers (critical issues)
2. **Wednesday**: Check progress on top 3 issues
3. **Friday**: Sprint wrap-up and preview of next week's work

### Success Criteria

- [ ] All 6 critical issues labeled and assigned by EOW
- [ ] Sprint 1 milestone created and populated
- [ ] Team leads have confirmed ownership
- [ ] #541 (privacy) resolved by end of this week
- [ ] #540, #527, #513 in progress by end of this week

---

## Issue-by-Issue Owner Recommendations

### This Week (Days 1-5)

| # | Issue | Owner | Effort | Why First |
|---|-------|-------|--------|-----------|
| 541 | Privacy leak | Security Lead | 1 day | **Compliance risk** |
| 540 | Wrong data | Core API Owner | 2 days | **Trust killer** |
| 527 | Alert deletion | Core API Owner | 1 day | **Data loss** |
| 513 | Script overwrite | Editor Owner | 2 days | **Data loss** |
| 542 | Session loss | Platform Lead | 2 days | **Reliability** |

### Week 2 (Days 6-10)

| # | Issue | Owner | Effort | Why Next |
|---|-------|-------|--------|----------|
| 496 | MSIX crash | Windows Build Lead | 3 days | **Platform blocker** |
| 546 | Privacy framework | Security Lead | 2 days | **Production readiness** |
| 497 | Plot corruption | Charting Owner | 2 days | **UX impact** |
| 484 | Replay stuck | Charting Owner | 2 days | **Cascading failures** |
| 489 | Layout switch | Layout Manager | 1 day | **Silent failure** |

---

## Implementation Checklist

```
Priority Framework Setup:
  [ ] Create 4 priority labels (critical, high, medium, low)
  [ ] Apply labels to all 25 issues
  [ ] Create "Sprint 1: Critical Fixes" milestone
  [ ] Assign 6 critical issues to milestone

Owner Assignment:
  [ ] Assign #541 to Security Lead
  [ ] Assign #540 to Core API Owner  
  [ ] Assign #527 to Core API Owner
  [ ] Assign #513 to Editor Owner
  [ ] Assign #542 to Platform Lead
  [ ] Assign #496 to Windows Build Lead

Communication:
  [ ] Announce priorities to team
  [ ] Share PRIORITY_TRACKER.md with stakeholders
  [ ] Schedule Sprint 1 kickoff with critical path owners
  [ ] Set up daily standup tracking for critical issues

Tracking:
  [ ] Create GitHub Project board (optional)
  [ ] Link sprint board to Slack/wiki
  [ ] Weekly sync scheduled
  [ ] Progress metrics defined
```

---

## Key Metrics to Track

### Burn-Down (Sprint 1)
- Target: Resolve all 6 critical issues in 2 weeks
- Measurement: Issues closed / total critical issues per day

### By Category
- **Silent Failures** (8 issues): Should decrease as validation improves
- **Data Loss** (4 issues): Critical priority; all should have fixes by end of week 2
- **Platform Blockers** (2 issues): Must unblock enterprise adoption

### Owner Capacity
- Core API Owner: 4 days capacity (2 critical issues)
- Windows Build Lead: 5 days capacity (2 critical issues)
- Charting Owner: 5 days capacity (1 high + 2 medium)

---

## Reference

Full analysis document: `PRIORITY_TRACKER.md`
PR with implementation: `#7 on 55d9czt4sg-ui/YANKEE-24`

**Questions?** See PRIORITY_TRACKER.md for detailed rationale on each issue.
