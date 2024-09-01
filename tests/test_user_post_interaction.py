def test_user_can_create_and_view_post(test_client):
    # Register and login user
    test_client.post('/register', json={
        'username': 'user1',
        'email': 'user1@example.com',
        'password': 'password123'
    })
    login_response = test_client.post('/login', json={
        'username': 'user1',
        'password': 'password123'
    })
    access_token = login_response.json['access_token']

    # User creates a post
    post_response = test_client.post('/posts', json={
        'title': 'User1 Post',
        'content': 'Content by user1',
        'author_id': 1
    }, headers={'Authorization': f'Bearer {access_token}'})

    # Verify post creation
    assert post_response.status_code == 201

    # Retrieve the post and verify the content
    post_id = post_response.json['id']
    get_post_response = test_client.get(f'/posts/{post_id}')
    assert get_post_response.status_code == 200
    assert get_post_response.json['title'] == 'User1 Post'
    assert get_post_response.json['content'] == 'Content by user1'