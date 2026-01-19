# File: tasks_api/utils/mongodb.py

from typing import Dict, Any, List, Optional, Union
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.collection import Collection
from pymongo.database import Database
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
from bson import ObjectId
import json
import logging
from contextlib import contextmanager
from functools import wraps
import time

logger = logging.getLogger(__name__)

class MongoDBConnectionError(Exception):
    """Custom exception for MongoDB connection issues"""
    pass

class MongoDBManager:
    """
    Singleton manager for MongoDB connections and operations.
    Handles connection pooling, retries, and caching.
    """
    
    _instance = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._connect()
    
    def _connect(self) -> None:
        """Establish MongoDB connection with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Get MongoDB settings
                mongo_settings = getattr(settings, 'MONGODB_SETTINGS', {
                    'host': 'localhost',
                    'port': 27017,
                    'db_name': 'jarvis_insights',
                    'username': None,
                    'password': None,
                    'auth_source': 'admin'
                })
                
                # Build connection URL
                if mongo_settings.get('username'):
                    mongo_url = (
                        f"mongodb://{mongo_settings['username']}:"
                        f"{mongo_settings['password']}@"
                        f"{mongo_settings['host']}:{mongo_settings['port']}/"
                        f"?authSource={mongo_settings['auth_source']}"
                    )
                else:
                    mongo_url = f"mongodb://{mongo_settings['host']}:{mongo_settings['port']}/"
                
                # Create client with connection pooling
                self._client = MongoClient(
                    mongo_url,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=60000,
                    connectTimeoutMS=5000,
                    serverSelectionTimeoutMS=5000,
                    retryWrites=True
                )
                
                # Test connection
                self._client.server_info()
                
                # Get database
                self._db = self._client[mongo_settings['db_name']]
                
                # Create indexes
                self._create_indexes()
                
                logger.info("MongoDB connection established successfully")
                break
                
            except ConnectionFailure as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"MongoDB connection attempt {attempt + 1} failed. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"Failed to connect to MongoDB: {str(e)}")
                    raise MongoDBConnectionError(
                        "Unable to establish MongoDB connection"
                    )
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for performance"""
        try:
            # Insights collection indexes
            insights = self._db.insights
            insights.create_index([("user_id", ASCENDING)])
            insights.create_index([("created_at", DESCENDING)])
            insights.create_index([("type", ASCENDING)])
            insights.create_index([
                ("user_id", ASCENDING),
                ("created_at", DESCENDING)
            ])
            
            # AI processing logs indexes
            ai_logs = self._db.ai_processing_logs
            ai_logs.create_index([("user_id", ASCENDING)])
            ai_logs.create_index([("timestamp", DESCENDING)])
            ai_logs.create_index([("processing_time", ASCENDING)])
            
            # Task patterns collection indexes
            patterns = self._db.task_patterns
            patterns.create_index([("user_id", ASCENDING)])
            patterns.create_index([("pattern_type", ASCENDING)])
            patterns.create_index([("confidence", DESCENDING)])
            
            # Search index for insights
            insights.create_index([("insights.text", TEXT)])
            
            logger.info("MongoDB indexes created successfully")
            
        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {str(e)}")
    
    @property
    def db(self) -> Database:
        """Get database instance"""
        if not self._db:
            self._connect()
        return self._db
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client"""
        if not self._client:
            self._connect()
        return self._client
    
    def get_collection(self, name: str) -> Collection:
        """Get collection by name"""
        return self.db[name]
    
    @contextmanager
    def session(self):
        """Context manager for MongoDB sessions"""
        session = self.client.start_session()
        try:
            yield session
        finally:
            session.end_session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            start_time = time.time()
            
            # Ping database
            self.client.admin.command('ping')
            
            # Get server status
            server_info = self.client.server_info()
            
            # Get database stats
            db_stats = self.db.command('dbStats')
            
            return {
                'status': 'healthy',
                'response_time': time.time() - start_time,
                'version': server_info.get('version'),
                'collections': db_stats.get('collections'),
                'storage_size': db_stats.get('storageSize'),
                'indexes': db_stats.get('indexes')
            }
            
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Global instance
_mongodb_manager = MongoDBManager()

def get_mongodb_manager() -> MongoDBManager:
    """Get MongoDB manager instance"""
    return _mongodb_manager

def get_insights_collection() -> Collection:
    """Get insights collection"""
    return _mongodb_manager.get_collection('insights')

def get_ai_logs_collection() -> Collection:
    """Get AI processing logs collection"""
    return _mongodb_manager.get_collection('ai_processing_logs')

def get_patterns_collection() -> Collection:
    """Get task patterns collection"""
    return _mongodb_manager.get_collection('task_patterns')

def with_mongodb_retry(retries: int = 3, delay: float = 1.0):
    """
    Decorator for MongoDB operations with retry logic.
    
    Args:
        retries: Number of retry attempts
        delay: Initial delay between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (ConnectionFailure, OperationFailure) as e:
                    last_exception = e
                    if attempt < retries - 1:
                        logger.warning(
                            f"MongoDB operation failed (attempt {attempt + 1}/{retries}). "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= 2
                    else:
                        logger.error(
                            f"MongoDB operation failed after {retries} attempts: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator

class InsightsRepository:
    """Repository for AI-generated insights operations"""
    
    @staticmethod
    @with_mongodb_retry()
    def save_insight(
        user_id: int,
        insight_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Save AI-generated insight.
        
        Args:
            user_id: User identifier
            insight_data: Insight data to save
            session_id: Optional session ID
            
        Returns:
            Inserted document ID
        """
        collection = get_insights_collection()
        
        document = {
            'user_id': user_id,
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'type': insight_data.get('type', 'general'),
            'insights': insight_data,
            'confidence_scores': insight_data.get('confidence_scores', {}),
            'recommendations': insight_data.get('recommendations', []),
            'metadata': insight_data.get('metadata', {})
        }
        
        result = collection.insert_one(document)
        
        # Invalidate cache
        cache_key = f"user_insights:{user_id}"
        cache.delete(cache_key)
        
        return str(result.inserted_id)
    
    @staticmethod
    @with_mongodb_retry()
    def get_user_insights(
        user_id: int,
        limit: int = 10,
        insight_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's insights with caching.
        
        Args:
            user_id: User identifier
            limit: Maximum number of insights
            insight_type: Filter by type
            
        Returns:
            List of insights
        """
        # Check cache
        cache_key = f"user_insights:{user_id}:{insight_type}:{limit}"
        cached_insights = cache.get(cache_key)
        if cached_insights:
            return cached_insights
        
        collection = get_insights_collection()
        
        # Build query
        query = {'user_id': user_id}
        if insight_type:
            query['type'] = insight_type
        
        # Fetch insights
        cursor = collection.find(query).sort(
            'created_at', DESCENDING
        ).limit(limit)
        
        insights = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            insights.append(doc)
        
        # Cache for 5 minutes
        cache.set(cache_key, insights, 300)
        
        return insights
    
    @staticmethod
    @with_mongodb_retry()
    def get_aggregated_insights(
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregated insights for analytics.
        
        Args:
            user_id: User identifier
            days: Number of days to aggregate
            
        Returns:
            Aggregated insights data
        """
        collection = get_insights_collection()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'created_at': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1},
                    'avg_confidence': {
                        '$avg': '$confidence_scores.overall'
                    },
                    'recommendations': {
                        '$push': '$recommendations'
                    }
                }
            },
            {
                '$project': {
                    'type': '$_id',
                    'count': 1,
                    'avg_confidence': 1,
                    'top_recommendations': {
                        '$slice': [
                            {'$reduce': {
                                'input': '$recommendations',
                                'initialValue': [],
                                'in': {'$concatArrays': ['$$value', '$$this']}
                            }},
                            5
                        ]
                    }
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        
        return {
            'user_id': user_id,
            'period_days': days,
            'insight_types': results,
            'total_insights': sum(r['count'] for r in results),
            'average_confidence': (
                sum(r.get('avg_confidence', 0) * r['count'] for r in results) /
                sum(r['count'] for r in results)
                if results else 0
            )
        }
    
    @staticmethod
    @with_mongodb_retry()
    def search_insights(
        user_id: int,
        search_text: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search user's insights using text search.
        
        Args:
            user_id: User identifier
            search_text: Text to search for
            limit: Maximum results
            
        Returns:
            List of matching insights
        """
        collection = get_insights_collection()
        
        results = collection.find(
            {
                'user_id': user_id,
                '$text': {'$search': search_text}
            },
            {
                'score': {'$meta': 'textScore'}
            }
        ).sort(
            [('score', {'$meta': 'textScore'})]
        ).limit(limit)
        
        insights = []
        for doc in results:
            doc['_id'] = str(doc['_id'])
            insights.append(doc)
        
        return insights

class TaskPatternsRepository:
    """Repository for task pattern analysis"""
    
    @staticmethod
    @with_mongodb_retry()
    def save_pattern(
        user_id: int,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        confidence: float
    ) -> str:
        """Save discovered task pattern"""
        collection = get_patterns_collection()
        
        document = {
            'user_id': user_id,
            'pattern_type': pattern_type,
            'pattern_data': pattern_data,
            'confidence': confidence,
            'discovered_at': datetime.utcnow(),
            'usage_count': 0,
            'last_used': None
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    @with_mongodb_retry()
    def get_user_patterns(
        user_id: int,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get user's discovered patterns"""
        collection = get_patterns_collection()
        
        patterns = collection.find({
            'user_id': user_id,
            'confidence': {'$gte': min_confidence}
        }).sort('confidence', DESCENDING)
        
        return [
            {**doc, '_id': str(doc['_id'])}
            for doc in patterns
        ]
    
    @staticmethod
    @with_mongodb_retry()
    def update_pattern_usage(pattern_id: str) -> None:
        """Update pattern usage statistics"""
        collection = get_patterns_collection()
        
        collection.update_one(
            {'_id': ObjectId(pattern_id)},
            {
                '$inc': {'usage_count': 1},
                '$set': {'last_used': datetime.utcnow()}
            }
        )

class AILogsRepository:
    """Repository for AI processing logs"""
    
    @staticmethod
    @with_mongodb_retry()
    def log_ai_processing(
        user_id: int,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        processing_time: float,
        success: bool,
        error: Optional[str] = None
    ) -> str:
        """Log AI processing request and response"""
        collection = get_ai_logs_collection()
        
        document = {
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'request': request_data,
            'response': response_data,
            'processing_time': processing_time,
            'success': success,
            'error': error,
            'model_used': request_data.get('model', 'ollama'),
            'token_count': response_data.get('token_count', 0)
        }
        
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    @with_mongodb_retry()
    def get_processing_stats(
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get AI processing statistics"""
        collection = get_ai_logs_collection()
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'timestamp': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_requests': {'$sum': 1},
                    'successful_requests': {
                        '$sum': {'$cond': ['$success', 1, 0]}
                    },
                    'avg_processing_time': {'$avg': '$processing_time'},
                    'total_tokens': {'$sum': '$token_count'},
                    'errors': {
                        '$push': {
                            '$cond': [
                                {'$ne': ['$error', None]},
                                '$error',
                                '$$REMOVE'
                            ]
                        }
                    }
                }
            }
        ]
        
        results = list(collection.aggregate(pipeline))
        
        if results:
            stats = results[0]
            stats['success_rate'] = (
                stats['successful_requests'] / stats['total_requests'] * 100
                if stats['total_requests'] > 0 else 0
            )
            del stats['_id']
            return stats
        
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_processing_time': 0,
            'total_tokens': 0,
            'success_rate': 0,
            'errors': []
        }

# Utility functions
def cleanup_old_data(days_to_keep: int = 90) -> Dict[str, int]:
    """
    Clean up old data from MongoDB collections.
    
    Args:
        days_to_keep: Number of days to keep data
        
    Returns:
        Dictionary with deletion counts
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    results = {}
    
    try:
        # Clean insights
        insights_result = get_insights_collection().delete_many({
            'created_at': {'$lt': cutoff_date}
        })
        results['insights'] = insights_result.deleted_count
        
        # Clean AI logs
        logs_result = get_ai_logs_collection().delete_many({
            'timestamp': {'$lt': cutoff_date}
        })
        results['ai_logs'] = logs_result.deleted_count
        
        # Clean old patterns
        patterns_result = get_patterns_collection().delete_many({
            'last_used': {'$lt': cutoff_date},
            'usage_count': {'$lt': 5}
        })
        results['patterns'] = patterns_result.deleted_count
        
        logger.info(f"Cleaned up old MongoDB data: {results}")
        
    except Exception as e:
        logger.error(f"Failed to clean up MongoDB data: {str(e)}")
        
    return results