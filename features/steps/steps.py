import time
from behave import *
from nose import tools
from features.steps.environment import Environment
from features.steps.support import PhotomosaicAccessor
accessor = PhotomosaicAccessor()

### Register User


@given(u'A user named "{username}" does not exist')
def step_make_sure_user_does_not_exist(context, username):
    resp = accessor.delete_user(username)
    tools.assert_equals(resp.json(), {'message': f'Deleted user: {username}'})


@given(u'I register an account with username "{username}" and email "{email}"')
def step_register_account(context, username, email):
    # user_info = {'username': username, 'email': email, 'password': Environment().test_password}
    resp = accessor.register(username=username, email=email)
    print(resp.json())
    context.response = resp


@then(u'An email should have been sent')
def step_check_email(context):
    tools.assert_equal(context.response.json(), {'message': 'sent email'})


### Validate User
@given(u'A new account has just been created with username "{username}" and email "{email}"')
def step_create_new_user(context, username, email):
    resp = accessor.register(username=username, email=email)
    user_info = {
        'username': username,
        'email': email,
        'password': Environment().behave_password
    }
    context.user_info = user_info
    context.response = resp
    step_ok_response(context)


@when(u'I attempt to login as "{username}" I am stopped for not being validated')
def step_check_validation(context, username):
    pswd = context.user_info.get('password')
    resp = accessor.post('/login', json={'username': username, 'password': pswd})
    tools.assert_equal(resp.status_code, 401)
    tools.assert_equal(resp.json(), {'message': 'User not validated'})
    context.status = resp.status_code


@then(u'I validate the user "{username}"')
def step_validate_user(context, username):
    # raise NotImplementedError(u'STEP: Then I validate the user "Behave Test"')
    payload = {'username': username, 'password': context.user_info.get('password')}
    resp = accessor.post('/validate', json=payload)
    tools.assert_equal(resp.status_code // 100, 2)
    context.status = resp.status_code


@then(u'I can login to the account with username "{username}"')
def step_login_user(context, username):
    payload = {'username': username, 'password': context.user_info.get('password')}
    resp = accessor.post('/validate', json=payload)
    tools.assert_equal(resp.status_code // 100, 2)
    context.status = resp.status_code


### Gallery

@given(u'I can login to an account {username}')
def step_setup_user(context, username):
    resp = accessor.create_user(username=username)
    context.response = resp
    step_ok_response(context)
    user_info = {'username': username, 'password': Environment().behave_password, 'email': Environment().behave_email}
    context.user_info = user_info
    # resp = accessor.post('/register', json=user_info)
    # tools.assert_equal(resp.status_code // 100, 2)
    # resp = accessor.post('/validate', json={'username': username, 'password': user_info.get('password')})
    # tools.assert_equal(resp.status_code // 100, 2)
    # context.user_info = user_info


@when(u'I upload a new file {fp}')
def step_file_upload(context, fp):
    username = context.user_info.get('username')
    resp = accessor.upload_file(username, fp)
    context.response = resp
    # with open(fp, 'rb') as fn:
    #     resp = accessor.post(f'/users/{username}/uploads', files={'file': fn})
    #     context.response = resp


@then(u'The status should be ok')
def step_ok_response(context):
    tools.assert_equal(context.response.status_code // 100, 2, msg=context.response.text)
    # raise NotImplementedError(u'STEP: Then The status should be ok')


@then(u'The thumbnail and image should be accessible')
def step_check_image(context):
    body = context.response.json()
    img_response = accessor.get(f'/images/{body.get("file_id")}')
    thumbnail_response = accessor.get(f'/images/{body.get("thumbnail_id")}')
    tools.assert_equal(img_response.status_code // 100, 2, "Upload image unavailable")
    tools.assert_equal(thumbnail_response.status_code // 100, 2, "Thumbnail image unavailable")


### New Gallery

@given(u'I upload a new file {fp}')
def step_given_file_upload(context, fp):
    step_file_upload(context, fp)
    # raise NotImplementedError(u'STEP: Given I upload a new file data/chuck.jpg')


@when(u'I send a new message with enlargement {enlargement} and tile_size {size}')
def step_send_message(context, enlargement, size):
    username = context.user_info.get('username')
    file_id = context.response.json().get('file_id')
    resp = accessor.send_message(username=username, file_id=file_id,
                          enlargement=int(enlargement), tile_size=int(size))
    context.response = resp
    time.sleep(3)  # Wait for things to settle down
    step_ok_response(context)
    # raise NotImplementedError(u'STEP: When I send a new message with enlargement 1 and tile_size 8')


@then(u'I can poll the pending endpoint until the job completes')
def step_poll_pending(context):
    username = context.user_info.get('username')
    start_at = time.time()
    expire_at = start_at + 240
    progress = 0.0
    while progress < 1 and time.time() < expire_at:
        resp = accessor.get_pending(username=username)
        progress = float(resp.json().get('progress', 0.0))
    tools.assert_less(time.time(), expire_at, 'Ran out of time')
    print(f'Created item in {time.time() - start_at}')
    # raise NotImplementedError(u'STEP: Then I can poll the pending endpoint until the job completes')


@then(u'Verify the resulting gallery against {image_file}')
def step_verify_gallery(context, image_file):
    username = context.user_info.get('username')
    resp = accessor.get(f'/users/{username}/gallery')
    context.response = resp
    step_ok_response(context)
    # raise NotImplementedError(u'STEP: Then Verify the resulting gallery against data/chuck.jpg')