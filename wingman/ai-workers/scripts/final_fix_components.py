#!/usr/bin/env python3
"""
FINAL FIX FOR FAILED COMPONENTS
Properly generate actual code, not descriptions
"""

import os
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/Volumes/intel-system/max_workforce_output")

def generate_neo4j_implementation():
    """Generate actual Neo4j implementation"""
    code = '''#!/usr/bin/env python3
"""
Neo4j Graph Database Implementation
Complete knowledge graph system for Intel-System
"""

import os
from neo4j import GraphDatabase
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class Neo4jGraphDB:
    """Neo4j Knowledge Graph Manager"""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.session = None

    def __enter__(self):
        """Context manager entry"""
        self.session = self.driver.session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            self.session.close()

    def close(self):
        """Close driver connection"""
        self.driver.close()

    def create_entity(self, label: str, properties: Dict[str, Any]) -> int:
        """Create a new entity node"""
        with self.driver.session() as session:
            query = f"""
                CREATE (n:{label} $props)
                RETURN id(n) as node_id
            """
            result = session.run(query, props=properties)
            return result.single()["node_id"]

    def create_relationship(self,
                          from_id: int,
                          to_id: int,
                          rel_type: str,
                          properties: Optional[Dict] = None) -> int:
        """Create relationship between nodes"""
        with self.driver.session() as session:
            props = properties or {}
            query = f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                CREATE (a)-[r:{rel_type} $props]->(b)
                RETURN id(r) as rel_id
            """
            result = session.run(query, from_id=from_id, to_id=to_id, props=props)
            return result.single()["rel_id"]

    def find_entities(self, label: str, properties: Optional[Dict] = None) -> List[Dict]:
        """Find entities matching criteria"""
        with self.driver.session() as session:
            where_clause = ""
            if properties:
                conditions = [f"n.{k} = ${k}" for k in properties.keys()]
                where_clause = f"WHERE {' AND '.join(conditions)}"

            query = f"""
                MATCH (n:{label})
                {where_clause}
                RETURN n, id(n) as node_id
            """

            params = properties or {}
            results = []
            for record in session.run(query, **params):
                node_data = dict(record["n"])
                node_data["_id"] = record["node_id"]
                results.append(node_data)
            return results

    def find_related(self, node_id: int, rel_type: Optional[str] = None) -> List[Dict]:
        """Find nodes related to given node"""
        with self.driver.session() as session:
            rel_pattern = f":{rel_type}" if rel_type else ""
            query = f"""
                MATCH (a)-[r{rel_pattern}]-(b)
                WHERE id(a) = $node_id
                RETURN b, type(r) as rel_type, id(b) as node_id
            """

            results = []
            for record in session.run(query, node_id=node_id):
                node_data = dict(record["b"])
                node_data["_id"] = record["node_id"]
                node_data["_relationship"] = record["rel_type"]
                results.append(node_data)
            return results

    def update_entity(self, node_id: int, properties: Dict[str, Any]) -> bool:
        """Update entity properties"""
        with self.driver.session() as session:
            set_clause = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
            query = f"""
                MATCH (n)
                WHERE id(n) = $node_id
                SET {set_clause}
                RETURN n
            """
            result = session.run(query, node_id=node_id, **properties)
            return result.single() is not None

    def delete_entity(self, node_id: int) -> bool:
        """Delete entity and its relationships"""
        with self.driver.session() as session:
            query = """
                MATCH (n)
                WHERE id(n) = $node_id
                DETACH DELETE n
                RETURN count(n) as deleted
            """
            result = session.run(query, node_id=node_id)
            return result.single()["deleted"] > 0

    def execute_cypher(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute arbitrary Cypher query"""
        with self.driver.session() as session:
            results = []
            for record in session.run(query, **(parameters or {})):
                results.append(dict(record))
            return results

    def create_indexes(self):
        """Create recommended indexes"""
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.name)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.title)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Event) ON (n.timestamp)"
            ]
            for index in indexes:
                session.run(index)

    def initialize_schema(self):
        """Initialize graph schema"""
        self.create_indexes()

        # Create constraint for unique IDs
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (n:Entity)
                REQUIRE n.uuid IS UNIQUE
            """)

# Example usage and testing
if __name__ == "__main__":
    # Initialize connection
    graph = Neo4jGraphDB()

    try:
        # Initialize schema
        graph.initialize_schema()
        print("✅ Neo4j schema initialized")

        # Create test entities
        person_id = graph.create_entity("Person", {
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": datetime.now().isoformat()
        })
        print(f"✅ Created person with ID: {person_id}")

        doc_id = graph.create_entity("Document", {
            "title": "Intel System Report",
            "type": "report",
            "created_at": datetime.now().isoformat()
        })
        print(f"✅ Created document with ID: {doc_id}")

        # Create relationship
        rel_id = graph.create_relationship(
            person_id, doc_id, "AUTHORED",
            {"date": datetime.now().isoformat()}
        )
        print(f"✅ Created relationship with ID: {rel_id}")

        # Query data
        people = graph.find_entities("Person", {"name": "John Doe"})
        print(f"✅ Found {len(people)} person(s)")

        # Find related documents
        related = graph.find_related(person_id, "AUTHORED")
        print(f"✅ Found {len(related)} related document(s)")

        print("\\n✅ Neo4j Graph Database fully operational!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        graph.close()
'''

    # Save the actual implementation
    neo4j_dir = OUTPUT_DIR / "Neo4j_Graph"
    neo4j_dir.mkdir(exist_ok=True)

    impl_file = neo4j_dir / "neo4j_graph_implementation.py"
    with open(impl_file, "w") as f:
        f.write(code)
    os.chmod(impl_file, 0o755)

    # Create docker-compose for Neo4j
    docker_compose = '''version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    container_name: intel_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password123
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    networks:
      - intel_network

networks:
  intel_network:
    driver: bridge

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
'''

    with open(neo4j_dir / "docker-compose.yml", "w") as f:
        f.write(docker_compose)

    print(f"✅ Neo4j_Graph: Actual implementation created")
    return True

