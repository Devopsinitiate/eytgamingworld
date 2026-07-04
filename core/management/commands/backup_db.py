"""
Management command to backup the database.

Supports PostgreSQL (pg_dump) and SQLite, with local or S3 storage.
Usage:
    python manage.py backup_db                          # default: local
    python manage.py backup_db --s3                     # upload to S3
    python manage.py backup_db --database sqlite        # force SQLite mode
"""
import gzip
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Backup the database to a compressed file (local or S3)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--s3',
            action='store_true',
            help='Upload backup to S3 instead of saving locally',
        )
        parser.add_argument(
            '--database',
            choices=['auto', 'postgresql', 'sqlite'],
            default='auto',
            help='Force a specific database backend (default: auto-detect)',
        )
        parser.add_argument(
            '--output-dir',
            default=None,
            help='Directory to save backups (default: backups/)',
        )

    def _detect_backend(self):
        """Detect database backend from Django's connection."""
        vendor = connection.vendor
        if vendor == 'postgresql':
            return 'postgresql'
        elif vendor == 'sqlite':
            return 'sqlite'
        raise CommandError(f'Unsupported database backend: {vendor}')

    def _get_db_settings(self):
        """Extract database connection parameters from Django settings."""
        db = settings.DATABASES['default']
        return db

    def _backup_postgresql(self, output_path):
        """Run pg_dump and compress."""
        db = self._get_db_settings()
        host = db.get('HOST', 'localhost')
        port = db.get('PORT', '5432')
        name = db.get('NAME', 'eytgaming_db')
        user = db.get('USER', 'postgres')
        password = db.get('PASSWORD', '')

        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password

        self.stdout.write(f'Backing up PostgreSQL database: {name}@{host}:{port}')

        result = subprocess.run(
            ['pg_dump', '--no-owner', '--no-acl', '-h', host, '-p', str(port), '-U', user, '-d', name],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise CommandError(f'pg_dump failed: {result.stderr}')

        # Compress
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(result.stdout)

        self.stdout.write(f'  → Compressed to: {output_path}')

    def _backup_sqlite(self, output_path):
        """Copy the SQLite database file and compress."""
        db = self._get_db_settings()
        db_path = db.get('NAME', 'db.sqlite3')

        if not os.path.exists(db_path):
            raise CommandError(f'SQLite database file not found: {db_path}')

        self.stdout.write(f'Backing up SQLite database: {db_path}')
        temp_sqlite = output_path.replace('.sql.gz', '.sqlite3')

        # Use sqlite3 .backup for safe online backup
        result = subprocess.run(
            ['sqlite3', db_path, '.backup', temp_sqlite],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            # Fallback: direct file copy
            shutil.copy2(db_path, temp_sqlite)

        # Compress
        with open(temp_sqlite, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(temp_sqlite)
        self.stdout.write(f'  → Compressed to: {output_path}')

    def _upload_s3(self, file_path):
        """Upload backup file to S3."""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise CommandError('boto3 is required for S3 uploads. Install: pip install boto3')

        bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'eytgaming-backups')
        key = f'database-backups/{Path(file_path).name}'

        self.stdout.write(f'Uploading to S3: s3://{bucket}/{key}')

        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
        )

        try:
            s3.upload_file(file_path, bucket, key)
            self.stdout.write(self.style.SUCCESS(f'  → Uploaded to S3: s3://{bucket}/{key}'))
        except ClientError as e:
            raise CommandError(f'S3 upload failed: {e}')

    def _cleanup_old(self, output_dir, keep=7):
        """Remove backups older than `keep` days."""
        cutoff = datetime.now().timestamp() - (keep * 86400)
        removed = 0
        for f in Path(output_dir).glob('*.sql.gz'):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        if removed:
            self.stdout.write(f'Cleaned up {removed} old backup(s) (retention: {keep} days)')

    def handle(self, *args, **options):
        backend = options['database']
        if backend == 'auto':
            backend = self._detect_backend()

        output_dir = options.get('output_dir') or os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = 'sql.gz'
        filename = f'db_backup_{timestamp}.{ext}'
        output_path = os.path.join(output_dir, filename)

        try:
            if backend == 'postgresql':
                self._backup_postgresql(output_path)
            elif backend == 'sqlite':
                self._backup_sqlite(output_path)

            if options['s3']:
                self._upload_s3(output_path)

            self._cleanup_old(output_dir)

            self.stdout.write(self.style.SUCCESS(
                f'Backup completed successfully: {output_path}'
            ))
        except subprocess.TimeoutExpired:
            raise CommandError('Backup timed out (300s limit)')
        except FileNotFoundError as e:
            raise CommandError(f'Required tool not found: {e}. Is pg_dump/sqlite3 installed?')
