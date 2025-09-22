# firebase_config.py
import os
import logging
from decouple import config
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Firebase only if credentials exist
try:
    firebase_cred_path = config('FIREBASE_CREDENTIALS_PATH', default='core/serviceAccountkey.json')
    if os.path.exists(firebase_cred_path):
        import firebase_admin
        from firebase_admin import credentials, firestore, auth
        
        # Check if already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': config('FIREBASE_DATABASE_URL', default='')
            })
        
        db = firestore.client()
        FIREBASE_ENABLED = True
        logger.info("Firebase initialized successfully")
    else:
        FIREBASE_ENABLED = False
        db = None
        logger.warning(f"Firebase credentials not found at {firebase_cred_path}. Firebase features disabled.")
except Exception as e:
    FIREBASE_ENABLED = False
    db = None
    logger.warning(f"Firebase initialization failed: {e}. Firebase features disabled.")

class FirebaseManager:
    
    @staticmethod
    def is_enabled():
        return FIREBASE_ENABLED and db is not None
    
    @staticmethod
    def initialize_collections():
        """Initialize Firebase collections with proper structure"""
        if not FirebaseManager.is_enabled():
            return False
            
        try:
            # Initialize customers collection
            customers_ref = db.collection('customers')
            if not customers_ref.limit(1).get():
                customers_ref.document('_init').set({
                    'initialized': True,
                    'created_at': datetime.now(),
                    'version': '1.0'
                })
            
            # Initialize deals collection
            deals_ref = db.collection('deals')
            if not deals_ref.limit(1).get():
                deals_ref.document('_init').set({
                    'initialized': True,
                    'created_at': datetime.now(),
                    'version': '1.0'
                })
            
            # Initialize interactions collection
            interactions_ref = db.collection('interactions')
            if not interactions_ref.limit(1).get():
                interactions_ref.document('_init').set({
                    'initialized': True,
                    'created_at': datetime.now(),
                    'version': '1.0'
                })
            
            logger.info("Firebase collections initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Firebase collections: {e}")
            return False
    
    @staticmethod
    def create_customer(data: dict) -> str:
        if not FirebaseManager.is_enabled():
            logger.warning("Firebase is not enabled. Using local ID.")
            import uuid
            return str(uuid.uuid4())
        
        try:
            # Add server timestamp
            data['created_at'] = firestore.SERVER_TIMESTAMP
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = db.collection('customers').add(data)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error creating customer in Firebase: {e}")
            import uuid
            return str(uuid.uuid4())
    
    @staticmethod
    def get_customers(filters: dict = None, limit: int = None) -> list:
        if not FirebaseManager.is_enabled():
            return []
        
        try:
            query = db.collection('customers')
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.where(field, '==', value)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            customers = []
            for doc in docs:
                if doc.id != '_init':  # Skip initialization document
                    customer_data = doc.to_dict()
                    customer_data['id'] = doc.id
                    customers.append(customer_data)
            
            return customers
        except Exception as e:
            logger.error(f"Error getting customers from Firebase: {e}")
            return []
    
    @staticmethod
    def update_customer(customer_id: str, data: dict) -> bool:
        if not FirebaseManager.is_enabled():
            return True
        
        try:
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            db.collection('customers').document(customer_id).update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            return False
    
    @staticmethod
    def delete_customer(customer_id: str) -> bool:
        if not FirebaseManager.is_enabled():
            return True
        
        try:
            db.collection('customers').document(customer_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            return False
    
    @staticmethod
    def create_deal(data: dict) -> str:
        if not FirebaseManager.is_enabled():
            import uuid
            return str(uuid.uuid4())
        
        try:
            data['created_at'] = firestore.SERVER_TIMESTAMP
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = db.collection('deals').add(data)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error creating deal in Firebase: {e}")
            import uuid
            return str(uuid.uuid4())
    
    @staticmethod
    def get_deals(filters: dict = None, limit: int = None) -> list:
        if not FirebaseManager.is_enabled():
            return []
        
        try:
            query = db.collection('deals')
            
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.where(field, '==', value)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            deals = []
            for doc in docs:
                if doc.id != '_init':
                    deal_data = doc.to_dict()
                    deal_data['id'] = doc.id
                    deals.append(deal_data)
            
            return deals
        except Exception as e:
            logger.error(f"Error getting deals from Firebase: {e}")
            return []
    
    @staticmethod
    def update_deal(deal_id: str, data: dict) -> bool:
        if not FirebaseManager.is_enabled():
            return True
        
        try:
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            db.collection('deals').document(deal_id).update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating deal: {e}")
            return False
    
    @staticmethod
    def create_interaction(data: dict) -> str:
        if not FirebaseManager.is_enabled():
            import uuid
            return str(uuid.uuid4())
        
        try:
            data['created_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = db.collection('interactions').add(data)
            return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error creating interaction in Firebase: {e}")
            import uuid
            return str(uuid.uuid4())
    
    @staticmethod
    def get_interactions(customer_id: str = None, limit: int = None) -> list:
        if not FirebaseManager.is_enabled():
            return []
        
        try:
            query = db.collection('interactions')
            
            if customer_id:
                query = query.where('customer_id', '==', customer_id)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            interactions = []
            for doc in docs:
                if doc.id != '_init':
                    interaction_data = doc.to_dict()
                    interaction_data['id'] = doc.id
                    interactions.append(interaction_data)
            
            return interactions
        except Exception as e:
            logger.error(f"Error getting interactions from Firebase: {e}")
            return []
    
    @staticmethod
    def create_sample_data():
        """Create sample data in Firebase"""
        if not FirebaseManager.is_enabled():
            logger.warning("Firebase not enabled, cannot create sample data")
            return False
            
        try:
            # Sample customers
            sample_customers = [
                {
                    'name': 'Acme Corporation',
                    'email': 'contact@acme.com',
                    'phone': '+1-555-0100',
                    'company': 'Acme Corp',
                    'status': 'Active',
                    'notes': 'Initial customer contact'
                },
                {
                    'name': 'TechStart Inc',
                    'email': 'info@techstart.com',
                    'phone': '+1-555-0101',
                    'company': 'TechStart',
                    'status': 'Lead',
                    'notes': 'Interested in our solutions'
                },
                {
                    'name': 'Global Solutions',
                    'email': 'sales@globalsolutions.com',
                    'phone': '+1-555-0102',
                    'company': 'Global Solutions',
                    'status': 'Active',
                    'notes': 'Active customer'
                }
            ]
            
            customer_ids = []
            for customer in sample_customers:
                customer_id = FirebaseManager.create_customer(customer)
                customer_ids.append(customer_id)
                logger.info(f"Created sample customer: {customer['name']}")
            
            # Sample deals
            sample_deals = [
                {
                    'title': 'Enterprise Software License',
                    'value': 150000,
                    'stage': 'Proposal',
                    'probability': 60,
                    'status': 'Active',
                    'customer_id': customer_ids[0] if customer_ids else 'sample_customer',
                    'notes': 'Enterprise software licensing deal'
                },
                {
                    'title': 'Cloud Migration Project',
                    'value': 85000,
                    'stage': 'Negotiation',
                    'probability': 75,
                    'status': 'Active',
                    'customer_id': customer_ids[1] if len(customer_ids) > 1 else 'sample_customer',
                    'notes': 'Cloud migration and setup'
                }
            ]
            
            for deal in sample_deals:
                deal_id = FirebaseManager.create_deal(deal)
                logger.info(f"Created sample deal: {deal['title']}")
            
            logger.info("Sample data created successfully in Firebase")
            return True
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            return False
    
    @staticmethod
    def setup_listeners(callback_func):
        """Setup real-time listeners for live updates"""
        if not FirebaseManager.is_enabled():
            logger.warning("Firebase is not enabled. Real-time updates disabled.")
            return None
        
        try:
            def on_snapshot(doc_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name == 'ADDED':
                        callback_func('added', change.document.to_dict())
                    elif change.type.name == 'MODIFIED':
                        callback_func('modified', change.document.to_dict())
                    elif change.type.name == 'REMOVED':
                        callback_func('removed', change.document.id)
            
            # Listen to deals collection
            deals_ref = db.collection('deals')
            deals_watch = deals_ref.on_snapshot(on_snapshot)
            
            return deals_watch
        except Exception as e:
            logger.error(f"Error setting up Firebase listeners: {e}")
            return None