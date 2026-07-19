from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workprint.adapters import GitAdapter
from workprint.ai_fluency import (
    build_ai_fluency_reflection,
    build_playbook_worksheet_markdown,
)
from workprint.engine import build_investigation
from workprint.extractor import extract_observations
from workprint.models import Investigation, Observation
from workprint.reports import render_json_dict, render_markdown


GIT = shutil.which("git")


class AIFluencyReflectionTests(unittest.TestCase):
    def test_attribution_and_disclaimer_are_present(self):
        reflection = build_ai_fluency_reflection(self._investigation([]))

        self.assertIn("Dakan", reflection.attribution)
        self.assertIn("Feller", reflection.attribution)
        self.assertIn("CC BY-NC-SA", reflection.attribution)
        self.assertIn("does not score", reflection.disclaimer.lower())

    def test_all_four_competencies_are_always_present(self):
        reflection = build_ai_fluency_reflection(self._investigation([]))

        keys = [competency.key for competency in reflection.competencies]
        self.assertEqual(
            keys, ["delegation", "description", "discernment", "diligence"]
        )

    def test_description_and_discernment_have_notes_not_evidence(self):
        reflection = build_ai_fluency_reflection(self._investigation([]))

        by_key = {item.key: item for item in reflection.competencies}
        self.assertEqual(by_key["description"].evidence, ())
        self.assertNotEqual(by_key["description"].note, "")
        self.assertEqual(by_key["discernment"].evidence, ())
        self.assertNotEqual(by_key["discernment"].note, "")

    def test_delegation_lists_each_present_source(self):
        observations = [
            self._obs("OBS-1", source="git"),
            self._obs("OBS-2", source="claude-code"),
        ]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        delegation = next(
            item for item in reflection.competencies if item.key == "delegation"
        )
        evidence_ids = {item.id for item in delegation.evidence}
        self.assertIn("fluency-delegation-git", evidence_ids)
        self.assertIn("fluency-delegation-claude-code", evidence_ids)
        self.assertIn("fluency-delegation-multi-source", evidence_ids)

    def test_delegation_notes_when_no_ai_source_present(self):
        observations = [self._obs("OBS-1", source="git")]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        delegation = next(
            item for item in reflection.competencies if item.key == "delegation"
        )
        evidence_ids = {item.id for item in delegation.evidence}
        self.assertIn("fluency-delegation-no-ai-source", evidence_ids)

    def test_diligence_detects_test_file_changes(self):
        observations = [
            self._obs(
                "OBS-1",
                source="git",
                source_type="repository",
                activity="artifact",
                artifact="tests/test_foo.py",
            ),
        ]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        diligence = next(
            item for item in reflection.competencies if item.key == "diligence"
        )
        evidence_ids = {item.id for item in diligence.evidence}
        self.assertIn("fluency-diligence-test-changes", evidence_ids)

    def test_diligence_does_not_match_bare_spec_directory(self):
        # Regression: dogfooding against Workprint's own repo showed
        # spec/01-principles.md (a product spec document, not a test)
        # matching a looser pattern. "spec/" alone is too ambiguous.
        observations = [
            self._obs(
                "OBS-1",
                source="git",
                source_type="repository",
                activity="artifact",
                artifact="spec/01-principles.md",
            ),
        ]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        diligence = next(
            item for item in reflection.competencies if item.key == "diligence"
        )
        evidence_ids = {item.id for item in diligence.evidence}
        self.assertNotIn("fluency-diligence-test-changes", evidence_ids)
        self.assertIn("fluency-diligence-no-evidence", evidence_ids)

    def test_diligence_detects_ai_mention_in_commit(self):
        observations = [
            self._obs(
                "OBS-1",
                source="git",
                source_type="repository",
                activity="implementation",
                statement="Git recorded commit abc123: Add Claude Code adapter.",
            ),
        ]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        diligence = next(
            item for item in reflection.competencies if item.key == "diligence"
        )
        evidence_ids = {item.id for item in diligence.evidence}
        self.assertIn("fluency-diligence-ai-mentions", evidence_ids)

    def test_diligence_notes_when_no_signals_found(self):
        observations = [self._obs("OBS-1", source="git", source_type="repository")]
        reflection = build_ai_fluency_reflection(self._investigation(observations))

        diligence = next(
            item for item in reflection.competencies if item.key == "diligence"
        )
        evidence_ids = {item.id for item in diligence.evidence}
        self.assertIn("fluency-diligence-no-evidence", evidence_ids)

    def test_render_json_dict_includes_ai_fluency(self):
        data = render_json_dict(self._investigation([self._obs("OBS-1")]))

        self.assertIn("ai_fluency", data)
        self.assertEqual(len(data["ai_fluency"]["competencies"]), 4)

    def test_render_markdown_includes_ai_fluency_section(self):
        rendered = render_markdown(self._investigation([self._obs("OBS-1")]))

        self.assertIn("## AI Fluency Evidence", rendered)
        self.assertIn("### Delegation", rendered)
        self.assertIn("### Description", rendered)
        self.assertIn("### Discernment", rendered)
        self.assertIn("### Diligence", rendered)

    def test_playbook_worksheet_has_fill_in_columns_and_real_evidence(self):
        observations = [self._obs("OBS-1", source="claude-code")]
        worksheet = build_playbook_worksheet_markdown(
            self._investigation(observations)
        )

        self.assertIn("_(fill in)_", worksheet)
        self.assertIn("Claude Code evidence", worksheet)
        self.assertIn("Your reflection", worksheet)
        self.assertIn("Your action next time", worksheet)

    @staticmethod
    def _investigation(observations):
        return Investigation(
            project="Workprint",
            source_files=("fixture.json",),
            observations=tuple(observations),
            findings=(),
            unknowns=("Offline work cannot be determined.",),
            limitations=(),
        )

    @staticmethod
    def _obs(
        obs_id,
        *,
        source="ChatGPT",
        source_type="conversation",
        activity="observation",
        actor="Human",
        artifact=None,
        statement=None,
    ):
        return Observation(
            id=obs_id,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source=source,
            source_type=source_type,
            actor=actor,
            activity=activity,
            statement=statement or f"{actor} stated something in {source}.",
            evidence_refs=(f"{obs_id}.json#1",),
            artifact=artifact,
            metadata={},
        )


