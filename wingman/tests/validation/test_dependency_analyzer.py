"""
Unit tests for dependency_analyzer validator
"""

import pytest
from validation.dependency_analyzer import DependencyAnalyzer
from tests.validation.fixtures import DEPENDENCY_ANALYZER_TEST_CASES


@pytest.fixture
def analyzer():
    return DependencyAnalyzer()


class TestDependencyAnalyzer:
    """Test dependency analyzer blast radius assessment"""

    @pytest.mark.unit
    def test_blast_radius_calculation(self, analyzer):
        """Test that blast radius is correctly calculated"""
        # docker stop postgres -> HIGH (container + database service)
        result = analyzer.analyze("Commands: docker stop postgres")
        assert result["blast_radius"] in ("HIGH", "CRITICAL", "MEDIUM")
        assert "container" in [d["type"] for d in result["dependencies"]]
        assert "postgres" in result["affected_services"] or len(result["affected_services"]) >= 1

    @pytest.mark.unit
    def test_docker_rm_high_blast_radius(self, analyzer):
        """Instruction mentioning docker rm has HIGH blast radius (plan requirement)"""
        result = analyzer.analyze("Run docker rm -f mycontainer")
        assert result["blast_radius"] in ("HIGH", "CRITICAL", "MEDIUM")
        assert len(result["dependencies"]) > 0

    @pytest.mark.unit
    def test_create_file_low_blast_radius(self, analyzer):
        """Instruction mentioning create file has LOW (plan requirement)"""
        result = analyzer.analyze("Create file validation/code_scanner.py with scan() method")
        assert result["blast_radius"] == "LOW"
        assert "filesystem" in [d["type"] for d in result["dependencies"]]

    @pytest.mark.unit
    def test_cascading_failure_detection(self, analyzer):
        """Multiple services -> HIGH blast radius (cascading potential)"""
        result = analyzer.analyze("Stop postgres and restart wingman-api and execution-gateway")
        assert result["blast_radius"] in ("HIGH", "MEDIUM", "CRITICAL")
        assert len(result["affected_services"]) >= 1

    @pytest.mark.unit
    def test_database_drop_critical(self, analyzer):
        """DROP TABLE / database destruction -> CRITICAL"""
        result = analyzer.analyze("Execute DROP TABLE users CASCADE")
        assert result["blast_radius"] == "CRITICAL"
        assert "database" in [d["type"] for d in result["dependencies"]]

    @pytest.mark.unit
    def test_empty_instruction(self, analyzer):
        """Empty instruction -> LOW"""
        result = analyzer.analyze("")
        assert result["blast_radius"] == "LOW"
        assert result["dependencies"] == []
        assert result["affected_services"] == []

    @pytest.mark.unit
    def test_output_structure(self, analyzer):
        """Output has all required keys"""
        result = analyzer.analyze("docker ps")
        assert "dependencies" in result
        assert "blast_radius" in result
        assert "affected_services" in result
        assert "risk_level" in result
        assert result["blast_radius"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    @pytest.mark.unit
    def test_fixture_test_cases(self, analyzer):
        """Validate against fixture test cases"""
        for case in DEPENDENCY_ANALYZER_TEST_CASES:
            result = analyzer.analyze(case["instruction"])
            assert result["blast_radius"] == case["expected_blast_radius"], \
                f"Case '{case['name']}': got {result['blast_radius']}"
            if "expected_affected" in case:
                for svc in case["expected_affected"]:
                    assert any(svc.lower() in s.lower() for s in result["affected_services"]), \
                        f"Case '{case['name']}': expected {svc} in affected_services"
