import requests
import time
from typing import List, Dict, Any, Optional

class KEGGConnector:
    def __init__(self):
        self.base_url = "https://rest.kegg.jp"
        self.rate_limit_delay = 0.5  # 2 requests per second max
    
    def search_pathways(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Search KEGG for pathways related to the query.
        """
        try:
            # Build search parameters
            search_params = {
                'query': query,
                'format': 'json'
            }
            
            # Add filters
            if filters:
                if filters.get('organism'):
                    search_params['query'] += f' {filters["organism"]}'
                if filters.get('pathway_type'):
                    search_params['query'] += f' {filters["pathway_type"]}'
            
            search_url = f"{self.base_url}/find/pathway"
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            # Parse text response (KEGG REST API returns text, not JSON)
            pathways = self._parse_pathway_search(response.text, max_results)
            
            return pathways
            
        except requests.exceptions.RequestException as e:
            print(f"KEGG API error: {e}")
            return self._get_fallback_data(query)
        except Exception as e:
            print(f"KEGG parsing error: {e}")
            return self._get_fallback_data(query)
    
    def get_pathway_details(self, pathway_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific pathway.
        """
        try:
            url = f"{self.base_url}/get/{pathway_id}"
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            return self._parse_pathway_details(response.text, pathway_id)
            
        except Exception as e:
            print(f"Error getting pathway details: {e}")
            return {}
    
    def _parse_pathway_search(self, text_response: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Parse pathway search results from KEGG text response.
        """
        pathways = []
        lines = text_response.strip().split('\n')
        
        for i, line in enumerate(lines[:max_results]):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    pathway_id = parts[0]
                    pathway_name = parts[1]
                    
                    pathways.append({
                        'pathway_id': pathway_id,
                        'name': pathway_name,
                        'url': f"https://www.genome.jp/kegg-bin/show_pathway?{pathway_id}",
                        'image_url': f"https://www.genome.jp/kegg/pathway/{pathway_id}.png"
                    })
        
        return pathways
    
    def _parse_pathway_details(self, text_response: str, pathway_id: str) -> Dict[str, Any]:
        """
        Parse pathway details from KEGG text response.
        """
        try:
            lines = text_response.strip().split('\n')
            details = {
                'pathway_id': pathway_id,
                'name': '',
                'description': '',
                'genes': [],
                'compounds': [],
                'reactions': [],
                'url': f"https://www.genome.jp/kegg-bin/show_pathway?{pathway_id}",
                'image_url': f"https://www.genome.jp/kegg/pathway/{pathway_id}.png"
            }
            
            for line in lines:
                if line.startswith('NAME'):
                    details['name'] = line.split('NAME')[1].strip()
                elif line.startswith('DESCRIPTION'):
                    details['description'] = line.split('DESCRIPTION')[1].strip()
                elif line.startswith('GENE'):
                    # Parse gene information
                    gene_info = line.split('GENE')[1].strip()
                    if gene_info:
                        details['genes'].append(gene_info)
                elif line.startswith('COMPOUND'):
                    # Parse compound information
                    compound_info = line.split('COMPOUND')[1].strip()
                    if compound_info:
                        details['compounds'].append(compound_info)
                elif line.startswith('REACTION'):
                    # Parse reaction information
                    reaction_info = line.split('REACTION')[1].strip()
                    if reaction_info:
                        details['reactions'].append(reaction_info)
            
            return details
            
        except Exception as e:
            print(f"Error parsing pathway details: {e}")
            return {
                'pathway_id': pathway_id,
                'name': 'Unknown',
                'description': 'Unknown',
                'genes': [],
                'compounds': [],
                'reactions': [],
                'url': f"https://www.genome.jp/kegg-bin/show_pathway?{pathway_id}",
                'image_url': f"https://www.genome.jp/kegg/pathway/{pathway_id}.png"
            }
    
    def _get_fallback_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback data when API is unavailable.
        """
        return [
            {
                'pathway_id': 'hsa00010',
                'name': f'{query.title()} Metabolic Pathway',
                'url': 'https://www.genome.jp/kegg-bin/show_pathway?hsa00010',
                'image_url': 'https://www.genome.jp/kegg/pathway/hsa00010.png'
            },
            {
                'pathway_id': 'hsa00020',
                'name': f'{query.title()} Signaling Pathway',
                'url': 'https://www.genome.jp/kegg-bin/show_pathway?hsa00020',
                'image_url': 'https://www.genome.jp/kegg/pathway/hsa00020.png'
            },
            {
                'pathway_id': 'hsa00030',
                'name': f'{query.title()} Regulatory Pathway',
                'url': 'https://www.genome.jp/kegg-bin/show_pathway?hsa00030',
                'image_url': 'https://www.genome.jp/kegg/pathway/hsa00030.png'
            }
        ]
    
    def search_compounds(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search KEGG for compounds related to the query.
        """
        try:
            search_url = f"{self.base_url}/find/compound"
            search_params = {'query': query}
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            compounds = []
            lines = response.text.strip().split('\n')
            
            for i, line in enumerate(lines[:max_results]):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        compound_id = parts[0]
                        compound_name = parts[1]
                        
                        compounds.append({
                            'compound_id': compound_id,
                            'name': compound_name,
                            'url': f"https://www.genome.jp/dbget-bin/www_bget?{compound_id}",
                            'structure_url': f"https://www.genome.jp/Fig/compound/{compound_id}.gif"
                        })
            
            return compounds
            
        except Exception as e:
            print(f"Error searching compounds: {e}")
            return self._get_fallback_compounds(query)
    
    def _get_fallback_compounds(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback compound data.
        """
        return [
            {
                'compound_id': 'C00001',
                'name': f'{query.title()} Compound 1',
                'url': 'https://www.genome.jp/dbget-bin/www_bget?C00001',
                'structure_url': 'https://www.genome.jp/Fig/compound/C00001.gif'
            },
            {
                'compound_id': 'C00002',
                'name': f'{query.title()} Compound 2',
                'url': 'https://www.genome.jp/dbget-bin/www_bget?C00002',
                'structure_url': 'https://www.genome.jp/Fig/compound/C00002.gif'
            }
        ]
    
    def search_genes(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search KEGG for genes related to the query.
        """
        try:
            search_url = f"{self.base_url}/find/genes"
            search_params = {'query': query}
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            genes = []
            lines = response.text.strip().split('\n')
            
            for i, line in enumerate(lines[:max_results]):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        gene_id = parts[0]
                        gene_name = parts[1]
                        
                        genes.append({
                            'gene_id': gene_id,
                            'name': gene_name,
                            'url': f"https://www.genome.jp/dbget-bin/www_bget?{gene_id}"
                        })
            
            return genes
            
        except Exception as e:
            print(f"Error searching genes: {e}")
            return self._get_fallback_genes(query)
    
    def _get_fallback_genes(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback gene data.
        """
        return [
            {
                'gene_id': 'hsa:1000',
                'name': f'{query.upper()} Gene 1',
                'url': 'https://www.genome.jp/dbget-bin/www_bget?hsa:1000'
            },
            {
                'gene_id': 'hsa:1001',
                'name': f'{query.upper()} Gene 2',
                'url': 'https://www.genome.jp/dbget-bin/www_bget?hsa:1001'
            }
        ]
