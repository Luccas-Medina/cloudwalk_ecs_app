from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.queue import Kafka
from diagrams.onprem.monitoring import Prometheus
from diagrams.onprem.analytics import Spark
from diagrams.onprem.inmemory import Redis
from diagrams.generic import Generic
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SNS

with Diagram("Empathic Credit System Architecture", show=False):
    # Data Source: Customer Brain
    customer_brain = Users("Customer Brain (Emotions/Thoughts)")
    mobile_app = Generic("CloudWalk Mobile App")

    # Emotional Data Stream
    emotion_stream = Kafka("Emotional Data Stream")

    # API Layer
    api_gateway = Generic("RESTful API (Credit Limit)")

    # Database Cluster
    with Cluster("Databases"):
        user_db = Generic("User Profile DB")
        transaction_db = Generic("Transaction DB")
        emotion_db = Generic("Emotional Events DB")

    # ML Model
    ml_model = Spark("Pre-trained ML Model")

    # Credit Approval Worker
    worker = Lambda("Credit Approval Worker")

    # Notification
    notification = SNS("Mobile App Notification")

    # Observability
    monitoring = Prometheus("Observability & Health")

    # Data Flow
    customer_brain >> mobile_app >> emotion_stream
    emotion_stream >> api_gateway
    api_gateway >> [user_db, transaction_db, emotion_db]
    api_gateway >> ml_model
    ml_model >> api_gateway
    api_gateway >> worker
    worker >> user_db
    worker >> notification
    api_gateway >> monitoring
