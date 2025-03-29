import asyncio
import argparse
import sys
from aiokef import AsyncKefSpeaker

def get_command_help():
    """Return detailed help information for all commands"""
    return {
        'turn_on': 'Turn on the speaker. No parameters required.',
        'turn_off': 'Turn off the speaker. No parameters required.',
        'get_state': 'Get the current state of the speaker. No parameters required.',
        'get_volume': 'Get the current volume. No parameters required.',
        'set_volume': 'Set the volume. Required parameter: value (float between 0.0 and 1.0)',
        'get_source': 'Get the current source. No parameters required.',
        'set_source': 'Set the source. Required parameter: value (string: "Wifi", "Bluetooth", "Aux", "Optical", "Usb")',
        'get_mode': 'Get the current DSP mode. No parameters required.',
        'mute': 'Mute the speaker. No parameters required.',
        'unmute': 'Unmute the speaker. No parameters required.',
        'increase_volume': 'Increase volume by one step. No parameters required.',
        'decrease_volume': 'Decrease volume by one step. No parameters required.',
    }

async def execute_command(speaker, command, value=None):
    """Execute a single command on the speaker"""
    commands = {
        'turn_on': speaker.turn_on,
        'turn_off': speaker.turn_off,
        'get_state': speaker.get_state,
        'get_volume': speaker.get_volume,
        'set_volume': lambda: speaker.set_volume(float(value)),
        'get_source': speaker.get_source,
        'set_source': lambda: speaker.set_source(value),
        'get_mode': speaker.get_mode,
        'mute': speaker.mute,
        'unmute': speaker.unmute,
        'increase_volume': speaker.increase_volume,
        'decrease_volume': speaker.decrease_volume,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print("Available commands:", list(commands.keys()))
        return
    
    try:
        if command.startswith('set_') and value is None:
            print(f"Error: {command} requires a value")
            return
            
        result = await commands[command]()
        if result is not None:
            print(f"{command} result: {result}")
        else:
            print(f"{command} executed successfully")
    except Exception as e:
        print(f"Error executing {command}: {e}")

async def main():
    parser = argparse.ArgumentParser(
        description='Control KEF speakers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('commands', nargs='+', help='Commands to execute (space-separated)\n\nAvailable commands and their parameters:\n' + 
        '\n'.join(f'  {cmd}: {desc}' for cmd, desc in get_command_help().items()))
    parser.add_argument('--values', nargs='*', help='Values for commands that require them (in same order as commands)')
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        return
        
    args = parser.parse_args()
    
    # Create speaker instance with the IP address of your KEF speaker
    speaker = AsyncKefSpeaker('192.168.4.47')  # Replace with your speaker's IP
    
    try:
        # Check if speaker is online
        if not await speaker.is_online():
            print("Speaker is offline. Please check the connection.")
            return

        # Process each command
        values = args.values if args.values else []
        values.extend([None] * (len(args.commands) - len(values)))  # Pad with None if not enough values
        
        for command, value in zip(args.commands, values):
            await execute_command(speaker, command, value)
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
