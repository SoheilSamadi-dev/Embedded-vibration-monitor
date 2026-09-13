#!/usr/bin/env python3
# Copyright (c) 2026 Soheil Samadi
# SPDX-License-Identifier: AGPL-3.0-only
# Licensed under the GNU AGPL v3; see LICENSE in the repository root.

"""Telegram setup and sending; credentials never belong in project files."""
import argparse
import getpass
import json
import os
from pathlib import Path
import urllib.request


def api(token, method, payload):
    request = urllib.request.Request(
        'https://api.telegram.org/bot' + token + '/' + method,
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError('Telegram request failed')
    return result['result']


def send_message(path, text):
    credentials = json.loads(path.read_text())
    return api(credentials['token'], 'sendMessage', {'chat_id': credentials['chat_id'], 'text': text})


def setup(path):
    token = getpass.getpass('Paste BotFather token (hidden): ').strip()
    if not token or ':' not in token or any(c.isspace() for c in token):
        raise ValueError('Invalid token format')
    updates = api(token, 'getUpdates', {'timeout': 0, 'allowed_updates': ['message']})
    chats = {}
    for update in updates:
        chat = update.get('message', {}).get('chat', {})
        if chat.get('type') == 'private':
            chats[str(chat['id'])] = chat.get('first_name', '')
    if not chats:
        print('Open your bot in Telegram, send /start, then rerun setup.')
        return
    for chat_id, name in chats.items():
        print(chat_id, name)
    selected = input('Enter your chat ID from the list above: ').strip()
    if selected not in chats:
        raise ValueError('Choose one of the displayed private chats')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as file:
        os.fchmod(file.fileno(), 0o600)
        json.dump({'token': token, 'chat_id': selected}, file)
    print('Credentials saved privately. Run with --test to send a test notification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, default=Path.home() / '.config/condition-monitor/telegram.json')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    try:
        if args.test:
            send_message(args.file, 'Condition monitor test: your Pi can send Telegram notifications.')
            print('Telegram accepted the test message. Check your phone.')
        else:
            setup(args.file)
    except Exception:
        # Network exceptions can include the token-bearing URL. Never print them.
        print('Setup/send failed. Check connectivity, token and whether you started your bot.')
        raise SystemExit(1)
