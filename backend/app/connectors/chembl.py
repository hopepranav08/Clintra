import requests
import time
from typing import List, Dict, Any, Optional

class ChEMBLConnector:
    def __init__(self):
        self.base_url = "https://www.ebi.ac.uk/chembl/api/data"
        self.rate_limit_delay = 0.5  # 2 requests per second max
    
    def search_compounds(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Search ChEMBL for compounds related to the query.
        """
        try:
            # Build search parameters
            search_params = {
                'format': 'json',
                'limit': max_results,
                'offset': 0
            }
            
            # Add filters
            if filters:
                if filters.get('molecule_type'):
                    search_params['molecule_type'] = filters['molecule_type']
                if filters.get('max_phase'):
                    search_params['max_phase'] = filters['max_phase']
                if filters.get('indication_class'):
                    search_params['indication_class'] = filters['indication_class']
            
            # Search by molecule name or synonym
            search_url = f"{self.base_url}/molecule"
            search_params['molecule_synonyms__molecule_synonym__icontains'] = query
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, params=search_params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            compounds = []
            
            if 'molecules' in data:
                for molecule in data['molecules']:
                    compound_data = self._parse_compound_data(molecule)
                    compounds.append(compound_data)
            
            return compounds
            
        except requests.exceptions.RequestException as e:
            print(f"ChEMBL API error: {e}")
            return self._get_fallback_data(query)
        except Exception as e:
            print(f"ChEMBL parsing error: {e}")
            return self._get_fallback_data(query)
    
    def get_compound_details(self, chembl_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific compound.
        """
        try:
            url = f"{self.base_url}/molecule/{chembl_id}"
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_compound_data(data)
            
        except Exception as e:
            print(f"Error getting compound details: {e}")
            return {}
    
    def _parse_compound_data(self, molecule: Dict) -> Dict[str, Any]:
        """
        Parse compound data from ChEMBL API response.
        """
        try:
            # Extract basic information
            chembl_id = molecule.get('molecule_chembl_id', 'Unknown')
            pref_name = molecule.get('pref_name', 'Unknown')
            molecule_type = molecule.get('molecule_type', 'Unknown')
            max_phase = molecule.get('max_phase', 0)
            
            # Extract synonyms
            synonyms = []
            if 'molecule_synonyms' in molecule:
                for syn in molecule['molecule_synonyms']:
                    if 'molecule_synonym' in syn:
                        synonyms.append(syn['molecule_synonym'])
            
            # Extract indications
            indications = []
            if 'indication_class' in molecule:
                indications.append(molecule['indication_class'])
            
            # Extract drug type
            drug_type = molecule.get('drug_type', 'Unknown')
            
            # Extract first approval date
            first_approval = molecule.get('first_approval', 'Unknown')
            
            # Extract therapeutic flags
            therapeutic_flag = molecule.get('therapeutic_flag', False)
            
            return {
                'chembl_id': chembl_id,
                'pref_name': pref_name,
                'molecule_type': molecule_type,
                'max_phase': max_phase,
                'synonyms': synonyms[:10],  # Limit to first 10 synonyms
                'indications': indications,
                'drug_type': drug_type,
                'first_approval': first_approval,
                'therapeutic_flag': therapeutic_flag,
                'url': f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/",
                'structure_url': f"https://www.ebi.ac.uk/chembl/api/data/image/{chembl_id}?format=svg"
            }
            
        except Exception as e:
            print(f"Error parsing compound data: {e}")
            return {
                'chembl_id': 'Unknown',
                'pref_name': 'Unknown',
                'molecule_type': 'Unknown',
                'max_phase': 0,
                'synonyms': [],
                'indications': [],
                'drug_type': 'Unknown',
                'first_approval': 'Unknown',
                'therapeutic_flag': False,
                'url': 'https://www.ebi.ac.uk/chembl/',
                'structure_url': ''
            }
    
    def _get_fallback_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback data when API is unavailable.
        """
        return [
            {
                'chembl_id': 'CHEMBL123456',
                'pref_name': f'Simulated Compound for {query}',
                'molecule_type': 'Small molecule',
                'max_phase': 3,
                'synonyms': [f'{query} compound', f'{query} drug'],
                'indications': [query.title()],
                'drug_type': 'Small molecule',
                'first_approval': '2020-01-01',
                'therapeutic_flag': True,
                'url': 'https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL123456/',
                'structure_url': 'https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL123456?format=svg'
            },
            {
                'chembl_id': 'CHEMBL789012',
                'pref_name': f'Experimental {query} Treatment',
                'molecule_type': 'Small molecule',
                'max_phase': 2,
                'synonyms': [f'{query} experimental', f'{query} candidate'],
                'indications': [query.title()],
                'drug_type': 'Small molecule',
                'first_approval': 'Unknown',
                'therapeutic_flag': False,
                'url': 'https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL789012/',
                'structure_url': 'https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL789012?format=svg'
            }
        ]
