# firebase_config.py
import os
import logging
from decouple import config

logger = logging.getLogger(__name__)

# Initialize Firebase only if credentials exist
try:
    firebase_cred_path = config('FIREBASE_CREDENTIALS_PATH', default='core/serviceAccountKey.json')
    if os.path.exists(firebase_cred_path):
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)
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
    def create_customer(data: dict) -> str:
        if not FIREBASE_ENABLED:
            logger.warning("Firebase is not enabled. Using local ID.")
            import uuid
            return str(uuid.uuid4())
        
        doc_ref = db.collection('customers').add(data)
        return doc_ref[1].id
    
    @staticmethod
    def get_customers(filters: dict = None) -> list:
        if not FIREBASE_ENABLED:
            return []
        
        query = db.collection('customers')
        if filters:
            for field, value in filters.items():
                query = query.where(field, '==', value)
        return [doc.to_dict() for doc in query.stream()]
    
    @staticmethod
    def update_customer(customer_id: str, data: dict) -> bool:
        if not FIREBASE_ENABLED:
            return True
        
        try:
            db.collection('customers').document(customer_id).update(data)
            return True
        except Exception as e:
            print(f"Error updating customer: {e}")
            return False
    
    @staticmethod
    def delete_customer(customer_id: str) -> bool:
        if not FIREBASE_ENABLED:
            return True
        
        try:
            db.collection('customers').document(customer_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting customer: {e}")
            return False
    
    @staticmethod
    def create_deal(data: dict) -> str:
        if not FIREBASE_ENABLED:
            import uuid
            return str(uuid.uuid4())
        
        doc_ref = db.collection('deals').add(data)
        return doc_ref[1].id
    
    @staticmethod
    def get_deals(filters: dict = None) -> list:
        if not FIREBASE_ENABLED:
            return []
        
        query = db.collection('deals')
        if filters:
            for field, value in filters.items():
                query = query.where(field, '==', value)
        return [doc.to_dict() for doc in query.stream()]
    
    @staticmethod
    def update_deal(deal_id: str, data: dict) -> bool:
        if not FIREBASE_ENABLED:
            return True
        
        try:
            db.collection('deals').document(deal_id).update(data)
            return True
        except Exception as e:
            print(f"Error updating deal: {e}")
            return False
    
    @staticmethod
    def create_interaction(data: dict) -> str:
        if not FIREBASE_ENABLED:
            import uuid
            return str(uuid.uuid4())
        
        doc_ref = db.collection('interactions').add(data)
        return doc_ref[1].id
    
    @staticmethod
    def get_interactions(customer_id: str) -> list:
        if not FIREBASE_ENABLED:
            return []
        
        query = db.collection('interactions').where('customer_id', '==', customer_id)
        return [doc.to_dict() for doc in query.stream()]
    
    @staticmethod
    def setup_listeners(callback_func):
        """Setup real-time listeners for live updates"""
        if not FIREBASE_ENABLED:
            logger.warning("Firebase is not enabled. Real-time updates disabled.")
            return None
        
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