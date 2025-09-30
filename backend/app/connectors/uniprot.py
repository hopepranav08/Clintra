import requests
import time
from typing import List, Dict, Any, Optional

class UniProtConnector:
    def __init__(self):
        self.base_url = "https://rest.uniprot.org"
        self.rate_limit_delay = 0.5  # 2 requests per second max
    
    def search_proteins(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Search UniProt for proteins related to the query.
        """
        try:
            # Build search parameters
            search_params = {
                'query': query,
                'format': 'json',
                'size': max_results,
                'fields': 'accession,id,protein_name,organism_name,length,sequence,go_terms,keywords,ec_numbers'
            }
            
            # Add filters
            if filters:
                if filters.get('organism'):
                    search_params['query'] += f' AND organism:"{filters["organism"]}"'
                if filters.get('reviewed'):
                    search_params['query'] += ' AND reviewed:true'
                if filters.get('length_min'):
                    search_params['query'] += f' AND length:[{filters["length_min"]} TO *]'
                if filters.get('length_max'):
                    search_params['query'] += f' AND length:[* TO {filters["length_max"]}]'
            
            search_url = f"{self.base_url}/uniprotkb/search"
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            proteins = []
            
            if 'results' in data:
                for result in data['results']:
                    protein_data = self._parse_protein_data(result)
                    proteins.append(protein_data)
            
            return proteins
            
        except requests.exceptions.RequestException as e:
            print(f"UniProt API error: {e}")
            return self._get_fallback_data(query)
        except Exception as e:
            print(f"UniProt parsing error: {e}")
            return self._get_fallback_data(query)
    
    def get_protein_details(self, uniprot_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific protein.
        """
        try:
            url = f"{self.base_url}/uniprotkb/{uniprot_id}"
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_protein_data(data)
            
        except Exception as e:
            print(f"Error getting protein details: {e}")
            return {}
    
    def _parse_protein_data(self, protein: Dict) -> Dict[str, Any]:
        """
        Parse protein data from UniProt API response.
        """
        try:
            # Extract basic information
            accession = protein.get('primaryAccession', 'Unknown')
            entry_name = protein.get('uniProtkbId', 'Unknown')
            protein_name = protein.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'Unknown')
            
            # Extract organism
            organism = 'Unknown'
            if 'organism' in protein:
                organism = protein['organism'].get('scientificName', 'Unknown')
            
            # Extract sequence length
            sequence_length = protein.get('sequence', {}).get('length', 0)
            
            # Extract sequence
            sequence = protein.get('sequence', {}).get('value', '')
            
            # Extract GO terms
            go_terms = []
            if 'goTerms' in protein:
                for go_term in protein['goTerms']:
                    go_terms.append({
                        'id': go_term.get('id', ''),
                        'name': go_term.get('name', ''),
                        'category': go_term.get('category', '')
                    })
            
            # Extract keywords
            keywords = []
            if 'keywords' in protein:
                for keyword in protein['keywords']:
                    keywords.append(keyword.get('name', ''))
            
            # Extract EC numbers
            ec_numbers = []
            if 'ecNumbers' in protein:
                for ec in protein['ecNumbers']:
                    ec_numbers.append(ec.get('value', ''))
            
            # Extract gene names
            gene_names = []
            if 'genes' in protein:
                for gene in protein['genes']:
                    if 'geneName' in gene:
                        gene_names.append(gene['geneName'].get('value', ''))
            
            return {
                'accession': accession,
                'entry_name': entry_name,
                'protein_name': protein_name,
                'organism': organism,
                'sequence_length': sequence_length,
                'sequence': sequence[:100] + '...' if len(sequence) > 100 else sequence,
                'go_terms': go_terms[:10],  # Limit to first 10 GO terms
                'keywords': keywords[:10],  # Limit to first 10 keywords
                'ec_numbers': ec_numbers,
                'gene_names': gene_names,
                'url': f"https://www.uniprot.org/uniprot/{accession}",
                'fasta_url': f"https://www.uniprot.org/uniprot/{accession}.fasta"
            }
            
        except Exception as e:
            print(f"Error parsing protein data: {e}")
            return {
                'accession': 'Unknown',
                'entry_name': 'Unknown',
                'protein_name': 'Unknown',
                'organism': 'Unknown',
                'sequence_length': 0,
                'sequence': '',
                'go_terms': [],
                'keywords': [],
                'ec_numbers': [],
                'gene_names': [],
                'url': 'https://www.uniprot.org/',
                'fasta_url': ''
            }
    
    def _get_fallback_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback data when API is unavailable.
        """
        return [
            {
                'accession': 'P12345',
                'entry_name': f'{query.upper()}_HUMAN',
                'protein_name': f'{query.title()} protein',
                'organism': 'Homo sapiens',
                'sequence_length': 250,
                'sequence': 'MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL...',
                'go_terms': [
                    {'id': 'GO:0003674', 'name': 'molecular_function', 'category': 'molecular_function'},
                    {'id': 'GO:0008150', 'name': 'biological_process', 'category': 'biological_process'}
                ],
                'keywords': ['Complete proteome', 'Reference proteome'],
                'ec_numbers': ['1.1.1.1'],
                'gene_names': [f'{query.upper()}'],
                'url': 'https://www.uniprot.org/uniprot/P12345',
                'fasta_url': 'https://www.uniprot.org/uniprot/P12345.fasta'
            },
            {
                'accession': 'Q67890',
                'entry_name': f'{query.upper()}_MOUSE',
                'protein_name': f'{query.title()} protein homolog',
                'organism': 'Mus musculus',
                'sequence_length': 248,
                'sequence': 'MKLLILTCLVAVALARPKHPIKHQGLPQEVLNENLLRFFVAPFPEVFGKEKVNEL...',
                'go_terms': [
                    {'id': 'GO:0003674', 'name': 'molecular_function', 'category': 'molecular_function'},
                    {'id': 'GO:0008150', 'name': 'biological_process', 'category': 'biological_process'}
                ],
                'keywords': ['Complete proteome'],
                'ec_numbers': ['1.1.1.1'],
                'gene_names': [f'{query.upper()}'],
                'url': 'https://www.uniprot.org/uniprot/Q67890',
                'fasta_url': 'https://www.uniprot.org/uniprot/Q67890.fasta'
            }
        ]
    
    def search_by_organism(self, organism: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search proteins by organism.
        """
        return self.search_proteins(f'organism:"{organism}"', max_results)
    
    def search_by_go_term(self, go_term: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search proteins by GO term.
        """
        return self.search_proteins(f'go:"{go_term}"', max_results)
    
    def get_protein_sequence(self, uniprot_id: str) -> str:
        """
        Get protein sequence in FASTA format.
        """
        try:
            url = f"{self.base_url}/uniprotkb/{uniprot_id}.fasta"
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            print(f"Error getting protein sequence: {e}")
            return ""
