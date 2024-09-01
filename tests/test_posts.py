import json
from flask_jwt_extended import create_access_token

def test_create_post(test_client, init_database):
    # Register and login user
    test_client.post('/register', json={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'password123'
    })
    login_response = test_client.post('/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    access_token = login_response.json['access_token']
    
    # Create a new post
    response = test_client.post('/posts', json={
        'title': 'Test Post',
        'content': 'This is a test post content.',
        'author_id': 1
    }, headers={'Authorization': f'Bearer {access_token}'})
    
    assert response.status_code == 201
    assert response.json['title'] == 'Test Post'

def test_read_posts(test_client, init_database):
    # Register a new user
    response = test_client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 201

    # Log in with the registered user to obtain an access token
    response = test_client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    access_token = response.json['access_token']

    # Create a post
    response = test_client.post('/posts', json={
        'title': 'Test Post',
        'content': 'This is a test post.',
        'author_id': 1  # Assuming the author exists in the database
    }, headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 201

    # Now, read the posts
    response = test_client.get('/posts', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    assert len(response.json) > 0  # Ensure there's at least one post

