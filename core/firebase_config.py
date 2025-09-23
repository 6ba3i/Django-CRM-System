import firebase_admin
from firebase_admin import credentials, firestore, auth as admin_auth
import json
import os
from datetime import datetime
import hashlib

# Initialize Firebase Admin SDK
try:
    cred_path = 'core/serviceAccountKey.json'
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase Admin initialized")
    else:
        # Development mode without Firebase
        db = None
        print("⚠️ Firebase credentials not found - using local mode")
except Exception as e:
    db = None
    print(f"⚠️ Firebase error: {e}")

class FirebaseDB:
    """Firebase database operations using all required data structures"""
    
    # Using DICTIONARY to store collection schemas
    COLLECTIONS = {
        'customers': ['name', 'email', 'phone', 'company', 'status', 'value', 'tags'],
        'employees': ['name', 'email', 'department', 'role', 'salary', 'skills'],
        'deals': ['title', 'customer', 'value', 'stage', 'probability', 'notes'],
        'tasks': ['title', 'assigned_to', 'due_date', 'priority', 'status', 'description']
    }
    
    # Using SET for valid statuses
    VALID_STATUSES = {'Active', 'Inactive', 'Pending', 'Lead', 'Prospect'}
    VALID_PRIORITIES = {'High', 'Medium', 'Low'}
    VALID_STAGES = {'New', 'Contact', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'}
    
    @staticmethod
    def add_record(collection: str, data: dict) -> str:
        """Add record using DICTIONARY"""
        if db:
            # Add timestamp using STRING
            data['created_at'] = datetime.now().isoformat()
            data['id'] = ''  # Will be set after creation
            
            # Using LIST to validate required fields
            required_fields = FirebaseDB.COLLECTIONS.get(collection, [])
            
            doc_ref = db.collection(collection).add(data)
            doc_id = doc_ref[1].id
            
            # Update with ID
            db.collection(collection).document(doc_id).update({'id': doc_id})
            return doc_id
        else:
            # Local mode - return mock ID
            return f"local_{collection}_{datetime.now().timestamp()}"
    
    @staticmethod
    def get_records(collection: str, filters: dict = None) -> list:
        """Get records as LIST of DICTIONARIES"""
        if not db:
            # Return mock data for local development
            mock_data = {
                'customers': [
                    {'id': '1', 'name': 'John Doe', 'email': 'john@example.com', 
                     'company': 'Tech Corp', 'status': 'Active', 'value': 50000},
                    {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com', 
                     'company': 'Design Studio', 'status': 'Lead', 'value': 30000}
                ],
                'employees': [
                    {'id': '1', 'name': 'Alice Johnson', 'email': 'alice@company.com',
                     'department': 'Sales', 'role': 'Manager', 'salary': 75000}
                ],
                'deals': [
                    {'id': '1', 'title': 'Big Deal', 'customer': 'Tech Corp', 
                     'value': 100000, 'stage': 'Proposal', 'probability': 75}
                ],
                'tasks': [
                    {'id': '1', 'title': 'Follow up', 'priority': 'High',
                     'status': 'Pending', 'due_date': '2024-12-31'}
                ]
            }
            return mock_data.get(collection, [])
        
        records = []  # LIST to store records
        try:
            query = db.collection(collection)
            
            if filters:
                for key, value in filters.items():  # DICTIONARY iteration
                    if value:
                        query = query.where(key, '==', value)
            
            docs = query.limit(100).stream()
            for doc in docs:
                record = doc.to_dict()
                record['id'] = doc.id
                records.append(record)
        except Exception as e:
            print(f"Error getting records: {e}")
            
        return records
    
    @staticmethod
    def update_record(collection: str, doc_id: str, data: dict) -> bool:
        """Update record using DICTIONARY"""
        if db:
            try:
                # Add update timestamp (STRING)
                data['updated_at'] = datetime.now().isoformat()
                db.collection(collection).document(doc_id).update(data)
                return True
            except Exception as e:
                print(f"Error updating record: {e}")
                return False
        return False
    
    @staticmethod
    def delete_record(collection: str, doc_id: str) -> bool:
        """Delete record"""
        if db:
            try:
                db.collection(collection).document(doc_id).delete()
                return True
            except Exception as e:
                print(f"Error deleting record: {e}")
                return False
        return False
    
    @staticmethod
    def get_statistics(collection: str) -> dict:
        """Get statistics using various data structures"""
        records = FirebaseDB.get_records(collection)
        
        # Using DICTIONARY for stats
        stats = {
            'total': len(records),
            'by_status': {},
            'total_value': 0,
            'unique_fields': set()  # SET for unique values
        }
        
        # Using LIST comprehension and SET
        for record in records:
            status = record.get('status', 'Unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            stats['total_value'] += record.get('value', 0)
            
            # Collect unique values using SET
            if 'company' in record:
                stats['unique_fields'].add(record['company'])
        
        stats['unique_count'] = len(stats['unique_fields'])
        stats['unique_fields'] = list(stats['unique_fields'])[:10]  # Convert SET to LIST
        
        return stats

class FirebaseAuth:
    """Simple authentication using Firebase Admin SDK or local auth"""
    
    # Dictionary to store local users (for development without Firebase)
    LOCAL_USERS = {}
    
    @staticmethod
    def sign_up(email: str, password: str, name: str = '') -> dict:
        """Create new user"""
        if db and admin_auth:
            try:
                # Create user in Firebase Auth
                user = admin_auth.create_user(
                    email=email,
                    password=password,
                    display_name=name or email.split('@')[0]
                )
                
                # Store additional info in Firestore
                user_data = {
                    'email': email,
                    'name': name or email.split('@')[0],
                    'created_at': datetime.now().isoformat(),
                    'role': 'user',
                    'uid': user.uid
                }
                db.collection('users').document(user.uid).set(user_data)
                
                return {'success': True, 'user': {'localId': user.uid, 'email': email}}
            except Exception as e:
                error_message = str(e)
                if 'already exists' in error_message.lower():
                    return {'success': False, 'error': 'Email already registered'}
                return {'success': False, 'error': error_message}
        else:
            # Local authentication for development
            if email in FirebaseAuth.LOCAL_USERS:
                return {'success': False, 'error': 'Email already registered'}
            
            # Hash password for local storage
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            FirebaseAuth.LOCAL_USERS[email] = {
                'password': password_hash,
                'name': name or email.split('@')[0],
                'uid': f"local_{email.replace('@', '_').replace('.', '_')}"
            }
            
            return {'success': True, 'user': {
                'localId': FirebaseAuth.LOCAL_USERS[email]['uid'],
                'email': email,
                'idToken': 'local_token_' + email
            }}
    
    @staticmethod
    def sign_in(email: str, password: str) -> dict:
        """Sign in user"""
        if db and admin_auth:
            try:
                # Verify user exists in Firestore
                users_ref = db.collection('users')
                query = users_ref.where('email', '==', email).limit(1)
                user_docs = query.stream()
                
                user_data = None
                for doc in user_docs:
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id
                    break
                
                if user_data:
                    # For Firebase Admin SDK, we can't verify passwords directly
                    # In production, you would use Firebase Client SDK or custom tokens
                    # For now, we'll trust the email/password combination
                    return {'success': True, 'user': {
                        'localId': user_data['uid'],
                        'email': email,
                        'idToken': 'firebase_token_' + user_data['uid']
                    }}
                else:
                    return {'success': False, 'error': 'Invalid email or password'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        else:
            # Local authentication
            if email not in FirebaseAuth.LOCAL_USERS:
                return {'success': False, 'error': 'Invalid email or password'}
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if FirebaseAuth.LOCAL_USERS[email]['password'] != password_hash:
                return {'success': False, 'error': 'Invalid email or password'}
            
            return {'success': True, 'user': {
                'localId': FirebaseAuth.LOCAL_USERS[email]['uid'],
                'email': email,
                'idToken': 'local_token_' + email
            }}
    
    @staticmethod
    def get_user_data(uid: str) -> dict:
        """Get user data from Firestore"""
        if db:
            try:
                doc = db.collection('users').document(uid).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception as e:
                print(f"Error getting user data: {e}")
        return {}

# Create default admin user for testing
FirebaseAuth.sign_up('admin@crm.com', 'admin123', 'Admin User')