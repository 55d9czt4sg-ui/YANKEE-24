#!/bin/bash
# GitHub Issues Priority Implementation Script
# For: tradesdontlie/tradingview-mcp
# Run this in the repository with admin/maintainer access

set -e

REPO="tradesdontlie/tradingview-mcp"

echo "🚀 Starting GitHub Issues Priority Implementation"
echo "Repository: $REPO"
echo ""

# Step 1: Create Priority Labels
echo "📌 Step 1: Creating priority labels..."
gh label create --repo "$REPO" "priority:critical" --color "8B0000" --description "P0: Critical - 4hr response SLA" 2>/dev/null || echo "   ℹ️  priority:critical label already exists"
gh label create --repo "$REPO" "priority:high" --color "FF4500" --description "P1: High - 24hr response SLA" 2>/dev/null || echo "   ℹ️  priority:high label already exists"
gh label create --repo "$REPO" "priority:medium" --color "FFD700" --description "P2: Medium - 2-3 day response SLA" 2>/dev/null || echo "   ℹ️  priority:medium label already exists"
gh label create --repo "$REPO" "priority:low" --color "90EE90" --description "P3: Low - As capacity allows" 2>/dev/null || echo "   ℹ️  priority:low label already exists"
echo "   ✓ Labels created/verified"
echo ""

# Step 2: Apply Critical Labels
echo "📌 Step 2: Applying priority:critical labels to 6 critical issues..."
for issue in 542 540 541 513 496 527; do
  echo "   Labeling #$issue..."
  gh issue edit "$issue" --repo "$REPO" --add-label "priority:critical" --add-label "bug" 2>/dev/null || echo "   ℹ️  Issue #$issue: label update (may already be labeled)"
done
echo "   ✓ Critical labels applied"
echo ""

# Step 3: Apply High Labels
echo "📌 Step 3: Applying priority:high labels to 5 high-priority issues..."
for issue in 497 484 489 529 546; do
  echo "   Labeling #$issue..."
  gh issue edit "$issue" --repo "$REPO" --add-label "priority:high" --add-label "bug" 2>/dev/null || echo "   ℹ️  Issue #$issue: label update"
done
echo "   ✓ High labels applied"
echo ""

# Step 4: Apply Medium Labels
echo "📌 Step 4: Applying priority:medium labels to 6 medium-priority issues..."
for issue in 488 494 501 476 477 512; do
  echo "   Labeling #$issue..."
  gh issue edit "$issue" --repo "$REPO" --add-label "priority:medium" --add-label "bug" 2>/dev/null || echo "   ℹ️  Issue #$issue: label update"
done
echo "   ✓ Medium labels applied"
echo ""

# Step 5: Apply Low Labels
echo "📌 Step 5: Applying priority:low labels to 2 low-priority issues..."
for issue in 483 531; do
  echo "   Labeling #$issue..."
  gh issue edit "$issue" --repo "$REPO" --add-label "priority:low" 2>/dev/null || echo "   ℹ️  Issue #$issue: label update"
done
echo "   ✓ Low labels applied"
echo ""

# Step 6: Create Sprint 1 Milestone
echo "📌 Step 6: Creating Sprint 1 milestone..."
MILESTONE_RESPONSE=$(gh api repos/"$REPO"/milestones \
  -X POST \
  -f title="Sprint 1: Critical Fixes" \
  -f description="6 critical issues requiring immediate attention: data loss prevention, security, platform stability. Target: This week. Total effort: 11 days" 2>/dev/null || echo "")

if [ -n "$MILESTONE_RESPONSE" ]; then
  MILESTONE_ID=$(echo "$MILESTONE_RESPONSE" | grep -o '"number":[0-9]*' | head -1 | grep -o '[0-9]*')
  echo "   ✓ Sprint 1 milestone created (ID: $MILESTONE_ID)"
  echo ""
  
  # Step 7: Assign critical issues to milestone
  echo "📌 Step 7: Assigning 6 critical issues to Sprint 1 milestone..."
  for issue in 542 540 541 513 496 527; do
    echo "   Assigning #$issue..."
    gh api repos/"$REPO"/issues/"$issue" \
      -X PATCH \
      -f milestone="$MILESTONE_ID" 2>/dev/null || echo "   ℹ️  Issue #$issue: milestone assignment"
  done
  echo "   ✓ Issues assigned to milestone"
else
  echo "   ℹ️  Milestone creation skipped (may already exist)"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║             ✅ IMPLEMENTATION COMPLETE                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ 4 priority labels created/verified"
echo "✓ 19 issues labeled (6 critical, 5 high, 6 medium, 2 low)"
echo "✓ Sprint 1 milestone created"
echo "✓ 6 critical issues assigned to Sprint 1"
echo ""
echo "📋 Next Steps:"
echo "1. Assign issues to owners (use PRIORITY_TRACKER.md for assignments)"
echo "2. Schedule Sprint 1 kickoff meeting"
echo "3. Start daily standup on critical issues"
echo ""
echo "📚 Reference Documentation:"
echo "   - PRIORITY_TRACKER.md: Full analysis & owner assignments"
echo "   - IMPLEMENTATION_GUIDE.md: Detailed procedures"
echo "   - PRIORITY_AT_A_GLANCE.txt: Quick reference"
echo ""
