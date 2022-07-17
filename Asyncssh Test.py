import asyncio
import asyncssh
import textfsm
import pandas as pd

jump_user = 'cwmdavies'
jump_pass = '!Lepsodizle0!'
switch_user = 'chris'
switch_pass = '!Lepsodizle0!'

jumper_server = {'host': '192.168.1.31', 'username': jump_user, 'password': jump_pass, 'known_hosts': None}


async def run_client(host, username, password, command):
    async with asyncssh.connect(**jumper_server) as jump:
        async with asyncssh.connect(
                host=host,
                tunnel=jump,
                username=username,
                password=password,
                known_hosts=None
                ) as connection:
            return await connection.run(command)


async def run_multiple_clients():
    tasks = list()

    hosts_list = [
        {
            'host': '192.168.1.2',
            'username': switch_user,
            'password': switch_pass,
            'command': 'show cdp nei detail'
         },
    ]

    for host in hosts_list:

        task = run_client(host['host'], host['username'], host['password'], host['command'])
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    i = 0
    for result in results:
        i += 1
        # if the result was an Exception then I'll print it out
        if isinstance(result, Exception):
            print(f'Task {i} failed: {str(result)}')
        # if the command' exit status was not zero that means there was an error, and I'll print it out
        elif result.exit_status != 0:
            print(f'Task {i} exited with status {result.exit_status}:')
            print(result.stderr, end='')
        else:  # and the else branch for the case where was neither an Exception was raised nor an error occurred.
            # print(f'Task {i} succeeded:')
            # print(result.stdout, end='')

            with open("textfsm/cisco_ios_show_cdp_neighbors_detail.textfsm") as f:
                re_table = textfsm.TextFSM(f)
                output = re_table.ParseText(result.stdout)
                output = [dict(zip(re_table.header, entry)) for entry in output]
                audit_array = pd.DataFrame(output)
                print(audit_array)


        # print('\n')
        # print(50 * '#')


asyncio.run(run_multiple_clients())

