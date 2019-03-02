from features.steps.environment import Environment


def update_stack():
    with open('config/stack.yml', 'r') as fn:
        text = fn.read()
        text = text.replace('___BROADCAST_IP___', Environment().broadcast_ip)
    with open('stack.yml', 'w+') as fn:
        fn.write(text)


if __name__ == '__main__':
    Environment().export_environments()
    update_stack()
