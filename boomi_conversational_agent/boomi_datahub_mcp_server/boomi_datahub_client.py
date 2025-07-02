# boomi_datahub_client_fixed.py
"""
Fixed version of the Boomi DataHub client with improved XML parsing and error handling
"""

import os
import requests
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import base64
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging from environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(level=logging_level)
logger = logging.getLogger(__name__)

@dataclass
class BoomiCredentials:
    """Boomi API credentials"""
    username: str
    password: str
    account_id: str
    base_url: str
    
    # Optional separate credentials for DataHub queries
    datahub_username: Optional[str] = None
    datahub_password: Optional[str] = None

class BoomiDataHubClient:
    """
    Boomi DataHub REST API Client with Fixed XML Parsing
    """
    
    def __init__(self, credentials: Optional[BoomiCredentials] = None):
        """
        Initialize the Boomi DataHub client
        
        Args:
            credentials: BoomiCredentials object, if None will load from environment
        """
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = self._load_credentials_from_env()
        
        self.session = requests.Session()
        self._setup_authentication()
    
    def _load_credentials_from_env(self) -> BoomiCredentials:
        """Load credentials from environment variables"""
        username = os.getenv('BOOMI_USERNAME')
        password = os.getenv('BOOMI_PASSWORD')
        account_id = os.getenv('BOOMI_ACCOUNT_ID')
        base_url = os.getenv('BOOMI_BASE_URL', 'https://api.boomi.com')
        
        # Load separate DataHub credentials if available
        datahub_username = os.getenv('BOOMI_DATAHUB_USERNAME')
        datahub_password = os.getenv('BOOMI_DATAHUB_PASSWORD')
        
        if not all([username, password, account_id]):
            raise ValueError("Missing required Boomi credentials in environment variables: BOOMI_USERNAME, BOOMI_PASSWORD, BOOMI_ACCOUNT_ID")
        
        return BoomiCredentials(
            username=username, 
            password=password, 
            account_id=account_id, 
            base_url=base_url,
            datahub_username=datahub_username,
            datahub_password=datahub_password
        )
    
    def set_datahub_credentials(self, username: str, password: str):
        """
        Set separate credentials for DataHub record queries
        
        Args:
            username: DataHub username
            password: DataHub password
        """
        self.credentials.datahub_username = username
        self.credentials.datahub_password = password
        logger.info("🔑 DataHub credentials updated")
    
    def has_datahub_credentials(self) -> bool:
        """
        Check if separate DataHub credentials are configured
        
        Returns:
            True if DataHub credentials are set, False otherwise
        """
        return bool(self.credentials.datahub_username and self.credentials.datahub_password)
    
    def _setup_authentication(self):
        """Setup authentication for API requests"""
        # Boomi uses Basic Auth with username:password base64 encoded
        auth_string = f"{self.credentials.username}:{self.credentials.password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update({
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json,application/xml',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an authenticated request to Boomi API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        url = f"{self.credentials.base_url.rstrip('/')}/mdm/api/rest/v1/{self.credentials.account_id}/{endpoint.lstrip('/')}"
        
        logger.debug(f"Making {method} request to: {url}")
        logger.debug(f"Request params: {kwargs.get('params', {})}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code >= 400:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response content: {response.text}")
                
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def _parse_xml_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse XML response from Boomi API
        
        Args:
            response_text: XML response text
            
        Returns:
            List of model dictionaries
        """
        try:
            root = ET.fromstring(response_text)
            models = []
            
            # Namespace for Boomi MDM XML
            ns = {'mdm': 'http://mdm.api.platform.boomi.com/'}
            
            # Handle different response types
            if root.tag.endswith('GetModelResponse'):
                # Single model response (from GET /models/{id})
                model = self._parse_single_model_xml(root, ns)
                if model:
                    models.append(model)
            else:
                # Multiple models response (from GET /models)
                for model_elem in root.findall('mdm:Model', ns):
                    model = self._parse_basic_model_xml(model_elem, ns)
                    if model:
                        models.append(model)
            
            return models
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            return []
    
    def _parse_basic_model_xml(self, model_elem, ns) -> Dict[str, Any]:
        """Parse basic model info from Models list response"""
        model = {}
        
        # Extract basic model fields
        name_elem = model_elem.find('mdm:name', ns)
        if name_elem is not None:
            model['name'] = name_elem.text
        
        id_elem = model_elem.find('mdm:id', ns)
        if id_elem is not None:
            model['id'] = id_elem.text
        
        status_elem = model_elem.find('mdm:publicationStatus', ns)
        if status_elem is not None:
            # Convert boolean string to readable status
            is_published = status_elem.text.lower() == 'true'
            model['publicationStatus'] = 'publish' if is_published else 'draft'
            model['published'] = is_published
        
        version_elem = model_elem.find('mdm:latestVersion', ns)
        if version_elem is not None:
            model['latestVersion'] = version_elem.text
        
        return model
    
    def _parse_single_model_xml(self, root, ns) -> Dict[str, Any]:
        """Parse detailed model info from GetModelResponse"""
        model = {}
        
        # Extract basic model fields
        name_elem = root.find('mdm:name', ns)
        if name_elem is not None:
            model['name'] = name_elem.text
        
        id_elem = root.find('mdm:id', ns)
        if id_elem is not None:
            model['id'] = id_elem.text
        
        version_elem = root.find('mdm:version', ns)
        if version_elem is not None:
            model['version'] = version_elem.text
            model['latestVersion'] = version_elem.text
        
        # Determine publication status (detailed model might not have this field)
        # For detailed models, assume published if version exists
        if 'version' in model:
            model['publicationStatus'] = 'publish'
            model['published'] = True
        
        # Extract fields with enhanced field mapping
        fields = []
        fields_elem = root.find('mdm:fields', ns)
        if fields_elem is not None:
            for field_elem in fields_elem.findall('mdm:field', ns):
                field = {}
                
                # Get the original field name first
                original_name = field_elem.get('name', '')
                
                # Get field attributes
                field['type'] = field_elem.get('type', '')
                field['uniqueId'] = field_elem.get('uniqueId', '')
                field['required'] = field_elem.get('required', 'false').lower() == 'true'
                field['repeatable'] = field_elem.get('repeatable', 'false').lower() == 'true'
                
                # Store field information with consistent uppercase naming
                field['name'] = original_name.upper()  # Always store as uppercase
                field['displayName'] = original_name.upper()  # Display as uppercase
                field['queryFieldId'] = original_name.upper()  # Query as uppercase
                field['originalName'] = original_name  # Keep original for reference
                
                fields.append(field)
        
        if fields:
            model['fields'] = fields
            model['fieldCount'] = len(fields)
        
        # Extract sources
        sources = []
        sources_elem = root.find('mdm:sources', ns)
        if sources_elem is not None:
            for source_elem in sources_elem.findall('mdm:source', ns):
                source = {}
                source['id'] = source_elem.get('id', '')
                source['type'] = source_elem.get('type', '')
                source['allowMultipleLinks'] = source_elem.get('allowMultipleLinks', 'false').lower() == 'true'
                source['default'] = source_elem.get('default', 'false').lower() == 'true'
                sources.append(source)
        
        if sources:
            model['sources'] = sources
            model['sourceCount'] = len(sources)
        
        # Extract match rules
        match_rules_elem = root.find('mdm:matchRules', ns)
        if match_rules_elem is not None:
            match_rules = []
            for rule_elem in match_rules_elem.findall('mdm:matchRule', ns):
                rule = {}
                rule['topLevelOperator'] = rule_elem.get('topLevelOperator', '')
                
                # Extract simple expressions
                expressions = []
                for expr_elem in rule_elem.findall('mdm:simpleExpression', ns):
                    field_id_elem = expr_elem.find('mdm:fieldUniqueId', ns)
                    if field_id_elem is not None:
                        expressions.append({'fieldUniqueId': field_id_elem.text})
                
                if expressions:
                    rule['expressions'] = expressions
                
                match_rules.append(rule)
            
            if match_rules:
                model['matchRules'] = match_rules
        
        # Extract record title
        title_elem = root.find('mdm:recordTitle', ns)
        if title_elem is not None:
            title_params = []
            params_elem = title_elem.find('mdm:titleParameters', ns)
            if params_elem is not None:
                for param_elem in params_elem.findall('mdm:parameter', ns):
                    unique_id = param_elem.get('uniqueId', '')
                    if unique_id:
                        title_params.append(unique_id)
            
            if title_params:
                model['recordTitleFields'] = title_params
        
        return model
    
    def _get_response(self, method: str, endpoint: str, **kwargs) -> List[Dict[str, Any]]:
        """Make request and return parsed response"""
        response = self._make_request(method, endpoint, **kwargs)
        
        # Check if response is XML or JSON
        content_type = response.headers.get('content-type', '').lower()
        
        if 'xml' in content_type:
            return self._parse_xml_response(response.text)
        else:
            try:
                json_response = response.json()
                # Handle different JSON response formats
                if isinstance(json_response, list):
                    return json_response
                else:
                    return json_response.get('models', json_response.get('model', []))
            except ValueError:
                logger.warning("Response is neither valid XML nor JSON, attempting XML parse")
                return self._parse_xml_response(response.text)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Boomi DataHub API
        
        Returns:
            Dictionary with connection test results
        """
        test_result = {
            'success': False,
            'error': None,
            'status_code': None,
            'url': None,
            'response_content': None,
            'account_id': self.credentials.account_id,
            'has_datahub_credentials': self.has_datahub_credentials()
        }
        
        try:
            url = f"{self.credentials.base_url.rstrip('/')}/mdm/api/rest/v1/{self.credentials.account_id}/models"
            test_result['url'] = url
            
            logger.info(f"Testing connection with account ID '{self.credentials.account_id}': {url}")
            response = self.session.get(url)
            
            test_result['status_code'] = response.status_code
            test_result['response_content'] = response.text[:500] if response.text else None
            
            if response.status_code == 200:
                test_result['success'] = True
                logger.info("Connection test successful")
            else:
                test_result['error'] = f"HTTP {response.status_code}: {response.reason}"
                logger.warning(f"Connection test failed: {test_result['error']}")
                
        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"Connection test exception: {e}")
        
        return test_result
    
    # API Methods
    
    def get_models(self, status: Optional[str] = None, name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve models from DataHub (all repositories)
        
        Args:
            status: Filter by publication status ('published', 'draft', 'all', or None for all)
            name: Filter by model name (optional)
            
        Returns:
            List of model objects from all repositories
        """
        endpoint = "models"
        params = {}
        
        if status:
            # Map user-friendly status values to API values
            status_mapping = {
                'published': 'publish',
                'draft': 'draft', 
                'all': 'all'
            }
            
            api_status = status_mapping.get(status.lower(), status)
            params['publicationStatus'] = api_status
        
        if name:
            params['name'] = name
        
        try:
            return self._get_response('GET', endpoint, params=params)
        except Exception as e:
            logger.error(f"Failed to retrieve models: {e}")
            return []
    
    def get_published_models(self) -> List[Dict[str, Any]]:
        """
        Retrieve all published models from all repositories
        
        Returns:
            List of published model objects
        """
        # Filter published models from all models (since API doesn't support status filtering)
        all_models = self.get_models()
        return [model for model in all_models if model.get('published', False)]
    
    def get_draft_models(self) -> List[Dict[str, Any]]:
        """
        Retrieve all draft models from all repositories
        
        Returns:
            List of draft model objects
        """
        # Filter draft models from all models (since API doesn't support status filtering)
        all_models = self.get_models()
        return [model for model in all_models if not model.get('published', True)]
    
    def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve both published and draft models from all repositories
        
        Returns:
            Dictionary with 'published' and 'draft' keys containing respective models
        """
        return {
            'published': self.get_published_models(),
            'draft': self.get_draft_models()
        }
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific model by ID
        
        Args:
            model_id: The model identifier
            
        Returns:
            Model object or None if not found
        """
        endpoint = f"models/{model_id}"
        
        try:
            models = self._get_response('GET', endpoint)
            return models[0] if models else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Model {model_id} not found")
                return None
            raise
    
    # FIXED: Parameterised Query Methods with Better XML Parsing
    
    def query_records_by_parameters(self, universe_id: str, repository_id: str, 
                               fields: List[str] = None, filters: List[Dict[str, Any]] = None,
                               limit: int = 100, offset_token: str = "") -> Dict[str, Any]:
        """
        Execute a parameterised query against Boomi DataHub records
        
        Args:
            universe_id: The universe/model identifier
            repository_id: The repository identifier within the universe
            fields: List of field names to retrieve (if None, gets all model fields)
            filters: List of filter dictionaries with fieldId, operator, and value
            limit: Maximum number of records to return (default: 100, max: 1000)
            offset_token: Pagination token for continuing previous queries
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Validate inputs
            if not universe_id or not repository_id:
                raise ValueError("universe_id and repository_id are required")
                
            limit = min(max(1, limit), 1000)  # Clamp between 1 and 1000
            
            # Get model details to validate fields if not provided
            if fields is None:
                model_details = self.get_model_by_id(universe_id)
                if model_details and 'fields' in model_details:
                    # Use queryFieldId if available, otherwise convert name to uppercase
                    fields = []
                    for field in model_details['fields']:
                        if field.get('queryFieldId'):
                            fields.append(field['queryFieldId'])
                        elif field.get('name'):
                            fields.append(field['name'].upper())
                else:
                    raise ValueError(f"Could not retrieve field information for universe {universe_id}")
            else:
                # Convert provided field names to uppercase for queries
                fields = [field.upper() for field in fields]
            
            # Convert filter field names to uppercase
            if filters:
                for filter_def in filters:
                    if 'fieldId' in filter_def:
                        filter_def['fieldId'] = filter_def['fieldId'].upper()
            
            # Build XML request body
            query_request = self._build_query_xml(fields, filters, limit, offset_token)
            
            # Construct the API URL - use DataHub URL structure
            # Convert api.boomi.com to the hub URL if needed
            hub_base_url = self.credentials.base_url.replace('api.boomi.com', 'c01-aus-local.hub.boomi.com')
            base_url = f"{hub_base_url.rstrip('/')}/mdm/universes/{universe_id}/records/query"
            params = {"repositoryId": repository_id}
            
            # Use DataHub credentials if available, otherwise use regular credentials
            if self.credentials.datahub_username and self.credentials.datahub_password:
                auth_username = self.credentials.datahub_username
                auth_password = self.credentials.datahub_password
                logger.info("🔑 Using separate DataHub credentials for record query")
            else:
                auth_username = self.credentials.username
                auth_password = self.credentials.password
                logger.info("🔑 Using regular API credentials for record query")
            
            # Create auth header with appropriate credentials
            auth_string = f"{auth_username}:{auth_password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            # Prepare headers with multiple authentication attempts
            headers = {
                "Content-Type": "application/xml",
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/xml",
                "User-Agent": "BoomiDataHubClient/1.0"
            }
            
            logger.info(f"🔍 Executing query to: {base_url}")
            logger.debug(f"📋 Query XML: {query_request}")
            logger.debug(f"📋 Headers: {headers}")
            
            # Execute the request
            response = requests.post(
                base_url,
                params=params,
                headers=headers,
                data=query_request,
                timeout=30
            )
            
            logger.info(f"📊 Response status: {response.status_code}")
            logger.debug(f"📋 Response headers: {dict(response.headers)}")
            logger.debug(f"📋 Response content (first 1000 chars): {response.text[:1000]}")
            
            # Special handling for 401 errors with detailed troubleshooting
            if response.status_code == 401:
                logger.error("❌ 401 UNAUTHORIZED - Authentication failed for DataHub queries")
                
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Authentication failed for DataHub record queries",
                    "status_code": 401,
                    "troubleshooting": {
                        "issue": "DataHub query authentication failed",
                        "possible_causes": [
                            "Different permissions required for DataHub vs API access",
                            "User account lacks DataHub query permissions",
                            "Universe or repository access restrictions",
                            "Different authentication method required for DataHub"
                        ],
                        "next_steps": [
                            "Set separate DataHub credentials using BOOMI_DATAHUB_USERNAME and BOOMI_DATAHUB_PASSWORD",
                            "Or use client.set_datahub_credentials(username, password)",
                            "Verify your DataHub query credentials with your Boomi administrator",
                            "Test with the auth_debug.py script after setting DataHub credentials",
                            "Contact Boomi administrator for DataHub query permissions"
                        ],
                        "auth_info": {
                            "model_api_works": "Yes (you can retrieve model information)",
                            "datahub_query_fails": "Yes (401 UNAUTHORIZED)",
                            "url_used": base_url,
                            "auth_header": f"Basic {auth_b64[:20]}...",
                            "has_datahub_credentials": self.has_datahub_credentials()
                        }
                    },
                    "query_parameters": {
                        "universe_id": universe_id,
                        "repository_id": repository_id,
                        "fields": fields,
                        "filters": filters or [],
                        "limit": limit
                    }
                }
            
            # Process the response
            if response.status_code == 200:
                # Parse XML response and convert to JSON
                try:
                    records_data = self._parse_query_response_fixed(response.text)
                    
                    result = {
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                        "query_parameters": {
                            "universe_id": universe_id,
                            "repository_id": repository_id,
                            "fields": fields,
                            "filters": filters or [],
                            "limit": limit,
                            "offset_token": offset_token
                        },
                        "data": records_data,
                        "metadata": {
                            "records_returned": len(records_data.get("records", [])),
                            "has_more": records_data.get("has_more", False),
                            "next_offset_token": records_data.get("next_offset_token", "")
                        }
                    }
                    
                    logger.info(f"✅ Query successful: {len(records_data.get('records', []))} records returned")
                    return result
                    
                except Exception as parse_error:
                    logger.error(f"❌ XML parsing failed: {parse_error}")
                    
                    # Return the raw response for debugging
                    return {
                        "status": "error",
                        "timestamp": datetime.now().isoformat(),
                        "error": f"XML parsing failed: {str(parse_error)}",
                        "status_code": response.status_code,
                        "raw_response": response.text,
                        "query_parameters": {
                            "universe_id": universe_id,
                            "repository_id": repository_id,
                            "fields": fields,
                            "filters": filters or [],
                            "limit": limit
                        }
                    }
                
            else:
                # Handle API errors
                error_message = f"API request failed with status {response.status_code}"
                
                try:
                    # Try to parse error response
                    error_xml = ET.fromstring(response.text)
                    error_detail = error_xml.find(".//message")
                    if error_detail is not None:
                        error_message = error_detail.text
                except ET.ParseError:
                    # If XML parsing fails, use status text
                    error_message = f"{error_message}: {response.text[:200]}"
                
                logger.error(f"❌ Query failed: {error_message}")
                
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": error_message,
                    "status_code": response.status_code,
                    "response_body": response.text[:500],  # First 500 chars for debugging
                    "query_parameters": {
                        "universe_id": universe_id,
                        "repository_id": repository_id,
                        "fields": fields,
                        "filters": filters or [],
                        "limit": limit
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Query exception: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "query_parameters": {
                    "universe_id": universe_id,
                    "repository_id": repository_id,
                    "fields": fields or [],
                    "filters": filters or [],
                    "limit": limit
                }
            }

    def _build_query_xml(self, fields: List[str], filters: List[Dict[str, Any]] = None, 
                        limit: int = 100, offset_token: str = "") -> str:
        """
        Build the XML request body for Boomi DataHub query
        
        Args:
            fields: List of field names to include in the view
            filters: List of filter dictionaries
            limit: Maximum records to return
            offset_token: Pagination token
            
        Returns:
            XML string for the request body
        """
        # Create root element
        root = ET.Element("RecordQueryRequest")
        root.set("limit", str(limit))
        root.set("offsetToken", offset_token)
        
        # Add view section with fields
        view = ET.SubElement(root, "view")
        for field in fields:
            field_elem = ET.SubElement(view, "fieldId")
            field_elem.text = field
        
        # Add filter section if filters are provided
        if filters:
            filter_root = ET.SubElement(root, "filter")
            
            # Use AND for multiple filters (change to OR if needed)
            if len(filters) > 1:
                filter_root.set("op", "AND")
            
            for filter_def in filters:
                field_value = ET.SubElement(filter_root, "fieldValue")
                
                # Field ID
                field_id_elem = ET.SubElement(field_value, "fieldId")
                field_id_elem.text = filter_def.get("fieldId", "")
                
                # Operator
                operator_elem = ET.SubElement(field_value, "operator")
                operator_elem.text = filter_def.get("operator", "EQUALS")
                
                # Value
                value_elem = ET.SubElement(field_value, "value")
                value_elem.text = str(filter_def.get("value", ""))
        
        # Convert to string
        return ET.tostring(root, encoding='unicode')

    def _parse_query_response_fixed(self, xml_response: str) -> Dict[str, Any]:
        import xml.etree.ElementTree as ET
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            root = ET.fromstring(xml_response)
            
            # Detect namespace if present
            if '}' in root.tag:
                namespace = root.tag.split('}')[0][1:]
                ns = {'ns': namespace}
            else:
                ns = {}
            
            records = []
            
            # Find all Record elements
            record_elems = root.findall('.//ns:Record', ns) if ns else root.findall('.//Record')
            
            for record_elem in record_elems:
                record_data = {}
                
                # Extract record attributes
                record_id = record_elem.get('recordId')
                if record_id:
                    record_data['_record_id'] = record_id
                
                # Find Fields element
                fields_elem = record_elem.find('ns:Fields', ns) if ns else record_elem.find('Fields')
                if fields_elem is not None:
                    # Find the root field element (first child of Fields)
                    root_field_elem = list(fields_elem)[0] if len(fields_elem) > 0 else None
                    if root_field_elem is not None:
                        # Extract field values
                        for field_elem in root_field_elem:
                            field_name = field_elem.tag.split('}')[-1] if ns else field_elem.tag
                            field_value = field_elem.text or ""
                            record_data[field_name] = field_value
                
                records.append(record_data)
            
            # Extract pagination info
            result_count = int(root.get('resultCount', 0))
            total_count = int(root.get('totalCount', 0))
            offset_token = root.get('offsetToken', '')
            
            result = {
                "records": records,
                "total_returned": len(records),
                "total_count": total_count,
                "has_more": len(records) < total_count,
                "next_offset_token": offset_token if len(records) < total_count else ""
            }
            
            return result
        
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Failed to parse XML response: {e}")
        except Exception as e:
            logger.error(f"General parsing error: {e}")
            raise ValueError(f"Failed to process XML response: {e}")

    # def _parse_query_response_fixed(self, xml_response: str) -> Dict[str, Any]:
    #     """
    #     FIXED: Parse XML response from Boomi DataHub query into JSON format with namespace handling
        
    #     Args:
    #         xml_response: XML response string from Boomi API
            
    #     Returns:
    #         Dictionary containing parsed records and metadata
    #     """
    #     try:
    #         logger.debug(f"🔍 Parsing XML response (length: {len(xml_response)})")
    #         logger.debug(f"🔍 First 500 chars of XML: {xml_response[:500]}")
            
    #         root = ET.fromstring(xml_response)
    #         logger.debug(f"🔍 Root element: {root.tag}")
            
    #         # Extract namespace from root element
    #         if '}' in root.tag:
    #             ns_uri = root.tag.split('}')[0][1:]
    #             ns = {'ns': ns_uri}
    #         else:
    #             ns = {}
            
    #         records = []
            
    #         # Find record elements with namespace
    #         record_elements = root.findall(".//ns:record", ns) if ns else root.findall(".//record")
    #         if not record_elements:
    #             record_elements = root.findall(".//ns:Record", ns) if ns else root.findall(".//Record")
            
    #         logger.debug(f"🔍 Found {len(record_elements)} record elements")
            
    #         for record_elem in record_elements:
    #             record_data = {}
                
    #             # Extract record ID if available
    #             record_id = record_elem.get("id") or record_elem.get("ID")
    #             if record_id:
    #                 record_data["_record_id"] = record_id
                
    #             logger.debug(f"🔍 Processing record element: {record_elem.tag}")
    #             logger.debug(f"🔍 Record children: {[child.tag for child in record_elem]}")
                
    #             # Try to find field elements with namespace
    #             field_elements = record_elem.findall(".//ns:field", ns) if ns else record_elem.findall(".//field")
    #             if not field_elements:
    #                 field_elements = record_elem.findall(".//ns:Field", ns) if ns else record_elem.findall(".//Field")
                
    #             logger.debug(f"🔍 Found {len(field_elements)} field elements")
                
    #             for field_elem in field_elements:
    #                 field_id = field_elem.get("id") or field_elem.get("ID") or field_elem.get("name")
    #                 if not field_id and ns:
    #                     field_id = field_elem.tag.split('}')[-1]
    #                 elif not field_id:
    #                     field_id = field_elem.tag
                    
    #                 field_value = field_elem.text or ""
    #                 if field_id:
    #                     record_data[field_id] = field_value
    #                     logger.debug(f"🔍 Added field: {field_id} = {field_value}")
                
    #             if not field_elements:
    #                 logger.debug("🔍 No field elements found, trying direct children")
    #                 for child in record_elem:
    #                     if ns and '}' in child.tag:
    #                         field_name = child.tag.split('}')[-1]
    #                     else:
    #                         field_name = child.tag
    #                     field_value = child.text or ""
    #                     record_data[field_name] = field_value
    #                     logger.debug(f"🔍 Added direct child: {field_name} = {field_value}")
                
    #             if record_data:
    #                 records.append(record_data)
    #                 logger.debug(f"🔍 Added record with {len(record_data)} fields")
            
    #         # Extract pagination information
    #         has_more = False
    #         next_offset_token = ""
            
    #         for elem in root.iter():
    #             if 'pagination' in elem.tag.lower():
    #                 logger.debug(f"🔍 Found pagination element: {elem.tag}")
    #                 for child in elem:
    #                     if 'hasmore' in child.tag.lower():
    #                         has_more = child.text.lower() == "true"
    #                     elif 'offset' in child.tag.lower() or 'token' in child.tag.lower():
    #                         next_offset_token = child.text or ""
            
    #         result = {
    #             "records": records,
    #             "total_returned": len(records),
    #             "has_more": has_more,
    #             "next_offset_token": next_offset_token
    #         }
            
    #         logger.info(f"✅ Successfully parsed {len(records)} records from XML response")
    #         return result
            
    #     except ET.ParseError as e:
    #         logger.error(f"❌ XML parsing error: {e}")
    #         raise ValueError(f"Failed to parse XML response: {e}")
    #     except Exception as e:
    #         logger.error(f"❌ General parsing error: {e}")
    #         logger.error(f"❌ XML content that failed: {xml_response[:1000]}")
    #         raise ValueError(f"Failed to process XML response: {e}")

    # def _parse_query_response_fixed(self, xml_response: str) -> Dict[str, Any]:
    #     """
    #     FIXED: Parse XML response from Boomi DataHub query into JSON format
        
    #     Args:
    #         xml_response: XML response string from Boomi API
            
    #     Returns:
    #         Dictionary containing parsed records and metadata
    #     """
    #     try:
    #         logger.debug(f"🔍 Parsing XML response (length: {len(xml_response)})")
    #         logger.debug(f"🔍 First 500 chars of XML: {xml_response[:500]}")
            
    #         root = ET.fromstring(xml_response)
    #         logger.debug(f"🔍 Root element: {root.tag}")
            
    #         records = []
            
    #         # Try multiple approaches to find record elements
    #         # Approach 1: Look for direct record elements
    #         record_elements = root.findall(".//record")
    #         if not record_elements:
    #             # Approach 2: Look for Record with capital R
    #             record_elements = root.findall(".//Record")
            
    #         if not record_elements:
    #             # Approach 3: Look for any element that might contain records
    #             # Check all child elements to understand the structure
    #             logger.debug(f"🔍 Root children: {[child.tag for child in root]}")
                
    #             # Try to find any elements that might be records
    #             for elem in root.iter():
    #                 logger.debug(f"🔍 Found element: {elem.tag} with attribs: {elem.attrib}")
    #                 if elem.tag.lower().endswith('record') or 'record' in elem.tag.lower():
    #                     record_elements.append(elem)
            
    #         logger.debug(f"🔍 Found {len(record_elements)} record elements")
            
    #         for record_elem in record_elements:
    #             record_data = {}
                
    #             # Extract record ID if available
    #             record_id = record_elem.get("id") or record_elem.get("ID")
    #             if record_id:
    #                 record_data["_record_id"] = record_id
                
    #             logger.debug(f"🔍 Processing record element: {record_elem.tag}")
    #             logger.debug(f"🔍 Record children: {[child.tag for child in record_elem]}")
                
    #             # Extract field values - try different structures
    #             field_elements = record_elem.findall(".//field")
    #             if not field_elements:
    #                 field_elements = record_elem.findall(".//Field")
                
    #             logger.debug(f"🔍 Found {len(field_elements)} field elements")
                
    #             for field_elem in field_elements:
    #                 field_id = field_elem.get("id") or field_elem.get("ID") or field_elem.get("name")
    #                 field_value = field_elem.text or ""
                    
    #                 if field_id:
    #                     record_data[field_id] = field_value
    #                     logger.debug(f"🔍 Added field: {field_id} = {field_value}")
                
    #             # If no field elements found, try direct child elements
    #             if not field_elements:
    #                 logger.debug("🔍 No field elements found, trying direct children")
    #                 for child in record_elem:
    #                     field_name = child.tag
    #                     field_value = child.text or ""
    #                     record_data[field_name] = field_value
    #                     logger.debug(f"🔍 Added direct child: {field_name} = {field_value}")
                
    #             if record_data:  # Only add if we found some data
    #                 records.append(record_data)
    #                 logger.debug(f"🔍 Added record with {len(record_data)} fields")
            
    #         # Extract pagination information
    #         has_more = False
    #         next_offset_token = ""
            
    #         # Look for pagination elements
    #         for elem in root.iter():
    #             if 'pagination' in elem.tag.lower():
    #                 logger.debug(f"🔍 Found pagination element: {elem.tag}")
    #                 for child in elem:
    #                     if 'hasmore' in child.tag.lower():
    #                         has_more = child.text.lower() == "true"
    #                     elif 'offset' in child.tag.lower() or 'token' in child.tag.lower():
    #                         next_offset_token = child.text or ""
            
    #         result = {
    #             "records": records,
    #             "total_returned": len(records),
    #             "has_more": has_more,
    #             "next_offset_token": next_offset_token
    #         }
            
    #         logger.info(f"✅ Successfully parsed {len(records)} records from XML response")
    #         return result
            
    #     except ET.ParseError as e:
    #         logger.error(f"❌ XML parsing error: {e}")
    #         raise ValueError(f"Failed to parse XML response: {e}")
    #     except Exception as e:
    #         logger.error(f"❌ General parsing error: {e}")
    #         logger.error(f"❌ XML content that failed: {xml_response[:1000]}")
    #         raise ValueError(f"Failed to process XML response: {e}")

    def get_supported_filter_operators(self) -> List[str]:
        """
        Get list of supported filter operators for Boomi DataHub queries
        
        Returns:
            List of supported operator strings
        """
        return [
            "EQUALS",           # Exact match
            "NOT_EQUALS",       # Not equal to
            "CONTAINS",         # Contains substring
            "NOT_CONTAINS",     # Does not contain substring
            "STARTS_WITH",      # Starts with prefix
            "ENDS_WITH",        # Ends with suffix
            "GREATER_THAN",     # Greater than (for numbers/dates)
            "LESS_THAN",        # Less than (for numbers/dates)
            "GREATER_THAN_OR_EQUAL",  # Greater than or equal
            "LESS_THAN_OR_EQUAL",     # Less than or equal
            "IS_NULL",          # Field is null/empty
            "IS_NOT_NULL"       # Field is not null/empty
        ]

    # Utility Methods
    
    def print_model_summary(self, models: List[Dict[str, Any]], title: str = "Models"):
        """
        Print a summary of models
        
        Args:
            models: List of model objects
            title: Title for the summary
        """
        print(f"\n{title} ({len(models)} total):")
        print("-" * 60)
        
        for i, model in enumerate(models, 1):
            model_id = model.get('id', 'N/A')
            model_name = model.get('name', 'N/A')
            model_status = model.get('publicationStatus', 'N/A')
            model_version = model.get('latestVersion', 'N/A')
            is_published = model.get('published', False)
            
            print(f"{i}. {model_name}")
            print(f"   ID: {model_id}")
            print(f"   Status: {model_status} ({'Published' if is_published else 'Draft'})")
            print(f"   Version: {model_version}")
            print()
    
    def export_models_to_json(self, models: List[Dict[str, Any]], filename: str):
        """
        Export models to JSON file
        
        Args:
            models: List of model objects
            filename: Output filename
        """
        try:
            with open(filename, 'w') as f:
                json.dump(models, f, indent=2)
            logger.info(f"Models exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export models: {e}")


def main():
    """
    Main function demonstrating the client usage
    """
    try:
        # Initialize the client
        client = BoomiDataHubClient()
        
        print("Boomi DataHub REST API Client with Fixed XML Parsing")
        print("=" * 60)
        
        # Test the connection first
        print("Testing API connection...")
        test_result = client.test_connection()
        
        if not test_result['success']:
            print(f"❌ Connection test failed!")
            print(f"   URL: {test_result['url']}")
            print(f"   Status Code: {test_result['status_code']}")
            print(f"   Error: {test_result['error']}")
            return 1
        else:
            print("✅ Connection test successful!")
            if test_result.get('has_datahub_credentials'):
                print("🔑 DataHub credentials configured")
            else:
                print("⚠️  No separate DataHub credentials - using API credentials for queries")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        return 1


if __name__ == "__main__":
    exit(main())