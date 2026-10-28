
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)

    # VULN-BASELINE: MD5 hash, no salt. Fix in hardened branch
    password = db.Column(db.String(500), nullable=False)

    user_type = db.Column(db.String(20), nullable=False, default="sales")

    lock_status = db.Column(db.String(20), nullable=False, default="active")
    resign_status = db.Column(db.String(20), nullable=False, default="active")
    about_me = db.Column(db.Text, nullable=False, default="")
    employment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    resign_date = db.Column(db.Date, nullable=True)
    profile_picture = db.Column(db.String(500), nullable=False, default="")
    position = db.Column(db.String(50), nullable=False, default="")

    # Present in schema but INTENTIONALLY unused in vuln-baseline route logic
    failed_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    locked_until = db.Column(db.DateTime, nullable=True)

    phone = db.Column(db.String(20), nullable=True)

    # --- Added for hardened branch later
    mfa_secret = db.Column(db.String(64), nullable=True)          
    mfa_enabled = db.Column(db.Boolean, default=False, nullable=False)

    leads = db.relationship("Lead", backref="agent", lazy=True)


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    locked_until = db.Column(db.DateTime, nullable=True)


class Project(db.Model):
    """A property listing."""
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2))            
    discount_price = db.Column(db.Numeric(12, 2))
    discount_reason = db.Column(db.String(255))
    image_path = db.Column(db.String(255))           
    google_map = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship("ProjectImage", backref="project", lazy=True,
                              cascade="all, delete-orphan")
    inquiries = db.relationship("Inquiry", backref="project", lazy=True)
    reviews = db.relationship("Review", backref="project", lazy=True)


class ProjectImage(db.Model):
    __tablename__ = "project_images"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)          
    inquiry_date = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(100))
    rating = db.Column(db.SmallInteger)
    comment = db.Column(db.Text)         
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, nullable=True)      
    actor_username = db.Column(db.String(50), nullable=True)  
    action = db.Column(db.String(50), nullable=False)         
    target_type = db.Column(db.String(50), nullable=True)     
    target_id = db.Column(db.Integer, nullable=True)
    before_state = db.Column(db.Text, nullable=True)          
    after_state = db.Column(db.Text, nullable=True)           
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subscriber(db.Model):
    __tablename__ = "subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Lead(db.Model):
   
    __tablename__ = "leads"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="new")

    interest = db.Column(db.String(20))                
    remark = db.Column(db.Text)
    history = db.Column(db.Text)

    agent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    registration_date = db.Column(db.Date, default=datetime.utcnow)

    # VULN-BASELINE (route-layer, not schema): GET /leads/<id> will NOT check
    # that current_user.id == lead.agent_id (unless user_type == 'admin').
    # That missing check IS the IDOR — fix it in the hardened branch.
