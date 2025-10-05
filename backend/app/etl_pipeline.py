import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .deps import get_db
from .connectors.pubmed import PubMedConnector
from .connectors.trials import ClinicalTrialsConnector
from .connectors.chembl import ChEMBLConnector
from .connectors.drugbank import DrugBankConnector
from .connectors.uniprot import UniProtConnector
from .connectors.kegg import KEGGConnector
from .vector_db import vector_db
from .models import Activity
from .data_quality import data_quality_validator

logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.pubmed_connector = PubMedConnector()
        self.trials_connector = ClinicalTrialsConnector()
        self.chembl_connector = ChEMBLConnector()
        self.drugbank_connector = DrugBankConnector()
        self.uniprot_connector = UniProtConnector()
        self.kegg_connector = KEGGConnector()
        
        # ETL configuration
        self.batch_size = 100
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    async def run_full_pipeline(self, db: Session) -> Dict[str, Any]:
        """
        Run the complete ETL pipeline for all data sources.
        """
        start_time = datetime.utcnow()
        results = {
            'start_time': start_time.isoformat(),
            'sources': {},
            'total_processed': 0,
            'errors': []
        }
        
        try:
            # Run ETL for each data source
            sources = [
                ('pubmed', self._etl_pubmed),
                ('clinical_trials', self._etl_clinical_trials),
                ('chembl', self._etl_chembl),
                ('drugbank', self._etl_drugbank),
                ('uniprot', self._etl_uniprot),
                ('kegg', self._etl_kegg)
            ]
            
            for source_name, etl_function in sources:
                try:
                    logger.info(f"Starting ETL for {source_name}")
                    source_result = await etl_function(db)
                    results['sources'][source_name] = source_result
                    results['total_processed'] += source_result.get('processed', 0)
                    
                except Exception as e:
                    error_msg = f"ETL failed for {source_name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['sources'][source_name] = {'error': str(e), 'processed': 0}
            
            results['end_time'] = datetime.utcnow().isoformat()
            results['duration'] = (datetime.utcnow() - start_time).total_seconds()
            
            # Log pipeline completion
            logger.info(f"ETL pipeline completed. Processed {results['total_processed']} items in {results['duration']:.2f} seconds")
            
            return results
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {str(e)}")
            results['error'] = str(e)
            results['end_time'] = datetime.utcnow().isoformat()
            return results
    
    async def _etl_pubmed(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for PubMed data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different biomedical topics
            search_queries = [
                'cancer treatment',
                'drug discovery',
                'biomarker identification',
                'clinical trials',
                'pharmacology',
                'therapeutics',
                'molecular biology',
                'genetics',
                'immunology',
                'neuroscience'
            ]
            
            for query in search_queries:
                try:
                    # Search PubMed
                    articles = self.pubmed_connector.search_articles(
                        query, 
                        max_results=20,
                        filters={'start_date': '2023/01/01', 'end_date': '2024/12/31'}
                    )
                    
                    # Validate and clean articles
                    if articles:
                        # Validate batch
                        validation_result = data_quality_validator.validate_batch(articles, 'pubmed')
                        
                        # Clean valid articles
                        cleaned_articles = []
                        for i, article in enumerate(articles):
                            if validation_result['validation_results'][i]['is_valid']:
                                cleaned_article = data_quality_validator.clean_document(article, 'pubmed')
                                cleaned_articles.append(cleaned_article)
                        
                        # Add to vector database
                        if cleaned_articles:
                            success = vector_db.add_literature_articles(cleaned_articles)
                            if success:
                                result['processed'] += len(cleaned_articles)
                                logger.info(f"Added {len(cleaned_articles)} validated PubMed articles for query: {query}")
                            else:
                                result['errors'].append(f"Failed to add PubMed articles for query: {query}")
                        
                        # Log validation results
                        if validation_result['invalid_documents'] > 0:
                            logger.warning(f"Filtered out {validation_result['invalid_documents']} invalid PubMed articles for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_pubmed',
                        query=query,
                        result_summary=f"Processed {len(articles)} articles",
                        details={'articles_count': len(articles), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"PubMed ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"PubMed ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _etl_clinical_trials(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for ClinicalTrials.gov data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different conditions
            search_queries = [
                'cancer',
                'diabetes',
                'cardiovascular disease',
                'Alzheimer disease',
                'Parkinson disease',
                'multiple sclerosis',
                'rheumatoid arthritis',
                'depression',
                'hypertension',
                'asthma'
            ]
            
            for query in search_queries:
                try:
                    # Search clinical trials
                    trials_data = self.trials_connector.search_trials(
                        query,
                        max_results=15,
                        filters={'status': 'Recruiting'}
                    )
                    
                    trials = trials_data.get('trials', [])
                    
                    # Validate and clean trials
                    if trials:
                        # Validate batch
                        validation_result = data_quality_validator.validate_batch(trials, 'clinical_trial')
                        
                        # Clean valid trials
                        cleaned_trials = []
                        for i, trial in enumerate(trials):
                            if validation_result['validation_results'][i]['is_valid']:
                                cleaned_trial = data_quality_validator.clean_document(trial, 'clinical_trial')
                                cleaned_trials.append(cleaned_trial)
                        
                        # Add to vector database
                        if cleaned_trials:
                            success = vector_db.add_clinical_trials(cleaned_trials)
                            if success:
                                result['processed'] += len(cleaned_trials)
                                logger.info(f"Added {len(cleaned_trials)} validated clinical trials for query: {query}")
                            else:
                                result['errors'].append(f"Failed to add clinical trials for query: {query}")
                        
                        # Log validation results
                        if validation_result['invalid_documents'] > 0:
                            logger.warning(f"Filtered out {validation_result['invalid_documents']} invalid clinical trials for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_clinical_trials',
                        query=query,
                        result_summary=f"Processed {len(trials)} trials",
                        details={'trials_count': len(trials), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"Clinical trials ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Clinical trials ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _etl_chembl(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for ChEMBL data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different compound types
            search_queries = [
                'antineoplastic',
                'antihypertensive',
                'antidiabetic',
                'antibiotic',
                'antiviral',
                'anti-inflammatory',
                'antidepressant',
                'anticoagulant',
                'bronchodilator',
                'analgesic'
            ]
            
            for query in search_queries:
                try:
                    # Search ChEMBL
                    compounds = self.chembl_connector.search_compounds(
                        query,
                        max_results=10,
                        filters={'molecule_type': 'Small molecule'}
                    )
                    
                    # Add to vector database
                    if compounds:
                        # Convert to documents for vector DB
                        documents = []
                        for compound in compounds:
                            text = f"{compound.get('pref_name', '')} {compound.get('molecule_type', '')} {', '.join(compound.get('indications', []))}"
                            documents.append({
                                'text': text,
                                'metadata': {
                                    'type': 'chembl_compound',
                                    'chembl_id': compound.get('chembl_id', ''),
                                    'pref_name': compound.get('pref_name', ''),
                                    'molecule_type': compound.get('molecule_type', ''),
                                    'max_phase': compound.get('max_phase', 0),
                                    'indications': compound.get('indications', []),
                                    'url': compound.get('url', '')
                                }
                            })
                        
                        success = vector_db.add_documents(documents)
                        if success:
                            result['processed'] += len(compounds)
                            logger.info(f"Added {len(compounds)} ChEMBL compounds for query: {query}")
                        else:
                            result['errors'].append(f"Failed to add ChEMBL compounds for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_chembl',
                        query=query,
                        result_summary=f"Processed {len(compounds)} compounds",
                        details={'compounds_count': len(compounds), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"ChEMBL ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"ChEMBL ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _etl_drugbank(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for DrugBank data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different drug categories
            search_queries = [
                'oncology',
                'cardiology',
                'endocrinology',
                'neurology',
                'psychiatry',
                'immunology',
                'infectious disease',
                'respiratory',
                'gastroenterology',
                'dermatology'
            ]
            
            for query in search_queries:
                try:
                    # Search DrugBank
                    drugs = self.drugbank_connector.search_drugs(
                        query,
                        max_results=10
                    )
                    
                    # Add to vector database
                    if drugs:
                        # Convert to documents for vector DB
                        documents = []
                        for drug in drugs:
                            text = f"{drug.get('name', '')} {drug.get('description', '')} {', '.join(drug.get('indications', []))}"
                            documents.append({
                                'text': text,
                                'metadata': {
                                    'type': 'drugbank_drug',
                                    'drugbank_id': drug.get('drugbank_id', ''),
                                    'name': drug.get('name', ''),
                                    'description': drug.get('description', ''),
                                    'indications': drug.get('indications', []),
                                    'drug_type': drug.get('drug_type', ''),
                                    'approval_status': drug.get('approval_status', ''),
                                    'url': drug.get('url', '')
                                }
                            })
                        
                        success = vector_db.add_documents(documents)
                        if success:
                            result['processed'] += len(drugs)
                            logger.info(f"Added {len(drugs)} DrugBank drugs for query: {query}")
                        else:
                            result['errors'].append(f"Failed to add DrugBank drugs for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_drugbank',
                        query=query,
                        result_summary=f"Processed {len(drugs)} drugs",
                        details={'drugs_count': len(drugs), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"DrugBank ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"DrugBank ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _etl_uniprot(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for UniProt data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different protein types
            search_queries = [
                'kinase',
                'receptor',
                'enzyme',
                'transcription factor',
                'membrane protein',
                'cytokine',
                'hormone',
                'antibody',
                'channel protein',
                'transport protein'
            ]
            
            for query in search_queries:
                try:
                    # Search UniProt
                    proteins = self.uniprot_connector.search_proteins(
                        query,
                        max_results=10,
                        filters={'reviewed': True, 'organism': 'Homo sapiens'}
                    )
                    
                    # Add to vector database
                    if proteins:
                        # Convert to documents for vector DB
                        documents = []
                        for protein in proteins:
                            text = f"{protein.get('protein_name', '')} {protein.get('organism', '')} {', '.join(protein.get('keywords', []))}"
                            documents.append({
                                'text': text,
                                'metadata': {
                                    'type': 'uniprot_protein',
                                    'accession': protein.get('accession', ''),
                                    'entry_name': protein.get('entry_name', ''),
                                    'protein_name': protein.get('protein_name', ''),
                                    'organism': protein.get('organism', ''),
                                    'sequence_length': protein.get('sequence_length', 0),
                                    'keywords': protein.get('keywords', []),
                                    'go_terms': protein.get('go_terms', []),
                                    'url': protein.get('url', '')
                                }
                            })
                        
                        success = vector_db.add_documents(documents)
                        if success:
                            result['processed'] += len(proteins)
                            logger.info(f"Added {len(proteins)} UniProt proteins for query: {query}")
                        else:
                            result['errors'].append(f"Failed to add UniProt proteins for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_uniprot',
                        query=query,
                        result_summary=f"Processed {len(proteins)} proteins",
                        details={'proteins_count': len(proteins), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"UniProt ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"UniProt ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def _etl_kegg(self, db: Session) -> Dict[str, Any]:
        """
        ETL pipeline for KEGG data.
        """
        result = {'processed': 0, 'errors': []}
        
        try:
            # Define search queries for different pathway types
            search_queries = [
                'metabolic pathway',
                'signaling pathway',
                'disease pathway',
                'drug pathway',
                'immune system',
                'nervous system',
                'endocrine system',
                'cardiovascular system',
                'digestive system',
                'respiratory system'
            ]
            
            for query in search_queries:
                try:
                    # Search KEGG
                    pathways = self.kegg_connector.search_pathways(
                        query,
                        max_results=10
                    )
                    
                    # Add to vector database
                    if pathways:
                        # Convert to documents for vector DB
                        documents = []
                        for pathway in pathways:
                            text = f"{pathway.get('name', '')} {query}"
                            documents.append({
                                'text': text,
                                'metadata': {
                                    'type': 'kegg_pathway',
                                    'pathway_id': pathway.get('pathway_id', ''),
                                    'name': pathway.get('name', ''),
                                    'url': pathway.get('url', ''),
                                    'image_url': pathway.get('image_url', '')
                                }
                            })
                        
                        success = vector_db.add_documents(documents)
                        if success:
                            result['processed'] += len(pathways)
                            logger.info(f"Added {len(pathways)} KEGG pathways for query: {query}")
                        else:
                            result['errors'].append(f"Failed to add KEGG pathways for query: {query}")
                    
                    # Add activity log
                    activity = Activity(
                        user_id=1,  # System user
                        activity_type='etl_kegg',
                        query=query,
                        result_summary=f"Processed {len(pathways)} pathways",
                        details={'pathways_count': len(pathways), 'query': query}
                    )
                    db.add(activity)
                    
                except Exception as e:
                    error_msg = f"KEGG ETL error for query '{query}': {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"KEGG ETL failed: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    async def run_incremental_update(self, db: Session, hours_back: int = 24) -> Dict[str, Any]:
        """
        Run incremental ETL update for recent data.
        """
        start_time = datetime.utcnow()
        cutoff_time = start_time - timedelta(hours=hours_back)
        
        result = {
            'start_time': start_time.isoformat(),
            'cutoff_time': cutoff_time.isoformat(),
            'sources': {},
            'total_processed': 0,
            'errors': []
        }
        
        try:
            # Run incremental updates for each source
            # This would typically check for new data since the cutoff time
            # For now, we'll run a smaller batch
            
            logger.info(f"Running incremental ETL update for last {hours_back} hours")
            
            # Run a smaller version of the full pipeline
            sources = [
                ('pubmed', self._etl_pubmed),
                ('clinical_trials', self._etl_clinical_trials)
            ]
            
            for source_name, etl_function in sources:
                try:
                    logger.info(f"Starting incremental ETL for {source_name}")
                    source_result = await etl_function(db)
                    result['sources'][source_name] = source_result
                    result['total_processed'] += source_result.get('processed', 0)
                    
                except Exception as e:
                    error_msg = f"Incremental ETL failed for {source_name}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
                    result['sources'][source_name] = {'error': str(e), 'processed': 0}
            
            result['end_time'] = datetime.utcnow().isoformat()
            result['duration'] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Incremental ETL completed. Processed {result['total_processed']} items in {result['duration']:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Incremental ETL pipeline failed: {str(e)}")
            result['error'] = str(e)
            result['end_time'] = datetime.utcnow().isoformat()
            return result

# Global ETL pipeline instance
etl_pipeline = ETLPipeline()
