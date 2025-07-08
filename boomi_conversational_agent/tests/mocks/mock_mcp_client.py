"""
Mock MCP client for testing without real Boomi connection
"""
from typing import Dict, Any, List

class MockMCPClient:
    """Mock MCP client for testing without real Boomi DataHub connection"""
    
    def __init__(self):
        self.call_count = 0
        self.last_query = None
        
        # Mock data representing Boomi DataHub models
        self._models = [
            {
                "id": "Product",
                "name": "Product", 
                "description": "Product information including details, pricing, and specifications",
                "status": "published",
                "field_count": 15,
                "record_count": 50000
            },
            {
                "id": "Campaign",
                "name": "Marketing Campaign",
                "description": "Marketing campaign data including budgets, timelines, and performance metrics",
                "status": "published", 
                "field_count": 8,
                "record_count": 1200
            },
            {
                "id": "Launch",
                "name": "Product Launch",
                "description": "Product launch schedules, dates, and associated campaigns",
                "status": "published",
                "field_count": 6,
                "record_count": 800
            },
            {
                "id": "Customer",
                "name": "Customer",
                "description": "Customer information, demographics, and purchase history",
                "status": "published",
                "field_count": 20,
                "record_count": 100000
            },
            {
                "id": "Sales",
                "name": "Sales Data",
                "description": "Sales transactions, revenue, and performance data",
                "status": "published",
                "field_count": 12,
                "record_count": 250000
            }
        ]
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Return mock model data"""
        self.call_count += 1
        return self._models.copy()
    
    def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """Return detailed model information"""
        self.call_count += 1
        
        model = next((m for m in self._models if m['id'] == model_id), None)
        if not model:
            return {"error": f"Model {model_id} not found"}
        
        return model.copy()
    
    def get_model_fields(self, model_id: str) -> List[Dict[str, Any]]:
        """Return field information for a model"""
        self.call_count += 1
        
        # Mock field data for different models
        fields_data = {
            "Product": [
                {"name": "product_id", "type": "string", "description": "Unique product identifier"},
                {"name": "product_name", "type": "string", "description": "Product name"},
                {"name": "brand_name", "type": "string", "description": "Product brand"},
                {"name": "category", "type": "string", "description": "Product category"},
                {"name": "price", "type": "decimal", "description": "Product price"},
                {"name": "launch_date", "type": "date", "description": "Product launch date"},
                {"name": "sku", "type": "string", "description": "Stock keeping unit"}
            ],
            "Campaign": [
                {"name": "campaign_id", "type": "string", "description": "Campaign identifier"},
                {"name": "campaign_name", "type": "string", "description": "Campaign name"},
                {"name": "start_date", "type": "date", "description": "Campaign start date"},
                {"name": "end_date", "type": "date", "description": "Campaign end date"},
                {"name": "budget", "type": "decimal", "description": "Campaign budget"},
                {"name": "target_audience", "type": "string", "description": "Target audience"}
            ],
            "Launch": [
                {"name": "launch_id", "type": "string", "description": "Launch identifier"},
                {"name": "product_id", "type": "string", "description": "Associated product"},
                {"name": "launch_date", "type": "date", "description": "Launch date"},
                {"name": "quarter_year", "type": "string", "description": "Quarter and year"}
            ]
        }
        
        return fields_data.get(model_id, [])
    
    def execute_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query and return mock results"""
        self.call_count += 1
        
        query_type = query.get('query_type', 'LIST')
        model_id = query.get('model_id', 'Unknown')
        filters = query.get('filters', [])
        
        # Handle timeout simulation
        if query.get('timeout', 10) < 0.01:
            return {
                'error': 'Query timeout exceeded',
                'query_type': query_type
            }
        
        # Generate mock data based on query type
        if query_type == 'COUNT':
            return self._mock_count_result(model_id, filters)
        elif query_type == 'LIST':
            return self._mock_list_result(model_id, filters, query.get('fields', []))
        elif query_type == 'COMPARE':
            return self._mock_comparison_result(model_id, filters, query.get('grouping', {}))
        else:
            return self._mock_generic_result(model_id, filters)
    
    def _mock_count_result(self, model_id: str, filters: List[Dict]) -> Dict[str, Any]:
        """Generate mock count result"""
        # Simulate different counts based on filters
        base_counts = {
            'Product': 15000,
            'Campaign': 850,
            'Launch': 420
        }
        
        base_count = base_counts.get(model_id, 1000)
        
        # Reduce count based on filters (simulating filtering effect)
        filtered_count = base_count
        for filter_item in filters:
            if filter_item.get('field') == 'brand_name' and filter_item.get('value') == 'Sony':
                filtered_count = int(filtered_count * 0.3)  # Sony has 30% market share
            elif filter_item.get('field') == 'brand_name' and filter_item.get('value') == 'Samsung':
                filtered_count = int(filtered_count * 0.25)  # Samsung has 25% market share
        
        return {
            'count': filtered_count,
            'model_id': model_id,
            'filters_applied': len(filters)
        }
    
    def _mock_list_result(self, model_id: str, filters: List[Dict], fields: List[str]) -> List[Dict[str, Any]]:
        """Generate mock list result"""
        if model_id == 'Product':
            products = [
                {'product_id': 'P001', 'product_name': 'Sony TV 55"', 'brand_name': 'Sony', 'price': 899.99},
                {'product_id': 'P002', 'product_name': 'Sony Speaker', 'brand_name': 'Sony', 'price': 199.99},
                {'product_id': 'P003', 'product_name': 'Samsung TV 55"', 'brand_name': 'Samsung', 'price': 849.99},
                {'product_id': 'P004', 'product_name': 'Sony Headphones', 'brand_name': 'Sony', 'price': 299.99}
            ]
            
            # Apply filters
            filtered_products = products
            for filter_item in filters:
                if filter_item.get('field') == 'brand_name':
                    brand_value = filter_item.get('value')
                    filtered_products = [p for p in filtered_products if p['brand_name'] == brand_value]
            
            # Apply field selection
            if fields and fields != ['*']:
                filtered_products = [
                    {field: record.get(field) for field in fields if field in record}
                    for record in filtered_products
                ]
            
            return filtered_products
        
        return []
    
    def _mock_comparison_result(self, model_id: str, filters: List[Dict], grouping: Dict) -> List[Dict[str, Any]]:
        """Generate mock comparison result"""
        if grouping.get('field') == 'brand_name':
            return [
                {'brand_name': 'Sony', 'product_count': 12, 'avg_price': 299.99},
                {'brand_name': 'Samsung', 'product_count': 8, 'avg_price': 349.99}
            ]
        
        return []
    
    def _mock_generic_result(self, model_id: str, filters: List[Dict]) -> List[Dict[str, Any]]:
        """Generate generic mock result"""
        return [
            {'id': '1', 'name': f'Sample {model_id} 1'},
            {'id': '2', 'name': f'Sample {model_id} 2'}
        ]
    
    def test_connection(self) -> Dict[str, Any]:
        """Mock connection test"""
        self.call_count += 1
        return {
            "success": True,
            "message": "Mock MCP connection successful",
            "timestamp": "2025-01-07T10:00:00Z",
            "server_version": "v2.0.0-mock"
        }
    
    def reset_stats(self):
        """Reset call statistics for testing"""
        self.call_count = 0
        self.last_query = None