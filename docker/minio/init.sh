#!/bin/sh

set -eu

until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null; do
  echo "waiting for minio..."
  sleep 1
done

mc mb --ignore-existing "local/$MINIO_DOCUMENTS_BUCKET_NAME"
mc anonymous set none "local/$MINIO_DOCUMENTS_BUCKET_NAME"

cat > /tmp/book-rag-read.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::$MINIO_DOCUMENTS_BUCKET_NAME/chat-documents/*"]
    }
  ]
}
EOF

mc admin policy create local book-rag-read /tmp/book-rag-read.json
mc admin user add local "$BOOK_RAG_MINIO_ACCESS_KEY" "$BOOK_RAG_MINIO_SECRET_KEY"
mc admin policy attach local book-rag-read --user "$BOOK_RAG_MINIO_ACCESS_KEY" || true

echo "minio init done"