class AIFluencyRealGitEvidenceTests(unittest.TestCase):
    @unittest.skipUnless(GIT, "git executable is required")
    def test_real_test_file_commit_surfaces_diligence_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve()
            self._git(repo, "init")
            self._git(repo, "config", "user.name", "Workprint Tester")
            self._git(repo, "config", "user.email", "tester@example.com")

            test_file = repo / "tests" / "test_sample.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            self._git(repo, "add", "tests/test_sample.py")
            self._git(
                repo,
                "commit",
                "-m",
                "Add test coverage with Claude Code",
                env={
                    "GIT_AUTHOR_DATE": "2026-02-01T12:00:00+00:00",
                    "GIT_COMMITTER_DATE": "2026-02-01T12:00:00+00:00",
                },
            )

            records = GitAdapter().read(repo)
            observations = extract_observations(list(records))
            investigation = build_investigation(
                project="Test Project",
                source_files=[str(repo)],
                observations=observations,
            )

            reflection = build_ai_fluency_reflection(investigation)
            diligence = next(
                item for item in reflection.competencies if item.key == "diligence"
            )
            evidence_ids = {item.id for item in diligence.evidence}
            self.assertIn("fluency-diligence-test-changes", evidence_ids)
            self.assertIn("fluency-diligence-ai-mentions", evidence_ids)

    @staticmethod
    def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
        command = [GIT, "-C", str(repo), *args]
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=merged_env,
        )
        return result.stdout


if __name__ == "__main__":
    unittest.main()
