#!/bin/bash
cd "$(dirname "$0")"

gcloud kms encrypt \
  --location=global \
  --keyring=secrets \
  --key=prod_secrets_encryption_key \
  --plaintext-file="./params.json" \
  --ciphertext-file="./params.json.encrypted"
