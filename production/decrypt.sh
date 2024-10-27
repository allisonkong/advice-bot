#!/bin/bash

cd "$(dirname "$0")"

gcloud kms decrypt \
  --location=global \
  --keyring=secrets \
  --key=prod_secrets_encryption_key \
  --ciphertext-file="./params.textproto.encrypted" \
  --plaintext-file="./params.textproto"
