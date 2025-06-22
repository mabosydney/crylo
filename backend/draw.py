#!/usr/bin/env python3
"""Trigger weekly draw"""
from .app import app
from .config import load_config

if __name__ == '__main__':
    config = load_config()
    with app.test_request_context('/draw', method='POST', data={'password': config['admin_password']}):
        print(app.view_functions['draw']())
