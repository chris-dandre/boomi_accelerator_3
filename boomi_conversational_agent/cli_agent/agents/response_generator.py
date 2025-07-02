"""
ResponseGenerator Agent - Phase 5 TDD Implementation
Generates natural language responses from query results
"""
from typing import Dict, Any, List, Optional
import json
import re

class ResponseGenerator:
    """
    Generate natural language responses from query results
    Uses Claude LLM for intelligent, context-aware response generation
    """
    
    def __init__(self, mcp_client=None, claude_client=None):
        """
        Initialize ResponseGenerator agent
        
        Args:
            mcp_client: Optional MCP client (will create default if None)
            claude_client: Optional Claude client (will create default if None)
        """
        self.mcp_client = mcp_client or self._create_default_mcp_client()
        self.claude_client = claude_client or self._create_default_claude_client()
        
        # Response templates for different query types
        self.response_templates = {
            'COUNT': "I found {count} {subject}",
            'LIST': "Here are the {subject} I found:",
            'COMPARE': "Comparing {subjects}:",
            'ERROR': "I apologize, but I encountered an issue: {error_message}"
        }
        
        # Large dataset threshold
        self.large_dataset_threshold = 100
    
    def _create_default_mcp_client(self):
        """Create default MCP client - placeholder for real implementation"""
        return None
    
    def _create_default_claude_client(self):
        """Create default Claude client - placeholder for real implementation"""
        return None
    
    def generate_response(self, user_query: str, query_result: Dict[str, Any], 
                         user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate natural language response from query results
        
        Args:
            user_query: Original user question
            query_result: Results from DataRetrieval agent
            user_context: Optional user context for personalization
            
        Returns:
            Formatted response with message, type, and metadata
        """
        # Handle error results
        if 'error' in query_result:
            return self._generate_error_response(user_query, query_result)
        
        query_type = query_result.get('query_type', 'UNKNOWN')
        data = query_result.get('data', {})
        metadata = query_result.get('metadata', {})
        
        # Generate response based on query type
        if query_type == 'COUNT':
            response = self._generate_count_response(user_query, data, metadata)
        elif query_type == 'LIST':
            response = self._generate_list_response(user_query, data, metadata)
        elif query_type == 'COMPARE':
            response = self._generate_comparison_response(user_query, data, metadata)
        else:
            response = self._generate_generic_response(user_query, data, metadata)
        
        # Personalize response if user context provided
        if user_context:
            response['message'] = self.personalize_response_tone(
                response['message'], 
                user_context
            )
        
        # Add metadata and suggestions
        response['metadata'] = self._build_response_metadata(query_result, user_context)
        
        return response
    
    def format_data_for_display(self, data: List[Dict[str, Any]], 
                               display_type: str = 'list') -> str:
        """
        Format data for human-readable display
        
        Args:
            data: Data to format
            display_type: Type of display (list, table, summary)
            
        Returns:
            Formatted string representation
        """
        if not data:
            return "No data to display"
        
        if display_type == 'table':
            return self._format_as_table(data)
        elif display_type == 'summary':
            return self._format_as_summary(data)
        else:  # default to list
            return self._format_as_list(data)
    
    def generate_summary_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for a dataset
        
        Args:
            data: Dataset to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {'total_records': 0}
        
        summary = {
            'total_records': len(data),
            'fields': list(data[0].keys()) if data else []
        }
        
        # Analyze specific fields
        if data:
            # Count unique brands if brand field exists
            brand_field = None
            for field in ['brand_name', 'brand', 'manufacturer']:
                if field in data[0]:
                    brand_field = field
                    break
            
            if brand_field:
                unique_brands = len(set(record.get(brand_field) for record in data))
                summary['unique_brands'] = unique_brands
            
            # Analyze price if price field exists
            price_field = None
            for field in ['price', 'cost', 'amount']:
                if field in data[0]:
                    price_field = field
                    break
            
            if price_field:
                prices = [record.get(price_field) for record in data if record.get(price_field) is not None]
                if prices:
                    summary['price_range'] = {
                        'min': min(prices),
                        'max': max(prices),
                        'avg': sum(prices) / len(prices)
                    }
        
        return summary
    
    def personalize_response_tone(self, base_response: str, 
                                 user_context: Dict[str, Any]) -> str:
        """
        Personalize response tone based on user context
        
        Args:
            base_response: Base response text
            user_context: User role, experience level, etc.
            
        Returns:
            Personalized response
        """
        role = user_context.get('role', 'user')
        experience = user_context.get('experience_level', 'intermediate')
        detail_level = user_context.get('preferred_detail_level', 'standard')
        
        # For executives, make responses more concise and business-focused
        if 'executive' in role.lower():
            if detail_level == 'summary':
                # Remove technical details, focus on key numbers
                lines = base_response.split('\n')
                summary_lines = [line for line in lines if any(char.isdigit() for char in line)]
                if summary_lines:
                    return summary_lines[0]
        
        # For technical roles, can include more detail
        # For now, return base response with minor adjustments
        return base_response
    
    def add_visualization_suggestions(self, query_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest appropriate visualizations for the data
        
        Args:
            query_result: Query result to analyze
            
        Returns:
            List of visualization suggestions
        """
        suggestions = []
        query_type = query_result.get('query_type')
        data = query_result.get('data', {})
        
        if query_type == 'COUNT':
            suggestions.append({
                'type': 'metric_card',
                'title': 'Count Result',
                'description': 'Display the count as a large metric'
            })
        
        elif query_type == 'COMPARE':
            suggestions.extend([
                {
                    'type': 'bar_chart',
                    'title': 'Comparison Bar Chart',
                    'description': 'Compare values across categories'
                },
                {
                    'type': 'pie_chart',
                    'title': 'Comparison Pie Chart',
                    'description': 'Show proportional comparison'
                }
            ])
        
        elif query_type == 'LIST':
            if isinstance(data, list) and len(data) > 5:
                suggestions.append({
                    'type': 'table',
                    'title': 'Data Table',
                    'description': 'Display detailed data in tabular format'
                })
        
        return suggestions
    
    def _generate_count_response(self, user_query: str, data: Dict[str, Any], 
                                metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for COUNT queries"""
        count = data.get('count', 0)
        
        # Use Claude for natural language generation
        if self.claude_client:
            prompt = f"""
Generate a natural, user-friendly response for this count query.

User Query: {user_query}
Count Result: {count}
Model: {metadata.get('model_id', 'unknown')}

Generate a helpful response that:
1. Directly answers the user's question
2. Includes the count number
3. Uses natural language
4. Is concise but informative

Return only the response text, no JSON or formatting.
"""
            try:
                natural_response = self.claude_client.query(prompt)
                return {
                    'response_type': 'COUNT',
                    'message': natural_response.strip(),
                    'count': count
                }
            except:
                pass
        
        # Fallback response
        subject = self._extract_subject_from_query(user_query)
        message = f"I found {count} {subject}."
        
        return {
            'response_type': 'COUNT',
            'message': message,
            'count': count
        }
    
    def _generate_list_response(self, user_query: str, data: List[Dict[str, Any]], 
                               metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for LIST queries"""
        if not data:
            return {
                'response_type': 'LIST',
                'message': "I didn't find any results matching your criteria.",
                'item_count': 0
            }
        
        record_count = len(data)
        
        # Handle large datasets
        if record_count > self.large_dataset_threshold:
            return self._generate_large_dataset_response(user_query, data, metadata)
        
        # Use Claude for intelligent field selection and natural language generation
        if self.claude_client:
            print("🧠 Claude Analysis: Analyzing data structure and user intent...")
            
            prompt = f"""
Generate a natural, user-friendly response for this list query that shows meaningful business data.

User Query: {user_query}
Number of Results: {record_count}
Data to Display: {json.dumps(data[:min(10, record_count)], indent=2)}

Your task:
1. Analyze the available fields in the data
2. Select the most relevant fields to display based on the user's query
3. Generate a helpful response that lists the actual business values (not IDs)
4. Use natural language that matches what the user asked for

For example:
- If they asked about "products Sony is advertising", show the PRODUCT names like "Sony ZV-E10 II"
- If they asked about "users", show names like "John Smith" using FIRSTNAME + LASTNAME, or USERID if names not available
- If they asked about "opportunities", show opportunity names/titles not IDs

Generate the response in this format:
Here are the [items] I found ([count] total):

1. [meaningful business value]
2. [meaningful business value]
...

IMPORTANT: 
- Always show actual data from the provided records, not placeholders
- If total results > 10: show exactly 10 items and mention "... and X more items"
- If total results <= 10: show all available items
- Use the best available fields (names > IDs)
- Extract actual field values from the data, don't use generic placeholders

Return only the response text, no JSON or additional formatting.
"""
            
            print(f"🔍 Claude Prompt Preview:")
            print(f"   User Query: {user_query}")
            print(f"   Data Fields Available: {list(data[0].keys()) if data else 'None'}")
            print(f"   Record Count: {record_count}")
            
            try:
                print("💭 Claude Processing: Selecting optimal fields and generating response...")
                natural_response = self.claude_client.query(prompt)
                print(f"✅ Claude Generated Response:")
                print(f"   Length: {len(natural_response)} characters")
                print(f"   Preview: {natural_response[:100]}...")
                
                return {
                    'response_type': 'LIST',
                    'message': natural_response.strip(),
                    'item_count': record_count,
                    'data_preview': data[:5]
                }
            except Exception as e:
                print(f"❌ Claude response generation failed: {e}")
                print("🔄 Falling back to rule-based field selection...")
                pass
        
        # Fallback response with smarter field selection
        print("🔧 Rule-Based Analysis: Using fallback field selection logic...")
        print(f"   Query Context: '{user_query}'")
        print(f"   Available Fields: {list(data[0].keys()) if data else 'None'}")
        
        # Apply smart limit: show 10 if > 10, otherwise show all
        display_limit = min(10, record_count)
        display_data = data[:display_limit]
        formatted_data = self._format_list_with_smart_fields(display_data, user_query)
        message = f"Here are the results I found ({record_count} total):\n\n{formatted_data}"
        
        print(f"✅ Rule-Based Response Generated:")
        print(f"   Field Selection Logic Applied")
        print(f"   Items Formatted: {display_limit}")
        
        if record_count > 10:
            message += f"\n\n... and {record_count - 10} more items."
        
        return {
            'response_type': 'LIST',
            'message': message,
            'item_count': record_count,
            'data_preview': data[:5]
        }
    
    def _generate_comparison_response(self, user_query: str, data: List[Dict[str, Any]], 
                                    metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for COMPARE queries"""
        if not data:
            return {
                'response_type': 'COMPARE',
                'message': "I couldn't find any data to compare.",
                'comparison_count': 0
            }
        
        # Use Claude for natural language generation
        if self.claude_client:
            prompt = f"""
Generate a natural, user-friendly comparison response.

User Query: {user_query}
Comparison Data: {json.dumps(data, indent=2)}

Generate a helpful response that:
1. Clearly compares the different groups
2. Highlights key differences or insights
3. Uses natural language
4. Is easy to understand

Return only the response text, no JSON or formatting.
"""
            try:
                natural_response = self.claude_client.query(prompt)
                return {
                    'response_type': 'COMPARE',
                    'message': natural_response.strip(),
                    'comparison_count': len(data),
                    'comparison_data': data
                }
            except:
                pass
        
        # Fallback response
        formatted_data = self.format_data_for_display(data, 'table')
        message = f"Here's the comparison you requested:\n\n{formatted_data}"
        
        return {
            'response_type': 'COMPARE',
            'message': message,
            'comparison_count': len(data),
            'comparison_data': data
        }
    
    def _generate_error_response(self, user_query: str, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for error cases"""
        error_message = error_result.get('error', 'Unknown error')
        
        # Use Claude for natural language generation
        if self.claude_client:
            prompt = f"""
Generate a helpful, apologetic error response for the user.

User Query: {user_query}
Error: {error_message}

Generate a response that:
1. Apologizes for the issue
2. Explains what went wrong in simple terms
3. Suggests what the user might try instead
4. Is empathetic and helpful

Return only the response text, no JSON or formatting.
"""
            try:
                natural_response = self.claude_client.query(prompt)
                return {
                    'response_type': 'ERROR',
                    'message': natural_response.strip(),
                    'error_details': error_message
                }
            except:
                pass
        
        # Fallback response
        return {
            'response_type': 'ERROR',
            'message': f"I apologize, but I encountered an issue while processing your request. {error_message}",
            'error_details': error_message
        }
    
    def _generate_generic_response(self, user_query: str, data: Any, 
                                  metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic response for unknown query types"""
        return {
            'response_type': 'GENERIC',
            'message': "I've processed your request and found some information from the Boomi DataHub.",
            'data_summary': self._summarize_data(data)
        }
    
    def _generate_large_dataset_response(self, user_query: str, data: List[Dict[str, Any]], 
                                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response for large datasets"""
        record_count = len(data)
        summary_stats = self.generate_summary_statistics(data)
        
        message = f"I found {record_count} results for your query. Here's a summary:\n\n"
        message += f"• Total records: {record_count}\n"
        
        if 'unique_brands' in summary_stats:
            message += f"• Unique brands: {summary_stats['unique_brands']}\n"
        
        if 'price_range' in summary_stats:
            price_range = summary_stats['price_range']
            message += f"• Price range: ${price_range['min']:.2f} - ${price_range['max']:.2f}\n"
        
        message += f"\nShowing first 5 results:\n"
        message += self.format_data_for_display(data[:5])
        
        return {
            'response_type': 'LIST',
            'message': message,
            'item_count': record_count,
            'data_preview': data[:5],
            'metadata': {
                'suggestions': [
                    'Try adding filters to narrow down the results',
                    'Use pagination to browse through all results'
                ]
            }
        }
    
    def _build_response_metadata(self, query_result: Dict[str, Any], 
                                user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build metadata for the response"""
        original_metadata = query_result.get('metadata', {})
        
        response_metadata = {
            'execution_time_ms': original_metadata.get('execution_time_ms', 0),
            'data_summary': self._summarize_data(query_result.get('data')),
            'visualization_suggestions': self.add_visualization_suggestions(query_result)
        }
        
        # Add suggestions for large datasets
        if isinstance(query_result.get('data'), list):
            data_length = len(query_result['data'])
            if data_length > self.large_dataset_threshold:
                response_metadata['suggestions'] = [
                    'Consider adding filters to narrow down results',
                    'Use pagination for better performance'
                ]
        
        return response_metadata
    
    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """Create a summary of the data"""
        if isinstance(data, dict):
            if 'count' in data:
                return {'type': 'count', 'value': data['count']}
            return {'type': 'object', 'keys': list(data.keys())}
        elif isinstance(data, list):
            return {'type': 'list', 'length': len(data)}
        else:
            return {'type': 'unknown', 'value': str(data)}
    
    def _extract_subject_from_query(self, query: str) -> str:
        """Extract the subject being queried about"""
        # Simple keyword extraction
        if 'product' in query.lower():
            return 'products'
        elif 'campaign' in query.lower():
            return 'campaigns'
        elif 'launch' in query.lower():
            return 'launches'
        else:
            return 'items'
    
    def _format_list_with_smart_fields(self, data: List[Dict[str, Any]], user_query: str) -> str:
        """Format data list with intelligent field selection based on query"""
        if not data:
            return "No items to display"
        
        formatted_items = []
        for i, item in enumerate(data[:10], 1):  # Limit to 10 items
            # Smart field selection based on query context
            display_value = self._select_best_display_field(item, user_query)
            formatted_items.append(f"{i}. {display_value}")
        
        return '\n'.join(formatted_items)
    
    def _select_best_display_field(self, item: Dict[str, Any], user_query: str) -> str:
        """Select the best field to display based on query context"""
        if not item:
            return "Unknown"
        
        query_lower = user_query.lower()
        
        # Query-specific field priorities
        if 'product' in query_lower:
            # For product queries, prioritize PRODUCT field
            print(f"   🎯 Product Query Detected: Prioritizing product-related fields")
            for field in ['PRODUCT', 'product_name', 'name']:
                if field in item and item[field] and item[field] != '_RECORD_ID':
                    print(f"   ✅ Selected Field: {field} = '{item[field]}'")
                    return str(item[field])
        
        elif 'user' in query_lower:
            # For user queries, try to construct full name first
            print(f"   🎯 User Query Detected: Prioritizing user name fields")
            firstname = item.get('FIRSTNAME', '').strip()
            lastname = item.get('LASTNAME', '').strip()
            if firstname and lastname:
                full_name = f"{firstname} {lastname}"
                print(f"   ✅ Selected Combined Name: {full_name}")
                return full_name
            elif firstname:
                print(f"   ✅ Selected First Name: {firstname}")
                return firstname
            elif lastname:
                print(f"   ✅ Selected Last Name: {lastname}")
                return lastname
            # Fallback to other user fields
            for field in ['USER_NAME', 'username', 'name', 'email', 'USERID']:
                if field in item and item[field] and item[field] != '_RECORD_ID':
                    print(f"   ✅ Selected Field: {field} = '{item[field]}'")
                    return str(item[field])
        
        elif 'opportunity' in query_lower:
            # For opportunity queries, prioritize opportunity name/title
            for field in ['opportunity_name', 'title', 'name', 'subject']:
                if field in item and item[field] and item[field] != '_RECORD_ID':
                    return str(item[field])
        
        elif 'campaign' in query_lower or 'advertisement' in query_lower:
            # For campaign/ad queries, show meaningful combination of advertiser and product
            print(f"   🎯 Advertisement Query Detected: Combining ADVERTISER and PRODUCT")
            advertiser = item.get('ADVERTISER', '')
            product = item.get('PRODUCT', '')
            if advertiser and product and advertiser != '_RECORD_ID' and product != '_RECORD_ID':
                combined = f"{advertiser} - {product}"
                print(f"   ✅ Selected Combined: {combined}")
                return combined
            # Fallback to single fields
            for field in ['CAMPAIGN', 'ADVERTISER', 'PRODUCT', 'name', 'title']:
                if field in item and item[field] and item[field] != '_RECORD_ID':
                    print(f"   ✅ Selected Field: {field} = '{item[field]}'")
                    return str(item[field])
        
        # General fallback: find the most meaningful field
        # Prioritize business fields over technical IDs
        priority_fields = [
            'PRODUCT', 'ADVERTISER', 'USER_NAME', 'name', 'title', 
            'campaign_name', 'opportunity_name', 'subject', 'description'
        ]
        
        for field in priority_fields:
            if field in item and item[field] and item[field] != '_RECORD_ID':
                return str(item[field])
        
        # Last resort: use first non-ID field
        for key, value in item.items():
            if not key.endswith('_ID') and key != '_RECORD_ID' and value:
                return str(value)
        
        # Final fallback
        return "Unknown item"

    def _format_as_list(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a simple list (legacy method)"""
        if not data:
            return "No items to display"
        
        formatted_items = []
        for i, item in enumerate(data[:10], 1):  # Limit to 10 items
            # Find the most relevant field to display
            display_field = None
            for field in ['PRODUCT', 'product_name', 'name', 'title', 'campaign_name', 'ADVERTISER']:
                if field in item:
                    display_field = field
                    break
            
            if display_field:
                formatted_items.append(f"{i}. {item[display_field]}")
            else:
                # Use first available field
                first_key = list(item.keys())[0] if item else 'unknown'
                formatted_items.append(f"{i}. {item.get(first_key, 'Unknown')}")
        
        return '\n'.join(formatted_items)
    
    def _format_as_table(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a simple table"""
        if not data:
            return "No data to display"
        
        # Use key fields for table display
        headers = list(data[0].keys())[:4]  # Limit to 4 columns
        
        # Create header row
        header_row = " | ".join(f"{h:15}" for h in headers)
        separator = "-" * len(header_row)
        
        # Create data rows
        rows = [header_row, separator]
        for item in data[:10]:  # Limit to 10 rows
            row_values = []
            for header in headers:
                value = str(item.get(header, ''))[:15]  # Truncate long values
                row_values.append(f"{value:15}")
            rows.append(" | ".join(row_values))
        
        return '\n'.join(rows)
    
    def _format_as_summary(self, data: List[Dict[str, Any]]) -> str:
        """Format data as a summary"""
        if not data:
            return "No data to summarize"
        
        summary_stats = self.generate_summary_statistics(data)
        summary_text = f"Summary of {summary_stats['total_records']} records:\n"
        
        if 'unique_brands' in summary_stats:
            summary_text += f"• {summary_stats['unique_brands']} unique brands\n"
        
        if 'price_range' in summary_stats:
            price_range = summary_stats['price_range']
            summary_text += f"• Price range: ${price_range['min']:.2f} - ${price_range['max']:.2f}\n"
            summary_text += f"• Average price: ${price_range['avg']:.2f}\n"
        
        return summary_text