import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workprint.cli import main
from workprint.copy_audit import (
    AuditWaiver,
    CopyQualityAuditor,
    structural_review,
)
from workprint.executive import (
    UNSLOP_TEXT_PINNED_REVISION,
    build_executive_report,
    classify_decision_leadership,
)
from workprint.guided import GuidedOptions, run_guided
from workprint.models import (
    CopyQualityAudit,
    ExecutiveFinding,
    Investigation,
    Observation,
    TimelineEvent,
    TimelineInvolvement,
)
from workprint.reports import render_json_dict, render_markdown
from workprint.timeline import build_timeline


class ExecutiveReportTests(unittest.TestCase):
    def test_missing_project_goal_is_unknown(self):
        investigation = self._investigation([
            self._obs("OBS-1", "Human stated: Build something useful."),
        ])

        report = build_executive_report(investigation)

        goal = report.executive_brief.project_goal
        self.assertEqual(goal.status, "unknown")
        self.assertIn("No explicit statement", goal.summary)

    def test_implementation_decision_does_not_become_project_goal(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "google-docs stated a decision or acceptance: We should use deterministic parsing for static Google Docs exports.",
                source="google-docs",
                source_type="document",
                activity="decision",
            ),
            self._obs(
                "OBS-2",
                "Human stated a decision or acceptance: Let's call the project Workprint.",
                activity="decision",
            ),
        ])

        goal = build_executive_report(investigation).executive_brief.project_goal

        self.assertEqual(goal.status, "unknown")
        self.assertEqual(
            goal.summary,
            "No explicit statement of the project's overall goal appears in the supplied evidence.",
        )

    def test_explicit_project_goal_uses_evidence(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Human stated: The project goal is to explain work clearly.",
            ),
        ])

        report = build_executive_report(investigation)

        goal = report.executive_brief.project_goal
        self.assertEqual(goal.status, "explicitly_supported")
        self.assertEqual(goal.evidence_ids, ("OBS-1",))

    def test_project_goal_accepts_project_purpose_language(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Human stated: This project helps people reconstruct evidence-backed work history.",
            ),
        ])

        goal = build_executive_report(investigation).executive_brief.project_goal

        self.assertEqual(goal.status, "explicitly_supported")
        self.assertIn("reconstruct evidence-backed work history", goal.summary)

    def test_output_classifications(self):
        produced = self._investigation([
            self._obs(
                "OBS-1",
                "Human reported implementation activity: I built report.md as the project report deliverable.",
                activity="implementation",
            )
        ])
        planned = self._investigation([
            self._obs(
                "OBS-1",
                "Human suggested: We should generate a JSON report.",
                activity="suggestion",
            )
        ])
        missing = self._investigation([
            self._obs("OBS-1", "Human asked: What happened?", activity="question")
        ])

        self.assertEqual(
            build_executive_report(produced).executive_brief.project_outputs[0].status,
            "explicitly_produced",
        )
        self.assertEqual(
            build_executive_report(planned).executive_brief.project_outputs[0].status,
            "referenced_or_planned",
        )
        self.assertEqual(
            build_executive_report(missing).executive_brief.project_outputs[0].status,
            "not_established",
        )

    def test_low_level_fixture_or_component_output_is_not_project_output(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "google-docs reported implementation activity: I added a fixture that represents document-level metadata and paragraph blocks.",
                source="google-docs",
                source_type="document",
                activity="implementation",
            ),
            self._obs(
                "OBS-2",
                "figma stated: Figma component Report Card; component metadata: component_key=cmp-report-card, component_name=Report Card; explicit evidence metadata present",
                source="figma",
                source_type="design",
                activity="artifact",
            ),
        ])

        outputs = build_executive_report(investigation).executive_brief.project_outputs

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].status, "not_established")
        self.assertIn("No completed or planned", outputs[0].summary)

    def test_key_milestones_filter_routine_observations(self):
        observations = [
            self._obs("OBS-1", "Human stated: Routine note."),
            self._obs(
                "OBS-2",
                "Human stated a decision or acceptance: I chose Markdown.",
                activity="decision",
            ),
        ]
        investigation = self._investigation(observations)

        milestones = build_executive_report(investigation).key_milestones

        self.assertEqual(len(milestones), 1)
        self.assertEqual(milestones[0].evidence_ids, ("OBS-2",))

    def test_executive_milestones_deduplicate_supported_near_duplicates(self):
        observations = [
            self._obs(
                "OBS-1",
                "Human stated a decision or acceptance: Let's use Workprint as the project name.",
                activity="decision",
                ref="claude.json#1",
            ),
            self._obs(
                "OBS-2",
                "Human stated a decision or acceptance: Let's call the project Workprint.",
                activity="decision",
                ref="chatgpt.json#1",
            ),
            self._obs(
                "OBS-3",
                "Human reported implementation activity: I created the repository and pushed the initial files.",
                activity="implementation",
                ref="claude.json#2",
            ),
            self._obs(
                "OBS-4",
                "Human reported implementation activity: I created the GitHub repository and pushed the first commit.",
                activity="implementation",
                ref="chatgpt.json#2",
            ),
        ]
        investigation = self._investigation(observations)

        milestones = build_executive_report(investigation).key_milestones

        self.assertEqual(len(milestones), 2)
        self.assertEqual(milestones[0].evidence_ids, ("OBS-1", "OBS-2"))
        self.assertEqual(milestones[1].evidence_ids, ("OBS-3", "OBS-4"))
        self.assertIn("Decision:", milestones[0].title)
        self.assertNotIn("stated a decision", milestones[0].summary)

    def test_evidence_sources_are_separate_from_project_tools(self):
        no_tool = self._investigation([
            self._obs(
                "OBS-1",
                "ChatGPT suggested: A report structure could help.",
                actor="ChatGPT",
                source="ChatGPT",
            )
        ])
        explicit_tool = self._investigation([
            self._obs(
                "OBS-1",
                "Human stated: We used Figma to inspect the design.",
                source="ChatGPT",
            )
        ])

        no_tool_overview = build_executive_report(no_tool).project_overview
        tool_overview = build_executive_report(explicit_tool).project_overview

        self.assertIn("does not explicitly establish", no_tool_overview[1].summary)
        self.assertIn("Figma", tool_overview[1].summary)
        self.assertIn("ChatGPT", no_tool_overview[0].summary)

    def test_fixture_boundary_is_reported_when_all_sources_are_fixtures(self):
        investigation = self._investigation(
            [self._obs("OBS-1", "Human stated: Sample note.")],
            source_files=("fixtures/chatgpt/sample-conversations.json",),
        )

        report = build_executive_report(investigation)
        rendered = render_markdown(investigation)

        self.assertTrue(report.metadata["fixture_boundary"]["all_selected_evidence_is_fixture"])
        self.assertIn("sample fixture evidence", report.project_overview[0].summary)
        self.assertIn("sample fixture evidence", report.investigation_assurance)
        self.assertIn("sample fixture evidence", rendered)

    def test_all_decision_leadership_labels(self):
        human_decision = [
            self._obs("OBS-1", "Human stated a decision: I choose Markdown.", activity="decision")
        ]
        ai_proposed_human_decided = [
            self._obs(
                "OBS-1",
                "ChatGPT suggested: Use Markdown.",
                actor="ChatGPT",
                source="ChatGPT",
                activity="suggestion",
            ),
            self._obs("OBS-2", "Human stated a decision: I choose Markdown.", activity="decision"),
        ]
        jointly_shaped = [
            self._obs("OBS-1", "Human asked: Should we use Markdown?", activity="question"),
            self._obs(
                "OBS-2",
                "ChatGPT suggested: Use Markdown.",
                actor="ChatGPT",
                source="ChatGPT",
                activity="suggestion",
            ),
        ]
        ai_executed = [
            self._obs(
                "OBS-1",
                "ChatGPT reported implementation activity: I created report.md.",
                actor="ChatGPT",
                source="ChatGPT",
                activity="implementation",
            )
        ]
        unknown = [
            self._obs("OBS-1", "Human stated: Something happened.")
        ]

        self.assertEqual(classify_decision_leadership(human_decision)[0], "human_led")
        self.assertEqual(
            classify_decision_leadership(ai_proposed_human_decided)[0],
            "ai_proposed_human_decided",
        )
        self.assertEqual(classify_decision_leadership(jointly_shaped)[0], "jointly_shaped")
        self.assertEqual(classify_decision_leadership(ai_executed)[0], "ai_executed")
        self.assertEqual(classify_decision_leadership(unknown)[0], "unknown")

    def test_confidence_bands_are_rule_based(self):
        very_high = self._investigation(
            [
                self._obs("OBS-1", "Human stated a decision: I choose A.", activity="decision", source_type="conversation"),
                self._obs("OBS-2", "Human stated a decision: I choose A.", activity="decision", source_type="document"),
                self._obs("OBS-3", "Human stated: Supporting design evidence.", source_type="design"),
            ],
            timeline=(
                self._event(
                    "TL-001",
                    ("OBS-1", "OBS-2"),
                    ("a#1", "b#2"),
                    confidence="high",
                ),
            ),
            unknowns=(),
        )
        moderate = self._investigation([
            self._obs("OBS-1", "Human stated a decision: I choose A.", activity="decision")
        ])
        limited = self._investigation([
            self._obs("OBS-1", "Human stated: A note.")
        ])
        low = self._investigation([], timeline=(), unknowns=())

        self.assertEqual(build_executive_report(very_high).confidence_assessment.band, "Moderate")
        self.assertEqual(build_executive_report(moderate).confidence_assessment.band, "Moderate")
        self.assertEqual(build_executive_report(limited).confidence_assessment.band, "Limited")
        self.assertEqual(build_executive_report(low).confidence_assessment.band, "Low")

    def test_fixture_confidence_calibrates_to_moderate_without_goal_or_corroboration(self):
        investigation = self._investigation([
            self._obs("OBS-1", "Human stated a decision: I choose A.", activity="decision", source_type="conversation"),
            self._obs("OBS-2", "Human stated: Supporting design evidence.", source_type="design"),
            self._obs("OBS-3", "Human stated: Supporting document evidence.", source_type="document"),
        ])

        self.assertEqual(
            build_executive_report(investigation).confidence_assessment.band,
            "Moderate",
        )

    def test_corroboration_requires_same_claim_not_source_diversity(self):
        source_diverse = self._investigation([
            self._obs("OBS-1", "Human stated: Conversation note.", source_type="conversation"),
            self._obs("OBS-2", "Human stated: Document note.", source_type="document"),
        ])
        corroborated = self._investigation(
            [
                self._obs("OBS-1", "Human stated a decision: I choose A.", activity="decision", source_type="conversation"),
                self._obs(
                    "OBS-2",
                    "google-docs stated a decision: I choose A.",
                    actor="google-docs",
                    source="google-docs",
                    activity="decision",
                    source_type="document",
                ),
            ],
            timeline=(
                self._event("TL-001", ("OBS-1", "OBS-2"), ("a#1", "b#2")),
            ),
            unknowns=(),
        )

        self.assertIn(
            "No executive claim",
            build_executive_report(source_diverse).confidence_assessment.corroboration,
        )
        self.assertIn(
            "MS-001",
            build_executive_report(corroborated).confidence_assessment.corroboration,
        )

    def test_gap_count_is_canonical_and_deduplicates_static_revision_unknown(self):
        investigation = self._investigation(
            [
                self._obs(
                    "OBS-1",
                    "google-docs stated a decision: I choose A.",
                    actor="google-docs",
                    source="google-docs",
                    source_type="document",
                    activity="decision",
                )
            ],
            unknowns=("Revision history is not available in this static export.",),
        )

        report = build_executive_report(investigation)

        self.assertEqual(len(report.evidence_gaps), 3)
        self.assertIn("3 executive evidence gap", report.confidence_assessment.gaps)
        self.assertIn("3 evidence gap", report.executive_brief.unknowns_summary)

    def test_git_evidence_removes_git_history_unavailable_gap(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git recorded commit abc1234: Add report.",
                actor="Git author: Workprint Tester <tester@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/abc1234",
            )
        ])

        report = build_executive_report(investigation)

        summaries = [item.summary for item in report.evidence_gaps]
        self.assertNotIn("Git history was not analyzed.", summaries)

    def test_shallow_git_history_is_disclosed(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git history is shallow or incomplete for /repo; earlier commits may be unavailable.",
                actor="Git",
                source="git",
                source_type="repository",
                activity="unknown",
                ref="/repo#git/repository",
                metadata={"is_shallow": True},
            )
        ])

        report = build_executive_report(investigation)

        self.assertTrue(
            any("shallow or incomplete" in item.summary for item in report.evidence_gaps)
        )

    def test_git_presence_alone_does_not_raise_confidence(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git repository metadata was captured for /repo on main.",
                actor="Git",
                source="git",
                source_type="repository",
                activity="observation",
                ref="/repo#git/repository",
            )
        ])

        report = build_executive_report(investigation)

        self.assertEqual(report.confidence_assessment.band, "Limited")

    def test_git_merge_commit_supports_branch_integration_milestone(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git recorded merge commit abc1234: Merge feature branch.",
                actor="Git author: Workprint Tester <tester@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/abc1234",
                metadata={
                    "commit_sha": "abc1234",
                    "subject": "Merge pull request #1 from owner/feature/reporting",
                    "is_merge": True,
                    "parent_shas": ("p1", "p2"),
                },
            )
        ])

        report = build_executive_report(investigation)

        self.assertEqual(report.key_milestones[0].status, "a branch integration")
        self.assertIn("Reporting merged", report.key_milestones[0].title)

    def test_git_source_diversity_alone_is_not_corroboration(self):
        investigation = self._investigation([
            self._obs("OBS-1", "Human stated: A planning note."),
            self._obs(
                "OBS-2",
                "Git recorded commit abc1234: Add implementation.",
                actor="Git author: Workprint Tester <tester@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/abc1234",
            ),
        ])

        report = build_executive_report(investigation)

        self.assertIn("No executive claim", report.confidence_assessment.corroboration)

    def test_two_git_commits_do_not_create_independent_corroboration(self):
        observations = [
            self._obs(
                "OBS-1",
                "Git recorded commit aaa1111: feat(timeline): add deterministic timeline report.",
                actor="Git author: A <a@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/aaa1111",
                metadata={"commit_sha": "aaa1111", "subject": "feat(timeline): add deterministic timeline report"},
            ),
            self._obs(
                "OBS-2",
                "Git recorded commit bbb2222: feat(timeline): add deterministic timeline report.",
                actor="Git author: B <b@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/bbb2222",
                metadata={"commit_sha": "bbb2222", "subject": "feat(timeline): add deterministic timeline report"},
            ),
        ]
        investigation = self._investigation(
            observations,
            timeline=(self._event("TL-001", ("OBS-1", "OBS-2"), ("a#1", "b#2")),),
        )

        report = build_executive_report(investigation)

        self.assertIn("No executive claim", report.confidence_assessment.corroboration)

    def test_git_plus_chatgpt_same_claim_can_corroborate(self):
        observations = [
            self._obs(
                "OBS-1",
                "ChatGPT reported implementation activity: I added the deterministic timeline report.",
                actor="ChatGPT",
                source="ChatGPT",
                activity="implementation",
                ref="chatgpt#1",
            ),
            self._obs(
                "OBS-2",
                "Git recorded commit aaa1111: feat(timeline): add deterministic timeline report.",
                actor="Git author: A <a@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/aaa1111",
                metadata={"commit_sha": "aaa1111", "subject": "feat(timeline): add deterministic timeline report"},
            ),
        ]
        investigation = self._investigation(
            observations,
            timeline=(self._event("TL-001", ("OBS-1", "OBS-2"), ("chatgpt#1", "/repo#commit/aaa1111")),),
        )

        report = build_executive_report(investigation)

        self.assertIn("MS-001", report.confidence_assessment.corroboration)

    def test_unrelated_git_and_chatgpt_evidence_does_not_correlate(self):
        investigation = self._investigation([
            self._obs("OBS-1", "ChatGPT stated: A planning note.", actor="ChatGPT", source="ChatGPT"),
            self._obs(
                "OBS-2",
                "Git recorded commit aaa1111: feat(timeline): add deterministic timeline report.",
                actor="Git author: A <a@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/aaa1111",
                metadata={"commit_sha": "aaa1111", "subject": "feat(timeline): add deterministic timeline report"},
            ),
        ])

        report = build_executive_report(investigation)

        self.assertIn("No executive claim", report.confidence_assessment.corroboration)

    def test_git_file_changes_and_routine_commits_are_not_milestones(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git recorded repository file change A for src/workprint/foo.py in commit aaa1111. Additions and deletions describe repository changes, not effort or value.",
                actor="Git",
                source="git",
                source_type="repository",
                activity="artifact",
                ref="/repo#commit/aaa1111/file/src/workprint/foo.py",
                metadata={"commit_sha": "aaa1111", "subject": "chore: update helper", "file_path": "src/workprint/foo.py"},
            ),
            self._obs(
                "OBS-2",
                "Git recorded commit aaa1111: chore: update helper.",
                actor="Git author: A <a@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/aaa1111",
                metadata={"commit_sha": "aaa1111", "subject": "chore: update helper"},
            ),
        ])

        report = build_executive_report(investigation)

        self.assertEqual(report.key_milestones[0].status, "not_established")

    def test_git_milestones_are_capped_and_reader_facing(self):
        observations = []
        for index in range(12):
            sha = f"abc{index:04d}"
            observations.append(
                self._obs(
                    f"OBS-{index}",
                    f"Git recorded commit {sha}: feat(timeline): add deterministic timeline report.",
                    actor="Git author: A <a@example.com>",
                    source="git",
                    source_type="repository",
                    activity="implementation",
                    ref=f"/repo#commit/{sha}",
                    metadata={"commit_sha": sha, "subject": "feat(timeline): add deterministic timeline report"},
                )
            )
        report = build_executive_report(self._investigation(observations))

        self.assertLessEqual(len(report.key_milestones), 8)
        self.assertTrue(
            any(item.title == "Timeline reporting added" for item in report.key_milestones)
        )
        self.assertTrue(
            any("feat(timeline): add deterministic timeline report" in item.summary for item in report.key_milestones)
        )

    def test_git_authorship_boundary_and_repository_summary_appear(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Git repository metadata was captured for /repo on main.",
                actor="Git",
                source="git",
                source_type="repository",
                activity="observation",
                ref="/repo#git/repository",
                metadata={"repository_root": "/repo", "current_branch": "main", "is_shallow": False},
            ),
            self._obs(
                "OBS-2",
                "Git recorded commit aaa1111: feat(timeline): add deterministic timeline report.",
                actor="Git author: A <a@example.com>",
                source="git",
                source_type="repository",
                activity="implementation",
                ref="/repo#commit/aaa1111",
                metadata={"commit_sha": "aaa1111", "subject": "feat(timeline): add deterministic timeline report"},
            ),
        ])

        report = build_executive_report(investigation)

        self.assertIn("Git author and committer fields", report.investigation_assurance)
        self.assertIn("personally wrote every changed line", report.investigation_assurance)
        self.assertTrue(
            any(item.title == "Git repository analyzed" and "1 commit" in item.summary for item in report.project_overview)
        )
        self.assertFalse(
            any("Static exports may omit revision history" == item.summary for item in report.evidence_gaps)
        )

    def test_copy_audit_runs_and_records_attribution_metadata(self):
        report = build_executive_report(self._investigation([]))

        audit = report.copy_quality_audit
        self.assertEqual(audit.status, "passed")
        self.assertEqual(audit.upstream_author, "JCarterJohnson")
        self.assertEqual(audit.upstream_project, "vibecoded-design-tells")
        self.assertEqual(audit.upstream_license, "MIT")
        self.assertEqual(audit.pinned_revision, UNSLOP_TEXT_PINNED_REVISION)
        self.assertEqual(audit.upstream_revision, UNSLOP_TEXT_PINNED_REVISION)
        self.assertTrue(audit.scanner_available)
        self.assertTrue(audit.lexical_review_completed)
        self.assertTrue(audit.structural_review_completed)
        self.assertTrue(audit.evidence_preservation_confirmed)
        self.assertFalse(audit.override_used)
        self.assertIn("NOTICE.md", audit.attribution_notice)
        self.assertIn("incorporates", audit.disclosure)
        self.assertIn("developed by JCarterJohnson", audit.disclosure)
        self.assertIn("attribution and licensing information", audit.disclosure)
        self.assertIn("lexical findings alone cannot assess overall writing quality", audit.disclosure)
        self.assertIn("A passing audit indicates", audit.disclosure)
        self.assertIn("does not establish human authorship", audit.disclosure)

    def test_copy_audit_missing_scanner_is_unavailable_with_upstream_credit(self):
        audit = CopyQualityAuditor(
            scanner_path=Path("missing-unslop-text-scanner.py")
        ).audit({"Executive Brief": "Plain evidence-backed text."})

        self.assertEqual(audit.status, "unavailable")
        self.assertFalse(audit.lexical_review_completed)
        self.assertIn("JCarterJohnson", audit.disclosure)
        self.assertIn("vibecoded-design-tells", audit.disclosure)
        self.assertIn("configured to incorporate", audit.disclosure)
        self.assertIn("lexical review was not completed", audit.disclosure.lower())

    def test_copy_audit_high_severity_finding_fails(self):
        audit = CopyQualityAuditor().audit({
            "Executive Brief": "This sentence ships an em dash — which should fail.",
        })

        self.assertEqual(audit.status, "failed")
        self.assertGreaterEqual(audit.severity_counts.get("high", 0), 1)
        self.assertTrue(any(item["rule"] == "em-dash" for item in audit.findings))

    def test_copy_audit_medium_low_findings_with_waivers_pass_with_waivers(self):
        waivers = (
            AuditWaiver(
                rule="hype-marketing",
                section="Executive Brief",
                reason="Retained in a test fixture to exercise waiver handling.",
            ),
            AuditWaiver(
                rule="promotional-language",
                section="Executive Brief",
                reason="Retained in a test fixture to exercise waiver handling.",
            ),
        )
        audit = CopyQualityAuditor(waivers=waivers).audit({
            "Executive Brief": "The report avoids revolutionary claims.",
        })

        self.assertEqual(audit.status, "passed_with_waivers")
        self.assertEqual(len(audit.waivers), 2)

    def test_copy_audit_medium_low_findings_without_waivers_fail(self):
        audit = CopyQualityAuditor().audit({
            "Executive Brief": "The report avoids revolutionary claims.",
        })

        self.assertEqual(audit.status, "failed")
        self.assertIn("without documented waivers", audit.disclosure)

    def test_copy_audit_model_statuses(self):
        passed = CopyQualityAudit(
            status="passed",
            scanner="unslop_text_scan.py",
            upstream_repository="repo",
            pinned_revision="rev",
            scanned_sections=("Executive Brief",),
            structural_review_completed=True,
            lexical_review_completed=True,
            evidence_preservation_confirmed=True,
        )
        waived = CopyQualityAudit(
            status="passed_with_waivers",
            scanner="unslop_text_scan.py",
            upstream_repository="repo",
            pinned_revision="rev",
            scanned_sections=("Executive Brief",),
            waivers=({"finding": "medium", "reason": "intentional"},),
            structural_review_completed=True,
            lexical_review_completed=True,
            evidence_preservation_confirmed=True,
        )
        failed = CopyQualityAudit(
            status="failed",
            scanner="unslop_text_scan.py",
            upstream_repository="repo",
            pinned_revision="rev",
            scanned_sections=("Executive Brief",),
            findings=({"severity": "high"},),
        )

        self.assertEqual(passed.to_dict()["status"], "passed")
        self.assertEqual(waived.to_dict()["status"], "passed_with_waivers")
        self.assertEqual(failed.to_dict()["status"], "failed")
        with self.assertRaises(ValueError):
            CopyQualityAudit(
                status="passed",
                scanner="unslop_text_scan.py",
                upstream_repository="repo",
                pinned_revision="rev",
                scanned_sections=("Executive Brief",),
            )

    def test_markdown_places_executive_report_before_detailed_report(self):
        rendered = render_markdown(self._investigation([
            self._obs("OBS-1", "Human stated a decision: I choose Markdown.", activity="decision")
        ]))

        self.assertLess(
            rendered.index("# Executive Report: Workprint"),
            rendered.index("# Workprint Investigation: Workprint"),
        )
        self.assertIn("## Executive Brief", rendered)
        self.assertIn("## Investigation Assurance", rendered)
        self.assertNotIn("70%", rendered)
        self.assertNotIn("reported implementation activity", rendered)
        self.assertNotIn("stated a decision or acceptance", rendered)

    def test_markdown_copy_audit_discloses_attribution_and_revision(self):
        rendered = render_markdown(self._investigation([]))

        self.assertIn("### Copy-Quality Audit", rendered)
        self.assertIn("JCarterJohnson", rendered)
        self.assertIn("vibecoded-design-tells", rendered)
        self.assertIn("unslop-text", rendered)
        self.assertIn("incorporates the `unslop-text` scanner", rendered)
        self.assertIn("lexical findings alone cannot assess overall writing quality", rendered)
        self.assertIn(UNSLOP_TEXT_PINNED_REVISION, rendered)
        self.assertIn("not an authorship detector", rendered)
        self.assertNotIn("endorsed by", rendered.lower())
        self.assertNotIn("certified by", rendered.lower())

    def test_json_adds_executive_report_without_breaking_existing_keys(self):
        data = render_json_dict(self._investigation([
            self._obs("OBS-1", "Human stated a decision: I choose Markdown.", activity="decision")
        ]))

        for key in {
            "project",
            "source_files",
            "observations",
            "timeline",
            "timeline_summary",
            "findings",
            "unknowns",
            "limitations",
        }:
            self.assertIn(key, data)
        self.assertEqual(data["executive_report"]["schema_version"], "1.0")
        audit = data["executive_report"]["copy_quality_audit"]
        self.assertEqual(audit["upstream_author"], "JCarterJohnson")
        self.assertEqual(audit["upstream_project"], "vibecoded-design-tells")
        self.assertEqual(audit["upstream_revision"], UNSLOP_TEXT_PINNED_REVISION)
        self.assertEqual(audit["upstream_license"], "MIT")
        self.assertIn("NOTICE.md", audit["attribution_notice"])
        self.assertIn("A passing audit indicates", audit["disclosure"])

    def test_structural_checks_detect_representative_patterns(self):
        findings = structural_review({
            "Executive Brief": (
                "In conclusion, this is not just a report, but a revolutionary change. "
                "Honestly, it is robust."
            )
        })
        rules = {item["rule"] for item in findings}

        self.assertIn("not-just-x-y", rules)
        self.assertIn("unnecessary-recap", rules)
        self.assertIn("promotional-language", rules)
        self.assertIn("manufactured-casualness", rules)

    def test_appendix_only_evidence_is_excluded_from_copy_scan(self):
        investigation = self._investigation([
            self._obs(
                "OBS-1",
                "Human stated: This raw evidence has an em dash — but is not executive narrative.",
                activity="observation",
            )
        ])

        report = build_executive_report(investigation)

        self.assertEqual(report.copy_quality_audit.status, "passed")

    def test_copy_audit_does_not_claim_human_authorship_or_no_ai_involvement(self):
        rendered = render_markdown(self._investigation([])).lower()

        self.assertNotIn("human-written", rendered)
        self.assertNotIn("not ai-generated", rendered)
        self.assertNotIn("ai-free", rendered)
        self.assertNotIn("passed an ai detector", rendered)
        self.assertIn("does not establish human authorship", rendered)
        self.assertIn("prove that ai was not involved", rendered)

    def test_cli_and_guided_use_shared_json_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            cli_output = Path(directory) / "cli.json"
            guided_dir = Path(directory) / "guided"
            result = main([
                "investigate",
                "chatgpt",
                "fixtures/chatgpt/sample-conversations.json",
                "--project",
                "Workprint",
                "--format",
                "json",
                "--output",
                str(cli_output),
            ])
            self.assertEqual(result, 0)
            guided_result = run_guided(
                input_func=lambda prompt: "",
                output=io.StringIO(),
                cwd=".",
                options=GuidedOptions(
                    path="fixtures/chatgpt",
                    include="chatgpt",
                    project="Workprint",
                    output_dir=guided_dir,
                    yes=True,
                ),
            )
            self.assertEqual(guided_result, 0)

            cli_payload = json.loads(cli_output.read_text(encoding="utf-8"))
            guided_payload = json.loads((guided_dir / "report.json").read_text(encoding="utf-8"))

        self.assertIn("executive_report", cli_payload)
        self.assertIn("executive_report", guided_payload)
        self.assertEqual(
            cli_payload["executive_report"].keys(),
            guided_payload["executive_report"].keys(),
        )

    def _investigation(
        self,
        observations,
        timeline=None,
        unknowns=("Offline work cannot be determined.",),
        source_files=("fixture.json",),
    ):
        timeline = build_timeline(observations) if timeline is None else timeline
        return Investigation(
            project="Workprint",
            source_files=tuple(source_files),
            observations=tuple(observations),
            findings=(),
            unknowns=tuple(unknowns),
            limitations=("Observation counts do not represent ownership, effort, or value.",),
            timeline=timeline,
            timeline_summary={"event_count": len(timeline)},
        )

    @staticmethod
    def _obs(
        obs_id,
        statement,
        *,
        actor="Human",
        source="ChatGPT",
        source_type="conversation",
        activity="observation",
        ref=None,
        metadata=None,
    ):
        return Observation(
            id=obs_id,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source=source,
            source_type=source_type,
            actor=actor,
            activity=activity,
            statement=statement,
            evidence_refs=(ref or f"{obs_id}.json#1",),
            metadata={"conversation_id": "c1", **(metadata or {})},
        )

    @staticmethod
    def _event(event_id, observation_ids, evidence_refs, confidence="high"):
        return TimelineEvent(
            id=event_id,
            start_time=None,
            end_time=None,
            stage="decision",
            title="Decision",
            description="Human stated a decision.",
            source_observation_ids=tuple(observation_ids),
            evidence_refs=tuple(evidence_refs),
            confidence=confidence,
            user_involvement=(
                TimelineInvolvement(
                    activity="decided",
                    status="measured",
                    evidence_ids=tuple(observation_ids),
                ),
            ),
            activity_breakdown={"user_activity": tuple(observation_ids)},
            attribution_limits=("No percentages are inferred.",),
        )


if __name__ == "__main__":
    unittest.main()
