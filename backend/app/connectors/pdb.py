import requests
import time
from typing import Dict, Any, Optional

class PDBConnector:
    """
    Connector for RCSB Protein Data Bank API with real integration.
    """
    def __init__(self):
        self.base_url = "https://data.rcsb.org/rest/v1/core"
        self.search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
        self.files_url = "https://files.rcsb.org"
        self.rate_limit_delay = 0.5  # 2 requests per second max
    
    def get_protein_structure(self, pdb_id: str) -> Dict[str, Any]:
        """
        Fetches real protein structure information from RCSB PDB.
        """
        try:
            # Normalize PDB ID (uppercase, 4 characters)
            pdb_id = pdb_id.upper().strip()
            
            if len(pdb_id) != 4:
                return self._get_fallback_data(pdb_id)
            
            # Fetch structure data from RCSB API
            time.sleep(self.rate_limit_delay)
            response = requests.get(
                f"{self.base_url}/entry/{pdb_id}",
                headers={"Accept": "application/json"},
                timeout=10
            )
            
            if response.status_code == 404:
                return self._search_and_fetch(pdb_id)
            
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant information
            struct_info = data.get("struct", {})
            exptl = data.get("exptl", [{}])[0] if data.get("exptl") else {}
            refine = data.get("refine", [{}])[0] if data.get("refine") else {}
            
            return {
                "pdb_id": pdb_id,
                "title": struct_info.get("title", "No title available"),
                "deposition_date": data.get("rcsb_accession_info", {}).get("deposit_date", "Unknown"),
                "method": exptl.get("method", "Unknown"),
                "resolution": refine.get("ls_d_res_high", "N/A"),
                "organism": self._extract_organism(data),
                "authors": self._extract_authors(data),
                "url": f"https://www.rcsb.org/structure/{pdb_id}",
                "download_links": {
                    "pdb": f"{self.files_url}/download/{pdb_id}.pdb",
                    "cif": f"{self.files_url}/download/{pdb_id}.cif",
                    "xml": f"{self.files_url}/download/{pdb_id}.xml",
                    "fasta": f"{self.files_url}/download/{pdb_id}.fasta"
                },
                "visualization": f"https://www.rcsb.org/3d-view/{pdb_id}",
                "source": "RCSB PDB"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"PDB API error for {pdb_id}: {e}")
            return self._get_fallback_data(pdb_id)
        except Exception as e:
            print(f"PDB parsing error for {pdb_id}: {e}")
            return self._get_fallback_data(pdb_id)
    
    def _search_and_fetch(self, query: str) -> Dict[str, Any]:
        """
        Search for protein structures by name and return the first match.
        """
        try:
            search_query = {
                "query": {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "struct.title",
                        "operator": "contains_words",
                        "value": query
                    }
                },
                "return_type": "entry",
                "request_options": {
                    "results_content_type": ["experimental"],
                    "sort": [{"sort_by": "score", "direction": "desc"}],
                    "scoring_strategy": "combined"
                }
            }
            
            time.sleep(self.rate_limit_delay)
            response = requests.post(
                self.search_url,
                json=search_query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            results = response.json()
            
            if results.get("result_set") and len(results["result_set"]) > 0:
                first_result = results["result_set"][0]["identifier"]
                return self.get_protein_structure(first_result)
            else:
                return self._get_fallback_data(query)
                
        except Exception as e:
            print(f"PDB search error: {e}")
            return self._get_fallback_data(query)
    
    def _extract_organism(self, data: Dict) -> str:
        """
        Extract organism information from PDB data.
        """
        try:
            entity_src_gen = data.get("entity_src_gen", [])
            if entity_src_gen:
                return entity_src_gen[0].get("pdbx_gene_src_scientific_name", "Unknown organism")
            
            entity_src_nat = data.get("entity_src_nat", [])
            if entity_src_nat:
                return entity_src_nat[0].get("pdbx_organism_scientific", "Unknown organism")
            
            return "Unknown organism"
        except:
            return "Unknown organism"
    
    def _extract_authors(self, data: Dict) -> str:
        """
        Extract author information from PDB data.
        """
        try:
            audit_author = data.get("audit_author", [])
            if audit_author:
                authors = [author.get("name", "") for author in audit_author[:5]]
                return ", ".join(authors) if authors else "Unknown authors"
            return "Unknown authors"
        except:
            return "Unknown authors"
    
    def _get_fallback_data(self, pdb_id: str) -> Dict[str, Any]:
        """
        Return fallback data when API is unavailable or structure not found.
        """
        # Use 1CRN (Crambin) as a real example
        real_pdb_id = "1CRN"
        return {
            "pdb_id": real_pdb_id,
            "title": "Crambin (Example Protein Structure)",
            "deposition_date": "1981-04-28",
            "method": "X-RAY DIFFRACTION",
            "resolution": "0.945",
            "organism": "Crambe abyssinica (Abyssinian kale)",
            "authors": "Hendrickson, W.A., Teeter, M.M.",
            "url": f"https://www.rcsb.org/structure/{real_pdb_id}",
            "download_links": {
                "pdb": f"https://files.rcsb.org/download/{real_pdb_id}.pdb",
                "cif": f"https://files.rcsb.org/download/{real_pdb_id}.cif",
                "xml": f"https://files.rcsb.org/download/{real_pdb_id}.xml",
                "fasta": f"https://files.rcsb.org/download/{real_pdb_id}.fasta"
            },
            "visualization": f"https://www.rcsb.org/3d-view/{real_pdb_id}",
            "source": "RCSB PDB (Fallback)",
            "note": f"Original query '{pdb_id}' not found. Showing example structure (1CRN - Crambin)."
        }

# Backward compatibility
def get_protein_structure(pdb_id: str):
    """
    Backward compatibility function for existing code.
    """
    connector = PDBConnector()
    return connector.get_protein_structure(pdb_id)