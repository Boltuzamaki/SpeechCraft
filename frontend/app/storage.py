import logging
import os
import uuid

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import url_for
from werkzeug.utils import secure_filename

# AWS S3 Configuration (set these in Replit Secrets)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")

# Local storage fallback
LOCAL_STORAGE_PATH = os.path.join("app", "static", "uploads")


class StorageManager:
    def __init__(self):
        self.s3_enabled = all(
            [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]
        )

        if self.s3_enabled:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION,
                )
                # Test connection
                self.s3_client.head_bucket(Bucket=S3_BUCKET)
                logging.info(
                    f"S3 storage initialized successfully with bucket: {S3_BUCKET}"
                )
            except (ClientError, NoCredentialsError) as e:
                logging.warning(
                    f"S3 initialization failed: {e}. Falling back to local storage."
                )
                self.s3_enabled = False
        else:
            logging.info("S3 credentials not found. Using local storage.")

        # Ensure local directory exists
        os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

    def upload_file(self, file_obj, user_id, file_type="media"):
        """Upload file to S3 or local storage"""
        try:
            # Generate unique filename
            filename = secure_filename(file_obj.filename)
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"

            if self.s3_enabled:
                return self._upload_to_s3(file_obj, unique_filename, file_type)
            else:
                return self._upload_to_local(
                    file_obj, unique_filename, file_type
                )

        except Exception as e:
            logging.error(f"File upload failed: {e}")
            return {"success": False, "error": str(e)}

    def _upload_to_s3(self, file_obj, filename, file_type):
        """Upload file to S3"""
        try:
            key = f"{file_type}/{filename}"

            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                S3_BUCKET,
                key,
                ExtraArgs={
                    "ContentType": file_obj.content_type,
                    "ACL": "private",
                },
            )

            # Generate presigned URL for access
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET, "Key": key},
                ExpiresIn=3600 * 24 * 7,  # 7 days
            )

            return {
                "success": True,
                "filename": filename,
                "url": url,
                "storage_type": "s3",
                "key": key,
            }

        except ClientError as e:
            logging.error(f"S3 upload failed: {e}")
            # Fallback to local storage
            return self._upload_to_local(file_obj, filename, file_type)

    def _upload_to_local(self, file_obj, filename, file_type):
        """Upload file to local storage"""
        try:
            # Create type-specific directory
            type_dir = os.path.join(LOCAL_STORAGE_PATH, file_type)
            os.makedirs(type_dir, exist_ok=True)

            file_path = os.path.join(type_dir, filename)
            file_obj.save(file_path)

            # Generate relative URL
            relative_path = os.path.join("uploads", file_type, filename)
            try:
                url = url_for("static", filename=relative_path)
            except RuntimeError:
                url = f"/static/{relative_path}"

            return {
                "success": True,
                "filename": filename,
                "url": url,
                "storage_type": "local",
                "path": file_path,
            }

        except Exception as e:
            logging.error(f"Local upload failed: {e}")
            return {"success": False, "error": str(e)}

    def get_file_url(self, key, storage_type="s3"):
        """Get file URL for access"""
        if storage_type == "s3" and self.s3_enabled:
            try:
                return self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": S3_BUCKET, "Key": key},
                    ExpiresIn=3600 * 24,
                )
            except ClientError as e:
                logging.error(f"Failed to generate presigned URL: {e}")
                return None
        else:
            relative_path = os.path.join("uploads", key)
            try:
                return url_for("static", filename=relative_path)
            except RuntimeError:
                return f"/static/{relative_path}"

    def delete_file(self, key, storage_type="s3"):
        """Delete file from storage"""
        try:
            if storage_type == "s3" and self.s3_enabled:
                self.s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
            else:
                # Delete from local storage
                file_path = os.path.join(LOCAL_STORAGE_PATH, key)
                if os.path.exists(file_path):
                    os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"File deletion failed: {e}")
            return False


# Global storage manager instance
storage_manager = StorageManager()
