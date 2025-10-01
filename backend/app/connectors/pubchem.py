import requests
import time
from typing import Dict, Any, Optional

class PubChemConnector:
    """
    Connector for PubChem API with real integration.
    """
    def __init__(self):
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.rate_limit_delay = 0.2  # 5 requests per second max
    
    def get_compound_info(self, compound_name: str) -> Dict[str, Any]:
        """
        Fetches real compound information from PubChem.
        """
        try:
            # Search for compound by name first to get CID
            time.sleep(self.rate_limit_delay)
            search_url = f"{self.base_url}/compound/name/{compound_name}/cids/JSON"
            search_response = requests.get(search_url, timeout=10)
            
            if search_response.status_code == 404:
                return self._get_fallback_data(compound_name)
            
            search_response.raise_for_status()
            search_data = search_response.json()
            
            # Get the first CID
            cids = search_data.get("IdentifierList", {}).get("CID", [])
            if not cids:
                return self._get_fallback_data(compound_name)
            
            cid = cids[0]
            
            # Fetch compound properties
            time.sleep(self.rate_limit_delay)
            props_url = f"{self.base_url}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES,IsomericSMILES/JSON"
            props_response = requests.get(props_url, timeout=10)
            props_response.raise_for_status()
            props_data = props_response.json()
            
            if "PropertyTable" not in props_data or "Properties" not in props_data["PropertyTable"]:
                return self._get_fallback_data(compound_name)
            
            properties = props_data["PropertyTable"]["Properties"][0]
            
            # Fetch description
            description = self._get_compound_description(cid)
            
            return {
                "name": compound_name,
                "cid": str(cid),
                "molecular_formula": properties.get("MolecularFormula", "N/A"),
                "molecular_weight": str(properties.get("MolecularWeight", "N/A")),
                "iupac_name": properties.get("IUPACName", "N/A"),
                "canonical_smiles": properties.get("CanonicalSMILES", "N/A"),
                "isomeric_smiles": properties.get("IsomericSMILES", "N/A"),
                "description": description,
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                "download_links": {
                    "sdf": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF",
                    "json": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/JSON",
                    "xml": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/XML",
                    "png_2d": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG",
                    "3d_conformer": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
                },
                "visualization": f"https://pubchem.ncbi.nlm.nih.gov/3d-viewer?cid={cid}",
                "source": "PubChem"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"PubChem API error for {compound_name}: {e}")
            return self._get_fallback_data(compound_name)
        except Exception as e:
            print(f"PubChem parsing error for {compound_name}: {e}")
            return self._get_fallback_data(compound_name)
    
    def _get_compound_description(self, cid: int) -> str:
        """
        Get compound description from PubChem.
        """
        try:
            time.sleep(self.rate_limit_delay)
            desc_url = f"{self.base_url}/compound/cid/{cid}/description/JSON"
            desc_response = requests.get(desc_url, timeout=10)
            
            if desc_response.status_code == 200:
                desc_data = desc_response.json()
                if "InformationList" in desc_data and "Information" in desc_data["InformationList"]:
                    info = desc_data["InformationList"]["Information"]
                    if info and len(info) > 0 and "Description" in info[0]:
                        return info[0]["Description"]
            
            return "Description not available"
        except:
            return "Description not available"
    
    def _get_fallback_data(self, compound_name: str) -> Dict[str, Any]:
        """
        Return fallback data using Aspirin (CID 2244) as example.
        """
        # Use real Aspirin data as fallback
        real_cid = "2244"
        return {
            "name": "Aspirin (Example)",
            "cid": real_cid,
            "molecular_formula": "C9H8O4",
            "molecular_weight": "180.16",
            "iupac_name": "2-acetyloxybenzoic acid",
            "canonical_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "isomeric_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
            "description": "Aspirin is a common pain reliever and anti-inflammatory medication.",
            "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{real_cid}",
            "download_links": {
                "sdf": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/SDF",
                "json": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/JSON",
                "xml": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/XML",
                "png_2d": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/PNG",
                "3d_conformer": f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/SDF?record_type=3d"
            },
            "visualization": f"https://pubchem.ncbi.nlm.nih.gov/3d-viewer?cid={real_cid}",
            "source": "PubChem (Fallback)",
            "note": f"Compound '{compound_name}' not found. Showing example (Aspirin)."
        }

# Backward compatibility
def get_compound_info(compound_name: str):
    """
    Backward compatibility function for existing code.
    """
    connector = PubChemConnector()
    return connector.get_compound_info(compound_name)