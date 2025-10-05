import hashlib
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataQualityValidator:
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.validation_rules = {
            'pubmed': {
                'required_fields': ['pmid', 'title', 'authors', 'abstract'],
                'field_validation': {
                    'pmid': r'^\d+$',
                    'title': r'^.{10,500}$',
                    'authors': r'^.{5,1000}$',
                    'abstract': r'^.{50,5000}$'
                }
            },
            'clinical_trial': {
                'required_fields': ['nct_id', 'title', 'status', 'phase'],
                'field_validation': {
                    'nct_id': r'^NCT\d{8}$',
                    'title': r'^.{10,500}$',
                    'status': r'^(Recruiting|Active|Completed|Terminated|Suspended)$',
                    'phase': r'^(Phase I|Phase II|Phase III|Phase IV|Not specified)$'
                }
            },
            'chembl_compound': {
                'required_fields': ['chembl_id', 'pref_name', 'molecule_type'],
                'field_validation': {
                    'chembl_id': r'^CHEMBL\d+$',
                    'pref_name': r'^.{3,200}$',
                    'molecule_type': r'^(Small molecule|Antibody|Protein|Oligonucleotide|Other)$'
                }
            },
            'drugbank_drug': {
                'required_fields': ['drugbank_id', 'name', 'description'],
                'field_validation': {
                    'drugbank_id': r'^DB\d{5}$',
                    'name': r'^.{3,200}$',
                    'description': r'^.{20,1000}$'
                }
            },
            'uniprot_protein': {
                'required_fields': ['accession', 'protein_name', 'organism'],
                'field_validation': {
                    'accession': r'^[A-Z0-9]{6,10}$',
                    'protein_name': r'^.{5,300}$',
                    'organism': r'^.{5,100}$'
                }
            },
            'kegg_pathway': {
                'required_fields': ['pathway_id', 'name'],
                'field_validation': {
                    'pathway_id': r'^[a-z]{3}\d{5}$',
                    'name': r'^.{5,200}$'
                }
            }
        }
    
    def validate_document(self, document: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """
        Validate a single document against quality rules.
        
        Args:
            document: Document to validate
            doc_type: Type of document (pubmed, clinical_trial, etc.)
            
        Returns:
            Validation result with status and issues
        """
        result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'document_hash': self._generate_document_hash(document)
        }
        
        if doc_type not in self.validation_rules:
            result['issues'].append(f"Unknown document type: {doc_type}")
            result['is_valid'] = False
            return result
        
        rules = self.validation_rules[doc_type]
        
        # Check required fields
        for field in rules['required_fields']:
            if field not in document or not document[field]:
                result['issues'].append(f"Missing required field: {field}")
                result['is_valid'] = False
        
        # Validate field formats
        for field, pattern in rules['field_validation'].items():
            if field in document and document[field]:
                if not re.match(pattern, str(document[field])):
                    result['issues'].append(f"Invalid format for field '{field}': {document[field]}")
                    result['is_valid'] = False
        
        # Check for duplicates
        if result['document_hash'] in self.seen_hashes:
            result['warnings'].append("Duplicate document detected")
        else:
            self.seen_hashes.add(result['document_hash'])
        
        # Additional quality checks
        self._check_data_quality(document, doc_type, result)
        
        return result
    
    def _generate_document_hash(self, document: Dict[str, Any]) -> str:
        """
        Generate a hash for document deduplication.
        """
        # Create a normalized string for hashing
        key_fields = []
        
        if 'pmid' in document:
            key_fields.append(f"pmid:{document['pmid']}")
        elif 'nct_id' in document:
            key_fields.append(f"nct_id:{document['nct_id']}")
        elif 'chembl_id' in document:
            key_fields.append(f"chembl_id:{document['chembl_id']}")
        elif 'drugbank_id' in document:
            key_fields.append(f"drugbank_id:{document['drugbank_id']}")
        elif 'accession' in document:
            key_fields.append(f"accession:{document['accession']}")
        elif 'pathway_id' in document:
            key_fields.append(f"pathway_id:{document['pathway_id']}")
        
        # Add title for additional uniqueness
        if 'title' in document:
            key_fields.append(f"title:{document['title'][:100]}")
        
        hash_string = "|".join(key_fields)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _check_data_quality(self, document: Dict[str, Any], doc_type: str, result: Dict[str, Any]):
        """
        Perform additional data quality checks.
        """
        # Check for suspicious patterns
        if 'title' in document:
            title = document['title']
            
            # Check for excessive capitalization
            if len(re.findall(r'[A-Z]', title)) > len(title) * 0.7:
                result['warnings'].append("Title has excessive capitalization")
            
            # Check for repeated words
            words = title.lower().split()
            if len(words) != len(set(words)):
                result['warnings'].append("Title contains repeated words")
        
        # Check for valid URLs
        url_fields = ['url', 'structure_url', 'image_url', 'fasta_url']
        for field in url_fields:
            if field in document and document[field]:
                if not self._is_valid_url(document[field]):
                    result['warnings'].append(f"Invalid URL in field '{field}': {document[field]}")
        
        # Check for reasonable dates
        date_fields = ['publication_date', 'start_date', 'completion_date', 'first_approval']
        for field in date_fields:
            if field in document and document[field]:
                if not self._is_valid_date(document[field]):
                    result['warnings'].append(f"Invalid date in field '{field}': {document[field]}")
        
        # Check for reasonable numbers
        if 'sequence_length' in document and document['sequence_length']:
            length = document['sequence_length']
            if not isinstance(length, int) or length < 0 or length > 100000:
                result['warnings'].append(f"Unreasonable sequence length: {length}")
        
        if 'max_phase' in document and document['max_phase']:
            phase = document['max_phase']
            if not isinstance(phase, int) or phase < 0 or phase > 4:
                result['warnings'].append(f"Invalid phase number: {phase}")
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid.
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """
        Check if date string is valid.
        """
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            
            return False
        except:
            return False
    
    def validate_batch(self, documents: List[Dict[str, Any]], doc_type: str) -> Dict[str, Any]:
        """
        Validate a batch of documents.
        
        Args:
            documents: List of documents to validate
            doc_type: Type of documents
            
        Returns:
            Batch validation result
        """
        results = {
            'total_documents': len(documents),
            'valid_documents': 0,
            'invalid_documents': 0,
            'duplicate_documents': 0,
            'documents_with_warnings': 0,
            'validation_results': [],
            'summary': {
                'issues': [],
                'warnings': []
            }
        }
        
        for i, document in enumerate(documents):
            validation_result = self.validate_document(document, doc_type)
            results['validation_results'].append(validation_result)
            
            if validation_result['is_valid']:
                results['valid_documents'] += 1
            else:
                results['invalid_documents'] += 1
            
            if validation_result['warnings']:
                results['documents_with_warnings'] += 1
            
            # Collect issues and warnings
            results['summary']['issues'].extend(validation_result['issues'])
            results['summary']['warnings'].extend(validation_result['warnings'])
        
        # Remove duplicates from summary
        results['summary']['issues'] = list(set(results['summary']['issues']))
        results['summary']['warnings'] = list(set(results['summary']['warnings']))
        
        return results
    
    def clean_document(self, document: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """
        Clean and normalize a document.
        
        Args:
            document: Document to clean
            doc_type: Type of document
            
        Returns:
            Cleaned document
        """
        cleaned = document.copy()
        
        # Clean text fields
        text_fields = ['title', 'abstract', 'description', 'protein_name', 'name']
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self._clean_text(cleaned[field])
        
        # Clean author fields
        if 'authors' in cleaned and cleaned['authors']:
            cleaned['authors'] = self._clean_authors(cleaned['authors'])
        
        # Clean date fields
        date_fields = ['publication_date', 'start_date', 'completion_date', 'first_approval']
        for field in date_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self._clean_date(cleaned[field])
        
        # Clean URL fields
        url_fields = ['url', 'structure_url', 'image_url', 'fasta_url']
        for field in url_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self._clean_url(cleaned[field])
        
        # Clean numeric fields
        if 'sequence_length' in cleaned and cleaned['sequence_length']:
            try:
                cleaned['sequence_length'] = int(cleaned['sequence_length'])
            except (ValueError, TypeError):
                cleaned['sequence_length'] = 0
        
        if 'max_phase' in cleaned and cleaned['max_phase']:
            try:
                cleaned['max_phase'] = int(cleaned['max_phase'])
            except (ValueError, TypeError):
                cleaned['max_phase'] = 0
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _clean_authors(self, authors: str) -> str:
        """
        Clean and normalize author string.
        """
        if not authors:
            return ""
        
        # Split by common separators and clean each author
        separators = [';', ',', '|', '\n']
        for sep in separators:
            if sep in authors:
                author_list = [self._clean_text(author) for author in authors.split(sep)]
                return '; '.join([author for author in author_list if author])
        
        return self._clean_text(authors)
    
    def _clean_date(self, date_str: str) -> str:
        """
        Clean and normalize date string.
        """
        if not date_str:
            return ""
        
        # Remove timezone information
        date_str = re.sub(r'[+-]\d{2}:\d{2}$', '', date_str)
        date_str = re.sub(r'Z$', '', date_str)
        
        return date_str.strip()
    
    def _clean_url(self, url: str) -> str:
        """
        Clean and normalize URL.
        """
        if not url:
            return ""
        
        # Remove whitespace
        url = url.strip()
        
        # Ensure protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Get data quality metrics.
        
        Returns:
            Quality metrics
        """
        return {
            'total_documents_processed': len(self.seen_hashes),
            'duplicate_rate': 0,  # Would need to track duplicates separately
            'validation_rules': list(self.validation_rules.keys()),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def reset_duplicate_tracking(self):
        """
        Reset duplicate tracking (useful for testing or periodic cleanup).
        """
        self.seen_hashes.clear()
        logger.info("Duplicate tracking reset")

# Global data quality validator instance
data_quality_validator = DataQualityValidator()
