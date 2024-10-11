#!/bin/bash
cd "$(dirname "$0")"

gcloud kms decrypt \
  --location=global \
  --keyring=secrets \
  --key=prod_config_encryption_key \
  --ciphertext-file="./params.json.encrypted" \
  --plaintext-file="./params.json"
