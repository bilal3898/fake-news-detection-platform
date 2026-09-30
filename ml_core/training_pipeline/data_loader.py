# ml_core/training_pipeline/data_loader.py
import pandas as pd
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

logger = logging.getLogger(__name__)

class DatasetLoader:
    def __init__(self):
        current_dir = Path(__file__).parent
        self.base_path = current_dir.parent.parent / 'dataset'
        logger.info(f"Dataset base path: {self.base_path.absolute()}")
        
        # Verify path exists
        if not self.base_path.exists():
            logger.error(f"❌ Dataset path does not exist: {self.base_path}")
            # Create directory structure
            self.base_path.mkdir(parents=True, exist_ok=True)
            (self.base_path / 'raw').mkdir(exist_ok=True)
            (self.base_path / 'processed').mkdir(exist_ok=True)
        else:
            logger.info(f"✅ Dataset path verified")
        
    def load_kaggle_dataset(self, dataset_type: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Load Kaggle dataset - fixed and improved version
        """
        try:
            dataset_path = self.base_path / "raw"
            fake_df = None
            true_df = None
            
            if dataset_type == 'fake' or dataset_type is None:
                fake_file = dataset_path / "kaggle_fake.csv"
                if fake_file.exists():
                    logger.info(f"Loading Kaggle fake dataset from: {fake_file}")
                    fake_df = pd.read_csv(fake_file)
                    
                    # Handle different possible column names for text
                    text_column = None
                    for col in ['text', 'title', 'content', 'article']:
                        if col in fake_df.columns:
                            text_column = col
                            break
                    
                    if text_column:
                        fake_df = fake_df.rename(columns={text_column: 'statement'})
                        fake_df['label'] = 1  # Fake news
                        fake_df['source'] = 'kaggle_fake'
                        logger.info(f"✅ Loaded Kaggle fake dataset: {len(fake_df)} rows")
                    else:
                        logger.error(f"❌ No text column found in Kaggle fake dataset. Available columns: {fake_df.columns.tolist()}")
                        fake_df = None
                else:
                    logger.warning(f"⚠️ Kaggle fake file not found: {fake_file}")
            
            if dataset_type == 'true' or dataset_type is None:
                true_file = dataset_path / "kaggle_true.csv"
                if true_file.exists():
                    logger.info(f"Loading Kaggle true dataset from: {true_file}")
                    true_df = pd.read_csv(true_file)
                    
                    # Handle different possible column names for text
                    text_column = None
                    for col in ['text', 'title', 'content', 'article']:
                        if col in true_df.columns:
                            text_column = col
                            break
                    
                    if text_column:
                        true_df = true_df.rename(columns={text_column: 'statement'})
                        true_df['label'] = 0  # Real news
                        true_df['source'] = 'kaggle_true'
                        logger.info(f"✅ Loaded Kaggle true dataset: {len(true_df)} rows")
                    else:
                        logger.error(f"❌ No text column found in Kaggle true dataset. Available columns: {true_df.columns.tolist()}")
                        true_df = None
                else:
                    logger.warning(f"⚠️ Kaggle true file not found: {true_file}")
                    
            # Return based on requested type
            if dataset_type == 'fake':
                return fake_df
            elif dataset_type == 'true':
                return true_df
            else:
                # Return combined dataset
                if fake_df is not None and true_df is not None:
                    combined_df = pd.concat([fake_df, true_df], ignore_index=True)
                    logger.info(f"✅ Combined Kaggle dataset: {len(combined_df)} rows")
                    return combined_df
                elif fake_df is not None:
                    return fake_df
                elif true_df is not None:
                    return true_df
                else:
                    logger.error("❌ No Kaggle datasets found")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Error loading Kaggle dataset: {e}")
            return None
    
    def load_liar_dataset(self, split: str = 'train') -> Optional[pd.DataFrame]:
        """Load LIAR dataset splits with proper labeling - improved version"""
        try:
            split_path = self.base_path / 'raw' / 'liar' / f'{split}.tsv'
            
            logger.info(f"Looking for LIAR dataset at: {split_path}")
            liar_dir = self.base_path / 'raw' / 'liar'
            
            if not liar_dir.exists():
                logger.error(f"❌ LIAR directory not found: {liar_dir}")
                return None
            
            available_files = [f.name for f in liar_dir.iterdir() if f.is_file()]
            logger.info(f"Available files in liar directory: {available_files}")
            
            if not split_path.exists():
                logger.error(f"❌ LIAR split file not found: {split_path}")
                return None
            
            logger.info(f"Loading LIAR dataset: {split_path}")
            
            # Read file to determine column count
            sample_df = pd.read_csv(split_path, sep='\t', header=None, nrows=1)
            actual_columns = len(sample_df.columns)
            
            # Define column schemas based on actual column count
            column_schemas = {
                9: ['id', 'label', 'statement', 'subject', 'speaker', 
                    'job_title', 'state_info', 'party_affiliation', 'context'],
                13: ['id', 'label', 'statement', 'subject', 'speaker', 
                     'job_title', 'state_info', 'party_affiliation', 
                     'barely_true_counts', 'false_counts', 'half_true_counts', 
                     'mostly_true_counts', 'pants_on_fire_counts'],
                14: ['id', 'label', 'statement', 'subject', 'speaker', 
                     'job_title', 'state_info', 'party_affiliation', 
                     'barely_true_counts', 'false_counts', 'half_true_counts', 
                     'mostly_true_counts', 'pants_on_fire_counts', 'context']
            }
            
            if actual_columns in column_schemas:
                columns = column_schemas[actual_columns]
                logger.info(f"Using column schema for {actual_columns} columns")
            else:
                columns = [f'col_{i}' for i in range(actual_columns)]
                logger.warning(f"Using generic column names for {actual_columns} columns")
            
            # Read full dataset with proper columns
            df = pd.read_csv(split_path, sep='\t', header=None, names=columns)
            
            # Map LIAR labels to binary (fake=1, real=0)
            label_mapping = {
                'pants-fire': 1,    # Clearly fake
                'false': 1,         # Fake
                'barely-true': 1,   # Mostly fake
                'half-true': 0,     # Partially true
                'mostly-true': 0,   # Mostly true
                'true': 0           # True
            }
            
            # Convert label column to string and apply mapping
            df['label'] = df['label'].astype(str).str.strip().str.lower()
            df['binary_label'] = df['label'].map(label_mapping)
            
            # Handle any unmapped labels
            if df['binary_label'].isna().any():
                unmapped_labels = df[df['binary_label'].isna()]['label'].unique()
                logger.warning(f"Unmapped labels found: {unmapped_labels}")
                # Map numeric labels if present
                numeric_mapping = {str(i): 1 if i >= 3 else 0 for i in range(1, 7)}
                for label in unmapped_labels:
                    if label in numeric_mapping:
                        df.loc[df['label'] == label, 'binary_label'] = numeric_mapping[label]
                
                # Fill remaining with default (fake)
                df['binary_label'] = df['binary_label'].fillna(1)
            
            df['source'] = f'liar_{split}'
            
            logger.info(f"✅ LIAR {split} dataset loaded: {len(df)} statements")
            logger.info(f"Original label distribution: {df['label'].value_counts().to_dict()}")
            logger.info(f"Binary label distribution: {df['binary_label'].value_counts().to_dict()}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading LIAR dataset: {e}")
            return None
    
    def load_combined_dataset(self, use_liar: bool = True, use_kaggle: bool = True) -> Optional[pd.DataFrame]:
        """Load and combine multiple datasets for better training - FIXED"""
        datasets = []
        
        if use_kaggle:
            kaggle_data = self.load_kaggle_dataset()
            if kaggle_data is not None:
                # Ensure we have the required columns
                required_cols = []
                if 'statement' in kaggle_data.columns:
                    required_cols.append('statement')
                elif 'text' in kaggle_data.columns:
                    kaggle_data = kaggle_data.rename(columns={'text': 'statement'})
                    required_cols.append('statement')
                else:
                    logger.warning("❌ Kaggle data missing text/statement column")
                    kaggle_data = None
                
                if kaggle_data is not None:
                    if 'label' in kaggle_data.columns:
                        required_cols.extend(['label', 'source'])
                    else:
                        logger.warning("❌ Kaggle data missing label column")
                        kaggle_data = None
                
                if kaggle_data is not None:
                    kaggle_data = kaggle_data[required_cols]
                    datasets.append(kaggle_data)
                    logger.info(f"✅ Added Kaggle data: {len(kaggle_data)} rows")
        
        if use_liar:
            # Load all LIAR splits
            for split in ['train', 'test', 'valid']:
                liar_data = self.load_liar_dataset(split)
                if liar_data is not None:
                    # Use statement and binary_label
                    if 'statement' in liar_data.columns and 'binary_label' in liar_data.columns:
                        liar_data = liar_data[['statement', 'binary_label', 'source']]
                        liar_data = liar_data.rename(columns={'binary_label': 'label'})
                        datasets.append(liar_data)
                        logger.info(f"✅ Added LIAR {split} data: {len(liar_data)} rows")
                    else:
                        logger.warning(f"❌ LIAR {split} data missing required columns")
                        logger.warning(f"Available columns: {liar_data.columns.tolist()}")
    
        if not datasets:
            logger.error("❌ No datasets could be loaded")
            return None
        
        # Combine all datasets
        combined_df = pd.concat(datasets, ignore_index=True)
        
        # Clean the combined dataset
        initial_count = len(combined_df)
        
        # Remove duplicates based on statement
        combined_df = combined_df.drop_duplicates(subset=['statement'])
        
        # Remove empty statements
        combined_df = combined_df[combined_df['statement'].notna()]
        combined_df = combined_df[combined_df['statement'].str.strip().str.len() > 0]
        
        # Ensure label is integer
        combined_df['label'] = pd.to_numeric(combined_df['label'], errors='coerce').fillna(1).astype(int)
        
        final_count = len(combined_df)
        logger.info(f"✅ Combined dataset: {initial_count} -> {final_count} statements after cleaning")
        
        if final_count > 0:
            logger.info(f"Final label distribution: {combined_df['label'].value_counts().to_dict()}")
            logger.info(f"Dataset sources: {combined_df['source'].value_counts().to_dict()}")
            
            # Log sample data
            logger.info("Sample data:")
            for i, row in combined_df.head(3).iterrows():
                logger.info(f"  {i+1}. '{row['statement'][:100]}...' -> Label: {row['label']}, Source: {row['source']}")
        else:
            logger.error("❌ Combined dataset is empty after cleaning")
            return None
        
        return combined_df
    
    def load_processed_data(self, filename: str) -> Optional[pd.DataFrame]:
        """Load any processed dataset"""
        try:
            file_path = self.base_path / 'processed' / filename
            
            if not file_path.exists():
                logger.error(f"❌ Processed file not found: {file_path}")
                return None
            
            logger.info(f"Loading processed data: {file_path}")
            
            # Handle different file formats
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            elif filename.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                logger.error(f"Unsupported file format: {filename}")
                return None
            
            logger.info(f"✅ Processed data loaded: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading processed data: {e}")
            return None
    
    def save_processed_data(self, df: pd.DataFrame, filename: str) -> bool:
        """Save processed dataset"""
        try:
            file_path = self.base_path / 'processed' / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if filename.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif filename.endswith('.parquet'):
                df.to_parquet(file_path, index=False)
            elif filename.endswith('.json'):
                df.to_json(file_path, orient='records', indent=2)
            else:
                logger.error(f"Unsupported file format: {filename}")
                return False
            
            logger.info(f"✅ Processed data saved: {file_path} ({len(df)} rows)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving processed data: {e}")
            return False
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get comprehensive information about available datasets"""
        info = {
            'available_datasets': {},
            'file_paths': {},
            'status': 'initialized'
        }
        
        # Check Kaggle datasets
        kaggle_fake_path = self.base_path / 'raw' / "kaggle_fake.csv"
        kaggle_true_path = self.base_path / 'raw' / "kaggle_true.csv"
        
        info['file_paths']['kaggle_fake'] = {
            'path': str(kaggle_fake_path),
            'exists': kaggle_fake_path.exists(),
            'size': kaggle_fake_path.stat().st_size if kaggle_fake_path.exists() else 0
        }
        
        info['file_paths']['kaggle_true'] = {
            'path': str(kaggle_true_path),
            'exists': kaggle_true_path.exists(),
            'size': kaggle_true_path.stat().st_size if kaggle_true_path.exists() else 0
        }
        
        # Check LIAR datasets
        liar_splits = {}
        for split in ['train', 'test', 'valid']:
            split_path = self.base_path / 'raw' / 'liar' / f'{split}.tsv'
            liar_splits[split] = {
                'path': str(split_path),
                'exists': split_path.exists(),
                'size': split_path.stat().st_size if split_path.exists() else 0
            }
        
        info['file_paths']['liar'] = liar_splits
        
        # Check processed datasets
        processed_dir = self.base_path / 'processed'
        if processed_dir.exists():
            processed_files = []
            for f in processed_dir.iterdir():
                if f.is_file():
                    processed_files.append({
                        'name': f.name,
                        'size': f.stat().st_size,
                        'modified': f.stat().st_mtime
                    })
            info['processed_files'] = processed_files
        
        # Summary statistics
        total_files = 0
        existing_files = 0
        for dataset_type, files in info['file_paths'].items():
            if isinstance(files, dict):
                for file_info in files.values():
                    total_files += 1
                    if file_info['exists']:
                        existing_files += 1
        
        info['summary'] = {
            'total_files': total_files,
            'existing_files': existing_files,
            'missing_files': total_files - existing_files,
            'coverage_percentage': (existing_files / total_files * 100) if total_files > 0 else 0
        }
        
        return info
    
    def validate_dataset(self, df: pd.DataFrame, dataset_name: str = "unknown") -> Dict[str, Any]:
        """Validate dataset quality and completeness"""
        if df is None or len(df) == 0:
            return {
                'dataset_name': dataset_name,
                'status': 'empty',
                'error': 'Dataset is empty or None'
            }
        
        validation_result = {
            'dataset_name': dataset_name,
            'status': 'valid',
            'total_rows': len(df),
            'columns': df.columns.tolist(),
            'missing_values': df.isnull().sum().to_dict(),
            'label_distribution': {},
            'text_length_stats': {},
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        # Check for required columns
        required_columns = ['statement', 'label']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_result['status'] = 'invalid'
            validation_result['missing_columns'] = missing_columns
            validation_result['error'] = f"Missing required columns: {missing_columns}"
        
        if 'label' in df.columns:
            validation_result['label_distribution'] = df['label'].value_counts().to_dict()
            validation_result['label_info'] = {
                'min': df['label'].min(),
                'max': df['label'].max(),
                'unique': df['label'].nunique()
            }
        
        if 'statement' in df.columns:
            text_lengths = df['statement'].str.len()
            validation_result['text_length_stats'] = {
                'min': int(text_lengths.min()),
                'max': int(text_lengths.max()),
                'mean': float(text_lengths.mean()),
                'median': float(text_lengths.median())
            }
            
            # Check for empty statements
            empty_statements = (df['statement'].isna()) | (df['statement'].str.strip() == '')
            validation_result['empty_statements'] = int(empty_statements.sum())
        
        logger.info(f"Dataset validation for {dataset_name}:")
        logger.info(f"Status: {validation_result['status']}")
        logger.info(f"Rows: {validation_result['total_rows']}")
        if 'label_distribution' in validation_result:
            logger.info(f"Label distribution: {validation_result['label_distribution']}")
        
        return validation_result
    
    def create_sample_dataset(self, size: int = 1000) -> pd.DataFrame:
        """Create a sample dataset for testing when real data is not available"""
        logger.warning(f"Creating sample dataset with {size} rows (for testing only)")
        
        import random
        import string
        
        samples = []
        for i in range(size):
            # Generate random text
            text_length = random.randint(50, 200)
            text = ''.join(random.choices(string.ascii_letters + string.whitespace, k=text_length))
            
            # Random label (0 for real, 1 for fake)
            label = random.randint(0, 1)
            
            samples.append({
                'statement': f"Sample news text {i}: {text}",
                'label': label,
                'source': 'sample_data'
            })
        
        df = pd.DataFrame(samples)
        logger.info(f"Created sample dataset: {len(df)} rows")
        return df

# Create global instance
dataset_loader = DatasetLoader()

# Utility functions
def load_training_data(use_liar: bool = True, use_kaggle: bool = True, use_sample: bool = False):
    """Utility function to load training data with fallback to sample data"""
    combined_data = dataset_loader.load_combined_dataset(use_liar=use_liar, use_kaggle=use_kaggle)
    
    if combined_data is None and use_sample:
        logger.warning("No real datasets found, falling back to sample data")
        combined_data = dataset_loader.create_sample_dataset(1000)
    
    return combined_data

def get_dataset_stats():
    """Get comprehensive statistics about available datasets"""
    return dataset_loader.get_dataset_info()

def test_data_loader():
    """Enhanced test function for data loader"""
    loader = DatasetLoader()
    
    print("=== Dataset Information ===")
    info = loader.get_dataset_info()
    for dataset, paths in info['file_paths'].items():
        print(f"\n{dataset}:")
        if isinstance(paths, dict):
            for split, details in paths.items():
                status = "✅ EXISTS" if details['exists'] else "❌ MISSING"
                size_mb = details['size'] / (1024 * 1024) if details['size'] > 0 else 0
                print(f"  {split}: {status} ({size_mb:.2f} MB)")
        else:
            status = "✅ EXISTS" if paths['exists'] else "❌ MISSING"
            size_mb = paths['size'] / (1024 * 1024) if paths['size'] > 0 else 0
            print(f"  {status} ({size_mb:.2f} MB)")
    
    print(f"\n📊 Summary: {info['summary']['existing_files']}/{info['summary']['total_files']} files found ({info['summary']['coverage_percentage']:.1f}%)")
    
    print("\n=== Testing LIAR Dataset ===")
    liar_data = loader.load_liar_dataset('train')
    if liar_data is not None:
        validation = loader.validate_dataset(liar_data, "LIAR Train")
        print(f"LIAR dataset loaded: {len(liar_data)} rows")
        print(f"Status: {validation['status']}")
        print(f"Columns: {liar_data.columns.tolist()}")
        print(f"\nLabel distribution:")
        print(liar_data['label'].value_counts().sort_index())
        if 'binary_label' in liar_data.columns:
            print(f"\nBinary label distribution:")
            print(liar_data['binary_label'].value_counts().sort_index())
        
        print(f"\nSample data:")
        print(liar_data[['statement', 'label', 'binary_label']].head(3))
    else:
        print("❌ Failed to load LIAR dataset")
    
    print("\n=== Testing Kaggle Dataset ===")
    kaggle_data = loader.load_kaggle_dataset()
    if kaggle_data is not None:
        validation = loader.validate_dataset(kaggle_data, "Kaggle Combined")
        print(f"Kaggle dataset loaded: {len(kaggle_data)} rows")
        print(f"Status: {validation['status']}")
        print(f"Columns: {kaggle_data.columns.tolist()}")
        print(f"\nLabel distribution:")
        print(kaggle_data['label'].value_counts().sort_index())
    else:
        print("❌ Failed to load Kaggle dataset")
    
    print("\n=== Testing Combined Dataset ===")
    combined_data = loader.load_combined_dataset()
    if combined_data is not None:
        validation = loader.validate_dataset(combined_data, "Combined Dataset")
        print(f"Combined dataset loaded: {len(combined_data)} rows")
        print(f"Status: {validation['status']}")
        print(f"Source distribution:")
        print(combined_data['source'].value_counts())
        print(f"Final label distribution:")
        print(combined_data['label'].value_counts().sort_index())
    else:
        print("❌ Failed to load combined dataset")
        print("Creating sample dataset for testing...")
        sample_data = loader.create_sample_dataset(100)
        print(f"Sample dataset created: {len(sample_data)} rows")

if __name__ == "__main__":
    test_data_loader()