import asyncio
import asyncssh
import textfsm
import pandas as pd

jump_user = ''
jump_pass = ''
switch_user = ''
switch_pass = ''

jumper_server = {'host': '192.168.1.31', 'username': jump_user, 'password': jump_pass, 'known_hosts': None}
hosts_list = ['192.168.1.2']


async def run_client(host, command):
    async with asyncssh.connect(**jumper_server) as jump:
        async with asyncssh.connect(
                host=host,
                tunnel=jump,
                username=switch_user,
                password=switch_pass,
                known_hosts=None
                ) as connection:
            return await connection.run(command)


async def run_multiple_clients():
    global hosts_list
    tasks = list()

    for host in hosts_list:
        ip_address = host
        task = run_client(host, 'show cdp nei detail')
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
            with open("textfsm/cisco_ios_show_cdp_neighbors_detail.textfsm") as f:
                re_table = textfsm.TextFSM(f)
                output = re_table.ParseText(result.stdout)
                output = [dict(zip(re_table.header, entry)) for entry in output]
                for entry in output:
                    entry['LOCAL_IP'] = ip_address
                # audit_array = pd.DataFrame(output)
                print(output)

asyncio.run(run_multiple_clients())
