import json

def test_register(test_client, init_database):
    response = test_client.post('/register', json={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 201
    assert b'New user created!' in response.data

def test_login_correct_credentials(test_client, init_database):
    # First, register the user to ensure the credentials exist in the database
    test_client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword'
    })

    # Now, attempt to log in with the correct credentials
    response = test_client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })

    assert response.status_code == 200
    assert 'access_token' in response.json



def test_login_incorrect_credentials(test_client, init_database):
    # Attempt to login with incorrect credentials
    response = test_client.post('/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid credentials'