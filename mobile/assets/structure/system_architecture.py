from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.queue import RabbitMQ
from diagrams.onprem.analytics import Spark
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.database import PostgreSQL
from diagrams.programming.framework import FastAPI
from diagrams.generic import Generic
from diagrams.onprem.compute import Server
from diagrams.aws.integration import SNS

# Custom graph attributes for better customer-centric layout
graph_attr = {
    "fontsize": "45",
    "fontcolor": "black",
    "bgcolor": "white",
    "rankdir": "TB",
    "compound": "true",
    "concentrate": "false",
    "splines": "curved"
}

with Diagram("CloudWalk Empathic Credit System - Customer-Centric Architecture", 
             filename="empathic_credit_system_architecture", 
             show=False, 
             direction="TB",
             graph_attr=graph_attr):
    
    # ============ CUSTOMER AT THE CENTER (TOP) ============
    with Cluster("👤 CUSTOMER - The Heart of Our System", graph_attr={"bgcolor": "lightblue", "style": "rounded"}):
        customer_brain = Users("🧠 Customer's Brain\n(Emotions & Thoughts)\n💭 Neural Signals")
        mobile_app = Generic("📱 Customer's Mobile App\n(Personal Credit Assistant)")
    
    # ============ CUSTOMER INTERACTION LAYER ============
    with Cluster("🤝 Direct Customer Interface", graph_attr={"bgcolor": "lightgreen", "style": "rounded"}):
        customer_dashboard = Generic("📊 Personal Dashboard\n(Customer View)")
        customer_notifications = SNS("📢 Customer Notifications\n(Credit Offers & Updates)")
    
    # ============ REAL-TIME CUSTOMER SERVICE LAYER ============
    with Cluster("⚡ Real-time Customer Service Processing", graph_attr={"bgcolor": "lightyellow", "style": "rounded"}):
        emotion_stream = Generic("🌊 Customer Emotion Stream\n(Real-time Feelings)")
        fastapi_backend = FastAPI("🔄 Customer Service APIs\n(WebSocket + REST)")
    
    # ============ CUSTOMER DATA INTELLIGENCE ============
    with Cluster("� Customer Intelligence Engine", graph_attr={"bgcolor": "lightcyan", "style": "rounded"}):
        ml_model = Spark("🤖 Customer Risk AI\n(Personalized Scoring)")
        credit_engine = Generic("💡 Customer Credit Engine\n(Personalized Decisions)")
    
    # ============ CUSTOMER DATA VAULT ============
    with Cluster("🏦 Customer Data Vault", graph_attr={"bgcolor": "lavender", "style": "rounded"}):
        database = PostgreSQL("🗄️ Customer Database")
        customer_profile = Generic("👤 Customer Profile\n(Identity & Preferences)")
        customer_emotions = Generic("💝 Customer Emotions\n(Feeling History)")
        customer_transactions = Generic("💳 Customer Transactions\n(Financial Journey)")
        customer_credits = Generic("🎯 Customer Credit Offers\n(Personalized Deals)")
    
    # ============ BACKGROUND CUSTOMER SERVICE ============
    with Cluster("⚙️ Customer Service Infrastructure", graph_attr={"bgcolor": "mistyrose", "style": "rounded"}):
        message_queue = RabbitMQ("📮 Customer Request Queue")
        celery_workers = Server("� Customer Service Workers\n(Background Processing)")
        cache = Redis("⚡ Customer Session Cache")
    
    # ============ CUSTOMER-CENTRIC DATA FLOW ============
    
    # Phase 1: Customer Emotion Capture (Primary Flow - Thick Lines)
    customer_brain >> Edge(label="1. 🧠→📱\nThoughts & Emotions", color="red", style="bold", penwidth="3") >> mobile_app
    
    # Phase 2: Customer Real-time Processing
    mobile_app >> Edge(label="2. 📱→🌊\nEmotion Events", color="blue", style="bold", penwidth="3") >> emotion_stream
    emotion_stream >> Edge(label="3. 🌊→🔄\nReal-time Stream", color="blue", penwidth="2") >> fastapi_backend
    
    # Phase 3: Customer Service Queue
    fastapi_backend >> Edge(label="4. 🔄→📮\nCustomer Requests", color="green", penwidth="2") >> message_queue
    message_queue >> Edge(label="5. 📮→👥\nProcess Customer", color="green", penwidth="2") >> celery_workers
    
    # Phase 4: Customer Intelligence Processing
    celery_workers >> Edge(label="6. 👥→💡\nAnalyze Customer", color="purple", penwidth="2") >> credit_engine
    credit_engine >> Edge(label="7. 💡→🤖\nPersonalized Assessment", color="purple", style="bold", penwidth="3") >> ml_model
    ml_model >> Edge(label="8. 🤖→💡\nCustomer Risk Score", color="purple", style="bold", penwidth="3") >> credit_engine
    
    # Phase 5: Customer Data Operations
    celery_workers >> Edge(label="9. 👥→💝\nStore Customer Emotions", color="orange", penwidth="2") >> customer_emotions
    credit_engine >> Edge(label="10. 💡→🎯\nPersonalized Offers", color="orange", penwidth="2") >> customer_credits
    
    # Phase 6: Customer Data Lookup (Bidirectional)
    credit_engine >> Edge(label="11. 💡→👤\nCustomer Lookup", color="gray", penwidth="1") >> customer_profile
    credit_engine >> Edge(label="12. 💡→💳\nCustomer History", color="gray", penwidth="1") >> customer_transactions
    
    # Phase 7: Customer Notification (Return to Customer - Thick Lines)
    credit_engine >> Edge(label="13. 💡→📢\nCredit Approved!", color="gold", style="bold", penwidth="3") >> customer_notifications
    customer_notifications >> Edge(label="14. 📢→📱\nPersonalized Offer", color="gold", style="bold", penwidth="3") >> mobile_app
    
    # Phase 8: Customer Analytics & Monitoring
    fastapi_backend >> Edge(label="15. 🔄→📊\nCustomer Analytics", color="cyan", penwidth="2") >> customer_dashboard
    celery_workers >> Edge(label="16. 👥→📊\nCustomer Insights", color="cyan", penwidth="2") >> customer_dashboard
    
    # Infrastructure Support (Lighter connections)
    fastapi_backend >> Edge(color="lightgray", style="dashed") >> cache
    [customer_profile, customer_emotions, customer_transactions, customer_credits] >> Edge(color="lightgray", style="dotted") >> database
    
    # Customer Feedback Loop (Customer can view their dashboard)
    mobile_app >> Edge(label="Customer\nAccess", color="lightblue", style="dashed") >> customer_dashboard
