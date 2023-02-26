#!/bin/bash

# CONFIGURATION variable format:
# comma-separated base64 strings of:
# IMAP_SERVER=<A>;IMAP_FOLDER=<B>;EMAIL_ADDRESS=<C>;EMAIL_PASSWORD=<D>;EMAIL_MARK_READ=<E>;RAKUTEN_PASSWORD=<F>
# where
# A: imap server url
# B: folder to parse emails at
# C: email address
# D: email password
# E: mark unrelated emails in the same folder as read, true or false
# F: password on rakuten

cache=${CACHE_FOLDER:-cache}
mkdir -p "$cache"

echo "$CONFIGURATION" | tr ',' '\n' | \
while read -r config; do
    source <(base64 -dw0 <<< "$config")
    profile="`base64 -w0 <<< "$EMAIL_ADDRESS"`"
    python imap.py \
        "$cache/$profile" \
        "$IMAP_SERVER" \
        "$IMAP_FOLDER" \
        "$EMAIL_ADDRESS" \
        "$EMAIL_PASSWORD" \
        "$RAKUTEN_PASSWORD" \
        "$EMAIL_MARK_READ"
done
