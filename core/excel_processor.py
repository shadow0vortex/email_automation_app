"""
Excel Processor - Excel file reading and validation
Handles Excel/CSV file parsing with data validation
"""

import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelProcessor:
    """Process and validate Excel files for email campaigns"""
    
    def __init__(self):
        self.df = None
        self.file_path = None
        self.validation_results = {}
    
    def read_file(self, file_path):
        """Read Excel or CSV file"""
        try:
            self.file_path = file_path
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension in ['xlsx', 'xls']:
                self.df = pd.read_excel(file_path, engine='openpyxl' if file_extension == 'xlsx' else None)
            elif file_extension == 'csv':
                # Try different encodings
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if self.df is None:
                    return False, "Unable to read CSV with supported encodings"
            else:
                return False, f"Unsupported file format: {file_extension}"
            
            # Strip whitespace from column names
            self.df.columns = self.df.columns.str.strip()
            
            logger.info(f"File loaded successfully: {len(self.df)} rows")
            return True, f"Loaded {len(self.df)} rows successfully"
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return False, f"Error reading file: {str(e)}"
    
    def validate_data(self):
        """Validate Excel data for required columns and email format"""
        if self.df is None:
            return False, "No data loaded"
        
        validation_results = {
            'total_rows': len(self.df),
            'valid_emails': 0,
            'invalid_emails': 0,
            'missing_emails': 0,
            'has_name_column': False,
            'has_email_column': False,
            'columns': list(self.df.columns),
            'errors': []
        }
        
        # Check for Email column
        email_col = None
        for col in self.df.columns:
            if col.lower() in ['email', 'e-mail', 'email address', 'mail']:
                email_col = col
                validation_results['has_email_column'] = True
                break
        
        if not email_col:
            validation_results['errors'].append("Missing 'Email' column")
            return False, validation_results
        
        # Check for Name column
        name_col = None
        for col in self.df.columns:
            if col.lower() in ['name', 'full name', 'fullname', 'recipient name']:
                name_col = col
                validation_results['has_name_column'] = True
                break
        
        # Standardize column names
        if email_col != 'Email':
            self.df.rename(columns={email_col: 'Email'}, inplace=True)
        if name_col and name_col != 'Name':
            self.df.rename(columns={name_col: 'Name'}, inplace=True)
        
        # Validate each email
        for idx, row in self.df.iterrows():
            email = row.get('Email', '')
            
            if pd.isna(email) or email == '':
                validation_results['missing_emails'] += 1
            elif self.validate_email(str(email)):
                validation_results['valid_emails'] += 1
            else:
                validation_results['invalid_emails'] += 1
        
        self.validation_results = validation_results
        
        if validation_results['valid_emails'] == 0:
            return False, validation_results
        
        return True, validation_results
    
    @staticmethod
    def validate_email(email):
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_valid_recipients(self):
        """Return DataFrame with only valid email addresses"""
        if self.df is None:
            return None
        
        # Filter rows with valid emails
        valid_df = self.df[self.df['Email'].apply(
            lambda x: self.validate_email(str(x)) if pd.notna(x) else False
        )].copy()
        
        # Remove duplicates based on email
        valid_df = valid_df.drop_duplicates(subset=['Email'], keep='first')
        
        # Fill NaN values with empty strings
        valid_df = valid_df.fillna('')
        
        logger.info(f"Valid recipients: {len(valid_df)}")
        return valid_df
    
    def get_placeholders(self):
        """Extract placeholder names from columns"""
        if self.df is None:
            return []
        
        placeholders = []
        for col in self.df.columns:
            placeholder = f"{{{col.lower()}}}"
            placeholders.append({
                'placeholder': placeholder,
                'column': col
            })
        
        return placeholders
    
    def get_preview_data(self, rows=5):
        """Get preview of first few rows"""
        if self.df is None:
            return None
        
        return self.df.head(rows)
    
    def get_sample_row(self):
        """Get first row for preview"""
        if self.df is None or len(self.df) == 0:
            return None
        
        return self.df.iloc[0]
    
    def export_validation_report(self, output_path):
        """Export validation report to CSV"""
        try:
            if self.df is None:
                return False
            
            # Add validation column
            report_df = self.df.copy()
            report_df['Email_Valid'] = report_df['Email'].apply(
                lambda x: 'Valid' if (pd.notna(x) and self.validate_email(str(x))) else 'Invalid'
            )
            
            report_df.to_csv(output_path, index=False)
            logger.info(f"Validation report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False


class DataCleaner:
    """Clean and normalize data from Excel"""
    
    @staticmethod
    def clean_email(email):
        """Clean email address"""
        if pd.isna(email):
            return ''
        
        email = str(email).strip().lower()
        # Remove any whitespace
        email = ''.join(email.split())
        return email
    
    @staticmethod
    def clean_name(name):
        """Clean person name"""
        if pd.isna(name):
            return ''
        
        name = str(name).strip()
        # Capitalize first letter of each word
        name = ' '.join(word.capitalize() for word in name.split())
        return name
    
    @staticmethod
    def clean_phone(phone):
        """Clean phone number"""
        if pd.isna(phone):
            return ''
        
        phone = str(phone).strip()
        # Remove common formatting characters
        phone = re.sub(r'[^\d+]', '', phone)
        return phone
    
    @staticmethod
    def apply_cleaning(df):
        """Apply cleaning to entire DataFrame"""
        cleaned_df = df.copy()
        
        if 'Email' in cleaned_df.columns:
            cleaned_df['Email'] = cleaned_df['Email'].apply(DataCleaner.clean_email)
        
        if 'Name' in cleaned_df.columns:
            cleaned_df['Name'] = cleaned_df['Name'].apply(DataCleaner.clean_name)
        
        if 'Phone' in cleaned_df.columns:
            cleaned_df['Phone'] = cleaned_df['Phone'].apply(DataCleaner.clean_phone)
        
        return cleaned_df


if __name__ == "__main__":
    # Test Excel processor
    processor = ExcelProcessor()
    
    # Test with sample file
    success, message = processor.read_file("sample_recipients.xlsx")
    print(f"Read file: {success} - {message}")
    
    if success:
        is_valid, results = processor.validate_data()
        print(f"Validation: {is_valid}")
        print(f"Results: {results}")
        
        valid_df = processor.get_valid_recipients()
        print(f"Valid recipients: {len(valid_df)}")
        
        placeholders = processor.get_placeholders()
        print(f"Placeholders: {placeholders}")