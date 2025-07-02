"""
Test suite for QueryAnalyzer agent - TDD Phase 5
Following Red-Green-Refactor cycle
"""
import pytest
from cli_agent.agents.query_analyzer import QueryAnalyzer

class TestQueryAnalyzer:
    """Test cases for QueryAnalyzer agent"""
    
    @pytest.fixture
    def analyzer(self):
        """Create QueryAnalyzer instance for testing"""
        return QueryAnalyzer()
    
    def test_analyze_simple_count_query(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should extract COUNT intent and product entities from simple query
        """
        query = "How many products are we launching this quarter?"
        
        result = analyzer.analyze(query)
        
        # Expected structure
        assert isinstance(result, dict)
        assert 'intent' in result
        assert 'entities' in result
        assert 'query_type' in result
        
        # Expected values
        assert result['intent'] == 'COUNT'
        assert result['query_type'] == 'SIMPLE'
        
        # Check entities
        entities_text = [entity['text'] for entity in result['entities']]
        assert 'products' in entities_text
        assert 'quarter' in entities_text
    
    def test_analyze_brand_filter_query(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should extract COUNT intent and brand entities
        """
        query = "How many Sony products are in our inventory?"
        
        result = analyzer.analyze(query)
        
        assert result['intent'] == 'COUNT'
        assert result['query_type'] == 'SIMPLE'
        
        entities_text = [entity['text'] for entity in result['entities']]
        assert 'Sony' in entities_text
        assert 'products' in entities_text
    
    def test_analyze_comparison_query(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should extract COMPARE intent and multiple brand entities
        """
        query = "Compare Sony vs Samsung product portfolios"
        
        result = analyzer.analyze(query)
        
        assert result['intent'] == 'COMPARE'
        assert result['query_type'] == 'COMPLEX'
        
        entities_text = [entity['text'] for entity in result['entities']]
        assert 'Sony' in entities_text
        assert 'Samsung' in entities_text
    
    def test_analyze_empty_query(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should handle empty/invalid queries gracefully
        """
        result = analyzer.analyze("")
        
        assert result['intent'] == 'UNKNOWN'
        assert result['query_type'] == 'INVALID'
        assert result['entities'] == []
    
    def test_analyze_invalid_query(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should handle nonsensical queries
        """
        result = analyzer.analyze("asdfghjkl random nonsense")
        
        assert result['intent'] == 'UNKNOWN'
        assert result['query_type'] == 'INVALID'
    
    @pytest.mark.unit
    def test_entity_extraction_confidence(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should include confidence scores for entities
        """
        query = "How many Sony products are launching?"
        
        result = analyzer.analyze(query)
        
        # Check that entities have confidence scores
        for entity in result['entities']:
            assert 'confidence' in entity
            assert 0.0 <= entity['confidence'] <= 1.0
            assert 'type' in entity
    
    @pytest.mark.unit
    def test_intent_extraction_types(self, analyzer):
        """
        RED: Test should FAIL - QueryAnalyzer doesn't exist yet
        
        Test: Should correctly identify different intent types
        """
        test_cases = [
            ("How many products?", "COUNT"),
            ("Show me the product list", "LIST"),
            ("Compare Sony vs Samsung", "COMPARE"),
            ("Analyze product performance", "ANALYZE")
        ]
        
        for query, expected_intent in test_cases:
            result = analyzer.analyze(query)
            assert result['intent'] == expected_intent, f"Failed for query: {query}"