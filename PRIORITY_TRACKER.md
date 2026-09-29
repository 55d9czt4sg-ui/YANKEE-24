# GitHub Issues Priority & Owner Assignment

**Generated**: 2026-09-28  
**Review Period**: Latest 25 open issues  
**Status**: Ready for implementation

---

## 🔴 CRITICAL Priority (P0: 4hr Response SLA)
**Fix this sprint — Data loss & security risks**

| Issue | Title | Current Status | Owner | Effort | Start Date |
|-------|-------|--------|-------|--------|------------|
| **#542** | `tv_launch` kills running TradingView before checking whether CDP is already up | OPEN | Platform Lead | 2 days | This week |
| **#540** | `data_get_ohlcv` silently ignores `symbol`, `timeframe` and `bars` — returns the active chart instead | OPEN | Core API Owner | 2 days | This week |
| **#541** | `data_get_study_values` now returns the full base64 Pine source of protected scripts — 131 KB for 4 studies | OPEN | Security Lead | 1 day | **TODAY** |
| **#513** | `pine_open` / `pine_new` don't rebind the editor — saves silently overwrite the wrong script | OPEN | Editor/File Owner | 2 days | This week |
| **#496** | MSIX launch: sync EPERM bypasses fallback; local-copy crashes (STATUS_BREAKPOINT) ~1s in with false-positive success | OPEN | Windows Build Lead | 3 days | Next week |
| **#527** | z.coerce.boolean() reads the string "false" as true (alert_delete with delete_all: "false" deletes every alert) | OPEN | Core API Owner | 1 day | This week |

**Subtotal**: 11 days effort · 2 owners have 2 issues each

---

## 🟠 HIGH Priority (P1: 24hr Response SLA)
**Next 2 weeks — Stability and production blockers**

| Issue | Title | Current Status | Owner | Effort | Target Week |
|-------|-------|--------|-------|--------|-------------|
| **#497** | `indicator_set_inputs` corrupts user Pine studies — input registration wiped, all plots go empty until layout reload | OPEN | Charting Owner | 2 days | Week 2 |
| **#484** | `replay_stop` reports success but replay never exits — is_replay_started stays true, and draw_shape silently no-ops while stuck | OPEN | Replay/Charting Owner | 2 days | Week 2 |
| **#489** | `layout_switch` reports success but does not actually switch the active layout | OPEN | Layout Manager | 1 day | Week 2 |
| **#529** | `tv_launch` fails on MSIX (Store) installs: uncaught sync spawn EPERM skips local-copy fallback; copied binary then crashes without --no-sandbox | OPEN | Windows Build Lead | 2 days | Week 2 |
| **#546** | Privacy framework for local trade data — gitignore real logs, ship public examples for onboarding | OPEN | Security Lead | 2 days | Week 2 |

**Subtotal**: 9 days effort · 5 owners (1 issue each)

---

## 🟡 MEDIUM Priority (P2: 2-3 day Response SLA)
**Backlog / Next month — Scalability & UX improvements**

| Issue | Title | Current Status | Owner | Effort | Type |
|-------|-------|--------|-------|--------|------|
| **#488** | `draw_shape` silently fails (entity_id: null) on charts with many pre-existing drawings | OPEN | Drawing Owner | 1 day | Bug |
| **#494** | Chart tabs not discoverable via /json/list — CDP target discovery fails on certain launches (webview guest frames?) | OPEN | Core API Owner | 1 day | Bug |
| **#501** | `chart_scroll_to_date` silently no-ops when target date is outside already-loaded bars | OPEN | Charting Owner | 1 day | Bug |
| **#476** | `ui_evaluate` silently returns `{}` for any async expression | OPEN | UI Automation Owner | 1 day | Bug |
| **#477** | `ui_mouse_click` sends left clicks as "no button pressed", and reports success anyway | OPEN | UI Automation Owner | 1 day | Bug |
| **#512** | Proposal: load deeper history without zooming (data_load_history) + let data_get_ohlcv return more than 500 bars | OPEN | Product Manager | TBD | Enhancement |

**Subtotal**: 6 days effort · 6 owners (1 issue each)

---

## ⚪ LOW Priority (P3: As Capacity Allows)
**Polish, documentation, and incomplete issues**

| Issue | Title | Current Status | Owner | Effort | Type |
|-------|-------|--------|-------|--------|------|
| **#483** | Docs: SETUP_GUIDE Step 2 points to ~/.claude/.mcp.json, a path Claude Code never reads — server silently never loads | OPEN | Documentation Owner | 0.5 days | Docs |
| **#531** | trading | OPEN | Product Manager | TBD | Needs Scope |

