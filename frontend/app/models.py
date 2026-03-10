# app/models.py
from datetime import datetime

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    auth_type = db.Column(db.String(20), default="email")
    is_email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return (
            check_password_hash(self.password_hash, password)
            if self.password_hash
            else False
        )


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "browser_session_key",
            "provider",
            name="uq_user_browser_session_key_provider",
        ),
    )


class TranscriptionJob(db.Model):
    __tablename__ = "transcription_jobs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    api_task_id = db.Column(db.String, unique=True, nullable=True, index=True)
    filename = db.Column(db.String, nullable=False)
    file_type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="processing")
    transcription_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )
    user = db.relationship("User", backref="transcription_jobs")
    original_file_url = db.Column(db.String, nullable=True)
    audio_file_url = db.Column(db.String, nullable=True)
    storage_type = db.Column(db.String, default="local")
    storage_key = db.Column(db.String, nullable=True)
    duration = db.Column(db.Float, nullable=True)
    video_codec = db.Column(db.String, nullable=True)
    audio_codec = db.Column(db.String, nullable=True)


class TranscriptSegment(db.Model):
    __tablename__ = "transcript_segments"
    id = db.Column(db.Integer, primary_key=True)
    transcription_job_id = db.Column(
        db.Integer, db.ForeignKey("transcription_jobs.id"), nullable=False
    )
    segment_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    edited_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )
    transcription_job = db.relationship("TranscriptionJob", backref="segments")
