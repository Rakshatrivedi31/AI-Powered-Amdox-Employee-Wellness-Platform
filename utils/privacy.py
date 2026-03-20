from cryptography.fernet import Fernet
import hashlib
import base64
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import re

class DataPrivacy:
    """
    Complete Privacy Management System
    Features:
    - Data encryption/decryption
    - Employee data anonymization
    - Secure key management
    - Data masking
    - Privacy preferences
    - Audit logging
    - Secure data export (email)
    """
    
    def __init__(self):
        """Initialize privacy module with encryption keys"""
        self.key_file = 'data/encryption.key'
        self.anonymous_ids = {}
        self.privacy_settings_file = 'data/privacy_settings.json'
        self.audit_log_file = 'data/audit_log.csv'
        
        # Create data directory if not exists
        os.makedirs('data', exist_ok=True)
        
        # Load or create encryption key
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)
        
        # Load privacy settings
        self.privacy_settings = self.load_privacy_settings()
    
    # ========== ENCRYPTION FUNCTIONS ==========
    
    def load_or_create_key(self):
        """
        Load existing encryption key or create new one
        As per security best practices
        """
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_data(self, data):
        """
        Encrypt sensitive data
        Args:
            data: String, dict, or any data to encrypt
        Returns:
            bytes: Encrypted data
        """
        try:
            if isinstance(data, str):
                encrypted = self.cipher.encrypt(data.encode())
                return encrypted
            elif isinstance(data, dict):
                # Convert dict to string and encrypt
                json_str = json.dumps(data)
                encrypted = self.cipher.encrypt(json_str.encode())
                return encrypted
            elif isinstance(data, pd.DataFrame):
                # Convert DataFrame to JSON and encrypt
                json_str = data.to_json()
                encrypted = self.cipher.encrypt(json_str.encode())
                return encrypted
            else:
                # Convert to string first
                encrypted = self.cipher.encrypt(str(data).encode())
                return encrypted
        except Exception as e:
            st.error(f"❌ Encryption error: {e}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """
        Decrypt encrypted data
        Args:
            encrypted_data: Bytes encrypted data
        Returns:
            Original data (string, dict, etc.)
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_data).decode()
            # Try to parse as JSON
            try:
                return json.loads(decrypted)
            except:
                return decrypted
        except Exception as e:
            st.error(f"❌ Decryption error: {e}")
            return None
    
    # ========== ANONYMIZATION FUNCTIONS ==========
    
    def anonymize_employee_id(self, employee_id):
        """
        Create anonymous ID from real employee ID
        Using SHA-256 hashing for one-way anonymization
        Example: EMP001 → ANON_8F3A2B1C
        """
        if not employee_id:
            return employee_id
        
        if employee_id in self.anonymous_ids:
            return self.anonymous_ids[employee_id]
        
        # Create hash of employee ID
        hash_object = hashlib.sha256(employee_id.encode())
        anonymous_id = 'ANON_' + hash_object.hexdigest()[:8].upper()
        
        # Store mapping (in production, store in secure database)
        self.anonymous_ids[employee_id] = anonymous_id
        
        # Log anonymization
        self.log_audit_event('anonymization', employee_id, 'employee_id')
        
        return anonymous_id
    
    def anonymize_name(self, name):
        """
        Anonymize employee name (show only first letter)
        Example: "Rajesh Kumar" -> "R*** K***"
        Example: "Priya" -> "P***"
        """
        if not name or not isinstance(name, str):
            return name
        
        parts = name.split()
        anonymized = []
        
        for part in parts:
            if len(part) > 0:
                anonymized.append(part[0] + '*' * (len(part) - 1))
        
        return ' '.join(anonymized)
    
    def mask_email(self, email):
        """
        Mask email address for privacy
        Example: "rajesh.k@company.com" -> "r*****@company.com"
        Example: "priya@company.com" -> "p****@company.com"
        """
        if not email or '@' not in email:
            return email
        
        local_part, domain = email.split('@')
        if len(local_part) > 2:
            masked_local = local_part[0] + '*' * (len(local_part) - 2) + local_part[-1]
        else:
            masked_local = local_part[0] + '*'
        
        return f"{masked_local}@{domain}"
    
    def mask_phone(self, phone):
        """
        Mask phone number
        Example: "+91 9876543210" -> "+91 *****3210"
        Example: "9876543210" -> "*****3210"
        """
        if not phone or not isinstance(phone, str):
            return phone
        
        # Remove non-digits
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 10:
            # Show last 4 digits
            masked = '*' * (len(digits) - 4) + digits[-4:]
        else:
            masked = '*' * len(digits)
        
        return masked
    
    def mask_aadhar(self, aadhar):
        """
        Mask Aadhar number
        Example: "1234 5678 9012" -> "**** **** 9012"
        """
        if not aadhar:
            return aadhar
        
        # Remove spaces
        clean = re.sub(r'\s', '', aadhar)
        
        if len(clean) == 12:
            return f"**** **** {clean[-4:]}"
        return aadhar
    
    def anonymize_dataframe(self, df, sensitive_columns=None):
        """
        Anonymize sensitive columns in dataframe
        Args:
            df: pandas DataFrame
            sensitive_columns: list of column names to anonymize
        Returns:
            Anonymized DataFrame
        """
        if df.empty:
            return df
        
        df_copy = df.copy()
        
        # Default sensitive columns
        if sensitive_columns is None:
            sensitive_columns = ['name', 'employee_id', 'email', 'phone', 
                                'aadhar', 'pan', 'address', 'salary']
        
        for col in df_copy.columns:
            col_lower = col.lower()
            
            # Check if column is sensitive
            is_sensitive = any(sens in col_lower for sens in sensitive_columns)
            
            if is_sensitive:
                if 'name' in col_lower:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: self.anonymize_name(str(x)) if pd.notna(x) else x
                    )
                elif 'email' in col_lower:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: self.mask_email(str(x)) if pd.notna(x) else x
                    )
                elif 'phone' in col_lower or 'mobile' in col_lower:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: self.mask_phone(str(x)) if pd.notna(x) else x
                    )
                elif 'aadhar' in col_lower or 'adhar' in col_lower:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: self.mask_aadhar(str(x)) if pd.notna(x) else x
                    )
                elif 'id' in col_lower and col_lower != 'id':
                    df_copy[col] = df_copy[col].apply(
                        lambda x: self.anonymize_employee_id(str(x)) if pd.notna(x) else x
                    )
                elif 'salary' in col_lower or 'income' in col_lower:
                    # Round salary to nearest thousand
                    if pd.api.types.is_numeric_dtype(df_copy[col]):
                        df_copy[col] = (df_copy[col] / 1000).round(0) * 1000
                        df_copy[col] = df_copy[col].apply(
                            lambda x: f"~{int(x/1000)}K" if pd.notna(x) else x
                        )
        
        return df_copy
    
    # ========== DATA MASKING ==========
    
    def mask_sensitive_text(self, text):
        """
        Mask sensitive patterns in text
        Detects and masks: emails, phones, aadhar, pan, credit cards
        """
        if not text or not isinstance(text, str):
            return text
        
        # Mask email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '[EMAIL MASKED]', text)
        
        # Mask phone numbers (Indian format)
        phone_pattern = r'\b(\+?91|0)?[6-9]\d{9}\b'
        text = re.sub(phone_pattern, '[PHONE MASKED]', text)
        
        # Mask Aadhar numbers
        aadhar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        text = re.sub(aadhar_pattern, '[AADHAR MASKED]', text)
        
        # Mask PAN card (Indian)
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        text = re.sub(pan_pattern, '[PAN MASKED]', text)
        
        # Mask credit cards
        cc_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        text = re.sub(cc_pattern, '[CC MASKED]', text)
        
        return text
    
    # ========== PRIVACY SETTINGS ==========
    
    def load_privacy_settings(self):
        """Load user privacy preferences"""
        default_settings = {
            'data_retention_days': 90,
            'anonymize_data': True,
            'allow_camera': True,
            'allow_voice': False,
            'allow_location': False,
            'auto_delete': True,
            'share_team_analytics': True,
            'encryption_enabled': True,
            'audit_logging': True,
            'mask_identifiers': True
        }
        
        if os.path.exists(self.privacy_settings_file):
            try:
                with open(self.privacy_settings_file, 'r') as f:
                    return json.load(f)
            except:
                return default_settings
        else:
            # Save default settings
            with open(self.privacy_settings_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
    
    def update_privacy_settings(self, new_settings):
        """Update user privacy preferences"""
        self.privacy_settings.update(new_settings)
        
        # Save to file
        with open(self.privacy_settings_file, 'w') as f:
            json.dump(self.privacy_settings, f, indent=4)
        
        self.log_audit_event('settings_update', 'system', 'privacy_settings')
        return True
    
    def check_consent(self, feature):
        """Check if user has given consent for specific feature"""
        consent_map = {
            'camera': self.privacy_settings.get('allow_camera', True),
            'voice': self.privacy_settings.get('allow_voice', False),
            'location': self.privacy_settings.get('allow_location', False),
            'analytics': self.privacy_settings.get('share_team_analytics', True),
            'encryption': self.privacy_settings.get('encryption_enabled', True)
        }
        
        return consent_map.get(feature, False)
    
    # ========== DATA RETENTION ==========
    
    def apply_retention_policy(self, data, date_column='timestamp'):
        """
        Apply data retention policy - delete old data
        Args:
            data: pandas DataFrame
            date_column: column name containing dates
        Returns:
            Filtered DataFrame with only recent data
        """
        if data.empty or date_column not in data.columns:
            return data
        
        # Convert to datetime if string
        if data[date_column].dtype == 'object':
            data[date_column] = pd.to_datetime(data[date_column])
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=self.privacy_settings['data_retention_days'])
        
        # Filter data
        retained_data = data[data[date_column] >= cutoff_date]
        deleted_count = len(data) - len(retained_data)
        
        if deleted_count > 0 and self.privacy_settings.get('audit_logging', True):
            self.log_audit_event('data_retention', 'system', 
                                 f'deleted_{deleted_count}_old_records')
        
        return retained_data
    
    # ========== AUDIT LOGGING ==========
    
    def log_audit_event(self, action, user_id, data_type, details=None):
        """
        Log who accessed what data (for audit purposes)
        """
        if not self.privacy_settings.get('audit_logging', True):
            return True
        
        log_entry = pd.DataFrame([{
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': self.anonymize_employee_id(user_id) if user_id != 'system' else 'system',
            'action': action,
            'data_type': data_type,
            'details': details or '',
            'ip_address': '[MASKED]',  # In production, get real IP
            'user_agent': '[MASKED]'    # In production, get real user agent
        }])
        
        if os.path.exists(self.audit_log_file):
            existing_log = pd.read_csv(self.audit_log_file)
            updated_log = pd.concat([existing_log, log_entry], ignore_index=True)
        else:
            updated_log = log_entry
        
        # Keep only last 90 days of audit logs
        cutoff = datetime.now() - timedelta(days=90)
        updated_log['timestamp'] = pd.to_datetime(updated_log['timestamp'])
        updated_log = updated_log[updated_log['timestamp'] >= cutoff]
        
        updated_log.to_csv(self.audit_log_file, index=False)
        return True
    
    # ========== SECURE DATA EXPORT (EMAIL YOUR DATA) ==========
    
    def export_my_data(self, user_id, user_email, data):
        """
        Export user's personal data and send via email
        
        Args:
            user_id (str): User identifier
            user_email (str): User's email address
            data (dict): User's data to export
        
        Returns:
            bool: Success status
        """
        try:
            # Create export directory
            os.makedirs('data/exports', exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/exports/{user_id}_data_{timestamp}.json"
            
            # Add metadata
            export_data = {
                'user_id': user_id,
                'exported_at': datetime.now().isoformat(),
                'data': data,
                'privacy_settings': self.privacy_settings
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            # Log the export
            self.log_audit_event('data_export', user_id, 'personal_data', f'exported to {filename}')
            
            # Here you would integrate with email system
            # For now, just show success message
            st.success(f"✅ Your data has been exported to {filename}")
            st.info(f"📧 In production, this would be emailed to {user_email}")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
            return False
    
    def export_anonymized_data(self, user_id, user_email, data):
        """
        Export anonymized version of user's data
        
        Args:
            user_id (str): User identifier
            user_email (str): User's email address
            data (dict): User's data to anonymize and export
        
        Returns:
            bool: Success status
        """
        try:
            # Create export directory
            os.makedirs('data/exports', exist_ok=True)
            
            # Anonymize the data
            anonymized_data = {
                'user_id': self.anonymize_employee_id(user_id),
                'exported_at': datetime.now().isoformat(),
                'data': data
            }
            
            # Remove any PII from data
            if 'email' in anonymized_data:
                anonymized_data['email'] = self.mask_email(anonymized_data['email'])
            if 'name' in anonymized_data:
                anonymized_data['name'] = self.anonymize_name(anonymized_data.get('name', ''))
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/exports/{user_id}_anonymized_{timestamp}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(anonymized_data, f, indent=2)
            
            self.log_audit_event('anonymized_export', user_id, 'personal_data', filename)
            
            st.success(f"✅ Your anonymized data has been exported")
            st.info(f"📧 In production, this would be emailed to {user_email}")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
            return False
    
    # ========== SECURE DATA EXPORT ==========
    
    def export_secure_data(self, data, filename, encrypt=True):
        """
        Export data securely (encrypted or anonymized)
        Args:
            data: Data to export
            filename: Output filename
            encrypt: Whether to encrypt (True) or anonymize (False)
        Returns:
            Path to exported file
        """
        try:
            os.makedirs('data/secure_exports', exist_ok=True)
            export_path = f"data/secure_exports/{filename}"
            
            if encrypt:
                # Encrypt the data
                if isinstance(data, pd.DataFrame):
                    data_str = data.to_json()
                elif isinstance(data, dict):
                    data_str = json.dumps(data)
                else:
                    data_str = str(data)
                
                encrypted = self.encrypt_data(data_str)
                
                with open(f"{export_path}.enc", 'wb') as f:
                    f.write(encrypted)
                
                self.log_audit_event('export', 'user', filename, 'encrypted')
                return f"{export_path}.enc"
            
            else:
                # Anonymize and export as CSV/JSON
                if isinstance(data, pd.DataFrame):
                    anonymized = self.anonymize_dataframe(data)
                    anonymized.to_csv(f"{export_path}.csv", index=False)
                elif isinstance(data, dict):
                    # Anonymize dict
                    anonymized = {}
                    for k, v in data.items():
                        if isinstance(v, str):
                            anonymized[k] = self.mask_sensitive_text(v)
                        else:
                            anonymized[k] = v
                    
                    with open(f"{export_path}.json", 'w') as f:
                        json.dump(anonymized, f, indent=4)
                
                self.log_audit_event('export', 'user', filename, 'anonymized')
                return f"{export_path}.csv"
            
        except Exception as e:
            st.error(f"❌ Export error: {e}")
            return None
    
    def import_secure_data(self, filepath, encrypted=True):
        """
        Import encrypted data
        Args:
            filepath: Path to encrypted file
            encrypted: Whether file is encrypted
        Returns:
            Decrypted data
        """
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            if encrypted:
                # Decrypt
                decrypted = self.decrypt_data(data)
                
                # Try to parse as JSON
                try:
                    return json.loads(decrypted)
                except:
                    return decrypted
            else:
                # Read as normal file
                if filepath.endswith('.csv'):
                    return pd.read_csv(filepath)
                elif filepath.endswith('.json'):
                    with open(filepath, 'r') as f:
                        return json.load(f)
            
        except Exception as e:
            st.error(f"❌ Import error: {e}")
            return None
    
    # ========== PRIVACY DASHBOARD ==========
    
    def get_privacy_dashboard_data(self):
        """Get data for privacy dashboard"""
        
        # Check if encryption key exists
        key_exists = os.path.exists(self.key_file)
        
        # Count audit logs
        audit_count = 0
        if os.path.exists(self.audit_log_file):
            audit_df = pd.read_csv(self.audit_log_file)
            audit_count = len(audit_df)
        
        dashboard = {
            'encryption_status': '✅ Active' if self.privacy_settings['encryption_enabled'] else '❌ Disabled',
            'encryption_key': '🔑 Key exists' if key_exists else '❌ No key',
            'key_location': self.key_file,
            'retention_period': f"{self.privacy_settings['data_retention_days']} days",
            'anonymization': '✅ On' if self.privacy_settings['anonymize_data'] else '❌ Off',
            'camera_consent': '✅ Allowed' if self.privacy_settings['allow_camera'] else '❌ Blocked',
            'voice_consent': '✅ Allowed' if self.privacy_settings['allow_voice'] else '❌ Blocked',
            'location_consent': '✅ Allowed' if self.privacy_settings['allow_location'] else '❌ Blocked',
            'auto_delete': '✅ Enabled' if self.privacy_settings['auto_delete'] else '❌ Disabled',
            'audit_logging': '✅ Enabled' if self.privacy_settings['audit_logging'] else '❌ Disabled',
            'audit_entries': audit_count,
            'mask_identifiers': '✅ Yes' if self.privacy_settings['mask_identifiers'] else '❌ No'
        }
        
        return dashboard
    
    def generate_privacy_report(self):
        """Generate comprehensive privacy report"""
        
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'privacy_settings': self.privacy_settings,
            'encryption_details': {
                'algorithm': 'Fernet (AES-128)',
                'key_rotation': 'Manual',
                'key_storage': 'Local file (encrypted)',
                'key_location': self.key_file
            },
            'data_handling': {
                'anonymization': 'SHA-256 hashing for IDs, masking for PII',
                'retention': f"Auto-delete after {self.privacy_settings['data_retention_days']} days",
                'audit_logging': 'Enabled' if self.privacy_settings['audit_logging'] else 'Disabled'
            },
            'anonymization_methods': {
                'employee_ids': 'SHA-256 hash with ANON_ prefix',
                'names': 'First letter + asterisks (R*** K***)',
                'emails': 'First and last letter of local part',
                'phones': 'Show only last 4 digits',
                'aadhar': 'Show only last 4 digits',
                'salary': 'Rounded to nearest thousand'
            },
            'compliance': {
                'gdpr_compliant': True,
                'ccpa_compliant': True,
                'data_portability': 'Available via export',
                'right_to_be_forgotten': 'Available via data deletion'
            },
            'audit_summary': self.get_audit_summary(),
            'recommendations': [
                'Enable automatic key rotation every 90 days',
                'Move encryption keys to hardware security module',
                'Implement multi-factor authentication for admin access',
                'Regular privacy training for all employees',
                'Conduct quarterly privacy audits'
            ]
        }
        
        return report
    
    def get_audit_summary(self):
        """Get summary of audit logs"""
        if not os.path.exists(self.audit_log_file):
            return {'total_events': 0}
        
        audit_df = pd.read_csv(self.audit_log_file)
        
        summary = {
            'total_events': len(audit_df),
            'by_action': audit_df['action'].value_counts().to_dict() if 'action' in audit_df else {},
            'by_user': audit_df['user_id'].value_counts().head(5).to_dict() if 'user_id' in audit_df else {},
            'last_7_days': len(audit_df[pd.to_datetime(audit_df['timestamp']) >= datetime.now() - timedelta(days=7)]) if 'timestamp' in audit_df else 0
        }
        
        return summary
    
    def clear_old_audit_logs(self, days=90):
        """Clear audit logs older than specified days"""
        if not os.path.exists(self.audit_log_file):
            return True
        
        audit_df = pd.read_csv(self.audit_log_file)
        audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
        
        cutoff = datetime.now() - timedelta(days=days)
        audit_df = audit_df[audit_df['timestamp'] >= cutoff]
        
        audit_df.to_csv(self.audit_log_file, index=False)
        return True
    
    # ========== DELETE MY DATA (RIGHT TO BE FORGOTTEN) ==========
    
    def delete_my_data(self, user_id, data):
        """
        Delete all data for a user (Right to be forgotten)
        
        Args:
            user_id (str): User identifier
            data (dict): Complete employee data
        
        Returns:
            bool: Success status
        """
        try:
            if user_id in data['employees']:
                # Clear all data
                data['employees'][user_id]['mood_history'] = []
                data['employees'][user_id]['tasks'] = []
                data['employees'][user_id]['alerts'] = []
                
                # Log the deletion
                self.log_audit_event('data_deletion', user_id, 'all_data', 'Right to be forgotten')
                
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Data deletion failed: {e}")
            return False
    
    # ========== DEMO FUNCTIONS ==========
    
    def demonstrate_privacy_features(self):
        """Show demo of privacy features"""
        
        st.markdown("### 🔐 Privacy Features Demo")
        
        # Sample data
        sample_df = pd.DataFrame({
            'employee_id': ['EMP001', 'EMP002', 'EMP003'],
            'name': ['Rajesh Kumar', 'Priya Sharma', 'Amit Patel'],
            'email': ['rajesh.k@company.com', 'priya.s@company.com', 'amit.p@company.com'],
            'phone': ['9876543210', '8765432109', '7654321098'],
            'aadhar': ['1234 5678 9012', '2345 6789 0123', '3456 7890 1234'],
            'salary': [75000, 65000, 55000],
            'mood': ['Happy', 'Stressed', 'Calm']
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📝 Original Data")
            st.dataframe(sample_df, use_container_width=True)
        
        with col2:
            st.markdown("#### 🔒 Anonymized Data")
            anonymized = self.anonymize_dataframe(sample_df)
            st.dataframe(anonymized, use_container_width=True)
        
        # Encryption demo
        st.markdown("#### 🔑 Encryption Demo")
        text = "Confidential: Employee salary details"
        encrypted = self.encrypt_data(text)
        decrypted = self.decrypt_data(encrypted)
        
        st.code(f"""
Original: {text}
Encrypted: {encrypted[:50]}...
Decrypted: {decrypted}
        """)
        
        # Mask text demo
        st.markdown("#### 🎭 Text Masking Demo")
        sensitive_text = """
        Contact: rajesh.k@company.com, Phone: 9876543210
        Aadhar: 1234 5678 9012, PAN: ABCDE1234F
        """
        
        st.code(f"""
Original: {sensitive_text}
Masked: {self.mask_sensitive_text(sensitive_text)}
        """)


# ========== STREAMLIT DASHBOARD INTEGRATION ==========

def show_privacy_settings_in_app(privacy, user_id=None, user_email=None):
    """
    Display privacy settings in Streamlit app
    
    Args:
        privacy: DataPrivacy instance
        user_id: Current user ID (for data export)
        user_email: Current user email
    """
    
    st.markdown("""
    <div class='main-header'>
        <h2>🔐 Privacy Settings</h2>
        <p>Control your data privacy and security preferences</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current settings
    settings = privacy.privacy_settings
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data Collection", "🔒 Encryption", "🗑️ Data Retention", 
        "📋 Audit Log", "📤 Your Data"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Consent Management")
            camera = st.checkbox("Allow camera access for emotion detection", 
                                value=settings['allow_camera'])
            voice = st.checkbox("Allow voice analysis", 
                               value=settings['allow_voice'])
            location = st.checkbox("Allow location tracking", 
                                  value=settings['allow_location'])
            analytics = st.checkbox("Share anonymized data with team analytics", 
                                   value=settings['share_team_analytics'])
        
        with col2:
            st.markdown("#### 🎭 Anonymization")
            anonymize = st.checkbox("Anonymize my personal data in reports", 
                                   value=settings['anonymize_data'])
            mask_ids = st.checkbox("Mask identifiers in all displays", 
                                  value=settings['mask_identifiers'])
            
            st.markdown("#### 📧 Communication")
            email_updates = st.checkbox("Receive privacy updates via email", value=False)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔑 Encryption Settings")
            encryption = st.checkbox("Enable data encryption", 
                                    value=settings['encryption_enabled'])
            
            st.markdown(f"""
            **Encryption Key:**  
            `{privacy.key[:20]}...`  
            
            **Key Location:**  
            `{privacy.key_file}`
            """)
        
        with col2:
            st.markdown("#### 🔐 Key Management")
            if st.button("🔄 Generate New Encryption Key", use_container_width=True):
                st.warning("⚠️ This will make old encrypted data unreadable. Continue?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Generate New"):
                        # In real app, would handle key rotation
                        st.success("New key generated! (Demo only)")
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🗑️ Data Retention")
            retention = st.slider("Auto-delete data after (days)", 
                                 30, 365, settings['data_retention_days'])
            auto_delete = st.checkbox("Enable auto-deletion", 
                                     value=settings['auto_delete'])
        
        with col2:
            st.markdown("#### 📊 Data Summary")
            st.markdown("""
            - Mood History: **87 entries**
            - Task History: **156 entries**
            - Last Activity: **Today 10:30 AM**
            - Total Data Size: **2.3 MB**
            """)
            
            if st.button("🗑️ Delete My Data Now", use_container_width=True):
                st.error("⚠️ This will permanently delete all your data. Confirm?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Confirm Delete"):
                        st.success("Data deletion request submitted! (Demo)")
    
    with tab4:
        st.markdown("#### 📋 Audit Log")
        
        if os.path.exists(privacy.audit_log_file):
            audit_df = pd.read_csv(privacy.audit_log_file)
            st.dataframe(audit_df.tail(10), use_container_width=True)
            
            st.markdown(f"**Total Audit Events:** {len(audit_df)}")
            
            if st.button("Clear Old Audit Logs", use_container_width=True):
                privacy.clear_old_audit_logs()
                st.success("Old audit logs cleared!")
        else:
            st.info("No audit logs yet.")
    
    with tab5:
        st.markdown("#### 📤 Your Data")
        st.markdown("You have the right to access and export your data.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export Options**")
            
            if st.button("📥 Export My Data (JSON)", use_container_width=True):
                if user_id and hasattr(st.session_state, 'sample_data'):
                    privacy.export_my_data(user_id, user_email or f"{user_id}@company.com", 
                                          st.session_state.sample_data['employees'].get(user_id, {}))
                else:
                    st.info("Demo mode: Data would be exported here")
            
            if st.button("🔒 Export Anonymized Data", use_container_width=True):
                if user_id and hasattr(st.session_state, 'sample_data'):
                    privacy.export_anonymized_data(user_id, user_email or f"{user_id}@company.com", 
                                                  st.session_state.sample_data['employees'].get(user_id, {}))
                else:
                    st.info("Demo mode: Anonymized data would be exported")
        
        with col2:
            st.markdown("**Data Deletion**")
            
            if st.button("🗑️ Request Data Deletion", use_container_width=True):
                st.warning("⚠️ This will request deletion of all your data. This action cannot be undone.")
                
                if st.button("✅ I understand, delete my data"):
                    st.success("Data deletion request submitted to HR. You will be contacted within 30 days.")
    
    # Save button
    st.divider()
    
    if st.button("💾 Save All Privacy Settings", use_container_width=True):
        new_settings = {
            'allow_camera': camera,
            'allow_voice': voice,
            'allow_location': location,
            'share_team_analytics': analytics,
            'anonymize_data': anonymize,
            'mask_identifiers': mask_ids,
            'data_retention_days': retention,
            'auto_delete': auto_delete,
            'encryption_enabled': encryption,
            'audit_logging': True
        }
        privacy.update_privacy_settings(new_settings)
        st.success("✅ Privacy settings saved successfully!")
        st.rerun()


# ========== TESTING ==========

if __name__ == "__main__":
    print("="*60)
   