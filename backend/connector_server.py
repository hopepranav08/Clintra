#!/usr/bin/env python3
"""
Simple HTTP server for connector microservices.
This implements the Docker MCP Gateway pattern for Clintra connectors.
"""
import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import importlib

class ConnectorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the connector."""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Get connector type from environment
            connector_type = os.getenv('CONNECTOR_TYPE', 'pubmed')
            
            # Import the appropriate connector module
            try:
                connector_module = importlib.import_module(f'app.connectors.{connector_type}')
            except ImportError as e:
                self.send_error(500, f"Could not import connector {connector_type}: {e}")
                return
            
            # Handle different endpoints
            if path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "connector_type": connector_type,
                    "message": f"{connector_type} connector is running"
                }
                self.wfile.write(json.dumps(response).encode())
                
            elif path == '/search' or path == '/query':
                # Handle search/query requests
                query = query_params.get('query', [''])[0]
                if not query:
                    self.send_error(400, "Query parameter is required")
                    return
                
                # Call the appropriate function based on connector type
                if connector_type == 'pubmed':
                    result = connector_module.search_pubmed(query)
                elif connector_type == 'pubchem':
                    result = connector_module.get_compound_info(query)
                elif connector_type == 'pdb':
                    result = connector_module.get_protein_structure(query)
                elif connector_type == 'trials':
                    result = connector_module.search_clinical_trials(query)
                else:
                    self.send_error(400, f"Unknown connector type: {connector_type}")
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "connector_type": connector_type,
                    "query": query,
                    "result": result,
                    "sponsor_tech": "Docker MCP Gateway microservice"
                }
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error(500, f"Internal server error: {e}")
    
    def do_POST(self):
        """Handle POST requests to the connector."""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Get connector type from environment
            connector_type = os.getenv('CONNECTOR_TYPE', 'pubmed')
            
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Import the appropriate connector module
            try:
                connector_module = importlib.import_module(f'app.connectors.{connector_type}')
            except ImportError as e:
                self.send_error(500, f"Could not import connector {connector_type}: {e}")
                return
            
            # Handle different endpoints
            if path == '/search' or path == '/query':
                # Handle search/query requests
                query = request_data.get('query', '')
                if not query:
                    self.send_error(400, "Query is required in request body")
                    return
                
                # Call the appropriate function based on connector type
                if connector_type == 'pubmed':
                    result = connector_module.search_pubmed(query)
                elif connector_type == 'pubchem':
                    result = connector_module.get_compound_info(query)
                elif connector_type == 'pdb':
                    result = connector_module.get_protein_structure(query)
                elif connector_type == 'trials':
                    result = connector_module.search_clinical_trials(query)
                else:
                    self.send_error(400, f"Unknown connector type: {connector_type}")
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "connector_type": connector_type,
                    "query": query,
                    "result": result,
                    "sponsor_tech": "Docker MCP Gateway microservice"
                }
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error(500, f"Internal server error: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass

def run_server():
    """Run the connector server."""
    port = int(os.getenv('PORT', 8001))
    connector_type = os.getenv('CONNECTOR_TYPE', 'pubmed')
    
    print(f"Starting {connector_type} connector server on port {port}")
    
    server = HTTPServer(('0.0.0.0', port), ConnectorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nShutting down {connector_type} connector server")
        server.shutdown()

if __name__ == '__main__':
    run_server()

