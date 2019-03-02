import time
from behave import *
from nose import tools
from features.steps.environment import Environment
from features.steps.support import PhotomosaicAccessor

import os
from PIL import Image
from io import BytesIO
import requests


accessor = PhotomosaicAccessor()


def get_image_from_response(response):
    streamer = BytesIO()
    streamer.write(response.content)
    streamer.seek(0)
    img = Image.open(streamer)
    streamer.close()
    return img


def get_image_from_path(path):
    with open(path, 'rb') as fn:
        img = Image.open(fn)
    return img


def verify_img(fp, response, message_info):
    original_size = get_image_from_path(fp).size
    print(f'original: {original_size}')
    expected = tuple(int(dim * float(message_info.get('enlargement', 1))) for dim in original_size)
    result = get_image_from_response(response)
    print(f'result: {result.size}')
    print(f'expect: {expected}')
    allow_diff = int(float(message_info.get('enlargement', 1)) * float(message_info.get('tile_size', 1)))
    max_diff = max(abs(i - j) for i, j in zip(expected, result.size))
    return max_diff < allow_diff


# Register User
@given(u'I am logged in with the {role} role')
def step_get_role(context, role):
    try:
        auth_header = context.tokens.get(role)
        if not auth_header:
            auth_header = accessor.get_auth_header(role)
        context.tokens[role] = auth_header
    except AttributeError:
        auth_header = accessor.get_auth_header(role)
        context.tokens = {role: auth_header}


@given(u'A user named "{username}" does not exist')
def step_make_sure_user_does_not_exist(context, username):
    step_get_role(context, 'admin')
    resp = accessor.delete_user(username, headers=context.tokens.get('admin', {}))
    tools.assert_equals(resp.json(), {'message': f'Deleted user: {username}'})


@then(u'An email should have been sent')
def step_check_email(context):
    tools.assert_equal(context.response.json(), {'message': f'registered {context.user_info.get("username")}'})


# Validate User
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
    context.tokens[username] = resp.json()


@then(u'I can login to the account with username "{username}"')
def step_login_user(context, username):
    payload = {'username': username, 'password': context.user_info.get('password')}
    resp = accessor.post('/validate', json=payload)
    tools.assert_equal(resp.status_code // 100, 2)
    context.status = resp.status_code
    context.tokens[username] = resp.json()

# Gallery

@given(u'I can login to an account {username}')
def step_setup_user(context, username):
    resp = accessor.create_user(username=username)
    context.response = resp
    step_ok_response(context)
    user_info = {'username': username, 'password': Environment().behave_password, 'email': Environment().behave_email}
    context.user_info = user_info
    context.tokens[username] = resp.json()


@when(u'I upload a new file {fp}')
def step_file_upload(context, fp):
    username = context.user_info.get('username')
    auth = context.tokens.get(username)
    resp = accessor.upload_file(username, fp, headers=auth)
    context.response = resp


@then(u'The status should be ok')
def step_ok_response(context):
    tools.assert_equal(context.response.status_code // 100, 2, msg=context.response.text)


@then(u'The thumbnail and image should be accessible')
def step_check_image(context):
    body = context.response.json()
    img_response = accessor.get(f'/images/{body.get("file_id")}')
    thumbnail_response = accessor.get(f'/images/{body.get("thumbnail_id")}')
    tools.assert_equal(img_response.status_code // 100, 2, "Upload image unavailable")
    tools.assert_equal(thumbnail_response.status_code // 100, 2, "Thumbnail image unavailable")


# New Gallery

@given(u'I upload a new file {fp}')
def step_given_file_upload(context, fp):
    img = get_image_from_path(fp)
    context.img_info = {'filename': os.path.basename(fp), 'size': img.size}
    step_file_upload(context, fp)
    # raise NotImplementedError(u'STEP: Given I upload a new file data/chuck.jpg')


@when(u'I send a new message with enlargement {enlargement} and tile_size {size}')
def step_send_message(context, enlargement, size):
    username = context.user_info.get('username')
    auth = context.tokens.get(username)
    context.message_info = {'enlargement': enlargement, 'tile_size': size}
    file_id = context.response.json().get('file_id')
    resp = accessor.send_message(username=username, file_id=file_id,
                                 enlargement=int(enlargement), tile_size=int(size), headers=auth)
    context.response = resp
    time.sleep(3)  # Wait for things to settle down
    step_ok_response(context)


@then(u'I can poll the pending endpoint until the job completes')
def step_poll_pending(context):
    username = context.user_info.get('username')
    start_at = time.time()
    expire_at = start_at + 240
    progress = 0.0
    auth = context.tokens.get(username)
    while progress < 1 and time.time() < expire_at:
        resp = accessor.get_pending(username=username, headers=auth)
        progress = float(resp.json().get('progress', 0.0))
        time.sleep(3)
    tools.assert_less(time.time(), expire_at, 'Ran out of time')
    print(f'Created item in {time.time() - start_at}')


@then(u'Verify the resulting gallery against {image_file}')
def step_verify_gallery(context, image_file):
    username = context.user_info.get('username')
    # img = get_image_from_path(image_file)
    # img_info = {'filename': os.path.basename(image_file), 'size': img.size}

    auth = context.tokens.get(username)
    resp = accessor.get_gallery(username, headers=auth)
    # resp = accessor.get(f'/users/{username}/gallery')
    context.response = resp
    step_ok_response(context)
    img_response = requests.get(resp.json()['results'][0]['mosaic_url'])
    context.response = img_response
    step_ok_response(context)
    tools.assert_true(verify_img(image_file, img_response, context.message_info))