**Subtotal**: 0.5 days effort · 2 owners

---

## 📊 Workload Summary by Owner

| Owner Role | Issues | Priority Breakdown | Total Effort | Critical Path |
|------------|--------|-------------------|--------------|----------------|
| **Core API Owner** | #540, #527, #494 | 2 Critical + 1 Medium | 4 days | **CRITICAL** |
| **Security Lead** | #541, #546 | 1 Critical + 1 High | 3 days | **CRITICAL** |
| **Platform Lead** | #542 | 1 Critical | 2 days | **CRITICAL** |
| **Windows Build Lead** | #496, #529 | 1 Critical + 1 High | 5 days | **CRITICAL** |
| **Editor/File Owner** | #513 | 1 Critical | 2 days | **CRITICAL** |
| **Charting Owner** | #497, #501, #484 | 1 High + 2 Medium | 5 days | High |
| **UI Automation Owner** | #476, #477 | 2 Medium | 2 days | Medium |
| **Drawing Owner** | #488 | 1 Medium | 1 day | Medium |
| **Layout Manager** | #489 | 1 High | 1 day | High |
| **Documentation Owner** | #483 | 1 Low | 0.5 days | Low |
| **Product Manager** | #512, #531 | 1 Medium + 1 Low (Scope) | TBD | Backlog |

---

## 🎯 Recommended Execution Timeline

### **This Week (Days 1-5)**
1. **#541** (Security) → Security Lead — Data privacy exposure  
2. **#540** (Core API) → Core API Owner — Wrong data being returned  
3. **#527** (Core API) → Core API Owner — Alert deletion bug  
4. **#513** (Editor) → Editor Owner — Script overwrite data loss  
5. **#542** (Platform) → Platform Lead — Session continuity  

**Parallel track**: Start planning #496 (Windows Build) for next week

### **Week 2 (Days 6-10)**
1. **#496** (Windows Build) → Windows Build Lead — MSIX crash  
2. **#546** (Security) → Security Lead — Privacy framework  
3. **#497** (Charting) → Charting Owner — Plot corruption  
4. **#484** (Replay) → Charting Owner — Replay stuck  
5. **#489** (Layout) → Layout Manager — Layout switch fails  
6. **#529** (Windows Build) → Windows Build Lead — MSIX install  

### **Week 3+ (Capacity-Based)**
- **HIGH** priority remaining work  
- **MEDIUM** priority backlog fixes  
- **LOW** priority / Polish  

---

## 🔍 Key Patterns in Issues

### Silent Failures (8 issues)
Issues where the API/function reports success but doesn't actually work:
- #540 (data_get_ohlcv)
- #542 (tv_launch)
- #489 (layout_switch)
- #484 (replay_stop)
- #488 (draw_shape)
- #501 (chart_scroll_to_date)
- #476 (ui_evaluate)
- #477 (ui_mouse_click)

**Recommendation**: Add assert-mode testing & response validation

### Data Loss (4 issues)
- #513 (script overwrite)
- #527 (alert deletion)
- #541 (data exposure)
- #497 (plot corruption)

**Recommendation**: Add transaction/rollback safety checks

### Platform Blockers (2 issues)
- #496, #529 (MSIX/Windows launch failures)

**Recommendation**: Highest priority for enterprise adoption

---

## 📝 Implementation Checklist

- [ ] Assign issues to owners (GitHub issue assignment)
- [ ] Apply priority labels to all issues
- [ ] Create GitHub project board with "Critical", "High", "Medium", "Low" columns
- [ ] Schedule team sync to discuss critical issues
- [ ] Create milestone "Sprint 1: Critical Fixes" for #542, #540, #541, #513, #496, #527
- [ ] Document any blockers or dependencies in issue comments
- [ ] Update team Slack/wiki with this prioritization

---

## Notes

**Review Date**: 2026-09-28 12:10 UTC  
**Total Open Issues Reviewed**: 25  
**Total Critical Issues**: 6  
**Total High Issues**: 5  
**Estimated Critical Path Effort**: ~20 days across distributed team  

This prioritization focuses on:
1. **Data loss prevention** (silent failures, overwrites)
2. **Security & privacy** (code exposure)
3. **Platform stability** (launch failures, store distribution)
4. **User trust** (false-positive success reports)