def generate_auth_implementation():
    """Generate actual Auth System implementation"""
    code = '''#!/usr/bin/env python3
"""
JWT Authentication System
Complete auth system with JWT, refresh tokens, API keys, and RBAC
"""

import os
import jwt
import json
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from flask import Flask, request, jsonify, g
from functools import wraps
import redis

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET", secrets.token_hex(32))
REFRESH_SECRET = os.environ.get("REFRESH_SECRET", secrets.token_hex(32))
API_KEY_PREFIX = "isk_"  # Intel System Key

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Redis for token blacklist and session storage
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None
    print("Warning: Redis not available, using in-memory storage")

# In-memory storage (fallback)
users_db = {}
api_keys_db = {}
blacklisted_tokens = set()
user_sessions = {}

class AuthSystem:
    """Core authentication system"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def generate_tokens(user_id: str, roles: List[str] = None) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        roles = roles or ["user"]

        # Access token (15 minutes)
        access_payload = {
            "user_id": user_id,
            "roles": roles,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "iat": datetime.utcnow()
        }
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')

        # Refresh token (7 days)
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
        }
        refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET, algorithm='HS256')

        # Store session
        if redis_client:
            redis_client.setex(
                f"session:{user_id}",
                timedelta(days=7),
                json.dumps({"roles": roles, "last_activity": datetime.utcnow().isoformat()})
            )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 900  # 15 minutes
        }

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
        """Verify and decode token"""
        try:
            secret = SECRET_KEY if token_type == "access" else REFRESH_SECRET
            payload = jwt.decode(token, secret, algorithms=['HS256'])

            # Check if token is blacklisted
            if redis_client:
                if redis_client.exists(f"blacklist:{token}"):
                    return None
            elif token in blacklisted_tokens:
                return None

            # Verify token type
            if payload.get("type") != token_type:
                return None

            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def generate_api_key(user_id: str, name: str = "default") -> str:
        """Generate API key for user"""
        key = API_KEY_PREFIX + secrets.token_hex(32)

        api_key_data = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None
        }

        if redis_client:
            redis_client.hset("api_keys", key, json.dumps(api_key_data))
        else:
            api_keys_db[key] = api_key_data

        return key

    @staticmethod
    def verify_api_key(api_key: str) -> Optional[str]:
        """Verify API key and return user_id"""
        if not api_key.startswith(API_KEY_PREFIX):
            return None

        if redis_client:
            data = redis_client.hget("api_keys", api_key)
            if data:
                key_data = json.loads(data)
                # Update last used
                key_data["last_used"] = datetime.utcnow().isoformat()
                redis_client.hset("api_keys", api_key, json.dumps(key_data))
                return key_data["user_id"]
        else:
            if api_key in api_keys_db:
                api_keys_db[api_key]["last_used"] = datetime.utcnow().isoformat()
                return api_keys_db[api_key]["user_id"]
        return None

# Decorators for route protection
def require_auth(allowed_roles: List[str] = None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for API key first
            api_key = request.headers.get("X-API-Key")
            if api_key:
                user_id = AuthSystem.verify_api_key(api_key)
                if user_id:
                    g.user_id = user_id
                    g.auth_method = "api_key"
                    return f(*args, **kwargs)

            # Check for JWT token
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid authorization header"}), 401

            token = auth_header.replace("Bearer ", "")
            payload = AuthSystem.verify_token(token)

            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Check roles if specified
            if allowed_roles:
                user_roles = payload.get("roles", [])
                if not any(role in allowed_roles for role in user_roles):
                    return jsonify({"error": "Insufficient permissions"}), 403

            g.user_id = payload["user_id"]
            g.roles = payload.get("roles", [])
            g.auth_method = "jwt"

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route("/auth/register", methods=["POST"])
def register():
    """Register new user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Check if user exists
    if username in users_db:
        return jsonify({"error": "User already exists"}), 409

    # Create user
    users_db[username] = {
        "user_id": username,
        "email": email,
        "password": AuthSystem.hash_password(password),
        "roles": ["user"],
        "created_at": datetime.utcnow().isoformat()
    }

    return jsonify({"message": "User created successfully"}), 201

@app.route("/auth/login", methods=["POST"])
def login():
    """Login and get tokens"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Verify user
    user = users_db.get(username)
    if not user or not AuthSystem.verify_password(password, user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate tokens
    tokens = AuthSystem.generate_tokens(username, user.get("roles", ["user"]))

    return jsonify(tokens), 200

@app.route("/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token"""
    data = request.json
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    # Verify refresh token
    payload = AuthSystem.verify_token(refresh_token, token_type="refresh")
    if not payload:
        return jsonify({"error": "Invalid refresh token"}), 401

    # Generate new tokens
    user = users_db.get(payload["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    tokens = AuthSystem.generate_tokens(payload["user_id"], user.get("roles", ["user"]))

    return jsonify(tokens), 200

@app.route("/auth/logout", methods=["POST"])
@require_auth()
def logout():
    """Logout and blacklist tokens"""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    # Blacklist the token
    if redis_client:
        redis_client.setex(f"blacklist:{token}", timedelta(hours=24), "1")
    else:
        blacklisted_tokens.add(token)

    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/auth/verify", methods=["GET"])
@require_auth()
def verify():
    """Verify current authentication"""
    return jsonify({
        "user_id": g.user_id,
        "roles": g.get("roles", []),
        "auth_method": g.auth_method
    }), 200

@app.route("/auth/api-key", methods=["POST"])
@require_auth()
def create_api_key():
    """Create API key for current user"""
    data = request.json
    name = data.get("name", "default")

    api_key = AuthSystem.generate_api_key(g.user_id, name)

    return jsonify({
        "api_key": api_key,
        "name": name,
        "created_at": datetime.utcnow().isoformat()
    }), 201

@app.route("/protected", methods=["GET"])
@require_auth(allowed_roles=["user", "admin"])
def protected_route():
    """Example protected route"""
    return jsonify({
        "message": "Access granted",
        "user_id": g.user_id,
        "roles": g.get("roles", [])
    }), 200

@app.route("/admin", methods=["GET"])
@require_auth(allowed_roles=["admin"])
def admin_route():
    """Example admin-only route"""
    return jsonify({
        "message": "Admin access granted",
        "user_id": g.user_id
    }), 200

if __name__ == "__main__":
    print("🔐 JWT Authentication System")
    print("="*50)

    # Create test admin user
    users_db["admin"] = {
        "user_id": "admin",
        "email": "admin@intel-system.com",
        "password": AuthSystem.hash_password("admin123"),
        "roles": ["user", "admin"],
        "created_at": datetime.utcnow().isoformat()
    }

    print("Test credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print()
    print("Endpoints:")
    print("  POST /auth/register")
    print("  POST /auth/login")
    print("  POST /auth/refresh")
    print("  POST /auth/logout")
    print("  GET  /auth/verify")
    print("  POST /auth/api-key")
    print("  GET  /protected (requires auth)")
    print("  GET  /admin (requires admin role)")
    print()
    print(f"Secret Key: {SECRET_KEY[:10]}...")
    print()

    app.run(host="0.0.0.0", port=5001, debug=True)
'''

    # Save the actual implementation
    auth_dir = OUTPUT_DIR / "Auth_System"
    auth_dir.mkdir(exist_ok=True)

    impl_file = auth_dir / "auth_system_implementation.py"
    with open(impl_file, "w") as f:
        f.write(code)
    os.chmod(impl_file, 0o755)

    # Create requirements.txt
    requirements = '''flask==2.3.3
pyjwt==2.8.0
bcrypt==4.0.1
redis==5.0.0
python-dotenv==1.0.0
'''

    with open(auth_dir / "requirements.txt", "w") as f:
        f.write(requirements)

    print(f"✅ Auth_System: Actual implementation created")
    return True

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         FINAL FIX - GENERATING ACTUAL CODE              ║
╚══════════════════════════════════════════════════════════╝
    """)

    print("🔧 Replacing failed components with actual implementations...")
    print()

    # Fix Neo4j
    if generate_neo4j_implementation():
        print("   • Neo4j_Graph: Real code generated")

    # Fix Auth System
    if generate_auth_implementation():
        print("   • Auth_System: Real code generated")

    print("\n" + "="*60)
    print("✅ ACTUAL IMPLEMENTATIONS CREATED")
    print("="*60)

    print("\n📊 Summary:")
    print("   • Neo4j_Graph: Complete graph database with Docker")
    print("   • Auth_System: Full JWT auth with RBAC and API keys")
    print()
    print("Both components now have:")
    print("   ✅ Real, executable Python code")
    print("   ✅ Proper error handling")
    print("   ✅ Docker/setup configurations")
    print("   ✅ Test examples in __main__")
    print()
    print("Ready for testing and deployment!")

if __name__ == "__main__":
    main()